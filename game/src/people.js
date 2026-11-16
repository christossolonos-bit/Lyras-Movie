import * as THREE from 'three';
import { HALL, HALL_X, HALL_Z } from './datacenter.js';
import { HL, COLD_AISLES, RACK_SLOTS, hallCenter, hallName } from './hallInterior.js';
import { getHeight, GATE_Z } from './terrain.js';
import { rng } from './noise.js';
import { stateAt } from './commute.js';
import { localClock } from './sun.js';

// Vira's staff on foot. Each person's car parks (traffic.js); they get out, walk to their
// post and work the shift: technicians at the racks, facilities engineers on equipment rounds,
// guards at the gate and on patrol, custodians sweeping, logistics unloading at the docks,
// contractors at the work zone, with a lunch break in the cafeteria. A shift's plan is a pure
// function of the person and the shift, so scrubbing the clock puts everyone where they'd be.
const MIN = 60000, WALK = 1.35;
const LANES_X = [31, 114, 198, 282, 368];                 // west road, three alleys, east lane
const LINES_Z = [-556, -257, -1, 255, 520];               // lot edge, cross roads, south end
const OPS_DOOR = [436, -381], OPS_STEP = [436, -372];     // front door of the operations building
const FENCE = { x0: 16, x1: 646, z0: GATE_Z + 4, z1: 544 };
const BOOTH = [41.6, GATE_Z + 16], ARM = [37.5, GATE_Z + 22];
// contractors' work zones in the solar field, where a cross gap meets the panel rows; work
// spots stay in the 2.4 m gaps between rows (x = 407.5 + 7k) or in the 8 m cross gap
const ZONES = [[470.5, 151], [470.5, 347]];
const zoneSpot = (zone, r) => (r() < 0.5
  ? [zone[0] + 7 * (Math.floor(r() * 5) - 2), zone[1] + (r() - 0.5) * 60]
  : [zone[0] + (r() - 0.5) * 30, zone[1] + (r() - 0.5) * 5]);
const DOCKS = [0, 1, 2, 3, 4, 5].map((i) => {             // trucks at the north ends of the first block
  const hx = HALL_X[i % 4], s = i < 4 ? -1 : 1;
  return { truck: [hx + s * 12, -504.5], door: [hx + s * 17.5, HALL_Z[0] - HALL.L / 2 - 1.5], hall: i % 4 };
});
const nearest = (arr, v) => arr.reduce((a, b) => (Math.abs(b - v) < Math.abs(a - v) ? b : a));
const OUT = -1, HIDE = -2;

// ---------- routing ----------
// Outdoors: along the lanes and cross roads (manhattan, never through a building).
function outdoor(a, b) {
  // in the solar field: out along a row gap to the cross gap and back up the other
  const zone = ZONES.find((z) => Math.abs(b[0] - z[0]) < 40 && Math.abs(b[1] - z[1]) < 40);
  if (zone && Math.abs(a[0] - zone[0]) < 40 && Math.abs(a[1] - zone[1]) < 40) return [a, [a[0], zone[1]], [b[0], zone[1]], b];
  if (zone) { const via = outdoor(a, [nearest(LANES_X, zone[0]), zone[1]]); return [...via, [b[0], zone[1]], b]; }
  if (ZONES.some((z) => Math.abs(a[0] - z[0]) < 40 && Math.abs(a[1] - z[1]) < 40)) return outdoor(b, a).reverse();
  const la = nearest(LANES_X, a[0]), lb = nearest(LANES_X, b[0]);
  if (la === lb) return [a, [la, a[1]], [la, b[1]], b];
  const zl = nearest(LINES_Z, (a[1] + b[1]) / 2);
  return [a, [la, a[1]], [la, zl], [lb, zl], [lb, b[1]], b];
}
// Inside a hall (local coords): along a corridor or the centre cross aisle, then down an aisle.
function inside(a, b) {
  const side = (x) => (Math.abs(x) > 24 ? Math.sign(x) * HL.corridorX : null);
  if (Math.abs(a[1] - b[1]) < 0.01) return [a, b];
  const cx = side(a[0]) ?? side(b[0]) ?? nearest([-HL.corridorX, 0, HL.corridorX], (a[0] + b[0]) / 2);
  return [a, [cx, a[1]], [cx, b[1]], b];
}
const hallSide = (h) => ((h % 4) < 2 ? -1 : 1);
const doorOf = (h) => { const s = hallSide(h); return { inL: [s * 29.6, HL.doorZ], outL: [s * 32.6, HL.doorZ] }; };
const toW = (h, p) => { const c = hallCenter(h); return [c.x + p[0], c.z + p[1]]; };
const toL = (h, p) => { const c = hallCenter(h); return [p[0] - c.x, p[1] - c.z]; };

