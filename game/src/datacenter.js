import * as THREE from 'three';
import { getHeight, GATE_Z } from './terrain.js';
import { rng, canvasTex, signTex, boxUV, part, mergeParts, mat4, instanced, flatRect, nightEmissive } from './util.js';
import * as TX from './textures.js';
import * as DX from './dctextures.js';
import { buildCars, buildTrucks, buildLightPoles, contactShadows } from './props.js';
import { VIRA_STALLS } from './homes.js';
import { buildViraInterior } from './interiorVira.js';

// Vira, laid out after the film's aerial stills: sixteen data halls in four blocks of four.
// Within a block the halls stand side by side (long walls facing across narrow equipment
// alleys); the blocks run end to end toward the mountains (south, +z). The substation sits
// beside the first block, east of the halls. The highway arrives at the north-west corner.
export const HALL = { W: 62, L: 230, H: 16 };
export const HALL_X = [70, 154, 238, 322];       // side by side, 22 m alleys
export const HALL_Z = [-385, -129, 127, 383];    // end to end, 26 m cross roads
const FENCE = { x0: 12, x1: 650, z0: GATE_Z, z1: 548 };
const GATE = { x: 31, half: 9 };
const SUB = { x0: 384, x1: 606, z0: -634, z1: -416 };

const std = (o) => new THREE.MeshStandardMaterial(o);
function rep(set, rx, ry) {
  const map = set.map.clone(); map.repeat.set(rx, ry); map.needsUpdate = true;
  const normal = set.normal.clone(); normal.repeat.set(rx, ry); normal.needsUpdate = true;
  return { map, normal };
}

export function buildDataCenter() {
  const g = new THREE.Group();
  const r = rng(42);

  const M = {
    gravel: std({ ...pick(TX.gravel()), roughness: 1 }),
    concrete: std({ ...pick(TX.concrete()), roughness: 0.92 }),
    asphalt: std({ ...pick(TX.asphalt()), roughness: 0.95 }),
    steel: std({ color: '#9aa1a8', roughness: 0.45, metalness: 0.7 }),
    darkSteel: std({ color: '#5a6067', roughness: 0.5, metalness: 0.6 }),
    galv: std({ color: '#b9c0c6', roughness: 0.4, metalness: 0.8 }),
    pipe: std({ color: '#d6dadd', roughness: 0.25, metalness: 0.85 }),
    coping: std({ color: '#c3c6c9', roughness: 0.6, metalness: 0.3 }),
    paint: std({ color: '#e8e4d8', roughness: 0.7 }),
    yellow: std({ color: '#d8a92a', roughness: 0.7 }),
  };

  buildGround(g, M);
  const roofUnits = buildHalls(g, M, r);
  buildYards(g, M, r);
  buildFront(g, M, r);
  const gate = buildFence(g, M);
  g.add(buildSubstation(M));
  const east = buildEastYard(g, M, r);
  g.add(buildSolarFarm());
  const steam = buildSteam(roofUnits, r);
  g.add(steam.points);

  return {
    group: g, gate, views: east.views, ops: east.ops,
    update(dt, t) { gate.update(dt); steam.update(t); },
    setDaylight: (d) => steam.setDaylight(d),
  };
}

const pick = (t) => ({ map: t.map, normalMap: t.normal });

// ---------- ground, roads, aprons ----------
function buildGround(g, M) {
  const { x0, x1, z0, z1 } = FENCE;
  g.add(flatRect(x1 - x0, z1 - z0, (x0 + x1) / 2, (z0 + z1) / 2, 0.05, M.gravel, 3));
  // concrete apron under each block of halls and their alleys
  for (const z of HALL_Z) g.add(flatRect(HALL_X[3] - HALL_X[0] + HALL.W + 40, HALL.L + 10, (HALL_X[0] + HALL_X[3]) / 2, z, 0.08, M.concrete, 6));
  // outside: perimeter road down the west side, spur to the gate
  g.add(flatRect(10, z1 - z0 + 40, 0, (z0 + z1) / 2 + 20, 0.11, M.asphalt, 10));
  g.add(flatRect(50, 16, 22, z0 - 6, 0.12, M.asphalt, 10));
  // inside: north drive, cross roads between blocks, alley lanes, east lane
  g.add(flatRect(385 - x0, 14, (x0 + 385) / 2, -545, 0.11, M.asphalt, 10));
  g.add(flatRect(12, 110, GATE.x, -595, 0.11, M.asphalt, 10));
  for (let k = 0; k < 3; k++) {
    const z = (HALL_Z[k] + HALL_Z[k + 1]) / 2;
    g.add(flatRect(HALL_X[3] + HALL.W / 2 + 22 - x0, 16, (x0 + HALL_X[3] + HALL.W / 2 + 22) / 2, z, 0.11, M.asphalt, 10));
    for (const s of [-1, 1]) g.add(flatRect(HALL_X[3] + HALL.W / 2 + 18 - x0, 0.15, (x0 + HALL_X[3] + HALL.W / 2 + 18) / 2, z + s * 7.2, 0.13, M.paint));
  }
  for (let i = 0; i < 3; i++) g.add(flatRect(8, HALL_Z[3] - HALL_Z[0] + HALL.L, (HALL_X[i] + HALL_X[i + 1]) / 2 + 2, (HALL_Z[0] + HALL_Z[3]) / 2, 0.115, M.asphalt, 10));
  g.add(flatRect(14, z1 - (-545) - 8, HALL_X[3] + HALL.W / 2 + 15, (z1 + -545) / 2, 0.11, M.asphalt, 10));
  g.add(flatRect(0.15, 1180, HALL_X[3] + HALL.W / 2 + 15, -50, 0.13, M.yellow));
}

