// World layout, road network and the terrain height/color functions.
// Pure math (no three.js) so the terrain worker threads can import it.
import { fbm, ridged, smoothstep } from './noise.js';

// World units are meters. Vira sits at the origin; north is -z.
export const MILE = 1609.344;
export const TOWN_Z = -Math.round(40 * MILE);   // Saltbrush, Marcus's town, 40 miles north of Vira
export const GATE_Z = -650;                      // Vira's front gate
export const ROAD_START = TOWN_Z - 1700;          // highway runs on past the north end of Saltbrush
export const ROAD_END = GATE_Z;
const ROAD_A = TOWN_Z + 1300;
const ROAD_B = GATE_Z - 500;

export const WORLD = { x0: -140000, x1: 80000, z0: -125000, z1: 60000 };

// Halcyon, Nova's city: a metropolis on a flat basin floor (ellipse), hills all around.
export const HALCYON = { x: -80000, z: -8000, rx: 7500, rz: 6000 };
export const CITY_GRID = 140; // street pitch (120 m blocks, 20 m streets)
export const FREEWAY_Z = HALCYON.z + 2 * CITY_GRID; // elevated freeway runs over this street

// Ironwood, Juno's city: a railroad and repair town in granite boulder hills, 40 miles northeast.
export const IRONWOOD = { x: 52000, z: -38000, rx: 3800, rz: 3000 };
export const IRON_GRID = 100;                    // older, tighter street grid
export const RAIL_Z = IRONWOOD.z + 400;          // main line runs east-west along this street

export function roadX(z) {
  if (z <= ROAD_A || z >= ROAD_B) return 0;
  let t = (z - ROAD_A) / (ROAD_B - ROAD_A);
  t = t * t * (3 - 2 * t);
  return 2300 * Math.sin(2 * Math.PI * t) * Math.sin(Math.PI * t) + 420 * Math.sin(6 * Math.PI * t);
}

// ---------- polylines ----------

function catmull(ctrl, step) {
  const out = [];
  const P = [ctrl[0], ...ctrl, ctrl[ctrl.length - 1]];
  for (let i = 1; i < P.length - 2; i++) {
    const [p0, p1, p2, p3] = [P[i - 1], P[i], P[i + 1], P[i + 2]];
    const n = Math.max(1, Math.ceil(Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step));
    for (let k = 0; k < n; k++) {
      const t = k / n, t2 = t * t, t3 = t2 * t;
      const f = (a, b, c, d) => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
      out.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]);
    }
  }
  out.push(ctrl[ctrl.length - 1]);
  return out;
}

function saltbrushPath(step) {
  const pts = [];
  for (let z = ROAD_START; z < ROAD_END; z += step) pts.push([roadX(z), z]);
  pts.push([roadX(ROAD_END), ROAD_END]);
  return pts;
}

// Interstate from the Saltbrush highway (just north of Vira) west through the range to Halcyon.
const JZ = -2600;
const HALCYON_CTRL = [
  [roadX(JZ), JZ], [roadX(JZ) - 900, JZ - 40], [-3500, -3000], [-7000, -4200], [-12000, -5200],
  [-20000, -4600], [-30000, -6200], [-40000, -5400], [-50000, -7400], [-58000, -8200],
  [-65000, -7900], [-70000, FREEWAY_Z], [-71500, FREEWAY_Z],
];
export const HALCYON_JUNCTION = [roadX(JZ), JZ];

// Nova's house on the hills above the north side of Halcyon, and the switchback road up to it.
export const NOVA_PAD = { x: HALCYON.x + 1200, z: HALCYON.z - 7440, r: 60 };
const NOVA_CTRL = [
  [HALCYON.x + 600, HALCYON.z - 5640], [HALCYON.x + 950, HALCYON.z - 6080], [HALCYON.x + 1550, HALCYON.z - 6330],
  [HALCYON.x + 820, HALCYON.z - 6680], [HALCYON.x + 1700, HALCYON.z - 7010], [HALCYON.x + 1080, HALCYON.z - 7250],
  [NOVA_PAD.x - 30, NOVA_PAD.z + 40],
];

