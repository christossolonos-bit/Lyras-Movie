import * as THREE from 'three';
import { rng, part, mergeParts, mat4, instanced, nightEmissive } from './util.js';
import { palmBark, shaggyBark, frondCard, canopyCard, blob } from './textures.js';
import { trailerSide } from './dctextures.js';
import { crossCards, cardMaterial } from './scatter.js';

// ---------- contact shadows ----------

let blobGeo = null;
export function contactShadows(list /* [{x, z, ry, w, d, y}] */) {
  if (!blobGeo) { blobGeo = new THREE.PlaneGeometry(1, 1); blobGeo.rotateX(-Math.PI / 2); }
  const mat = new THREE.MeshBasicMaterial({ map: blob(), transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4 });
  const m = instanced(blobGeo, mat, list.map((s) => mat4(s.x, (s.y || 0) + 0.04, s.z, s.ry || 0, s.w, 1, s.d)), { cast: false, receive: false });
  m.renderOrder = 2;
  return m;
}

// ---------- vehicles ----------

function extrude(points, depth, bevel = 0.04) {
  const shape = new THREE.Shape(points.map(([x, y]) => new THREE.Vector2(x, y)));
  const g = new THREE.ExtrudeGeometry(shape, { depth: depth - bevel * 2, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 1, curveSegments: 2 });
  g.translate(0, 0, -(depth - bevel * 2) / 2);
  g.rotateY(-Math.PI / 2); // profile x (front = +x) becomes +z
  return g;
}

const VEHICLES = {
  sedan: {
    body: [[-2.3, 0.3], [2.25, 0.3], [2.36, 0.55], [2.3, 0.76], [1.15, 0.92], [-1.55, 0.97], [-2.28, 0.92], [-2.36, 0.6]],
    glass: [[1.2, 0.9], [0.38, 1.4], [-0.92, 1.42], [-1.6, 0.95]],
    roof: [-0.92, 0.38, 1.42], width: 1.84, wheel: 0.33, axle: 1.38,
  },
  suv: {
    body: [[-2.35, 0.36], [2.3, 0.36], [2.42, 0.65], [2.38, 0.98], [1.45, 1.1], [-2.3, 1.12], [-2.42, 0.7]],
    glass: [[1.5, 1.08], [0.85, 1.72], [-2.25, 1.74], [-2.32, 1.1]],
    roof: [-2.28, 0.85, 1.74], width: 1.95, wheel: 0.4, axle: 1.45,
  },
  van: {
    body: [[-2.7, 0.35], [2.55, 0.35], [2.66, 0.75], [2.5, 1.15], [1.7, 1.3], [1.0, 2.25], [-2.7, 2.3]],
    glass: [[1.72, 1.27], [1.05, 2.16], [0.55, 2.16], [0.55, 1.27]],
    roof: [-2.6, 0.95, 2.27], width: 2.0, wheel: 0.37, axle: 1.7,
  },
  pickup: {
    body: [[-2.75, 0.42], [2.65, 0.42], [2.78, 0.72], [2.72, 1.05], [1.55, 1.15], [-0.6, 1.16], [-0.62, 1.05], [-2.72, 1.05], [-2.78, 0.75]],
    glass: [[1.6, 1.13], [1.0, 1.78], [-0.45, 1.8], [-0.58, 1.15]],
    roof: [-0.45, 1.0, 1.8], width: 2.0, wheel: 0.42, axle: 1.75,
  },
};
const vehicleGeo = {};
function buildVehicle(kind) {
  if (vehicleGeo[kind]) return vehicleGeo[kind];
  const v = VEHICLES[kind];
  const body = [colorize(extrude(v.body, v.width, 0.06), '#ffffff')];
  const [r0, r1, ry] = v.roof;
  const roof = new THREE.BoxGeometry(v.width - 0.22, 0.07, r1 - r0 - 0.15);
  roof.translate(0, ry + 0.01, (r0 + r1) / 2);
  body.push(colorize(roof, '#ffffff'));
  const glass = [colorize(extrude(v.glass, v.width - 0.2, 0.03), '#ffffff')];
  const trim = [];
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const tire = new THREE.CylinderGeometry(v.wheel, v.wheel, 0.26, 16);
    tire.rotateZ(Math.PI / 2); tire.translate(sx * (v.width / 2 - 0.12), v.wheel, sz * v.axle);
    const rim = new THREE.CylinderGeometry(v.wheel * 0.6, v.wheel * 0.6, 0.27, 12);
    rim.rotateZ(Math.PI / 2); rim.translate(sx * (v.width / 2 - 0.12), v.wheel, sz * v.axle);
    trim.push(colorize(tire, '#121212'), colorize(rim, '#8d9093'));
  }
  const front = Math.max(...v.body.map((p) => p[0]));
  const back = Math.min(...v.body.map((p) => p[0]));
  const lightY = v.body[2][1] + 0.12;
  for (const sx of [-1, 1]) {
    const hl = new THREE.BoxGeometry(0.42, 0.12, 0.06); hl.translate(sx * (v.width / 2 - 0.3), lightY, front + 0.01);
    const tl = new THREE.BoxGeometry(0.36, 0.14, 0.06); tl.translate(sx * (v.width / 2 - 0.26), lightY + 0.08, back - 0.01);
    trim.push(colorize(hl, '#f2f2ea'), colorize(tl, '#9a1414'));
  }
  const grille = new THREE.BoxGeometry(v.width * 0.45, 0.16, 0.05); grille.translate(0, lightY - 0.04, front + 0.02);
  trim.push(colorize(grille, '#1b1c1e'));
  return (vehicleGeo[kind] = { body: mergeParts(body), glass: mergeParts(glass), trim: mergeParts(trim) });
}
export function vehicleGeometry(kind) { return buildVehicle(kind); }
function colorize(g, c) { return part(g.index ? g.toNonIndexed() : g, c); }