// ---------- the sixteen halls ----------
function buildHalls(g, M, r) {
  const { W, L, H } = HALL;
  const clad = DX.hallCladding();
  const wall = std({ ...pick(clad), roughness: 0.75 });
  const memb = rep(TX.membrane(), 1 / 3, 1 / 3);
  const roof = std({ ...pick(memb), roughness: 0.8 });
  const hallGeo = boxUV(W, H, L, 4);
  hallGeo.translate(0, H / 2, 0);

  const lv = DX.louver();
  const louverMat = std({ ...pick(lv), roughness: 0.55, metalness: 0.5 });
  const colGeo = boxUV(3.2, H - 1.2, 1.3, 2, 2); colGeo.translate(0, (H - 1.2) / 2 + 0.6, 0);
  const cols = [], spouts = [], lights = [], doors = [], rollups = [], beacons = [], skirts = [];
  const decks = [], legs = [], units = [], supports = [], loops = [], branches = [], pent = [];
  const copingLong = [], copingShort = [];
  const labels = 'ABCD';

  HALL_Z.forEach((hz, col) => HALL_X.forEach((hx, row) => {
    const m = new THREE.Mesh(hallGeo, [wall, wall, roof, roof, wall, wall]);
    m.position.set(hx, 0, hz);
    m.castShadow = m.receiveShadow = true;
    g.add(m);
    skirts.push({ x: hx, z: hz, w: W + 6, d: L + 6 });
    for (const s of [-1, 1]) {
      copingLong.push(mat4(hx + s * (W / 2 - 0.2), H + 0.5, hz));
      copingShort.push(mat4(hx, H + 0.5, hz + s * (L / 2 - 0.2)));
    }
    // projecting louver columns along the long walls and the ends
    for (let z = -L / 2 + 11.5; z <= L / 2 - 11; z += 23) for (const s of [-1, 1]) {
      cols.push(mat4(hx + s * (W / 2 + 0.65), 0, hz + z, s * Math.PI / 2));
      lights.push(mat4(hx + s * (W / 2 + 0.25), 9.5, hz + z + 11.5));
      if (Math.abs(z) > 30) doors.push(mat4(hx + s * (W / 2 + 0.03), 1.15, hz + z + 6, s * Math.PI / 2));
    }
    for (const x of [-W / 2 + 9, 0, W / 2 - 9]) for (const s of [-1, 1]) cols.push(mat4(hx + x, 0, hz + s * (L / 2 + 0.65), s > 0 ? 0 : Math.PI));
    for (const s of [-1, 1]) for (const x of [-W / 4 - 2, W / 4 + 2]) rollups.push(mat4(hx + x, 2.7, hz + s * (L / 2 + 0.04), s > 0 ? 0 : Math.PI));
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) beacons.push(mat4(hx + sx * (W / 2 - 0.6), H + 1.3, hz + sz * (L / 2 - 0.6)));

    // rooftop: raised steel decks along both long edges, three lines of chiller modules each
    for (const s of [-1, 1]) {
      const dx = s * (W / 2 - 7.2);
      decks.push(mat4(hx + dx, H + 2.05, hz));
      for (let z = -L / 2 + 6; z <= L / 2 - 6; z += 10) for (const lx of [-4.2, 0, 4.2]) legs.push(mat4(hx + dx + lx, H + 1.05, hz + z));
      for (const lx of [-3.3, 0, 3.3]) for (let z = -L / 2 + 9; z <= L / 2 - 9; z += 8.4) units.push(mat4(hx + dx + lx, H + 2.2, hz + z));
      for (let z = -L / 2 + 14; z <= L / 2 - 14; z += 16.8) branches.push(mat4(hx + s * 10.5, H + 1.15, hz + z));
    }
    // central services corridor: supports every 8 m, expansion loops every ~46 m
    for (let z = -L / 2 + 6; z <= L / 2 - 6; z += 8) supports.push(mat4(hx, H, hz + z));
    for (let z = -L / 2 + 30; z <= L / 2 - 30; z += 46) loops.push(mat4(hx, H, hz + z));
    for (const s of [-1, 1]) pent.push(mat4(hx + s * 4, H, hz + s * (L / 2 - 14)));

    const label = new THREE.Mesh(new THREE.PlaneGeometry(7, 3.2), std({ map: signTex([`${labels[col]}${row + 1}`], { w: 256, h: 117, bg: '#ecebe6', fg: '#2a2f35', border: null, font: '600 96px Arial' }), roughness: 0.6 }));
    label.position.set(hx, 13.2, hz - L / 2 - 0.08);
    label.rotation.y = Math.PI;
    g.add(label);
  }));

  g.add(instanced(new THREE.BoxGeometry(0.6, 1, L), M.coping, copingLong));
  g.add(instanced(new THREE.BoxGeometry(W, 1, 0.6), M.coping, copingShort));
  g.add(instanced(colGeo, louverMat, cols));
  g.add(contactShadows(skirts.map((s) => ({ ...s, w: s.w * 1.06, d: s.d * 1.03 }))));

  const doorTex = canvasTex(64, 128, (c, w, h) => { c.fillStyle = '#8c9298'; c.fillRect(0, 0, w, h); c.fillStyle = '#6b7177'; c.fillRect(4, 4, w - 8, h - 4); c.fillStyle = '#cfd2d4'; c.fillRect(w - 14, h / 2, 6, 3); });
  g.add(instanced(new THREE.PlaneGeometry(1.1, 2.3), std({ map: doorTex, roughness: 0.5, metalness: 0.5 }), doors, { cast: false }));
  const rollTex = canvasTex(128, 128, (c, w, h) => { c.fillStyle = '#a7adb2'; c.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 6) { c.fillStyle = '#7f858a'; c.fillRect(0, y, w, 1); } c.fillStyle = '#e1b52a'; c.fillRect(0, h - 6, w, 6); });
  g.add(instanced(new THREE.PlaneGeometry(5, 5.4), std({ map: rollTex, roughness: 0.5, metalness: 0.6 }), rollups, { cast: false }));
  g.add(instanced(new THREE.BoxGeometry(0.7, 0.35, 0.3), nightEmissive(std({ color: '#666', emissive: '#ffe2b0' }), 5), lights, { cast: false }));
  g.add(instanced(new THREE.SphereGeometry(0.35, 8, 6), std({ color: '#400', emissive: '#ff2a1a', emissiveIntensity: 4 }), beacons, { cast: false }));

  // decks and legs
  const gr = rep(DX.grating(), 13, 230);
  g.add(instanced(new THREE.BoxGeometry(13, 0.3, L - 8), [M.darkSteel, M.darkSteel, std({ ...pick(gr), roughness: 0.6, metalness: 0.6 }), M.darkSteel, M.darkSteel, M.darkSteel], decks));
  g.add(instanced(new THREE.BoxGeometry(0.35, 2.1, 0.35), M.steel, legs, { receive: false }));

  // chiller modules: 8 m x 2.6 m, V-coil sides, six fans on top
  const coil = DX.coilSide();
  const coilMat = std({ ...pick(coil), roughness: 0.5, metalness: 0.5 });
  const topMat = std({ map: DX.unitTop(), roughness: 0.55, metalness: 0.4 });
  const endMat = std({ color: '#b4b9be', roughness: 0.5, metalness: 0.5 });
  const unitGeo = new THREE.BoxGeometry(2.6, 2.3, 8); unitGeo.translate(0, 1.15, 0);
  g.add(instanced(unitGeo, [coilMat, coilMat, topMat, endMat, endMat, endMat], units));
  const shrouds = [], disks = [];
  for (const fx of [-0.64, 0.64]) for (const fz of [-2.6, 0, 2.6]) {
    const sh = new THREE.CylinderGeometry(0.62, 0.62, 0.38, 18, 1, true); sh.translate(fx, 2.48, fz); shrouds.push(sh);
    const dk = new THREE.CircleGeometry(0.6, 18); dk.rotateX(-Math.PI / 2); dk.translate(fx, 2.36, fz); disks.push(dk);
  }
  const shroudMat = std({ color: '#c4c9cd', roughness: 0.4, metalness: 0.6, side: THREE.DoubleSide });
  g.add(instanced(mergeParts(shrouds.map((s) => { s.deleteAttribute('color'); return s; })), shroudMat, units, { cast: false }));
  g.add(instanced(mergeParts(disks), std({ map: DX.fanDisk(), roughness: 0.6, metalness: 0.3 }), units, { cast: false, receive: false }));

  // corridor pipes and cable trays (one long run per hall), supports, loops, branches
  const yellowT = DX.cables('#e2b51c', '#c9a215'), redT = DX.cables('#b8261c', '#8f1c15');
  for (const hz of HALL_Z) for (const hx of HALL_X) {
    [[-2.8, 0.55], [-1.4, 0.55], [0.2, 0.38], [1.2, 0.3]].forEach(([dx, rad]) => {
      const p = new THREE.Mesh(new THREE.CylinderGeometry(rad, rad, L - 12, 14), M.pipe);
      p.rotation.x = Math.PI / 2; p.position.set(hx + dx, H + 1.3 + rad, hz);
      p.castShadow = true;
      g.add(p);
    });
    for (const [dx, wdt, tex] of [[3.4, 1.4, yellowT], [5.1, 0.9, redT]]) {
      const t = tex.clone(); t.repeat.set(1, (L - 12) / 6); t.needsUpdate = true;
      const tray = new THREE.Mesh(new THREE.BoxGeometry(wdt, 0.25, L - 12), [M.steel, M.steel, std({ map: t, roughness: 0.6 }), M.steel, M.steel, M.steel]);
      tray.position.set(hx + dx, H + 1.5, hz);
      g.add(tray);
    }
    for (const s of [-1, 1]) {
      const walk = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.1, L - 12), std({ ...pick(rep(DX.grating(), 1.2, L - 12)), roughness: 0.6, metalness: 0.6 }));
      walk.position.set(hx + s * 7.2, H + 0.25, hz);
      g.add(walk);
    }
  }
  const supportGeo = mergeParts([
    part(new THREE.BoxGeometry(0.2, 1.3, 0.2), '#9aa1a8', -4.2, 0.65, 0),
    part(new THREE.BoxGeometry(0.2, 1.3, 0.2), '#9aa1a8', 6, 0.65, 0),
    part(new THREE.BoxGeometry(10.4, 0.2, 0.25), '#9aa1a8', 0.9, 1.3, 0),
  ]);
  g.add(instanced(supportGeo, std({ vertexColors: true, roughness: 0.45, metalness: 0.7 }), supports, { receive: false }));
  const loopParts = [];
  for (const dx of [-2.8, -1.4]) {
    for (const dz of [-3, 3]) { const v = new THREE.CylinderGeometry(0.55, 0.55, 3.2, 12); v.translate(dx, 3.4, dz); loopParts.push(v); }
    const h = new THREE.CylinderGeometry(0.55, 0.55, 6.6, 12); h.rotateX(Math.PI / 2); h.translate(dx, 5.0, 0); loopParts.push(h);
    for (const dz of [-3, 3]) { const e = new THREE.SphereGeometry(0.55, 12, 8); e.translate(dx, 5.0, dz); loopParts.push(e); }
  }
  g.add(instanced(mergeParts(loopParts), M.pipe, loops));
  const branchGeo = new THREE.CylinderGeometry(0.16, 0.16, 12, 8); branchGeo.rotateZ(Math.PI / 2);
  g.add(instanced(branchGeo, M.pipe, branches.map((b) => b), { receive: false }));
  const pentGeo = boxUV(7, 3.6, 5, 2, 2); pentGeo.translate(0, 1.8, 0);
  g.add(instanced(pentGeo, [louverMat, louverMat, std({ color: '#a8adb2' }), louverMat, louverMat, louverMat], pent));

  return units;
}

