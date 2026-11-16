// Vira's workforce: who works there, when, where they live, and the route they drive.
// Everything is a pure function of the world clock, so scrubbing or fast-forwarding time
// puts every car exactly where it would be.
import { roadPolyline, HALCYON, IRONWOOD, IRON_GRID, FREEWAY_Z, ROAD_START } from './heightfield.js';
import { HOMES, VIRA_STALLS } from './homes.js';
import { rng } from './noise.js';
import { freewayY, FREEWAY_X0, FREEWAY_X1 } from './city.js';

// ---------- staffing ----------
// A 16-hall hyperscale campus runs 24/7 with a few hundred people. Operations crews work
// 12-hour rotating shifts (2-2-3 "Pitman" pattern: two crews on days, two on nights),
// security works 8-hour shifts around the clock, and office, kitchen, logistics and
// contractors keep weekday hours.
export const ROLES = [
  { role: 'Critical facilities engineer', n: 72, sched: 'rot12' },
  { role: 'Data center technician', n: 64, sched: 'rot12' },
  { role: 'Network engineer', n: 12, sched: 'office', start: 8, len: 9 },
  { role: 'Security officer', n: 48, sched: 'sec8' },
  { role: 'Operations & research staff', n: 30, sched: 'office', start: 8, len: 9 },
  { role: 'Custodian', n: 16, sched: 'janitor' },
  { role: 'Cafeteria cook', n: 8, sched: 'office', start: 6, len: 9 },
  { role: 'Logistics & receiving', n: 10, sched: 'office', start: 7, len: 9 },
  { role: 'Contractor', n: 20, sched: 'office', start: 7, len: 8.5 },
];
// Where they live (share of staff): Marcus's town is closest; Halcyon is the long drive.
const CITY_SHARE = [['saltbrush', 0.45], ['ironwood', 0.35], ['halcyon', 0.2]];
export const CITY_NAMES = { saltbrush: 'Saltbrush', ironwood: 'Ironwood', halcyon: 'Halcyon' };

const FIRST = ['Dana', 'Luis', 'Kara', 'Mateo', 'Priya', 'Owen', 'Rosa', 'Darnell', 'Mei', 'Caleb', 'Ines', 'Tyler', 'Amara', 'Wes', 'Lena', 'Jorge', 'Hana', 'Ray', 'Talia', 'Grant',
  'Sofia', 'Malik', 'Erin', 'Victor', 'Noor', 'Cody', 'Yesenia', 'Brett', 'Kim', 'Andre', 'Lucia', 'Hector', 'Jada', 'Pete', 'Alma', 'Sam', 'Tess', 'Omar', 'Rhea', 'Gus',
  'Nadia', 'Eli', 'Paloma', 'Trent', 'Joy', 'Ramon', 'Bea', 'Felix', 'Iris', 'Dale', 'Marisol', 'Kofi', 'Wren', 'Ruben', 'Tara', 'Abe', 'Leti', 'Shane', 'Ivy', 'Nico'];
const LAST = ['Ruiz', 'Okafor', 'Brennan', 'Castillo', 'Nguyen', 'Harlan', 'Mendez', 'Pruitt', 'Tanaka', 'Whitcomb', 'Salas', 'Delgado', 'Kowalski', 'Begay', 'Holt', 'Vargas',
  'Lindqvist', 'Abara', 'Coyle', 'Ferreira', 'Jaramillo', 'Stroud', 'Patel', 'Yazzie', 'McAllister', 'Rojas', 'Petrov', 'Garza', 'Hendricks', 'Acosta', 'Barlow', 'Quintero',
  'Sato', 'Dunlap', 'Ochoa', 'Pryor', 'Navarro', 'Ellison', 'Fuentes', 'Kincaid'];