const PAINT = ['#f2f2f0', '#f2f2f0', '#e9e9e6', '#c9ccd0', '#b4b8bd', '#2b2d31', '#1d1e20', '#8d1f1f', '#1f3c6b', '#6f7378', '#d8cfb8', '#3d5a3a', '#7a6a55'];

// list: [{x, z, ry, y?, color?, kind?}]; returns a group (body, glass, trim, contact shadows)
export function buildCars(list, seed = 1) {
  const r = rng(seed);
  const g = new THREE.Group();
  const paint = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.32, metalness: 0.55 });
  const glassMat = new THREE.MeshStandardMaterial({ color: '#1b2329', roughness: 0.06, metalness: 0.9 });
  const trimMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.6, metalness: 0.2 });
  const by = { sedan: [], suv: [], pickup: [], van: [] };
  for (const c of list) {
    const kind = c.kind || (r() < 0.5 ? 'sedan' : r() < 0.6 ? 'suv' : 'pickup');
    by[kind].push({ ...c, color: c.color || PAINT[Math.floor(r() * PAINT.length)] });
  }
  for (const kind of Object.keys(by)) {
    const L = by[kind];
    if (!L.length) continue;
    const geo = buildVehicle(kind);
    const mats = L.map((c) => mat4(c.x, c.y || 0, c.z, c.ry || 0));
    g.add(instanced(geo.body, paint, mats, { colors: L.map((c) => c.color) }));
    g.add(instanced(geo.glass, glassMat, mats, { receive: false }));
    g.add(instanced(geo.trim, trimMat, mats, { receive: false }));
  }
  g.add(contactShadows(list.map((c) => ({ x: c.x, y: c.y, z: c.z, ry: c.ry, w: 2.6, d: 5.6 }))));
  return g;
}