// ---------- equipment yards: gensets in the alleys, cooling towers on the west side ----------
function buildYards(g, M, r) {
  const { W, L } = HALL;
  const gs = DX.gensetSide();
  const genSide = std({ ...pick(gs), roughness: 0.55, metalness: 0.3 });
  const genTop = std({ color: '#244a40', roughness: 0.6, metalness: 0.3 });
  const genGeo = new THREE.BoxGeometry(4.2, 3.6, 10); genGeo.translate(0, 1.8, 0);
  const gens = [], stacks = [], xfmr = [], towers = [], bridges = [], tanks = [];
  for (const hz of HALL_Z) {
    // alleys east of halls 1-4: gensets along the wall, transformers on the far side
    HALL_X.forEach((hx, i) => {
      const gx = hx + W / 2 + 3;
      for (let z = -L / 2 + 8; z <= L / 2 - 8; z += 12) { gens.push(mat4(gx, 0, hz + z)); stacks.push(mat4(gx, 0, hz + z - 3.2)); }
      if (i < 3) for (let z = -L / 2 + 14; z <= L / 2 - 14; z += 24) xfmr.push(mat4(HALL_X[i + 1] - W / 2 - 2.6, 0, hz + z));
    });
    // west yard of the first hall in each block: cooling towers piped back to the wall
    for (let z = -L / 2 + 6; z <= L / 2 - 6; z += 8.2) towers.push(mat4(24.5, 0, hz + z));
    for (let z = -L / 2 + 10; z <= L / 2 - 10; z += 16.4) { bridges.push(mat4(33.5, 5.2, hz + z)); tanks.push(mat4(34.5, 0, hz + z + 4)); }
  }
  g.add(instanced(genGeo, [genSide, genSide, genTop, genTop, genTop, genTop], gens));
  const stackGeo = mergeParts([
    part(new THREE.CylinderGeometry(0.32, 0.32, 3.2, 10), '#3a3d40', 0, 5.2, 0),
    part(new THREE.BoxGeometry(1.4, 0.9, 2.4), '#56595c', 0, 4.0, 0),
  ]);
  g.add(instanced(stackGeo, std({ vertexColors: true, roughness: 0.6, metalness: 0.6 }), stacks));

  const fins = [];
  for (let k = -3; k <= 3; k++) for (const s of [-1, 1]) fins.push(part(new THREE.BoxGeometry(0.1, 2.2, 1.5), '#7d847a', s * 1.55, 1.5, k * 0.5));
  const xGeo = mergeParts([part(new THREE.BoxGeometry(2.6, 2.6, 3.8), '#8a9187', 0, 1.3, 0), part(new THREE.BoxGeometry(3.2, 0.2, 4.4), '#9a9a94', 0, 0.1, 0), ...fins]);
  g.add(instanced(xGeo, std({ vertexColors: true, roughness: 0.55, metalness: 0.35 }), xfmr));

  const tw = DX.towerSide();
  const twSide = std({ ...pick(tw), roughness: 0.5, metalness: 0.5 });
  const twGeo = new THREE.BoxGeometry(7, 6, 7); twGeo.translate(0, 3, 0);
  g.add(instanced(twGeo, [twSide, twSide, std({ color: '#9ea4a9', roughness: 0.6, metalness: 0.4 }), twSide, twSide, twSide], towers));
  const stackRing = new THREE.CylinderGeometry(2.6, 2.6, 1.6, 28, 1, true); stackRing.translate(0, 6.8, 0);
  g.add(instanced(stackRing, std({ color: '#c6cbcf', roughness: 0.45, metalness: 0.6, side: THREE.DoubleSide }), towers, { cast: false }));
  const fanTop = new THREE.CircleGeometry(2.5, 28); fanTop.rotateX(-Math.PI / 2); fanTop.translate(0, 6.3, 0);
  g.add(instanced(fanTop, std({ map: DX.fanDisk(), roughness: 0.6 }), towers, { cast: false, receive: false }));
  const railGeo = new THREE.TorusGeometry(3.6, 0.04, 4, 32); railGeo.rotateX(Math.PI / 2); railGeo.translate(0, 7.1, 0);
  g.add(instanced(railGeo, M.steel, towers, { cast: false, receive: false }));
  // pipe bridges from the wall out to the towers, and small chemical tanks
  const bridgeGeo = mergeParts([
    part(new THREE.CylinderGeometry(0.3, 0.3, 11, 10), '#d6dadd', 0, 0, -0.45, 0, 0, Math.PI / 2),
    part(new THREE.CylinderGeometry(0.3, 0.3, 11, 10), '#d6dadd', 0, 0, 0.45, 0, 0, Math.PI / 2),
    part(new THREE.CylinderGeometry(0.3, 0.3, 2.4, 10), '#d6dadd', -5.4, -1.2, -0.45),
    part(new THREE.CylinderGeometry(0.3, 0.3, 2.4, 10), '#d6dadd', -5.4, -1.2, 0.45),
    part(new THREE.BoxGeometry(0.25, 5.2, 0.25), '#9aa1a8', 0, -2.6, 1.0),
  ]);
  g.add(instanced(bridgeGeo, std({ vertexColors: true, roughness: 0.3, metalness: 0.8 }), bridges));
  const tankGeo = new THREE.CylinderGeometry(0.9, 0.9, 2.4, 14); tankGeo.translate(0, 1.2, 0);
  g.add(instanced(tankGeo, std({ color: '#2f6b5a', roughness: 0.5, metalness: 0.3 }), tanks));
}