// State highway from the Saltbrush highway (north of Vira) northeast to Ironwood: Juno's route.
const IZ = -12000;
const IRONWOOD_CTRL = [
  [roadX(IZ), IZ], [roadX(IZ) + 900, IZ - 100], [6000, -14500], [14000, -18000], [24000, -22000],
  [33000, -27500], [41000, -33000], [46000, -36500], [48300, -37900], [48900, IRONWOOD.z],
];
export const IRONWOOD_JUNCTION = [roadX(IZ), IZ];

// Juno's loft up on the rocky edge of town, and the dirt drive to it.
export const JUNO_PAD = { x: IRONWOOD.x + 2600, z: IRONWOOD.z - 3500, r: 40 };
const JUNO_CTRL = [
  [IRONWOOD.x + 1700, IRONWOOD.z - 2400], [IRONWOOD.x + 2050, IRONWOOD.z - 2800],
  [IRONWOOD.x + 2380, IRONWOOD.z - 3120], [JUNO_PAD.x - 25, JUNO_PAD.z + 30],
];

export function roadPolyline(id, step = 8) {
  if (id === 'saltbrush') return saltbrushPath(step);
  if (id === 'halcyon') return catmull(HALCYON_CTRL, step);
  if (id === 'novahill') return catmull(NOVA_CTRL, step);
  if (id === 'ironwood') return catmull(IRONWOOD_CTRL, step);
  if (id === 'junodrive') return catmull(JUNO_CTRL, step);
  if (id === 'rail') { const p = []; for (let x = 22000; x <= 78000; x += step) p.push([x, RAIL_Z]); return p; }
  throw new Error(id);
}
const SHAPING = ['saltbrush', 'halcyon', 'ironwood', 'rail'];

// ---------- spatial queries ----------

let init = false;
let shapeSegs, segHash, farRaster, local;
const CELL = 1000, RAST = 1000;
const RW = Math.ceil((WORLD.x1 - WORLD.x0) / RAST) + 1, RH = Math.ceil((WORLD.z1 - WORLD.z0) / RAST) + 1;
export let NOVA_ELEV = 0;
export let JUNO_ELEV = 0;

let segT = 0; // parameter of the closest point from the last segDist call
function segDist(px, pz, ax, az, bx, bz) {
  const dx = bx - ax, dz = bz - az;
  const L2 = dx * dx + dz * dz;
  let t = L2 > 0 ? ((px - ax) * dx + (pz - az) * dz) / L2 : 0;
  t = t < 0 ? 0 : t > 1 ? 1 : t;
  segT = t;
  const qx = ax + dx * t - px, qz = az + dz * t - pz;
  return Math.sqrt(qx * qx + qz * qz);
}