const KINDS = [['sedan', 0.38], ['suv', 0.3], ['pickup', 0.27], ['van', 0.05]];
const PAINT = ['#f2f2f0', '#f2f2f0', '#e9e9e6', '#c9ccd0', '#b4b8bd', '#2b2d31', '#1d1e20', '#8d1f1f', '#1f3c6b', '#6f7378', '#d8cfb8', '#3d5a3a', '#7a6a55', '#5a1e1e', '#2f4f6f'];

// ---------- Death Valley calendar ----------
const DAY = 86400000, HOUR = 3600000, MIN = 60000;
const fmt = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Los_Angeles', year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric', hourCycle: 'h23' });
const offCache = new Map();
function tzOffset(t) {
  const key = Math.floor(t / (30 * MIN));
  if (offCache.has(key)) return offCache.get(key);
  const p = {};
  for (const x of fmt.formatToParts(new Date(t))) p[x.type] = x.value;
  const off = Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute, +p.second) - Math.floor(t / 1000) * 1000;
  offCache.set(key, off);
  return off;
}
export const dayIndex = (t) => Math.floor((t + tzOffset(t)) / DAY);
const dayStart = (d) => d * DAY - tzOffset(d * DAY + 12 * HOUR);
const dayOfWeek = (d) => (d + 4) % 7; // 0 = Sunday (day 0 of the epoch was a Thursday)

const PITMAN = [1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0];
const CREWS = ['A', 'B', 'C', 'D'];

// The shift an employee works on a given local day, or null for a day off.
export function shiftFor(emp, d) {
  const at = (h) => dayStart(d) + h * HOUR;
  switch (emp.sched) {
    case 'rot12': {
      const p = PITMAN[((d % 14) + 14) % 14];
      const on = emp.crew % 2 === 0 ? p : 1 - p;
      if (!on) return null;
      return emp.crew < 2 ? { start: at(6), end: at(18), label: 'day 6 AM - 6 PM' } : { start: at(18), end: at(30), label: 'night 6 PM - 6 AM' };
    }
    case 'sec8': {
      if (((d + emp.idx) % 7 + 7) % 7 >= 5) return null;
      const h = [6, 14, 22][emp.idx % 3];
      return { start: at(h), end: at(h + 8), label: ['6 AM - 2 PM', '2 PM - 10 PM', '10 PM - 6 AM'][emp.idx % 3] };
    }
    case 'janitor': {
      if (((d + emp.idx) % 7 + 7) % 7 >= 5) return null;
      const h = emp.idx % 2 ? 14.5 : 6;
      return { start: at(h), end: at(h + 8.5), label: emp.idx % 2 ? '2:30 PM - 11 PM' : '6 AM - 2:30 PM' };
    }
    default: {
      const w = dayOfWeek(d);
      if (w === 0 || w === 6) return null;
      const h = emp.start + emp.jitter;
      return { start: at(h), end: at(h + emp.len), label: 'weekdays' };
    }
  }
}

// Where an employee is at time t: home, driving in, at work, or driving home.
export function stateAt(emp, t) {
  const d = dayIndex(t);
  for (const day of [d - 1, d, d + 1]) {
    const sh = shiftFor(emp, day);
    if (!sh) continue;
    const ws = sh.start - emp.early, we = sh.end + emp.late, dur = emp.route.duration;
    if (t >= ws - dur && t < ws) return { mode: 'toWork', tau: t - (ws - dur), shift: sh, eta: ws - t };
    if (t >= ws && t < we) return { mode: 'work', shift: sh };
    if (t >= we && t < we + dur) return { mode: 'toHome', tau: t - we, shift: sh, eta: we + dur - t };
  }
  return { mode: 'home' };
}

export function nextShift(emp, t) {
  const d = dayIndex(t);
  for (let day = d; day < d + 10; day++) {
    const sh = shiftFor(emp, day);
    if (sh && sh.start - emp.early - emp.route.duration > t) return sh;
  }
  return null;
}