// ---------- front of house: gate, security, parking, trucks ----------
function buildFront(g, M, r) {
  const cars = [], trucks = [], stripes = [];
  // staff parking: rows north of the drive. The cars here are the staff's own, driven in
  // and out on their shifts by the commute simulation (traffic.js).
  for (const rz of [-626, -612, -586, -572]) {
    for (let x = 62; x <= 380; x += 2.9) {
      stripes.push(mat4(x - 1.45, 0.13, rz));
      VIRA_STALLS.push({ x, z: rz, aisle: rz < -600 ? -619 : -579 });
    }
  }
  g.add(flatRect(330, 70, 221, -599, 0.115, M.asphalt, 10));
  g.add(instanced(new THREE.BoxGeometry(0.12, 0.02, 5.2), new THREE.MeshBasicMaterial({ color: '#d9d9d2' }), stripes, { cast: false }));
  // trucks at the loading ends of the first block and along the north drive
  for (let i = 0; i < 6; i++) trucks.push({ x: HALL_X[i % 4] + (i < 4 ? -12 : 12), z: -512, ry: Math.PI, kind: i % 3 ? 'semi' : 'box' });
  for (const x of [120, 200, 280]) trucks.push({ x, z: -536, ry: Math.PI / 2, kind: 'box' });
  for (const hz of HALL_Z.slice(1)) for (const hx of [HALL_X[0], HALL_X[2]]) trucks.push({ x: hx - 14, z: hz - HALL.L / 2 - 8, ry: Math.PI / 2, kind: r() < 0.5 ? 'box' : 'semi' });
  for (let k = 0; k < 14; k++) {
    const hz = HALL_Z[k % 4], i = k % 3;
    cars.push({ x: (HALL_X[i] + HALL_X[i + 1]) / 2 + 2, z: hz + (r() - 0.5) * 180, ry: r() < 0.5 ? 0 : Math.PI, color: '#f2f2f0', kind: r() < 0.6 ? 'pickup' : 'van' });
  }
  g.add(buildCars(cars, 3));
  g.add(buildTrucks(trucks, 4));

  // security gatehouse and lift arms
  const glassTex = canvasTex(128, 64, (c, w, h) => {
    const grd = c.createLinearGradient(0, 0, 0, h); grd.addColorStop(0, '#6f8a96'); grd.addColorStop(1, '#a8bec6');
    c.fillStyle = grd; c.fillRect(0, 0, w, h);
    c.fillStyle = '#e6e6e2'; c.fillRect(0, 0, w, h * 0.25); c.fillRect(0, h * 0.85, w, h * 0.15);
    c.fillStyle = '#2b3237'; for (let x = 0; x < w; x += 32) c.fillRect(x, h * 0.25, 2, h * 0.6);
  });
  const glassLit = canvasTex(128, 64, (c, w, h) => { c.fillStyle = '#000'; c.fillRect(0, 0, w, h); c.fillStyle = '#ffd59a'; c.fillRect(0, h * 0.25, w, h * 0.6); });
  const booth = nightEmissive(std({ map: glassTex, emissiveMap: glassLit, emissive: '#ffffff', roughness: 0.2, metalness: 0.5 }), 0.6);
  const flat = std({ color: '#b5b3ad', roughness: 0.85 });
  const gh = new THREE.Mesh(boxUV(5, 3.2, 8, 5), [booth, booth, flat, flat, booth, booth]);
  gh.position.set(GATE.x + 14, 1.6, GATE_Z + 16);
  gh.castShadow = true;
  const ghRoof = new THREE.Mesh(new THREE.BoxGeometry(7, 0.4, 10), M.coping);
  ghRoof.position.set(GATE.x + 14, 3.4, GATE_Z + 16);
  g.add(gh, ghRoof);
  for (const s of [-1, 1]) {
    const arm = new THREE.Mesh(new THREE.BoxGeometry(5.5, 0.12, 0.12), std({ color: '#f2f2f0', roughness: 0.5 }));
    arm.position.set(GATE.x + s * 3, 1.05, GATE_Z + 24 + s * 4);
    g.add(arm);
  }
  const bollards = [];
  for (const x of [GATE.x - 12, GATE.x - 10.5, GATE.x + 10.5, GATE.x + 12]) bollards.push(mat4(x, 0.5, GATE_Z - 2));
  g.add(instanced(new THREE.CylinderGeometry(0.15, 0.15, 1, 10), std({ color: '#e8c11a', roughness: 0.5 }), bollards));

  // monument sign at the approach
  const viraTex = signTex([{ text: 'V I R A', font: '200 150px Arial' }], { w: 1024, h: 256, fg: '#7beeff', clear: true });
  const mono = new THREE.Mesh(new THREE.BoxGeometry(14, 3, 1.6), std({ color: '#d1c8b8', roughness: 0.9, map: TX.stucco().map }));
  mono.position.set(-22, 1.5, GATE_Z - 60);
  mono.rotation.y = Math.PI / 2;
  mono.castShadow = true;
  const monoText = new THREE.Mesh(new THREE.PlaneGeometry(11, 2.75), new THREE.MeshBasicMaterial({ map: viraTex, transparent: true, toneMapped: false }));
  monoText.position.set(-21.18, 1.6, GATE_Z - 60);
  monoText.rotation.y = Math.PI / 2;
  g.add(mono, monoText);
  const warn = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 1.6), std({
    map: signTex([{ text: 'RESTRICTED AREA', font: 'bold 52px Arial', color: '#b01616' }, { text: 'AUTHORIZED', font: 'bold 44px Arial' }, { text: 'PERSONNEL ONLY', font: 'bold 44px Arial' }],
      { w: 384, h: 256, bg: '#f4f4f0', fg: '#111', border: '#111' }), side: THREE.DoubleSide,
  }));
  warn.position.set(GATE.x - 15, 1.8, GATE_Z - 0.2);
  g.add(warn);

  // lighting along the drives and alleys
  const lamps = [];
  for (let x = 40; x <= 380; x += 50) lamps.push({ x, z: -553, ry: -Math.PI / 2 });
  for (let k = 0; k < 3; k++) for (let x = 40; x <= 380; x += 45) lamps.push({ x, z: (HALL_Z[k] + HALL_Z[k + 1]) / 2 - 8.5, ry: -Math.PI / 2 });
  for (let z = -520; z <= 520; z += 50) lamps.push({ x: HALL_X[3] + HALL.W / 2 + 7.5, z, ry: 0 });
  g.add(buildLightPoles(lamps, 10));
}