function ensureInit() {
  if (init) return;
  init = true;
  // shaping roads (desert highways at grade 0), 40 m segments in a hash
  shapeSegs = [];
  for (const id of SHAPING) {
    const p = roadPolyline(id, 40);
    for (let i = 0; i < p.length - 1; i++) shapeSegs.push([p[i][0], p[i][1], p[i + 1][0], p[i + 1][1]]);
  }
  segHash = new Map();
  shapeSegs.forEach((s, i) => {
    const x0 = Math.floor(Math.min(s[0], s[2]) / CELL), x1 = Math.floor(Math.max(s[0], s[2]) / CELL);
    const z0 = Math.floor(Math.min(s[1], s[3]) / CELL), z1 = Math.floor(Math.max(s[1], s[3]) / CELL);
    for (let cx = x0; cx <= x1; cx++) for (let cz = z0; cz <= z1; cz++) {
      const k = cx * 100003 + cz;
      if (!segHash.has(k)) segHash.set(k, []);
      segHash.get(k).push(i);
    }
  });
  // coarse distance raster for far-field shaping
  const coarse = [];
  for (const id of SHAPING) {
    const p = roadPolyline(id, 400);
    for (let i = 0; i < p.length - 1; i++) coarse.push([p[i][0], p[i][1], p[i + 1][0], p[i + 1][1]]);
  }
  farRaster = new Float32Array(RW * RH);
  for (let j = 0; j < RH; j++) for (let i = 0; i < RW; i++) {
    const x = WORLD.x0 + i * RAST, z = WORLD.z0 + j * RAST;
    let d = 1e9;
    for (const s of coarse) {
      // coarse segments are 400 m long chords of the road
      const dd = segDist(x, z, s[0], s[1], s[2], s[3]);
      if (dd < d) d = dd;
    }
    farRaster[j * RW + i] = d;
  }

  // local (graded) roads up to the hillside homes, each with its own elevation profile
  NOVA_ELEV = baseHeight(NOVA_PAD.x, NOVA_PAD.z) + 4;
  JUNO_ELEV = baseHeight(JUNO_PAD.x, JUNO_PAD.z) + 2;
  const graded = (id, top, inner, outer) => {
    const pts = roadPolyline(id, 10);
    let L = 0; const acc = [0];
    for (let i = 1; i < pts.length; i++) { L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); acc.push(L); }
    const elev = acc.map((a) => { const t = a / L; return top * (t * t * (3 - 2 * t) * 0.35 + t * 0.65); });
    let bx0 = 1e9, bx1 = -1e9, bz0 = 1e9, bz1 = -1e9;
    for (const [x, z] of pts) { bx0 = Math.min(bx0, x); bx1 = Math.max(bx1, x); bz0 = Math.min(bz0, z); bz1 = Math.max(bz1, z); }
    return { id, pts, elev, box: [bx0 - 200, bx1 + 200, bz0 - 200, bz1 + 200], inner, outer };
  };
  local = [graded('novahill', NOVA_ELEV, 14, 60), graded('junodrive', JUNO_ELEV, 10, 45)];
}

export function localRoadProfile(id) { ensureInit(); return local.find((r) => r.id === id) || null; }

// Distance to the nearest desert highway.
export function roadDistance(x, z) {
  ensureInit();
  const fx = (x - WORLD.x0) / RAST, fz = (z - WORLD.z0) / RAST;
  const i = Math.max(0, Math.min(RW - 2, Math.floor(fx))), j = Math.max(0, Math.min(RH - 2, Math.floor(fz)));
  const u = Math.min(1, Math.max(0, fx - i)), v = Math.min(1, Math.max(0, fz - j));
  const far = (farRaster[j * RW + i] * (1 - u) + farRaster[j * RW + i + 1] * u) * (1 - v) + (farRaster[(j + 1) * RW + i] * (1 - u) + farRaster[(j + 1) * RW + i + 1] * u) * v;
  if (far > 1800) return far; // bilinear error on a 1 km grid is under ~710 m
  const cx = Math.floor(x / CELL), cz = Math.floor(z / CELL);
  let d = 1e9;
  for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) {
    const list = segHash.get((cx + a) * 100003 + (cz + b));
    if (!list) continue;
    for (const k of list) { const s = shapeSegs[k]; const dd = segDist(x, z, s[0], s[1], s[2], s[3]); if (dd < d) d = dd; }
  }
  return d < 1000 ? d : Math.max(far, 1000);
}

function localRoad(x, z) {
  for (const r of local) {
    const [x0, x1, z0, z1] = r.box;
    if (x < x0 || x > x1 || z < z0 || z > z1) continue;
    let best = 1e9, elev = 0;
    for (let i = 0; i < r.pts.length - 1; i++) {
      const a = r.pts[i], b = r.pts[i + 1];
      const d = segDist(x, z, a[0], a[1], b[0], b[1]);
      if (d < best) { best = d; elev = r.elev[i] + (r.elev[i + 1] - r.elev[i]) * segT; }
    }
    if (best < r.outer) return { d: best, elev, r };
  }
  return null;
}

// ---------- sites and terrain shape ----------

const DC_C = [600, 500], DC_R = 2000;
const TOWN_R = 1800;

export function halcyonE(x, z) { return Math.hypot((x - HALCYON.x) / HALCYON.rx, (z - HALCYON.z) / HALCYON.rz); }
export function ironwoodE(x, z) { return Math.hypot((x - IRONWOOD.x) / IRONWOOD.rx, (z - IRONWOOD.z) / IRONWOOD.rz); }