// Nova's car: silver-white electric sports coupe, full-width light bar, blue accents.
export function buildNovaCar() {
  const g = new THREE.Group();
  const body = extrude([[-2.35, 0.32], [2.3, 0.32], [2.42, 0.47], [2.38, 0.6], [1.4, 0.8], [0.45, 1.2], [-0.95, 1.24], [-2.05, 0.95], [-2.43, 0.7]], 1.98, 0.09);
  const paint = new THREE.MeshStandardMaterial({ color: '#e9ebed', metalness: 0.65, roughness: 0.22 });
  const canopy = extrude([[1.36, 0.82], [0.5, 1.19], [-0.9, 1.22], [-1.8, 0.96]], 1.64, 0.04);
  const glass = new THREE.MeshStandardMaterial({ color: '#10161b', metalness: 0.9, roughness: 0.05 });
  const lightBar = new THREE.MeshBasicMaterial({ color: '#bfe8ff', toneMapped: false });
  const blue = new THREE.MeshBasicMaterial({ color: '#3aa8ff', toneMapped: false });
  const red = new THREE.MeshBasicMaterial({ color: '#ff3a3a', toneMapped: false });
  const add = (geo, mat, cast = true) => { const m = new THREE.Mesh(geo, mat); m.castShadow = cast; g.add(m); return m; };
  add(body, paint); add(canopy, glass);
  const bar = new THREE.BoxGeometry(1.78, 0.045, 0.05); bar.translate(0, 0.6, 2.4); add(bar, lightBar, false);
  const rear = new THREE.BoxGeometry(1.7, 0.05, 0.05); rear.translate(0, 0.74, -2.42); add(rear, red, false);
  const rearBlue = new THREE.BoxGeometry(1.2, 0.025, 0.05); rearBlue.translate(0, 0.66, -2.42); add(rearBlue, blue, false);
  for (const s of [-1, 1]) {
    const line = new THREE.BoxGeometry(0.02, 0.03, 3.2); line.translate(s * 1.0, 0.42, 0.1); add(line, blue, false);
  }
  const tireM = new THREE.MeshStandardMaterial({ color: '#121212', roughness: 0.8 });
  const rimM = new THREE.MeshStandardMaterial({ color: '#1c1f22', metalness: 0.7, roughness: 0.3 });
  for (const sx of [-1, 1]) for (const sz of [-1.45, 1.42]) {
    const t = new THREE.CylinderGeometry(0.37, 0.37, 0.28, 24); t.rotateZ(Math.PI / 2); t.translate(sx * 0.86, 0.37, sz); add(t, tireM);
    const r = new THREE.CylinderGeometry(0.27, 0.27, 0.29, 18); r.rotateZ(Math.PI / 2); r.translate(sx * 0.86, 0.37, sz); add(r, rimM);
    const ring = new THREE.TorusGeometry(0.25, 0.012, 6, 24); ring.rotateY(Math.PI / 2); ring.translate(sx * 1.005, 0.37, sz); add(ring, blue, false);
  }
  g.add(contactShadows([{ x: 0, z: 0, w: 2.6, d: 5.6 }]));
  return g;
}

// Semi trucks (tractor + 53' trailer) and box trucks. list: [{x, z, ry, kind: 'semi'|'box', color?}]
let truckGeo = null;
function buildTruckGeo() {
  if (truckGeo) return truckGeo;
  const wheels = (axles, w, r) => {
    const parts = [];
    for (const z of axles) for (const sx of [-1, 1]) {
      const t = new THREE.CylinderGeometry(r, r, 0.5, 16); t.rotateZ(Math.PI / 2); t.translate(sx * (w / 2 - 0.25), r, z);
      const h = new THREE.CylinderGeometry(r * 0.55, r * 0.55, 0.52, 10); h.rotateZ(Math.PI / 2); h.translate(sx * (w / 2 - 0.25), r, z);
      parts.push(colorize(t, '#121212'), colorize(h, '#a7a9ab'));
    }
    return parts;
  };
  const box = (w, h, d, x, y, z, c) => { const b = new THREE.BoxGeometry(w, h, d); b.translate(x, y, z); return colorize(b, c); };
  // semi: front of tractor at +z
  const semiCab = mergeParts([
    box(2.45, 2.7, 2.4, 0, 2.55, 7.2, '#ffffff'),      // cab
    box(2.45, 3.1, 1.6, 0, 2.75, 5.3, '#ffffff'),      // sleeper
    box(2.3, 1.3, 2.0, 0, 1.75, 9.3, '#ffffff'),       // hood
    box(2.5, 0.5, 0.4, 0, 0.95, 10.35, '#ffffff'),     // bumper
  ]);
  const semiTrim = mergeParts([
    box(2.3, 1.0, 0.06, 0, 3.3, 8.42, '#1b2329'),      // windshield
    box(1.4, 0.9, 0.05, 0, 1.8, 10.31, '#202224'),     // grille
    box(1.0, 0.25, 9.5, 0, 0.95, 5.2, '#2a2b2d'),      // chassis
    ...[-1, 1].map((s) => { const c = new THREE.CylinderGeometry(0.33, 0.33, 1.4, 12); c.rotateX(Math.PI / 2); c.translate(s * 1.05, 0.9, 6.4); return colorize(c, '#c9cccf'); }),
    ...[-1, 1].map((s) => { const c = new THREE.CylinderGeometry(0.1, 0.1, 3.2, 8); c.translate(s * 1.0, 3.8, 4.4); return colorize(c, '#b8bbbe'); }),
    ...wheels([9.0, 4.4, 3.1], 2.5, 0.52),
    ...wheels([-6.6, -7.9], 2.6, 0.52),
    box(2.4, 0.3, 0.3, 0, 0.85, -9.3, '#2a2b2d'),
  ]);
  const trailer = new THREE.BoxGeometry(2.6, 2.9, 16.2); trailer.translate(0, 2.75, -1.2);
  // box truck
  const boxCab = mergeParts([box(2.3, 2.2, 2.2, 0, 2.0, 3.3, '#ffffff'), box(2.2, 0.9, 1.0, 0, 1.35, 4.8, '#ffffff')]);
  const boxTrim = mergeParts([
    box(2.1, 0.9, 0.06, 0, 2.55, 4.42, '#1b2329'),
    box(0.9, 0.22, 7.6, 0, 0.8, 0.2, '#2a2b2d'),
    ...wheels([4.0, -2.4], 2.3, 0.45),
  ]);
  const boxBody = new THREE.BoxGeometry(2.45, 2.9, 6.6); boxBody.translate(0, 2.55, -1.2);
  return (truckGeo = { semiCab, semiTrim, trailer, boxCab, boxTrim, boxBody });
}