// ---------- perimeter fence, barbed wire, camera poles, sliding gate ----------
function buildFence(g, M) {
  const linkTex = canvasTex(64, 64, (c, w, h) => {
    c.clearRect(0, 0, w, h);
    c.strokeStyle = '#aeb4b8'; c.lineWidth = 2.2;
    for (let k = -64; k <= 128; k += 32) {
      c.beginPath(); c.moveTo(k, 0); c.lineTo(k + 64, 64); c.stroke();
      c.beginPath(); c.moveTo(k, 64); c.lineTo(k + 64, 0); c.stroke();
    }
  });
  const linkMat = std({ map: linkTex, alphaTest: 0.35, alphaToCoverage: true, side: THREE.DoubleSide, metalness: 0.7, roughness: 0.45 });
  const FH = 3.2, posts = [], arms = [], wire = [], cams = [];
  const seg = (x1, z1, x2, z2) => {
    const len = Math.hypot(x2 - x1, z2 - z1);
    const geo = new THREE.PlaneGeometry(len, FH);
    const uv = geo.attributes.uv;
    for (let k = 0; k < uv.count; k++) uv.setXY(k, uv.getX(k) * len / 0.9, uv.getY(k) * FH / 0.9);
    const m = new THREE.Mesh(geo, linkMat);
    m.position.set((x1 + x2) / 2, FH / 2, (z1 + z2) / 2);
    m.rotation.y = Math.atan2(-(z2 - z1), x2 - x1);
    m.castShadow = true;
    g.add(m);
    const n = Math.ceil(len / 3);
    const ox = (z2 - z1) / len, oz = -(x2 - x1) / len; // outward for a clockwise loop
    for (let i = 0; i <= n; i++) {
      const x = x1 + (x2 - x1) * i / n, z = z1 + (z2 - z1) * i / n;
      posts.push(mat4(x, 1.8, z));
      arms.push(mat4(x + ox * 0.25, FH + 0.35, z + oz * 0.25, Math.atan2(ox, oz), 1, 1, 1, 0.75));
    }
    for (const k of [0.15, 0.35, 0.55]) wire.push(x1 + ox * k, FH + 0.1 + k * 0.9, z1 + oz * k, x2 + ox * k, FH + 0.1 + k * 0.9, z2 + oz * k);
    for (let d = 60; d < len; d += 140) cams.push({ x: x1 + (x2 - x1) * d / len - ox * 1.2, z: z1 + (z2 - z1) * d / len - oz * 1.2, ry: Math.atan2(ox, oz) });
  };
  const { x0, x1, z0, z1 } = FENCE;
  seg(x0, z0, GATE.x - GATE.half, z0); seg(GATE.x + GATE.half, z0, x1, z0);
  seg(x1, z0, x1, z1); seg(x1, z1, x0, z1); seg(x0, z1, x0, z0);
  g.add(instanced(new THREE.CylinderGeometry(0.05, 0.05, 3.6, 6), M.steel, posts, { receive: false }));
  g.add(instanced(new THREE.BoxGeometry(0.04, 0.8, 0.04), M.steel, arms, { receive: false }));
  const wg = new THREE.BufferGeometry();
  wg.setAttribute('position', new THREE.Float32BufferAttribute(wire, 3));
  g.add(new THREE.LineSegments(wg, new THREE.LineBasicMaterial({ color: '#5c6266' })));

  // Lyra's eyes: camera poles around the perimeter and at the gate
  for (const [x, z] of [[x0 + 2, z0 + 2], [x1 - 2, z0 + 2], [x1 - 2, z1 - 2], [x0 + 2, z1 - 2], [GATE.x - 12, GATE_Z + 3], [GATE.x + 12, GATE_Z + 3]]) cams.push({ x, z, ry: Math.atan2(x - 330, z) });
  const camPole = mergeParts([
    part(new THREE.CylinderGeometry(0.08, 0.12, 6.5, 8), '#9aa0a5', 0, 3.25, 0),
    part(new THREE.BoxGeometry(0.08, 0.08, 0.7), '#9aa0a5', 0, 6.2, 0.3),
    part(new THREE.BoxGeometry(0.24, 0.24, 0.6), '#e9eaea', 0, 6.0, 0.62),
    part(new THREE.BoxGeometry(0.3, 0.06, 0.7), '#e9eaea', 0, 6.15, 0.62),
    part(new THREE.CylinderGeometry(0.09, 0.09, 0.05, 12), '#111111', 0, 6.0, 0.93, Math.PI / 2, 0, 0),
  ]);
  const camMats = cams.map((c) => mat4(c.x, 0, c.z, c.ry));
  g.add(instanced(camPole, std({ vertexColors: true, roughness: 0.4, metalness: 0.5 }), camMats, { receive: false }));
  const ledGeo = new THREE.SphereGeometry(0.03, 6, 4); ledGeo.translate(0.09, 6.12, 0.93);
  g.add(instanced(ledGeo, new THREE.MeshBasicMaterial({ color: '#ff2a1a', toneMapped: false }), camMats, { cast: false }));

  const leaves = [];
  for (const s of [-1, 1]) {
    const geo = new THREE.PlaneGeometry(GATE.half, 2.8);
    const uv = geo.attributes.uv;
    for (let k = 0; k < uv.count; k++) uv.setXY(k, uv.getX(k) * GATE.half / 0.9, uv.getY(k) * 2.8 / 0.9);
    const leaf = new THREE.Group();
    const mesh = new THREE.Mesh(geo, linkMat);
    mesh.position.y = 1.5;
    mesh.castShadow = true;
    for (const y of [0.1, 2.9]) { const b = new THREE.Mesh(new THREE.BoxGeometry(GATE.half, 0.08, 0.08), M.steel); b.position.y = y; leaf.add(b); }
    for (const x of [-GATE.half / 2, GATE.half / 2]) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.08, 2.9, 0.08), M.steel); b.position.set(x, 1.5, 0); leaf.add(b); }
    leaf.add(mesh);
    leaf.userData = { s, closedX: GATE.x + s * GATE.half / 2 };
    leaf.position.set(leaf.userData.closedX, 0, GATE_Z - 0.4);
    g.add(leaf);
    leaves.push(leaf);
  }
  return {
    open: false, auto: false, t: 0, // auto: Lyra opens it for staff cars
    toggle() { this.open = !this.open; },
    update(dt) {
      this.t = THREE.MathUtils.clamp(this.t + (this.open || this.auto ? dt : -dt) / 4, 0, 1);
      const e = this.t * this.t * (3 - 2 * this.t);
      for (const l of leaves) l.position.x = l.userData.closedX + l.userData.s * e * (GATE.half + 0.3);
    },
  };
}