// A place: { space: OUT | hall index | 'ops', p: [x, z] world }. Legs: [{ space, pts }].
function legs(a, b) {
  const out = [];
  if (a.space >= 0 && a.space === b.space) return [{ space: a.space, pts: inside(toL(a.space, a.p), toL(a.space, b.p)).map((q) => toW(a.space, q)) }];
  let from = a.p;
  if (a.space >= 0) {
    const d = doorOf(a.space);
    out.push({ space: a.space, pts: inside(toL(a.space, a.p), d.inL).map((q) => toW(a.space, q)) });
    out.push({ space: OUT, pts: [toW(a.space, d.inL), toW(a.space, d.outL)] });
    from = toW(a.space, d.outL);
  } else if (a.space === 'ops') {
    out.push({ space: OUT, pts: [OPS_DOOR, OPS_STEP] });
    from = OPS_STEP;
  }
  let to = b.p, tail = [];
  if (b.space >= 0) {
    const d = doorOf(b.space);
    to = toW(b.space, d.outL);
    tail = [{ space: OUT, pts: [to, toW(b.space, d.inL)] }, { space: b.space, pts: inside(d.inL, toL(b.space, b.p)).map((q) => toW(b.space, q)) }];
  } else if (b.space === 'ops') {
    to = OPS_STEP;
    tail = [{ space: OUT, pts: [OPS_STEP, OPS_DOOR] }];
  }
  out.push({ space: OUT, pts: outdoor(from, to) });
  return [...out, ...tail];
}

// ---------- a shift's plan ----------
// Segments: walk { t0, t1, pts, cum, len, speed, style } or act { t0, t1, x, z, h, pose }.
function polyline(pts) {
  const clean = [pts[0]];
  for (const q of pts) { const l = clean[clean.length - 1]; if (Math.hypot(q[0] - l[0], q[1] - l[1]) > 0.01) clean.push(q); }
  const cum = [0];
  for (let i = 1; i < clean.length; i++) cum.push(cum[i - 1] + Math.hypot(clean[i][0] - clean[i - 1][0], clean[i][1] - clean[i - 1][1]));
  return { pts: clean, cum, len: cum[cum.length - 1] };
}
class Plan {
  constructor(t, place) { this.segs = []; this.t = t; this.at = place; this.h = 0; }
  walk(ls, what, { style = 'walk', speed = WALK, prop = null } = {}) {
    for (const L of ls) {
      const pl = polyline(L.pts);
      if (pl.len < 0.05) continue;
      const dur = (pl.len / speed) * 1000;
      this.segs.push({ kind: 'walk', t0: this.t, t1: this.t + dur, space: L.space, ...pl, speed, style, prop, what });
      this.t += dur;
      const n = pl.pts.length;
      this.h = Math.atan2(pl.pts[n - 1][0] - pl.pts[n - 2][0], pl.pts[n - 1][1] - pl.pts[n - 2][1]);
    }
  }
  go(place, what, opt) { this.walk(legs(this.at, place), what, opt); this.at = place; }
  act(ms, pose, what, { h = this.h, prop = null } = {}) {
    const space = this.at.space === 'ops' ? HIDE : this.at.space;
    this.segs.push({ kind: 'act', t0: this.t, t1: this.t + ms, space, x: this.at.p[0], z: this.at.p[1], h, pose, prop, what });
    this.t += ms; this.h = h;
  }
  // stretch the last act so the next segment starts at t
  waitUntil(t) {
    if (t <= this.t) return;
    const s = this.segs[this.segs.length - 1];
    if (s && s.kind === 'act') { s.t1 = t; this.t = t; } else this.act(t - this.t, 'stand', 'Wrapping up');
  }
}

const carOf = (e) => ({ space: OUT, p: [e.stall.x + 1.45, e.stall.z] });
const lotEdge = (e) => ({ space: OUT, p: [e.stall.x + 1.45, LINES_Z[0]] });
const OPS = { space: 'ops', p: OPS_DOOR };
const aisleSpot = (h, r) => {
  const z = COLD_AISLES[Math.floor(r() * COLD_AISLES.length)], x = RACK_SLOTS[Math.floor(r() * RACK_SLOTS.length)];
  return { place: { space: h, p: toW(h, [x, z]) }, face: r() < 0.5 ? Math.PI : 0 }; // face the rack row on either side
};
const SECURITY_POSTS = ['gate', 'arm', 'perimeter', 'halls', 'gate', 'arm', 'perimeter', 'halls', 'campus', 'halls', 'perimeter', 'soc', 'campus', 'halls', 'perimeter', 'soc'];

export function postOf(e) {
  const j = Math.floor(e.idx / 4);
  switch (e.role) {
    case 'Data center technician': return { kind: 'tech', hall: j % 16 };
    case 'Critical facilities engineer': return { kind: 'facilities', hall: j % 16 };
    case 'Network engineer': return e.idx < 6 ? { kind: 'desk' } : { kind: 'network', hall: (e.idx * 5) % 16 };
    case 'Security officer': return { kind: SECURITY_POSTS[Math.floor(e.idx / 3) % 16], hall: (e.idx * 7) % 16 };
    case 'Custodian': return { kind: e.idx % 4 >= 3 ? 'grounds' : 'custodian', hall: (e.idx * 3) % 16 };
    case 'Logistics & receiving': return { kind: 'dock', dock: DOCKS[e.idx % 6] };
    case 'Contractor': return { kind: 'contractor', zone: ZONES[e.idx % 2] };
    default: return { kind: 'desk' }; // ops & research, cooks: offices and the kitchen in the ops building
  }
}