export function buildTrucks(list, seed = 5) {
  const T = buildTruckGeo();
  const r = rng(seed);
  const g = new THREE.Group();
  const paint = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.3, metalness: 0.5 });
  const trim = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.55, metalness: 0.4 });
  const ts = trailerSide();
  const box = new THREE.MeshStandardMaterial({ map: ts.map, normalMap: ts.normal, roughness: 0.5, metalness: 0.3 });
  const plain = new THREE.MeshStandardMaterial({ color: '#e9e9e6', roughness: 0.5, metalness: 0.3 });
  const cabColors = ['#f2f2f0', '#b3201c', '#1f3c6b', '#2b2d31', '#f2f2f0', '#c9ccd0'];
  const semis = list.filter((t) => t.kind === 'semi'), boxes = list.filter((t) => t.kind !== 'semi');
  const M = (L) => L.map((t) => mat4(t.x, t.y || 0, t.z, t.ry || 0));
  if (semis.length) {
    g.add(instanced(T.semiCab, paint, M(semis), { colors: semis.map((t) => t.color || cabColors[Math.floor(r() * cabColors.length)]) }));
    g.add(instanced(T.semiTrim, trim, M(semis)));
    g.add(instanced(T.trailer, [box, box, plain, plain, plain, plain], M(semis)));
  }
  if (boxes.length) {
    g.add(instanced(T.boxCab, paint, M(boxes), { colors: boxes.map((t) => t.color || '#f2f2f0') }));
    g.add(instanced(T.boxTrim, trim, M(boxes)));
    g.add(instanced(T.boxBody, [box, box, plain, plain, plain, plain], M(boxes)));
  }
  g.add(contactShadows(list.map((t) => ({ x: t.x, z: t.z, ry: t.ry, w: 3.4, d: t.kind === 'semi' ? 22 : 10 }))));
  return g;
}

// ---------- street / site lighting ----------

let poleGeo = null, headGeo = null, lensGeo = null;
export function buildLightPoles(list, height = 9) {
  // list: [{x, z, ry}] ; the arm reaches toward local +x
  if (!poleGeo) {
    poleGeo = mergeParts([
      part(new THREE.CylinderGeometry(0.08, 0.15, height, 8), '#8d9399', 0, height / 2, 0),
      part(new THREE.CylinderGeometry(0.24, 0.28, 0.5, 8), '#9a9a96', 0, 0.25, 0),
      part(new THREE.CylinderGeometry(0.05, 0.06, 1.9, 6), '#8d9399', 0.9, height - 0.15, 0, 0, 0, Math.PI / 2 - 0.12),
    ]);
    headGeo = mergeParts([part(new THREE.BoxGeometry(0.85, 0.16, 0.38), '#6d7277', 1.85, height + 0, 0)]);
    lensGeo = new THREE.PlaneGeometry(0.7, 0.28);
    lensGeo.rotateX(Math.PI / 2); lensGeo.translate(1.85, height - 0.09, 0);
  }
  const g = new THREE.Group();
  const mats = list.map((p) => mat4(p.x, p.y || 0, p.z, p.ry || 0));
  g.add(instanced(poleGeo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.45, metalness: 0.6 }), mats, { receive: false }));
  g.add(instanced(headGeo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.5, metalness: 0.5 }), mats, { receive: false }));
  const lens = nightEmissive(new THREE.MeshStandardMaterial({ color: '#d8d8d0', emissive: '#ffe3b8', roughness: 0.3 }), 6);
  g.add(instanced(lensGeo, lens, mats, { cast: false, receive: false }));
  return g;
}

// ---------- trees ----------

function frondStrip(len, a0, droop, width, uvFlip) {
  const seg = 6, pos = [], uv = [], nor = [], idx = [];
  for (let s = 0; s <= seg; s++) {
    const t = s / seg, d = t * len * Math.cos(a0) * 0.95, y = t * len * Math.sin(a0) - droop * t * t;
    for (const side of [-1, 1]) {
      pos.push(d, y + Math.abs(side) * t * 0.1, side * width / 2 * (1 - t * 0.35));
      uv.push(t, (side < 0) !== uvFlip ? 0 : 1);
      nor.push(0, 1, 0);
    }
  }
  for (let s = 0; s < seg; s++) { const a = s * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3, a + 1, a + 2, a, a + 3, a + 2, a + 1); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  return g.toNonIndexed();
}