// ---------- east yard: operations building and water storage beside the substation ----------
function buildEastYard(g, M, r) {
  const clad = () => std({ ...pick(DX.hallCladding()), roughness: 0.75 });
  // the operations building is hollow: lobby, ops room, Marcus's office and a server hall
  const ops = buildViraInterior(M, clad);
  g.add(ops.group);
  g.add(contactShadows([{ x: 470, z: -392, w: 88, d: 30 }]));
  const tankMat = std({ color: '#d9dcd6', roughness: 0.5, metalness: 0.4 });
  for (const [x, z, rad, h] of [[548, -392, 9, 12], [574, -380, 6, 9], [596, -392, 6, 9], [620, -380, 5, 7]]) {
    const t = new THREE.Mesh(new THREE.CylinderGeometry(rad, rad, h, 40), tankMat);
    t.position.set(x, h / 2, z);
    t.castShadow = t.receiveShadow = true;
    const cap = new THREE.Mesh(new THREE.ConeGeometry(rad + 0.2, 1.8, 40), tankMat);
    cap.position.set(x, h + 0.9, z);
    g.add(t, cap);
  }
  const cars = [];
  for (let x = 400; x <= 540; x += 2.9) if (r() < 0.55) cars.push({ x, z: -362, ry: Math.PI });
  g.add(flatRect(150, 14, 470, -360, 0.115, M.asphalt, 10));
  g.add(buildCars(cars, 21));
  return { views: ops.views, ops: ops.group };
}

// ---------- substation, after the film's substation still ----------
function latticeTex(rx, ry) {
  return canvasTex(64, 128, (c, w, h) => {
    c.clearRect(0, 0, w, h);
    c.strokeStyle = '#c3cacf'; c.lineWidth = 4;
    c.strokeRect(2, 2, w - 4, h - 4);
    c.lineWidth = 2.5;
    c.beginPath(); c.moveTo(0, 0); c.lineTo(w, h); c.moveTo(w, 0); c.lineTo(0, h); c.stroke();
  }, { repeat: [rx, ry] });
}
const latticeMat = (rx, ry) => std({ map: latticeTex(rx, ry), alphaTest: 0.4, alphaToCoverage: true, side: THREE.DoubleSide, metalness: 0.75, roughness: 0.4 });

const BAYS = [420, 465, 510, 555];
const GANTRY_COLS = [397, 442, 487, 532, 577];
const NORTH = { gantry: -622, sw1: -607, br: -595, sw2: -582, tr: -560 };
const SOUTH = { gantry: -428, sw1: -443, br: -455, sw2: -468, tr: -490 };