// One task: walk somewhere and work there. Returns nothing; advances the plan.
function task(P, post, r) {
  const m = (a, b) => (a + r() * (b - a)) * MIN;
  const H = (h) => hallName(h);
  switch (post.kind) {
    case 'tech':
    case 'network': {
      const h = post.hall, u = r();
      if (u < 0.22 && post.kind === 'tech') {
        // install: fetch a boxed server from staging, carry it to a rack
        const zs = r() < 0.5 ? -106 : 104;
        P.go({ space: h, p: toW(h, [(r() - 0.5) * 36, zs]) }, `Fetching hardware in ${H(h)}`);
        P.act(m(0.5, 1.5), 'kneel', `Unboxing a server in ${H(h)}`, { h: zs < 0 ? Math.PI : 0 });
        const s = aisleSpot(h, r);
        P.go(s.place, `Carrying a server to a rack in ${H(h)}`, { style: 'carry', prop: 'box' });
        P.act(m(8, 20), 'reach', `Racking a server in ${H(h)}`, { h: s.face });
      } else {
        const s = aisleSpot(h, r);
        P.go(s.place, `Walking to a rack in ${H(h)}`);
        const pose = u < 0.5 ? 'inspect' : u < 0.75 ? 'reach' : 'kneel';
        const what = { inspect: post.kind === 'network' ? 'Tracing a fiber link' : 'Checking alarms on a rack', reach: 'Swapping a drive', kneel: 'Re-cabling a low server' }[pose];
        P.act(m(6, 22), pose, `${what} in ${H(h)}`, { h: s.face, prop: pose === 'inspect' ? 'tablet' : null });
      }
      break;
    }
    case 'facilities': {
      const h = post.hall, c = hallCenter(h);
      if (r() < 0.6) {
        // generator yard on the hall's east side
        const z = -HALL.L / 2 + 8 + 12 * Math.floor(r() * 18);
        P.go({ space: OUT, p: [c.x + HALL.W / 2 + 6, c.z + z] }, `Rounds: generators at ${H(h)}`, { style: 'clipboard', prop: 'clipboard' });
        P.act(m(3, 9), r() < 0.35 ? 'kneel' : 'inspect', `Logging generator readings at ${H(h)}`, { h: -Math.PI / 2, prop: 'clipboard' });
      } else {
        // cooling units along the hall's walls
        const s = r() < 0.5 ? -1 : 1, z = COLD_AISLES[Math.floor(r() * COLD_AISLES.length)];
        P.go({ space: h, p: toW(h, [s * HL.corridorX, z]) }, `Rounds: cooling units in ${H(h)}`, { style: 'clipboard', prop: 'clipboard' });
        P.act(m(3, 8), 'inspect', `Checking a CRAH unit in ${H(h)}`, { h: s * Math.PI / 2, prop: 'clipboard' });
      }
      break;
    }
    case 'gate':
      P.go({ space: OUT, p: BOOTH }, 'Gatehouse');
      P.act(m(15, 35), 'post', 'On post at the gatehouse', { h: -Math.PI / 2 });
      P.go({ space: OUT, p: [BOOTH[0], BOOTH[1] - 10] }, 'Checking the gate');
      P.act(m(1, 3), 'look', 'Checking the gate', { h: Math.PI });
      break;
    case 'arm':
      P.go({ space: OUT, p: ARM }, 'Gate lane');
      P.act(m(10, 30), 'post', 'Checking badges at the lift arm', { h: -Math.PI / 2 });
      P.act(m(0.5, 2), 'radio', 'On the radio', { h: -Math.PI / 2 });
      break;
    case 'perimeter': {
      // the fence line, clockwise from the gate, with a pause at each corner
      const corners = [[FENCE.x0, FENCE.z0], [FENCE.x0, FENCE.z1], [FENCE.x1, FENCE.z1], [FENCE.x1, FENCE.z0], [FENCE.x0, FENCE.z0]];
      P.walk([{ space: OUT, pts: outdoor(P.at.p, corners[0]) }], 'Heading out on perimeter patrol');
      for (let k = 1; k < corners.length; k++) {
        P.at = { space: OUT, p: corners[k - 1] };
        P.walk([{ space: OUT, pts: [corners[k - 1], corners[k]] }], 'Perimeter patrol', { speed: 1.2 });
        P.at = { space: OUT, p: corners[k] };
        P.act(m(1, 3), 'look', 'Perimeter patrol: checking the fence');
      }
      break;
    }
    case 'halls': {
      // through a hall: in the door, down one corridor, across the staging end, back up the other
      const h = (post.hall + Math.floor(r() * 16)) % 16, s = hallSide(h);
      P.go({ space: h, p: toW(h, [s * HL.corridorX, -106]) }, `Security patrol: ${H(h)}`);
      P.go({ space: h, p: toW(h, [-s * HL.corridorX, -106]) }, `Security patrol: ${H(h)}`);
      P.go({ space: h, p: toW(h, [-s * HL.corridorX, 104]) }, `Security patrol: ${H(h)}`);
      P.act(m(0.5, 1.5), 'radio', `Calling in from ${H(h)}`);
      P.go({ space: h, p: toW(h, [s * HL.corridorX, 104]) }, `Security patrol: ${H(h)}`);
      break;
    }
    case 'campus': {
      const p = [nearest(LANES_X, 31 + r() * 340), -500 + r() * 1000];
      P.go({ space: OUT, p }, 'Campus patrol');
      P.act(m(1, 4), 'look', 'Campus patrol');
      break;
    }
    case 'custodian': {
      // sweep the length of a corridor, then mop the staging end
      const h = (post.hall + Math.floor(r() * 4)) % 16, s = r() < 0.5 ? -1 : 1;
      P.go({ space: h, p: toW(h, [s * HL.corridorX, -100]) }, `Going to clean ${H(h)}`);
      P.go({ space: h, p: toW(h, [s * HL.corridorX, 100]) }, `Sweeping ${H(h)}`, { style: 'sweep', speed: 0.3, prop: 'broom' });
      P.go({ space: h, p: toW(h, [-s * 20, 104]) }, `Mopping the staging area in ${H(h)}`, { style: 'sweep', speed: 0.22, prop: 'mop' });
      break;
    }
    case 'grounds': {
      const p = [OPS_STEP[0] - 4 - r() * 50, OPS_STEP[1] + (r() - 0.5) * 2];
      P.go({ space: OUT, p }, 'Grounds');
      P.walk([{ space: OUT, pts: [p, [p[0] - 18, p[1]]] }], 'Sweeping the walkways', { style: 'sweep', speed: 0.3, prop: 'broom' });
      P.at = { space: OUT, p: [p[0] - 18, p[1]] };
      break;
    }
    case 'dock': {
      const d = post.dock;
      P.go({ space: OUT, p: d.truck }, `Receiving at ${H(d.hall)}`);
      for (let k = 0; k < 4; k++) {
        P.at = { space: OUT, p: d.truck };
        P.act(m(0.3, 1), 'reach', `Unloading a truck at ${H(d.hall)}`, { h: Math.PI });
        P.walk([{ space: OUT, pts: [d.truck, d.door] }], `Carrying freight into ${H(d.hall)}`, { style: 'carry', prop: 'box' });
        P.at = { space: OUT, p: d.door };
        P.act(m(0.3, 0.8), 'kneel', `Stacking freight at ${H(d.hall)}`, { h: 0 });
        P.walk([{ space: OUT, pts: [d.door, d.truck] }], `Back to the truck at ${H(d.hall)}`);
      }
      P.at = { space: OUT, p: d.truck };
      P.act(m(2, 8), 'inspect', 'Checking the manifest', { prop: 'clipboard' });
      break;
    }
    case 'contractor': {
      const p = zoneSpot(post.zone, r);
      P.go({ space: OUT, p }, 'Heading out to the solar field');
      const u = r();
      if (u < 0.3) {
        const q = [p[0], post.zone[1] + (r() - 0.5) * 4];
        P.walk([{ space: OUT, pts: [p, q] }], 'Moving conduit', { style: 'carry', prop: 'box' });
        P.at = { space: OUT, p: q };
      }
      P.act(m(8, 25), u < 0.6 ? 'kneel' : u < 0.8 ? 'reach' : 'inspect', 'Running conduit in the solar field', { h: r() * Math.PI * 2 });
      break;
    }
    default: // desk: inside the ops building all shift
      P.go(OPS, 'Walking in');
      P.act(60 * MIN, 'hidden', 'At a desk in the operations building');
  }
}