function baseHeight(x, z) {
  const dRoad = roadDistance(x, z);
  const eH = halcyonE(x, z), eI = ironwoodE(x, z);
  const dSite = Math.min(Math.hypot(x - DC_C[0], z - DC_C[1]) - DC_R, Math.hypot(x, z - TOWN_Z) - TOWN_R, (eH - 1) * 6000, (eI - 1) * 3000);
  const siteMask = smoothstep(0, 900, dSite);
  const flat = Math.min(siteMask, smoothstep(250, 900, dRoad));

  let h = (fbm(x * 0.00035 + 11, z * 0.00035 - 4, 4) - 0.5) * 36 * flat;
  h += (fbm(x * 0.004, z * 0.004, 3) - 0.5) * 3 * flat;

  const nearH = smoothstep(1.9, 2.8, eH), nearI = smoothstep(1.8, 2.7, eI);
  const nearCity = Math.min(nearH, nearI);
  const far = Math.max(smoothstep(4000, 12000, dRoad), smoothstep(2600, 8000, z), smoothstep(2500, 8000, TOWN_Z - z)) * nearCity;
  const mMask = far * siteMask;
  if (mMask > 0) {
    const r = ridged(x * 0.00022, z * 0.00022, 7);
    const base = fbm(x * 0.00008 + 3, z * 0.00008 + 9, 3);
    h += mMask * (120 + r * 1300 * (0.5 + base)) * smoothstep(0, 0.35, mMask);
  }
  // Halcyon's hills: rounded, chaparral-covered, rising from the basin floor
  if (eH < 3) {
    const band = smoothstep(1.0, 1.38, eH) * (1 - nearH * 0.6);
    const roll = 0.55 + 0.7 * fbm(x * 0.0006 + 20, z * 0.0006 - 7, 4);
    h += band * (230 + 120 * fbm(x * 0.00025, z * 0.00025, 2)) * roll * smoothstep(200, 1100, dRoad);
  }
  // Ironwood's hills: granite domes and boulder piles
  if (eI < 3) {
    const band = smoothstep(1.0, 1.3, eI) * (1 - nearI * 0.6);
    const dome = ridged(x * 0.0009 + 5, z * 0.0009 - 3, 5) * (0.5 + fbm(x * 0.0004, z * 0.0004, 3));
    const bumps = Math.pow(fbm(x * 0.012, z * 0.012, 2), 3) * 22;
    h += band * (60 + 190 * dome + bumps) * smoothstep(200, 1100, dRoad);
  }
  const hill = smoothstep(0.58, 0.75, fbm(x * 0.00013 + 40, z * 0.00013 - 17, 4)) * smoothstep(1200, 2500, dRoad) * siteMask * (1 - far) * nearCity;
  if (hill > 0) h += hill * (180 + ridged(x * 0.0006, z * 0.0006, 6) * 380);
  return h;
}

export function heightAt(x, z) {
  ensureInit();
  let h = baseHeight(x, z);
  const lr = localRoad(x, z);
  if (lr) h += (lr.elev - h) * (1 - smoothstep(lr.r.inner, lr.r.outer, lr.d));
  for (const [P, E] of [[NOVA_PAD, NOVA_ELEV], [JUNO_PAD, JUNO_ELEV]]) {
    const dp = Math.hypot(x - P.x, z - P.z);
    if (dp < P.r * 2.2) h += (E - h) * (1 - smoothstep(P.r, P.r * 2.2, dp));
  }
  return h;
}

// ---------- terrain color ----------

const C = (h) => [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255].map((v) => Math.pow(v, 2.2));
const SAND_A = C(0xd2ad80), SAND_B = C(0xb78d60), PLAYA = C(0xe0d2b6), VARNISH = C(0x7d5a42);
const ROCK_A = C(0xa86d4d), ROCK_B = C(0x5c3b2b), CHAP_A = C(0x7a7650), CHAP_B = C(0x5d5a3a);
const GRANITE_A = C(0xc2b49a), GRANITE_B = C(0x9a8b74), PINYON = C(0x4a5534);
const lerp3 = (o, a, t) => { o[0] += (a[0] - o[0]) * t; o[1] += (a[1] - o[1]) * t; o[2] += (a[2] - o[2]) * t; };