function buildSubstation(M) {
  const g = new THREE.Group();
  const { x0, x1, z0, z1 } = SUB;
  const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, w = x1 - x0, d = z1 - z0;
  const dg = DX.darkGravel();
  g.add(flatRect(w, d, cx, cz, 0.12, std({ ...pick(rep(dg, w / 4, d / 4)), roughness: 1 })));
  const wallMat = std({ ...pick(rep(TX.concrete(), 20, 1)), color: '#d9d6cf', roughness: 0.9 });
  for (const [ww, dd, x, z] of [[w, 0.4, cx, z0], [w - 24, 0.4, cx + 12, z1], [0.4, d, x0, cz], [0.4, d, x1, cz]]) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(ww, 2.2, dd), wallMat);
    m.position.set(x, 1.1, z);
    m.castShadow = m.receiveShadow = true;
    g.add(m);
  }
  const lines = [];
  const rectLines = (x, z, rw, rd) => {
    lines.push(mat4(x, 0.14, z - rd / 2, 0, rw, 1, 0.15), mat4(x, 0.14, z + rd / 2, 0, rw, 1, 0.15));
    lines.push(mat4(x - rw / 2, 0.14, z, 0, 0.15, 1, rd), mat4(x + rw / 2, 0.14, z, 0, 0.15, 1, rd));
  };

  // main power transformers: one per bay on each side of the yard
  const fins = [];
  for (let k = -6; k <= 6; k++) for (const s of [-1, 1]) fins.push(part(new THREE.BoxGeometry(2.2, 4.2, 0.1), '#a9adb0', s * 5.2, 2.9, k * 0.42));
  const bush = (x, z, h) => part(new THREE.CylinderGeometry(0.16, 0.3, h, 10), '#c9b7a0', x, 5.6 + h / 2, z);
  const trGeo = mergeParts([
    part(new THREE.BoxGeometry(8, 5.2, 5.4), '#9aa0a3', 0, 3.0, 0),
    part(new THREE.BoxGeometry(8.6, 0.4, 6), '#7f8487', 0, 0.2, 0),
    ...fins,
    part(new THREE.CylinderGeometry(0.9, 0.9, 6, 16), '#9aa0a3', 0, 7.0, 2.2, 0, 0, Math.PI / 2),
    part(new THREE.BoxGeometry(0.3, 1.6, 0.3), '#7f8487', -2.6, 6.2, 2.2), part(new THREE.BoxGeometry(0.3, 1.6, 0.3), '#7f8487', 2.6, 6.2, 2.2),
    bush(-2.4, -1.2, 3.2), bush(0, -1.2, 3.2), bush(2.4, -1.2, 3.2),
    bush(-1.6, 1.0, 1.6), bush(0, 1.0, 1.6), bush(1.6, 1.0, 1.6),
    part(new THREE.BoxGeometry(1.4, 2.2, 1), '#8f9497', 3.2, 1.8, -3.1),
  ]);
  const trs = [];
  for (const x of BAYS) {
    trs.push(mat4(x, 0, NORTH.tr), mat4(x, 0, SOUTH.tr, Math.PI));
    rectLines(x, NORTH.tr, 16, 12); rectLines(x, SOUTH.tr, 16, 12);
  }
  g.add(instanced(trGeo, std({ vertexColors: true, roughness: 0.45, metalness: 0.5 }), trs));

  // breakers, disconnect switches and post insulators down each bay
  const brGeo = mergeParts([
    part(new THREE.BoxGeometry(0.2, 2.4, 0.2), '#9aa1a8', -1.2, 1.2, 0), part(new THREE.BoxGeometry(0.2, 2.4, 0.2), '#9aa1a8', 1.2, 1.2, 0),
    part(new THREE.BoxGeometry(3.2, 1.4, 1.2), '#b9bdc0', 0, 3.1, 0),
    ...[-1, 0, 1].map((k) => part(new THREE.CylinderGeometry(0.12, 0.22, 2.2, 10), '#c9b7a0', k * 1.05, 4.9, 0)),
  ]);
  const swGeo = mergeParts([
    part(new THREE.BoxGeometry(5, 0.25, 0.25), '#9aa1a8', 0, 4.6, 0),
    part(new THREE.BoxGeometry(0.3, 4.6, 0.3), '#9aa1a8', -2.3, 2.3, 0), part(new THREE.BoxGeometry(0.3, 4.6, 0.3), '#9aa1a8', 2.3, 2.3, 0),
    ...[-1.8, 0, 1.8].map((x) => part(new THREE.CylinderGeometry(0.1, 0.18, 2.4, 10), '#c9b7a0', x, 5.9, 0)),
    ...[-1.8, 0, 1.8].map((x) => part(new THREE.BoxGeometry(0.08, 0.08, 1.6), '#cfd6d8', x, 7.1, 0.5)),
  ]);
  const postGeo = mergeParts([
    part(new THREE.CylinderGeometry(0.14, 0.18, 3.6, 8), '#9aa1a8', 0, 1.8, 0),
    part(new THREE.CylinderGeometry(0.12, 0.2, 1.6, 10), '#c9b7a0', 0, 4.4, 0),
  ]);
  const breakers = [], switches = [], posts = [], gear = [];
  for (const x of BAYS) for (const S of [NORTH, SOUTH]) {
    switches.push(mat4(x, 0, S.sw1), mat4(x, 0, S.sw2));
    breakers.push(mat4(x, 0, S.br));
    for (const dx of [-1.8, 0, 1.8]) posts.push(mat4(x + dx, 0, (S.sw2 + S.tr) / 2 + 2), mat4(x + dx + 9, 0, S.br), mat4(x + dx + 9, 0, S.sw2));
  }
  // metal-clad switchgear between the transformer rows
  for (const x of BAYS.slice(0, 3)) gear.push(mat4(x, 0, (NORTH.tr + SOUTH.tr) / 2));
  g.add(instanced(brGeo, std({ vertexColors: true, roughness: 0.4, metalness: 0.6 }), breakers));
  g.add(instanced(swGeo, std({ vertexColors: true, roughness: 0.4, metalness: 0.7 }), switches));
  g.add(instanced(postGeo, std({ vertexColors: true, roughness: 0.4, metalness: 0.6 }), posts));
  const gearGeo = new THREE.BoxGeometry(12, 3.4, 5); gearGeo.translate(0, 1.7, 0);
  g.add(instanced(gearGeo, std({ color: '#e6e6e1', roughness: 0.55, metalness: 0.3 }), gear));

  // lattice gantries where the lines come in, and lightning masts
  const colG = new THREE.CylinderGeometry(0.6, 1.4, 20, 4, 1, true); colG.rotateY(Math.PI / 4);
  const gantCols = [], gantBeams = [], masts = [];
  for (const z of [NORTH.gantry, SOUTH.gantry]) {
    for (const x of GANTRY_COLS) gantCols.push(mat4(x, 10, z));
    for (let i = 0; i < GANTRY_COLS.length - 1; i++) gantBeams.push(mat4((GANTRY_COLS[i] + GANTRY_COLS[i + 1]) / 2, 19.5, z, 0, GANTRY_COLS[i + 1] - GANTRY_COLS[i], 1, 1));
  }
  for (const [x, z] of [[x0 + 4, z0 + 4], [x1 - 4, z0 + 4], [x0 + 4, z1 - 4], [x1 - 4, z1 - 4], [cx, cz]]) masts.push(mat4(x, 0, z));
  g.add(instanced(colG, latticeMat(4, 8), gantCols));
  g.add(instanced(new THREE.BoxGeometry(1, 1.4, 1.4), latticeMat(12, 1), gantBeams));
  const mastG = new THREE.CylinderGeometry(0.12, 0.3, 28, 8); mastG.translate(0, 14, 0);
  g.add(instanced(mastG, M.galv, masts));
  const red = std({ color: '#400', emissive: '#ff2a1a', emissiveIntensity: 4 });
  const mastLight = new THREE.SphereGeometry(0.3, 8, 6); mastLight.translate(0, 28.2, 0);
  g.add(instanced(mastLight, red, masts, { cast: false }));
  const beaconTops = [];
  for (const z of [NORTH.gantry, SOUTH.gantry]) for (const x of GANTRY_COLS) beaconTops.push(mat4(x, 20.4, z));
  g.add(instanced(new THREE.SphereGeometry(0.25, 8, 6), red, beaconTops, { cast: false }));

  // control house
  const clad = () => std({ ...pick(DX.hallCladding()), roughness: 0.75 });
  const ctrl = new THREE.Mesh(boxUV(12, 5, 30, 4), [clad(), clad(), M.coping, M.coping, clad(), clad()]);
  ctrl.position.set(586, 2.5, (NORTH.tr + SOUTH.tr) / 2);
  ctrl.castShadow = true;
  g.add(ctrl);
  rectLines(586, (NORTH.tr + SOUTH.tr) / 2, 16, 34);
  g.add(instanced(new THREE.BoxGeometry(1, 0.02, 1), std({ color: '#e8e6dc', roughness: 0.7 }), lines, { cast: false }));

  // buswork: gantry -> switch -> breaker -> switch -> transformer bushings
  const bus = [];
  const span = (A, B, sag, n = 10) => {
    for (let k = 0; k < n; k++) for (const t of [k / n, (k + 1) / n])
      bus.push(A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t - 4 * sag * t * (1 - t), A[2] + (B[2] - A[2]) * t);
  };
  for (const x of BAYS) for (const S of [NORTH, SOUTH]) for (const dx of [-1.8, 0, 1.8]) {
    const sgn = S === NORTH ? 1 : -1;
    span([x + dx, 18.8, S.gantry], [x + dx, 7.2, S.sw1], 0.5, 4);
    span([x + dx, 7.2, S.sw1], [x + dx * 0.6, 6.0, S.br], 0.15, 2);
    span([x + dx * 0.6, 6.0, S.br], [x + dx, 7.2, S.sw2], 0.15, 2);
    span([x + dx, 7.2, S.sw2], [x + dx * 1.3, 8.8, S.tr - sgn * 1.2], 0.3, 3);
  }
  // low-voltage bus between the transformer rows
  for (const dz of [-3, 0, 3]) span([BAYS[0], 6.2, (NORTH.tr + SOUTH.tr) / 2 + dz], [BAYS[3], 6.2, (NORTH.tr + SOUTH.tr) / 2 + dz], 0.6, 12);

  // transmission towers: two north of the wall, one east, then the line marches east across the desert
  const tBody = new THREE.CylinderGeometry(1.0, 5.2, 50, 4, 1, true); tBody.rotateY(Math.PI / 4); tBody.translate(0, 25, 0);
  const tArms = mergeParts([part(new THREE.BoxGeometry(1.6, 1.6, 22), '#ffffff', 0, 38, 0), part(new THREE.BoxGeometry(1.6, 1.6, 17), '#ffffff', 0, 45.5, 0)]);
  const towers = [], tops = [];
  const addTower = (x, z, ry = 0) => { const y = getHeight(x, z); towers.push(mat4(x, y, z, ry)); tops.push([x, y, z, ry]); };
  addTower(442, -705, Math.PI / 2); addTower(532, -705, Math.PI / 2);
  addTower(690, -428);
  for (let x = 1100; x <= 16000; x += 440) addTower(x, -705);
  g.add(instanced(tBody, latticeMat(4, 12), towers));
  g.add(instanced(tArms, latticeMat(12, 1), towers));
  const att = [[35, -10.5], [35, 10.5], [42.5, -8], [42.5, 8]];
  const end = (t, [y, a]) => [t[0] + Math.sin(t[3]) * a, t[1] + y, t[2] + Math.cos(t[3]) * a];
  for (let i = 3; i < tops.length - 1; i++) for (const a of att) span(end(tops[i], a), end(tops[i + 1], a), 8, 12);
  for (const a of att) span(end(tops[3], a), end(tops[1], a), 6, 12);
  for (const a of att) span(end(tops[1], a), end(tops[0], a), 3, 8);
  att.forEach((a, k) => {
    span(end(tops[k < 2 ? 0 : 1], a), [BAYS[k] + (k % 2 ? 1.8 : -1.8), 19.4, NORTH.gantry], 3, 10);
    span(end(tops[2], a), [BAYS[k], 19.4, SOUTH.gantry], 5, 12);
  });
  const bg = new THREE.BufferGeometry();
  bg.setAttribute('position', new THREE.Float32BufferAttribute(bus, 3));
  g.add(new THREE.LineSegments(bg, new THREE.LineBasicMaterial({ color: '#2a2a2a' })));
  return g;
}