function buildPlan(e, sh) {
  const ws = sh.start - e.early, we = sh.end + e.late;
  const r = rng(e.id * 7919 + Math.floor(ws / MIN));
  const post = postOf(e);
  const P = new Plan(ws, carOf(e));
  P.h = Math.PI;
  P.act(0.4 * MIN, 'stand', 'Getting out of the car');
  P.walk([{ space: OUT, pts: [carOf(e).p, lotEdge(e).p] }], 'Walking in from the lot');
  P.at = lotEdge(e);
  const ret = 32 * MIN;                                       // leave room to walk back to the car
  const desk = post.kind === 'desk' || post.kind === 'soc';
  const lunchAt = ws + (we - ws) * (0.42 + r() * 0.16);
  let lunched = we - ws < 7 * 3600000;
  let guard = 0;
  while (P.t < we - ret && guard++ < 400) {
    if (!lunched && P.t >= lunchAt) {
      lunched = true;
      if (desk) {
        P.act(30 * MIN, 'hidden', 'Lunch in the cafeteria');
      } else if (post.kind === 'contractor') {
        P.go({ space: OUT, p: [post.zone[0] - 12 + r() * 6, post.zone[1] + 2.5] }, 'Lunch');
        P.act(30 * MIN, 'sit', 'Lunch in the shade of the panels', { h: Math.PI });
      } else {
        P.go(OPS, 'Heading to the cafeteria');
        P.act(30 * MIN, 'hidden', 'Lunch in the cafeteria');
      }
      continue;
    }
    if (desk) {
      if (P.at !== OPS) P.go(OPS, 'Walking in to the operations building');
      const until = lunched ? we - ret : Math.max(P.t + MIN, lunchAt);
      P.act(until - P.t, 'hidden', post.kind === 'soc' ? 'Watching the cameras in the security office' : 'At work in the operations building');
      continue;
    }
    task(P, post, r);
  }
  // walk back out to the car, arriving as the shift's car leaves
  const back = [...legs(P.at, lotEdge(e)), { space: OUT, pts: [lotEdge(e).p, carOf(e).p] }];
  let len = 0; for (const L of back) len += polyline(L.pts).len;
  P.waitUntil(we - (len / WALK) * 1000 - 0.4 * MIN);
  P.walk(back, 'Walking back to the car');
  P.at = carOf(e);
  P.act(Math.max(0, we - P.t), 'stand', 'Getting in the car');
  return { segs: P.segs, post };
}