// ---------- routes ----------
// A route is a chain of legs; each leg runs along part of a polyline at one speed, in the
// right-hand lane (lane = offset to the right of travel, meters), at a road height.
function cumulative(pts) {
  const c = new Float64Array(pts.length);
  for (let i = 1; i < pts.length; i++) c[i] = c[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  return c;
}
const shared = {};
function sharedLine(id) {
  if (!shared[id]) { const pts = roadPolyline(id, 8); shared[id] = { pts, cum: cumulative(pts) }; }
  return shared[id];
}
function leg(line, i0, i1, speed, lane, y) {
  return { pts: line.pts, cum: line.cum, i0, i1, dir: i1 >= i0 ? 1 : -1, len: Math.abs(line.cum[i1] - line.cum[i0]), speed, lane, y };
}
function own(points, speed, lane, y) {
  const line = { pts: points, cum: cumulative(points) };
  return leg(line, 0, points.length - 1, speed, lane, y);
}
const reverseLeg = (L) => ({ ...L, i0: L.i1, i1: L.i0, dir: -L.dir });

class Route {
  constructor(legs) {
    this.legs = legs.filter((L) => L.len > 0.01);
    this.t0 = [];
    let t = 0;
    for (const L of this.legs) { this.t0.push(t); t += (L.len / L.speed) * 1000; }
    this.duration = t; // ms
  }
  reversed() { return new Route([...this.legs].reverse().map(reverseLeg)); }
  // Pose at tau ms into the route: position (lane-offset), height and travel direction.
  at(tau, out) {
    let k = this.legs.length - 1;
    while (k > 0 && this.t0[k] > tau) k--;
    const L = this.legs[k];
    const s = Math.min(L.len, Math.max(0, ((tau - this.t0[k]) / 1000) * L.speed));
    const c = L.cum[L.i0] + L.dir * s;
    const cum = L.cum;
    let lo = Math.min(L.i0, L.i1), hi = Math.max(L.i0, L.i1);
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (cum[m] <= c) lo = m; else hi = m; }
    const a = L.pts[lo], b = L.pts[hi];
    const seg = cum[hi] - cum[lo] || 1;
    const f = Math.min(1, Math.max(0, (c - cum[lo]) / seg));
    let tx = (b[0] - a[0]) * L.dir, tz = (b[1] - a[1]) * L.dir;
    const tl = Math.hypot(tx, tz) || 1; tx /= tl; tz /= tl;
    const x = a[0] + (b[0] - a[0]) * f, z = a[1] + (b[1] - a[1]) * f;
    out.x = x - tz * L.lane; out.z = z + tx * L.lane;
    out.y = typeof L.y === 'function' ? L.y(x) : L.y;
    out.hx = tx; out.hz = tz;
    out.speed = s < L.len ? L.speed : 0;
    return out;
  }
}

const I = IRONWOOD;
const saltIndexAtZ = (z) => Math.round((z - ROAD_START) / 8);