export function terrainColor(x, z, h, slope, out) {
  out[0] = SAND_A[0]; out[1] = SAND_A[1]; out[2] = SAND_A[2];
  lerp3(out, SAND_B, fbm(x * 0.0015, z * 0.0015, 3));
  lerp3(out, PLAYA, smoothstep(0.34, 0.24, fbm(x * 0.00009 + 5, z * 0.00009 + 5, 3)) * 0.8);
  lerp3(out, VARNISH, smoothstep(0.6, 0.75, fbm(x * 0.0004 - 8, z * 0.0004, 3)) * 0.35);
  const eH = halcyonE(x, z);
  if (eH > 0.98 && eH < 2.6) {
    const veg = smoothstep(0.98, 1.1, eH) * (1 - smoothstep(2.0, 2.6, eH));
    const c = [CHAP_A[0], CHAP_A[1], CHAP_A[2]];
    lerp3(c, CHAP_B, fbm(x * 0.003, z * 0.003, 3));
    lerp3(out, c, veg * (0.55 + 0.35 * fbm(x * 0.001 + 4, z * 0.001, 3)));
  }
  const eI = ironwoodE(x, z);
  if (eI > 0.98 && eI < 2.6) {
    const band = smoothstep(0.98, 1.08, eI) * (1 - smoothstep(2.0, 2.6, eI));
    const g = [GRANITE_A[0], GRANITE_A[1], GRANITE_A[2]];
    lerp3(g, GRANITE_B, fbm(x * 0.004, z * 0.004, 3));
    lerp3(g, PINYON, smoothstep(0.55, 0.75, fbm(x * 0.02 + 3, z * 0.02, 2)) * 0.7);
    lerp3(out, g, band * 0.9);
  }
  const r = [ROCK_A[0], ROCK_A[1], ROCK_A[2]];
  lerp3(r, ROCK_B, Math.min(1, fbm(x * 0.002 + 9, z * 0.002, 3) * 1.2));
  const soft = eH < 2.4 || eI < 2.4;
  lerp3(out, r, Math.max(smoothstep(0.12, 0.45, slope) * (soft ? 0.45 : 1), smoothstep(40, 260, h) * 0.85 * (soft ? 0.3 : 1)));
  return out;
}

// ---------- mesh data for a terrain tile (runs in workers) ----------

export const TILE = 4000;

export function tileData(tx, tz, segs, skirt) {
  ensureInit();
  const s = TILE / segs, n = segs + 1, nb = segs + 3;
  const x0 = tx * TILE, z0 = tz * TILE;
  const H = new Float32Array(nb * nb);
  for (let j = 0; j < nb; j++) for (let i = 0; i < nb; i++) H[j * nb + i] = heightAt(x0 + (i - 1) * s, z0 + (j - 1) * s);
  return buildGrid(H, nb, n, segs, s, x0, z0, skirt);
}

export function farData(step) {
  ensureInit();
  const nx = Math.round((WORLD.x1 - WORLD.x0) / step), nz = Math.round((WORLD.z1 - WORLD.z0) / step);
  const nbx = nx + 3, nbz = nz + 3;
  const H = new Float32Array(nbx * nbz);
  for (let j = 0; j < nbz; j++) for (let i = 0; i < nbx; i++) H[j * nbx + i] = heightAt(WORLD.x0 + (i - 1) * step, WORLD.z0 + (j - 1) * step);
  return buildGridRect(H, nbx, nx, nz, step, WORLD.x0, WORLD.z0);
}