// ---------- figures ----------
const LOOK = {
  'Data center technician': { shirt: '#5f8fbf', pants: '#24272b', hat: null },
  'Critical facilities engineer': { shirt: '#2d3f5e', pants: '#5b5244', hat: '#f2f0e8' },
  'Network engineer': { shirt: '#6e7479', pants: '#2d3138', hat: null },
  'Security officer': { shirt: '#1c2027', pants: '#1c2027', hat: '#14171c' },
  'Custodian': { shirt: '#3d7a6c', pants: '#2b3a36', hat: null },
  'Logistics & receiving': { shirt: '#c8d63a', pants: '#2f3a4a', hat: null },
  'Contractor': { shirt: '#e0782a', pants: '#3a4a5e', hat: '#f2c51e' },
};
const SKIN = ['#f1c8a6', '#e0ac85', '#c68b62', '#a8704a', '#8a5636', '#5f3a24'];
const HAIR = ['#1b1612', '#2d2118', '#4a3322', '#7a5a3a', '#a9875a', '#cfc6b8'];
const OFFICE = ['#e9e6df', '#8aa1b8', '#6d5b7b', '#b5655b', '#3f5a48', '#c9b28c'];

function limb(w, len, d, foot = false) {
  const g = new THREE.BoxGeometry(w, len, d); g.translate(0, -len / 2, 0);
  if (!foot) return g;
  const f = new THREE.BoxGeometry(w * 1.05, 0.07, 0.24); f.translate(0, -len - 0.005, 0.05);
  const merged = new THREE.BufferGeometry();
  const parts = [g.toNonIndexed(), f.toNonIndexed()];
  for (const name of ['position', 'normal', 'uv']) {
    const arrs = parts.map((p) => p.attributes[name].array);
    const out = new Float32Array(arrs.reduce((n, a) => n + a.length, 0)); let o = 0;
    for (const a of arrs) { out.set(a, o); o += a.length; }
    merged.setAttribute(name, new THREE.BufferAttribute(out, parts[0].attributes[name].itemSize));
  }
  return merged;
}