let palm = null;
function palmGeo() {
  if (palm) return palm;
  const R = rng(21);
  const trunk = new THREE.CylinderGeometry(0.24, 0.36, 1, 9, 1);
  trunk.translate(0, 0.5, 0);
  const fronds = [], dead = [];
  for (let k = 0; k < 18; k++) {
    const upper = k < 9;
    const f = frondStrip(3.6 + R() * 1.4, upper ? 0.75 + R() * 0.4 : 0.15 + R() * 0.3, upper ? 1.2 : 2.4, 1.25, R() < 0.5);
    f.rotateY((k / 9) * Math.PI * 2 + R() * 0.3);
    fronds.push(f);
  }
  for (let k = 0; k < 10; k++) {
    const f = frondStrip(2.4, -1.2, 0.1, 0.9, false);
    f.rotateY((k / 10) * Math.PI * 2);
    f.translate(0, -0.2, 0);
    dead.push(f);
  }
  return (palm = { trunk, crown: mergeParts(fronds), skirt: mergeParts(dead) });
}

// list: [{x, z, h, ry}]
export function buildPalms(list) {
  const geo = palmGeo();
  const g = new THREE.Group();
  const bark = palmBark();
  const bm = bark.map.clone(); bm.repeat.set(1, 4); bm.needsUpdate = true;
  g.add(instanced(geo.trunk, new THREE.MeshStandardMaterial({ map: bm, normalMap: bark.normal, roughness: 1 }),
    list.map((p) => mat4(p.x, p.y || 0, p.z, p.ry || 0, 1, p.h, 1))));
  const crowns = list.map((p) => mat4(p.x, (p.y || 0) + p.h, p.z, p.ry || 0));
  g.add(instanced(geo.crown, cardMaterial(frondCard()), crowns));
  g.add(instanced(geo.skirt, cardMaterial(frondCard(), { color: '#9a7a52' }), crowns));
  return g;
}

let tree = null;
function treeGeo() {
  if (tree) return tree;
  const R = rng(33);
  const wood = [], leaves = [];
  const limb = (x, y, z, rx, rz, len, rad) => {
    const c = new THREE.CylinderGeometry(rad * 0.6, rad, len, 6);
    c.translate(0, len / 2, 0);
    c.applyMatrix4(mat4(x, y, z, 0, 1, 1, 1, rx, rz));
    wood.push(c.toNonIndexed());
    return new THREE.Vector3(0, len, 0).applyEuler(new THREE.Euler(rx, 0, rz, 'YXZ')).add(new THREE.Vector3(x, y, z));
  };
  limb(0, 0, 0, 0.08, -0.05, 1.6, 0.22);
  for (let k = 0; k < 5; k++) {
    const a = (k / 5) * Math.PI * 2 + R() * 0.5, tilt = 0.6 + R() * 0.4;
    const tip = limb(0, 1.4, 0, Math.sin(a) * tilt, -Math.cos(a) * tilt, 2 + R() * 1.4, 0.13);
    const c = crossCards(3.4 + R(), 2.6, 3, -1.0);
    c.translate(tip.x, tip.y, tip.z);
    leaves.push(c);
  }
  const top = crossCards(3.8, 2.8, 3, 0); top.translate(0, 3.0, 0); leaves.push(top);
  return (tree = { wood: mergeParts(wood), leaves: mergeParts(leaves) });
}

// Mesquite / palo verde style desert shade tree. list: [{x, z, s, ry}]
export function buildTrees(list) {
  const geo = treeGeo();
  const g = new THREE.Group();
  const bark = shaggyBark();
  const mats = list.map((p) => mat4(p.x, p.y || 0, p.z, p.ry || 0, p.s || 1, p.s || 1, p.s || 1));
  g.add(instanced(geo.wood, new THREE.MeshStandardMaterial({ map: bark.map, normalMap: bark.normal, roughness: 1 }), mats));
  const lm = cardMaterial(canopyCard());
  const leaves = instanced(geo.leaves, lm, mats);
  const R = rng(7);
  for (let i = 0; i < list.length; i++) leaves.setColorAt(i, new THREE.Color().setHSL(0.17 + R() * 0.06, 0.25 + R() * 0.2, 0.75 + R() * 0.2));
  g.add(leaves);
  return g;
}