function buildGrid(H, nb, n, segs, s, x0, z0, skirt) {
  const per = [];
  for (let i = 0; i < segs; i++) per.push([i, 0]);
  for (let j = 0; j < segs; j++) per.push([segs, j]);
  for (let i = segs; i > 0; i--) per.push([i, segs]);
  for (let j = segs; j > 0; j--) per.push([0, j]);
  const vCount = n * n + per.length;
  const pos = new Float32Array(vCount * 3), nor = new Float32Array(vCount * 3), col = new Float32Array(vCount * 3), uv = new Float32Array(vCount * 2);
  const heights = new Float32Array(n * n);
  const c = [0, 0, 0];
  const put = (k, i, j, dy) => {
    const x = x0 + i * s, z = z0 + j * s, h = H[(j + 1) * nb + i + 1];
    const dx = (H[(j + 1) * nb + i + 2] - H[(j + 1) * nb + i]) / (2 * s);
    const dz = (H[(j + 2) * nb + i + 1] - H[j * nb + i + 1]) / (2 * s);
    const l = Math.hypot(dx, 1, dz);
    pos[k * 3] = x; pos[k * 3 + 1] = h - dy; pos[k * 3 + 2] = z;
    nor[k * 3] = -dx / l; nor[k * 3 + 1] = 1 / l; nor[k * 3 + 2] = -dz / l;
    terrainColor(x, z, h, Math.hypot(dx, dz), c);
    col[k * 3] = c[0]; col[k * 3 + 1] = c[1]; col[k * 3 + 2] = c[2];
    uv[k * 2] = x / 6; uv[k * 2 + 1] = z / 6;
    return h;
  };
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) heights[j * n + i] = put(j * n + i, i, j, 0);
  per.forEach(([i, j], k) => put(n * n + k, i, j, skirt));
  const idx = new Uint32Array(segs * segs * 6 + per.length * 6);
  let p = 0;
  for (let j = 0; j < segs; j++) for (let i = 0; i < segs; i++) {
    const a = j * n + i, b = a + 1, cc = a + n, d = cc + 1;
    idx[p++] = a; idx[p++] = cc; idx[p++] = b;
    idx[p++] = b; idx[p++] = cc; idx[p++] = d;
  }
  const L = per.length;
  for (let k = 0; k < L; k++) {
    const [ia, ja] = per[k], [ib, jb] = per[(k + 1) % L];
    const a = ja * n + ia, b = jb * n + ib, sa = n * n + k, sb = n * n + (k + 1) % L;
    idx[p++] = a; idx[p++] = b; idx[p++] = sb;
    idx[p++] = a; idx[p++] = sb; idx[p++] = sa;
  }
  return { pos, nor, col, uv, idx, heights, n, s, x0, z0 };
}

function buildGridRect(H, nbx, nx, nz, s, x0, z0) {
  const W = nx + 1, vCount = W * (nz + 1);
  const pos = new Float32Array(vCount * 3), nor = new Float32Array(vCount * 3), col = new Float32Array(vCount * 3), uv = new Float32Array(vCount * 2);
  const c = [0, 0, 0];
  for (let j = 0; j <= nz; j++) for (let i = 0; i <= nx; i++) {
    const k = j * W + i, x = x0 + i * s, z = z0 + j * s, h = H[(j + 1) * nbx + i + 1];
    const dx = (H[(j + 1) * nbx + i + 2] - H[(j + 1) * nbx + i]) / (2 * s);
    const dz = (H[(j + 2) * nbx + i + 1] - H[j * nbx + i + 1]) / (2 * s);
    const l = Math.hypot(dx, 1, dz);
    pos[k * 3] = x; pos[k * 3 + 1] = h; pos[k * 3 + 2] = z;
    nor[k * 3] = -dx / l; nor[k * 3 + 1] = 1 / l; nor[k * 3 + 2] = -dz / l;
    terrainColor(x, z, h, Math.hypot(dx, dz), c);
    col[k * 3] = c[0]; col[k * 3 + 1] = c[1]; col[k * 3 + 2] = c[2];
    uv[k * 2] = x / 6; uv[k * 2 + 1] = z / 6;
  }
  const idx = new Uint32Array(nx * nz * 6);
  let p = 0;
  for (let j = 0; j < nz; j++) for (let i = 0; i < nx; i++) {
    const a = j * W + i, b = a + 1, cc = a + W, d = cc + 1;
    idx[p++] = a; idx[p++] = cc; idx[p++] = b;
    idx[p++] = b; idx[p++] = cc; idx[p++] = d;
  }
  return { pos, nor, col, uv, idx };
}