export function buildPeople() {
  const group = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ roughness: 0.8, metalness: 0 });
  let staff = [];
  const N = 300;
  const torsoGeo = new THREE.BoxGeometry(0.38, 0.56, 0.22); torsoGeo.translate(0, 0.28, 0);
  const pelvisGeo = new THREE.BoxGeometry(0.34, 0.16, 0.21); pelvisGeo.translate(0, 0.02, 0);
  const headGeo = new THREE.SphereGeometry(0.11, 10, 8); headGeo.scale(0.9, 1.05, 1);
  const capGeo = new THREE.SphereGeometry(0.118, 10, 5, 0, Math.PI * 2, 0, Math.PI * 0.5);
  const parts = {
    torso: [torsoGeo, 1], pelvis: [pelvisGeo, 1], head: [headGeo, 1], cap: [capGeo, 1],
    upper: [limb(0.1, 0.3, 0.1), 2], fore: [limb(0.085, 0.29, 0.085), 2],
    thigh: [limb(0.14, 0.45, 0.15), 2], shin: [limb(0.12, 0.45, 0.13, true), 2],
  };
  const propGeo = {
    broom: (() => { const g = new THREE.CylinderGeometry(0.015, 0.015, 1, 5); g.translate(0, -0.5, 0); return g; })(),
    head: (() => { const g = new THREE.BoxGeometry(0.4, 0.07, 0.1); return g; })(),
    box: new THREE.BoxGeometry(0.48, 0.34, 0.4),
    clipboard: new THREE.BoxGeometry(0.24, 0.32, 0.02),
    tablet: new THREE.BoxGeometry(0.26, 0.18, 0.015),
  };
  const meshes = {};
  const mk = (name, geo, count, m = mat) => {
    const im = new THREE.InstancedMesh(geo, m, count);
    im.frustumCulled = false; im.castShadow = true; im.receiveShadow = true; im.count = 0;
    im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    im.setColorAt(0, new THREE.Color()); // allocate instanceColor
    group.add(im); meshes[name] = im;
  };
  for (const [name, [geo, k]] of Object.entries(parts)) mk(name, geo, N * k);
  mk('broom', propGeo.broom, N, new THREE.MeshStandardMaterial({ color: '#8a6a3c', roughness: 0.7 }));
  mk('broomHead', propGeo.head, N, new THREE.MeshStandardMaterial({ color: '#2a5d8a', roughness: 0.9 }));
  mk('box', propGeo.box, N, new THREE.MeshStandardMaterial({ color: '#b89a6a', roughness: 0.9 }));
  mk('clipboard', propGeo.clipboard, N, new THREE.MeshStandardMaterial({ color: '#d9d6cc', roughness: 0.8 }));
  mk('tablet', propGeo.tablet, N, new THREE.MeshStandardMaterial({ color: '#111', emissive: '#4fb8ff', emissiveIntensity: 0.6, roughness: 0.3 }));

  // the contractors' work zones: cones, barricades and stacked conduit
  const coneGeo = new THREE.ConeGeometry(0.18, 0.7, 10); coneGeo.translate(0, 0.35, 0);
  const cones = new THREE.InstancedMesh(coneGeo, new THREE.MeshStandardMaterial({ color: '#ff6a1a', roughness: 0.6 }), 48);
  const pipes = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.06, 0.06, 6, 8), new THREE.MeshStandardMaterial({ color: '#8f9498', roughness: 0.5, metalness: 0.5 }), 40);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e3 = new THREE.Euler(), v3 = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1);
  let ci = 0, pi = 0;
  for (const [zx, zz] of ZONES) {
    for (let k = 0; k < 24; k++) {
      const x = zx - 17 + (k % 12) * 3;
      cones.setMatrixAt(ci++, m4.makeTranslation(x, getHeight(x, zz), zz + (k < 12 ? -3.6 : 3.6)));
    }
    for (let k = 0; k < 20; k++) {
      q.setFromEuler(e3.set(0, 0, Math.PI / 2));
      pipes.setMatrixAt(pi++, m4.compose(v3.set(zx + 6, getHeight(zx, zz) + 0.07 + Math.floor(k / 5) * 0.12, zz - 6 + (k % 5) * 0.13 + Math.floor(k / 5) * 0.06), q, one));
    }
  }
  cones.castShadow = pipes.castShadow = true;
  group.add(cones, pipes);

  const plans = new Map(); // emp.id -> { key, segs, post }
  let following = null, currentHall = -1;
  const counts = { walking: 0, working: 0, inside: 0 };

  function planOf(e, sh) {
    let p = plans.get(e.id);
    if (!p || p.key !== sh.start) { p = { key: sh.start, ...buildPlan(e, sh) }; plans.set(e.id, p); }
    return p;
  }
  function segAt(segs, t) {
    let lo = 0, hi = segs.length - 1;
    if (!segs.length || t < segs[0].t0 || t >= segs[hi].t1) return null;
    while (lo < hi) { const m = (lo + hi + 1) >> 1; if (segs[m].t0 <= t) lo = m; else hi = m - 1; }
    return segs[lo];
  }

  // A person at t: position, heading, pose name, gait phase, prop, what they're doing.
  const where = (e, t, out) => {
    const st = e.state || stateAt(e, t);
    if (st.mode !== 'work') return null;
    const plan = planOf(e, st.shift);
    const s = segAt(plan.segs, t);
    if (!s || s.space === HIDE || s.pose === 'hidden') { out.hidden = true; out.what = s ? s.what : ''; return out; }
    out.hidden = false; out.space = s.space; out.what = s.what; out.prop = s.prop;
    if (s.kind === 'walk') {
      const d = Math.min(s.len, ((t - s.t0) / 1000) * s.speed);
      let i = 1; while (i < s.cum.length - 1 && s.cum[i] < d) i++;
      const a = s.pts[i - 1], b = s.pts[i], f = (d - s.cum[i - 1]) / ((s.cum[i] - s.cum[i - 1]) || 1);
      out.x = a[0] + (b[0] - a[0]) * f; out.z = a[1] + (b[1] - a[1]) * f;
      out.h = Math.atan2(b[0] - a[0], b[1] - a[1]);
      out.pose = s.style; out.phase = d / 0.72 * Math.PI; out.moving = true;
    } else {
      out.x = s.x; out.z = s.z; out.h = s.h; out.pose = s.pose; out.phase = 0; out.moving = false;
    }
    out.tl = (t - s.t0) / 1000;
    return out;
  };

  // ---------- poses ----------
  const P = { hipY: 0.92, lean: 0, twist: 0, head: 0, sh: [0, 0], el: [0, 0], ab: [0.06, 0.06], hip: [0, 0], kn: [0, 0] };
  function pose(w, t) {
    const ph = w.phase, sec = w.tl;
    P.hipY = 0.92; P.lean = 0.02; P.twist = 0; P.head = 0;
    P.sh[0] = P.sh[1] = 0.05; P.el[0] = P.el[1] = 0.15; P.ab[0] = P.ab[1] = 0.07;
    P.hip[0] = P.hip[1] = 0; P.kn[0] = P.kn[1] = 0.05;
    if (w.moving) {
      const a = Math.sin(ph), slow = w.pose === 'sweep' ? 0.4 : 1;
      P.hip[0] = 0.42 * a * slow; P.hip[1] = -0.42 * a * slow;
      P.kn[0] = 0.08 + 0.6 * Math.max(0, Math.sin(ph - 1.2)) * slow; P.kn[1] = 0.08 + 0.6 * Math.max(0, -Math.sin(ph - 1.2)) * slow;
      P.hipY = 0.92 - 0.025 * Math.abs(Math.cos(ph)) * slow;
      P.sh[0] = -0.38 * a; P.sh[1] = 0.38 * a; P.el[0] = P.el[1] = 0.3;
    } else {
      const sway = Math.sin(sec * 0.9 + w.seed) * 0.02;
      P.twist = sway; P.head = sway * 2;
    }
    switch (w.pose) {
      case 'carry': P.sh[0] = P.sh[1] = 0.85; P.el[0] = P.el[1] = 0.75; P.ab[0] = P.ab[1] = -0.05; break;
      case 'clipboard': P.sh[1] = 0.6; P.el[1] = 1.2; break;
      case 'sweep': {
        const s = Math.sin(sec * 2.6 + w.seed);
        P.lean = 0.16; P.twist = 0.28 * s; P.sh[0] = 0.75 + 0.2 * s; P.sh[1] = 0.55 - 0.2 * s; P.el[0] = P.el[1] = 0.5;
        P.ab[0] = P.ab[1] = -0.12; break;
      }
      case 'inspect': P.sh[0] = P.sh[1] = 0.62; P.el[0] = P.el[1] = 1.15; P.ab[0] = P.ab[1] = -0.12; P.head = 0.35; break;
      case 'reach': {
        const s = Math.sin(sec * 0.7 + w.seed);
        P.sh[1] = 1.15 + 0.35 * s; P.el[1] = 0.35; P.sh[0] = 0.75 - 0.3 * s; P.el[0] = 0.7; P.lean = 0.06; P.head = -0.1 * s; break;
      }
      case 'kneel':
        P.hipY = 0.5; P.hip[0] = 1.45; P.kn[0] = 1.5; P.hip[1] = -0.05; P.kn[1] = 1.57;
        P.lean = 0.32; P.sh[0] = P.sh[1] = 0.9 + 0.1 * Math.sin(sec * 1.3 + w.seed); P.el[0] = P.el[1] = 0.45; P.head = 0.3; break;
      case 'sit':
        P.hipY = 0.47; P.hip[0] = P.hip[1] = 1.5; P.kn[0] = P.kn[1] = 1.45; P.lean = -0.05;
        P.sh[0] = P.sh[1] = 0.45; P.el[0] = P.el[1] = 1.0; break;
      case 'post': P.sh[0] = P.sh[1] = 0.35; P.el[0] = P.el[1] = 1.45; P.ab[0] = P.ab[1] = -0.28; break;
      case 'radio': P.sh[1] = 0.4; P.el[1] = 2.3; P.ab[1] = 0.25; P.head = -0.1; break;
      case 'look': P.twist = 0.5 * Math.sin(sec * 0.4 + w.seed); P.head = -0.05; break;
    }
  }

  // ---------- matrices ----------
  const root = new THREE.Matrix4(), pel = new THREE.Matrix4(), tor = new THREE.Matrix4(), tmp = new THREE.Matrix4(), tmp2 = new THREE.Matrix4();
  const jt = [new THREE.Matrix4(), new THREE.Matrix4()], hand = [new THREE.Vector3(), new THREE.Vector3()];
  const T = (x, y, z) => tmp.makeTranslation(x, y, z);
  const Rx = (a) => tmp2.makeRotationX(a);
  const Ry = (a) => tmp2.makeRotationY(a);
  const Rz = (a) => tmp2.makeRotationZ(a);
  const slots = {};
  const put = (name, m, color) => { const im = meshes[name], i = slots[name]++; im.setMatrixAt(i, m); if (color) im.setColorAt(i, color); };
  const down = new THREE.Vector3(0, -1, 0), dir = new THREE.Vector3(), floorPt = new THREE.Vector3(), mid = new THREE.Vector3(), rootQ = new THREE.Quaternion(), sc = new THREE.Vector3();
  const pm = new THREE.Matrix4();

  function draw(e, w, y) {
    pose(w, 0);
    const s = e.look.scale;
    root.compose(v3.set(w.x, y, w.z), rootQ.setFromAxisAngle(THREE.Object3D.DEFAULT_UP, w.h), sc.set(s, s, s));
    pel.copy(root).multiply(T(0, P.hipY, 0)).multiply(Ry(P.twist * 0.3));
    put('pelvis', pel, e.look.pants);
    tor.copy(pel).multiply(T(0, 0.08, 0)).multiply(Rx(P.lean)).multiply(Ry(P.twist));
    put('torso', tor, e.look.shirt);
    const hd = jt[0].copy(tor).multiply(T(0, 0.69, 0)).multiply(Rx(P.head));
    put('head', hd, e.look.skin);
    put('cap', hd, e.look.hat);
    for (let k = 0; k < 2; k++) {
      const sd = k ? -1 : 1;
      const j = jt[k].copy(tor).multiply(T(sd * 0.245, 0.52, 0)).multiply(Rx(-P.sh[k])).multiply(Rz(sd * P.ab[k]));
      put('upper', j, e.look.shirt);
      j.multiply(T(0, -0.3, 0)).multiply(Rx(-P.el[k]));
      put('fore', j, e.look.skin);
      hand[k].setFromMatrixPosition(j.multiply(T(0, -0.29, 0)));
    }
    for (let k = 0; k < 2; k++) {
      const sd = k ? -1 : 1;
      const j = jt[k].copy(pel).multiply(T(sd * 0.1, 0, 0)).multiply(Rx(-P.hip[k]));
      put('thigh', j, e.look.pants);
      j.multiply(T(0, -0.45, 0)).multiply(Rx(P.kn[k]));
      put('shin', j, e.look.pants);
    }
    // props
    const prop = w.prop;
    if (prop === 'box') {
      mid.addVectors(hand[0], hand[1]).multiplyScalar(0.5);
      pm.compose(mid.add(dir.set(0, 0.08, 0)), rootQ, one); put('box', pm);
    } else if (prop === 'clipboard' || prop === 'tablet') {
      const hnd = prop === 'clipboard' && w.pose !== 'inspect' ? hand[1] : mid.addVectors(hand[0], hand[1]).multiplyScalar(0.5);
      q.setFromEuler(e3.set(-0.9, w.h, 0, 'YXZ'));
      pm.compose(hnd, q, one); put(prop, pm);
    } else if (prop === 'broom' || prop === 'mop') {
      // handle from the upper hand down to a point on the floor ahead
      const fwd = 0.85, sway = Math.sin(w.tl * 2.6 + e.look.seed) * 0.25;
      floorPt.set(sway, 0.03, fwd).applyQuaternion(rootQ).add(v3.set(w.x, y, w.z));
      dir.subVectors(floorPt, hand[0]); const len = dir.length(); dir.normalize();
      q.setFromUnitVectors(down, dir);
      pm.compose(hand[0], q, sc.set(1, len + 0.15, 1)); put('broom', pm);
      pm.compose(floorPt, rootQ, sc.set(prop === 'mop' ? 0.9 : 1, prop === 'mop' ? 1.4 : 1, 1)); put('broomHead', pm);
    }
  }

  const w = { seed: 0 };
  const camP = new THREE.Vector3();
  function update(t, cam, hallIndex) {
    currentHall = hallIndex;
    for (const k in meshes) slots[k] = 0;
    counts.walking = counts.working = counts.inside = 0;
    for (const e of staff) {
      e.walker = null;
      const r = where(e, t, e.wbuf);
      if (!r) continue;
      if (r.hidden) { counts.inside++; e.walker = r; continue; }
      counts[r.moving ? 'walking' : 'working']++;
      e.walker = r;
      const visible = r.space === OUT ? (r.x - cam.x) ** 2 + (r.z - cam.z) ** 2 < 1600 ** 2 : r.space === hallIndex;
      if (!visible) continue;
      w.seed = e.look.seed;
      Object.assign(w, r);
      const y = r.space === OUT ? Math.max(0, getHeight(r.x, r.z)) + 0.1 : HL.floor;
      e.wy = y;
      draw(e, w, y);
    }
    for (const k in meshes) {
      const im = meshes[k];
      im.count = slots[k];
      im.instanceMatrix.needsUpdate = true;
      if (im.instanceColor) im.instanceColor.needsUpdate = true;
    }
  }

  // ---------- follow ----------
  const camPos = new THREE.Vector3(), camLook = new THREE.Vector3();
  function followNearest(p) {
    let best = null, bd = 400 ** 2;
    for (const e of staff) {
      const r = e.walker;
      if (!r || r.hidden) continue;
      if (r.space !== OUT && r.space !== currentHall) continue;
      const d = (r.x - p.x) ** 2 + (r.z - p.z) ** 2;
      if (d < bd) { bd = d; best = e; }
    }
    following = best;
    if (best) camPos.set(Infinity, 0, 0);
    return best;
  }
  // Chase camera: over the shoulder. Returns false when there's nothing to show (they went indoors).
  function chase(camera, dt) {
    const e = following, r = e && e.walker;
    if (!r || r.hidden) return false;
    const fx = Math.sin(r.h), fz = Math.cos(r.h), y = e.wy ?? 0;
    if (r.space === OUT) camP.set(r.x - fx * 4.2 + fz * 0.9, y + 2.4, r.z - fz * 4.2 - fx * 0.9);
    // inside a hall the aisles are narrow: stay in the aisle, behind them walking, beside them at a rack
    else if (r.moving) camP.set(r.x - fx * 3.4, y + 2.3, r.z - fz * 3.4);
    else camP.set(r.x + fz * 3.4, y + 2.3, r.z - fx * 3.4);
    const k = dt > 0.5 ? 1 : 1 - Math.exp(-dt * 4);
    if (!Number.isFinite(camPos.x) || camPos.distanceTo(camP) > 60) camPos.copy(camP); else camPos.lerp(camP, k);
    camLook.set(r.x + fx * 2, y + 1.3, r.z + fz * 2);
    camera.position.copy(camPos);
    camera.lookAt(camLook);
    return true;
  }
  function describe(t) {
    const e = following;
    if (!e) return '';
    const r = e.walker;
    const doing = !r ? 'Off shift' : r.what || '';
    const st = e.state;
    return `<b>FOLLOWING</b><br>${e.name}${e.age ? `, ${e.age}` : ''}<br>${e.title || e.role}<br>${doing}` +
      (st && st.shift ? `<br>Shift ends ${localClock(new Date(st.shift.end))}` : '');
  }

  return {
    group, counts,
    // hook up the roster once traffic has built it
    setStaff(list) {
      staff = list;
      const r = rng(991);
      for (const e of staff) {
        const L = LOOK[e.role] || { shirt: OFFICE[Math.floor(r() * OFFICE.length)], pants: '#2e3238', hat: null };
        const hair = HAIR[Math.floor(r() * HAIR.length)];
        e.look = {
          shirt: new THREE.Color(L.shirt), pants: new THREE.Color(L.pants), skin: new THREE.Color(SKIN[Math.floor(r() * SKIN.length)]),
          hat: new THREE.Color(L.hat || hair), scale: 0.93 + r() * 0.12, seed: r() * 100,
        };
        e.wbuf = {};
      }
    },
    update, followNearest, chase, describe,
    get following() { return following; },
    unfollow() { following = null; },
    // for tests: the plan an employee is working through right now
    planFor(e, t) { const st = stateAt(e, t); return st.mode === 'work' ? planOf(e, st.shift) : null; },
  };
}