// ---------- solar field south of the halls and east of the fence ----------
function panelBox(len, width) {
  const geo = boxUV(len, 0.12, width, 20, 0);
  const uv = geo.attributes.uv;
  for (let k = 8; k < 12; k++) uv.setY(k, uv.getY(k) * 20 / 2.3 * 2);
  return geo;
}

function buildSolarFarm() {
  const g = new THREE.Group();
  const sp = TX.solarPanel();
  const panelGeo = panelBox(90, 4.6);
  panelGeo.rotateY(Math.PI / 2);
  const mat = std({ map: sp.map, normalMap: sp.normal, color: '#7d8aa6', metalness: 0.0, roughness: 0.5, envMapIntensity: 0.22 });
  const back = std({ color: '#5d636a', metalness: 0.5, roughness: 0.5 });
  const panels = [], tubes = [], legs = [];
  const field = (xa, xb, za, zb) => {
    for (let x = xa; x <= xb; x += 7) for (let z = za; z <= zb; z += 98) {
      if (Math.abs(x - (xa + xb) / 2) < 6) continue; // service road through the middle
      panels.push(mat4(x, 2.0, z, 0, 1, 1, 1, 0, -0.16));
      tubes.push(mat4(x, 1.85, z));
      for (let dz = -42; dz <= 42; dz += 14) legs.push(mat4(x, 0.9, z + dz));
    }
  };
  field(-160, 640, 640, 1620);
  field(760, 1500, -560, 1620);
  field(404, 640, -290, 500);
  g.add(instanced(panelGeo, [back, back, mat, back, back, back], panels, { receive: false }));
  const tubeGeo = new THREE.CylinderGeometry(0.08, 0.08, 90, 6); tubeGeo.rotateX(Math.PI / 2);
  g.add(instanced(tubeGeo, back, tubes, { cast: false, receive: false }));
  g.add(instanced(new THREE.BoxGeometry(0.15, 1.8, 0.15), back, legs, { cast: false, receive: false }));
  const inv = [];
  for (let x = -100; x <= 1450; x += 260) inv.push(mat4(x + 3.5, 0, 1130));
  const invGeo = new THREE.BoxGeometry(2.5, 2.6, 6); invGeo.translate(0, 1.3, 0);
  g.add(instanced(invGeo, std({ color: '#e3e3de', roughness: 0.6 }), inv));
  return g;
}

// ---------- steam drifting off the rooftop coolers ----------
function buildSteam(units, r) {
  const N = 2600, pos = new Float32Array(N * 3), seed = new Float32Array(N * 2);
  const p = new THREE.Vector3();
  for (let i = 0; i < N; i++) {
    units[Math.floor(r() * units.length)].decompose(p, new THREE.Quaternion(), new THREE.Vector3());
    pos[i * 3] = p.x + (r() - 0.5) * 2; pos[i * 3 + 1] = p.y + 2.8; pos[i * 3 + 2] = p.z + (r() - 0.5) * 6;
    seed[i * 2] = r(); seed[i * 2 + 1] = r();
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('seed', new THREE.BufferAttribute(seed, 2));
  const mat = new THREE.ShaderMaterial({
    uniforms: { time: { value: 0 }, scale: { value: 600 }, tint: { value: new THREE.Color('#eef0f2') } },
    vertexShader: /* glsl */`
      #include <common>
      #include <logdepthbuf_pars_vertex>
      attribute vec2 seed; uniform float time, scale; varying float vA;
      void main() {
        float age = fract(time * (0.06 + seed.y * 0.05) + seed.x);
        vec3 p = position + vec3(age * 14.0 + sin(seed.x * 40.0) * 2.0, age * age * 18.0 + age * 5.0, age * 6.0);
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        gl_Position = projectionMatrix * mv;
        gl_PointSize = (3.0 + age * 20.0) * scale / -mv.z;
        vA = smoothstep(0.0, 0.12, age) * (1.0 - age) * 0.3;
        #include <logdepthbuf_vertex>
      }`,
    fragmentShader: /* glsl */`
      #include <common>
      #include <logdepthbuf_pars_fragment>
      uniform vec3 tint;
      varying float vA;
      void main() {
        #include <logdepthbuf_fragment>
        vec2 d = gl_PointCoord - 0.5;
        float a = smoothstep(0.5, 0.0, length(d)) * vA;
        if (a < 0.004) discard;
        gl_FragColor = vec4(tint, a);
      }`,
    transparent: true, depthWrite: false,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  points.renderOrder = 3;
  const night = new THREE.Color('#2b3240'), day = new THREE.Color('#eef0f2');
  return {
    points,
    update(t) { mat.uniforms.time.value = t; mat.uniforms.scale.value = innerHeight * 0.9; },
    setDaylight(d) { mat.uniforms.tint.value.copy(night).lerp(day, d); },
  };
}