// Home driveway -> streets -> highway -> Vira's gate -> a parking stall.
function routeToWork(home, stall) {
  const salt = sharedLine('saltbrush');
  const [dx, dz] = home.drive, zs = home.street;
  const legs = [own([[dx, dz], [dx, zs]], 3, 0, home.city === 'saltbrush' ? 0.3 : 0.08)];
  if (home.city === 'saltbrush') {
    legs.push(own([[dx, zs], [0, zs]], 11, 2, 0.3));
    legs.push(leg(salt, saltIndexAtZ(zs), salt.pts.length - 1, 29, 1.8, 0.27));
  } else if (home.city === 'halcyon') {
    const hal = sharedLine('halcyon');
    legs.push(own([[dx, zs], [FREEWAY_X1, zs]], 12, 2.5, 0.08));
    legs.push(own([[FREEWAY_X1, zs], [FREEWAY_X1, FREEWAY_Z]], 12, 2.5, 0.08));
    const fw = [];
    for (let x = FREEWAY_X1; x <= FREEWAY_X0; x += 20) fw.push([x, FREEWAY_Z]);
    fw.push([FREEWAY_X0, FREEWAY_Z]);
    legs.push(own(fw, 27, 5.3, (x) => freewayY(x) + 0.35));
    legs.push(leg(hal, hal.pts.length - 1, 0, 31, 5.3, 0.27));
    legs.push(leg(salt, saltIndexAtZ(hal.pts[0][1]), salt.pts.length - 1, 29, 1.8, 0.27));
  } else {
    const irn = sharedLine('ironwood');
    const xc = I.x + Math.round((dx - I.x) / IRON_GRID) * IRON_GRID;
    legs.push(own([[dx, zs], [xc, zs]], 11, 2.5, 0.08));
    legs.push(own([[xc, zs], [xc, I.z]], 11, 2.5, 0.08));
    legs.push(own([[xc, I.z], [irn.pts[irn.pts.length - 1][0], I.z]], 13, 2.5, 0.08));
    legs.push(leg(irn, irn.pts.length - 1, 0, 27, 1.8, 0.27));
    legs.push(leg(salt, saltIndexAtZ(irn.pts[0][1]), salt.pts.length - 1, 29, 1.8, 0.27));
  }
  // through Lyra's gate and into the lot
  const end = salt.pts[salt.pts.length - 1];
  legs.push(own([[end[0], end[1]], [31, -662], [31, stall.aisle], [stall.x, stall.aisle]], 6, 1.5, 0.12));
  legs.push(own([[stall.x, stall.aisle], [stall.x, stall.z]], 2.5, 0, 0.12));
  return new Route(legs);
}

// ---------- the staff roster ----------
// roster: game/data/staff/roster.json (names, titles, shared homes), or null to use generated names.
export function buildStaff(roster = null) {
  const byId = new Map((roster?.people || []).map((p) => [p.id, p]));
  const r = rng(4747);
  const pick = (weighted) => { let u = r(); for (const [v, w] of weighted) { if ((u -= w) < 0) return v; } return weighted[0][0]; };
  const shuffle = (a) => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const homes = { saltbrush: shuffle([...HOMES.saltbrush]), ironwood: shuffle([...HOMES.ironwood]), halcyon: shuffle([...HOMES.halcyon]) };
  const stalls = shuffle([...VIRA_STALLS]);
  const staff = [];
  let id = 0;
  for (const role of ROLES) for (let k = 0; k < role.n; k++) {
    let city = pick(CITY_SHARE);
    if (!homes[city].length) city = Object.keys(homes).find((c) => homes[c].length);
    if (!city || !stalls.length) break;
    const home = homes[city].pop(), stall = stalls.pop();
    const emp = {
      id: id++, name: `${FIRST[Math.floor(r() * FIRST.length)]} ${LAST[Math.floor(r() * LAST.length)]}`,
      role: role.role, sched: role.sched, idx: k, crew: k % 4,
      start: role.start || 8, len: role.len || 9, jitter: role.sched === 'office' ? (r() - 0.5) * 0.8 : 0,
      early: (8 + r() * 17) * MIN, late: (2 + r() * 15) * MIN,
      city, home, stall, kind: pick(KINDS), color: PAINT[Math.floor(r() * PAINT.length)],
    };
    const card = byId.get(emp.id);
    if (card) {
      emp.name = card.name; emp.title = card.title; emp.age = card.age; emp.pronouns = card.pronouns;
      // couples who both work at Vira share a house; the second car parks further down the driveway
      const gd = card.home.game_drive;
      if (gd) emp.home = { ...home, drive: [gd.x, gd.z], street: gd.street };
    }
    emp.route = routeToWork(emp.home, stall);
    emp.routeHome = emp.route.reversed();
    staff.push(emp);
  }
  return staff;
}

export const crewName = (emp) => (emp.sched === 'rot12' ? `Crew ${CREWS[emp.crew]}` : '');
