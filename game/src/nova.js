import * as THREE from 'three';
import { HALCYON, NOVA_PAD } from './heightfield.js';
import * as HF from './heightfield.js';
import { rng, canvasTex, mat4, instanced, nightEmissive, part, mergeParts } from './util.js';
import * as TX from './textures.js';
import { buildPalms, buildTrees, contactShadows } from './props.js';
import { crossCards, cardMaterial } from './scatter.js';
import { registerRoom, std as istd, glow, glassMat as clearGlass, plane, addLight, onUpdate } from './interiors.js';

// Nova's house: a modernist glass house on the hills above Halcyon (nova_home_ref, nv1, nv4).
// Built in a local frame where +z faces the city.
const std = (o) => new THREE.MeshStandardMaterial(o);

function interiorTex(lit) {
  return canvasTex(512, 128, (c, w, h) => {
    if (lit) {
      const grd = c.createLinearGradient(0, 0, 0, h); grd.addColorStop(0, '#ffe2b0'); grd.addColorStop(0.6, '#d99a5a'); grd.addColorStop(1, '#5a3a22');
      c.fillStyle = grd; c.fillRect(0, 0, w, h);
      for (let x = 30; x < w; x += 110) { const r = c.createRadialGradient(x, 18, 2, x, 18, 40); r.addColorStop(0, 'rgba(255,250,235,1)'); r.addColorStop(1, 'rgba(255,240,210,0)'); c.fillStyle = r; c.fillRect(x - 40, 0, 80, 70); }
    } else {
      const grd = c.createLinearGradient(0, 0, 0, h); grd.addColorStop(0, '#7f97a4'); grd.addColorStop(0.5, '#3a4a54'); grd.addColorStop(1, '#2a2f33');
      c.fillStyle = grd; c.fillRect(0, 0, w, h);
    }
    // furniture silhouettes: sofas, chairs, a table, plants, art
    c.fillStyle = lit ? 'rgba(40,26,18,0.85)' : 'rgba(20,24,28,0.6)';
    for (const [x, ww, hh] of [[40, 90, 26], [170, 60, 20], [250, 40, 34], [330, 110, 24], [460, 34, 46]]) c.fillRect(x, h - hh - 8, ww, hh);
    c.fillStyle = lit ? 'rgba(60,40,26,0.8)' : 'rgba(30,34,38,0.5)';
    for (const x of [120, 300, 420]) c.fillRect(x, 30, 28, 22);
    c.fillStyle = '#26303a';
    for (let x = 0; x < w; x += 64) c.fillRect(x, 0, 3, h);
    c.fillRect(0, 0, w, 4);
  });
}

export function buildNovaHome() {
  HF.heightAt(NOVA_PAD.x, NOVA_PAD.z); // make sure the pad elevation is computed
  const g = new THREE.Group();
  g.position.set(NOVA_PAD.x, HF.NOVA_ELEV, NOVA_PAD.z);
  g.rotation.y = Math.atan2(HALCYON.x - NOVA_PAD.x, HALCYON.z - NOVA_PAD.z);

  const white = std({ map: TX.stucco().map, color: '#f1efe9', roughness: 0.8 });
  const stone = std({ map: TX.rock().map, normalMap: TX.rock().normal, color: '#8a7f74', roughness: 0.9 });
  const pavers = std({ map: TX.concrete().map, color: '#e4ddcf', roughness: 0.85 });
  const glassMat = nightEmissive(std({ map: interiorTex(false), emissiveMap: interiorTex(true), emissive: '#ffffff', metalness: 0.55, roughness: 0.08 }), 1.5);
  const box = (w, h, d, x, y, z, m, cast = true, parent = g) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
    mesh.position.set(x, y + h / 2, z);
    mesh.castShadow = cast; mesh.receiveShadow = true;
    parent.add(mesh);
    return mesh;
  };

  // stone terrace between the house and the pool, a lawn, gravel beds and the drive
  const flat = (w, d, x, z, m, y = 0.06, tile = 2) => {
    const geo = new THREE.PlaneGeometry(w, d);
    const uv = geo.attributes.uv;
    for (let k = 0; k < uv.count; k++) uv.setXY(k, uv.getX(k) * w / tile, uv.getY(k) * d / tile);
    const p = new THREE.Mesh(geo, m);
    p.rotation.x = -Math.PI / 2; p.position.set(x, y, z); p.receiveShadow = true;
    g.add(p);
  };
  // the terrace, paved around the pool (x -8..20, z 10.5..17.5 with its coping)
  flat(58, 18.4, 2, 1.2, pavers, 0.06, 4);                       // house side, z -8 .. 10.4
  flat(18.4, 7.6, -17.8, 14.2, pavers, 0.06, 4);                  // west of the pool
  flat(10.4, 7.6, 25.8, 14.2, pavers, 0.06, 4);                   // east of the pool
  flat(30, 16, 30, -16, std({ map: TX.sand().map, color: '#6f8a45', roughness: 0.95 }), 0.05);
  flat(22, 40, -40, -8, std({ map: TX.concrete().map, color: '#cfc8bb', roughness: 0.9 }), 0.05);
  flat(14, 30, 40, 8, std({ map: TX.gravel().map, normalMap: TX.gravel().normal, roughness: 1 }), 0.04);
  flat(14, 30, -36, 22, std({ map: TX.gravel().map, normalMap: TX.gravel().normal, roughness: 1 }), 0.04);

  // ground floor: floor-to-ceiling glass around a stone core, open on the living room
  box(6, 4.2, 14.4, -17, 0, -18, stone);
  buildLiving(g, box, white);
  // upper floor: white cantilevered volume with a glass front
  box(34, 0.6, 18, 2, 4.2, -15.5, white);            // floor slab, overhanging the terrace
  box(34, 0.7, 18, 2, 8.4, -15.5, white);            // roof slab
  for (const s of [-1, 1]) box(0.6, 3.6, 16, 2 + s * 16.7, 4.8, -16.5, white);
  box(33, 3.6, 0.6, 2, 4.8, -24.2, white);
  const up = new THREE.Mesh(new THREE.BoxGeometry(32.8, 3.6, 0.15), [glassMat, glassMat, white, white, glassMat, glassMat]);
  up.position.set(2, 6.6, -8.8); g.add(up);
  const rail = std({ color: '#cfe3ea', metalness: 0.2, roughness: 0.05, transparent: true, opacity: 0.25 });
  box(33, 1.1, 0.06, 2, 4.8, -6.8, rail, false);
  // west wing with garage and roof terrace
  box(14, 3.6, 13, -27, 0, -15, white);
  const gdoor = new THREE.Mesh(new THREE.PlaneGeometry(5.5, 2.6), std({ color: '#3b3f44', metalness: 0.5, roughness: 0.4 }));
  gdoor.position.set(-34.02, 1.3, -14); gdoor.rotation.y = -Math.PI / 2; g.add(gdoor);
  const wingGlass = new THREE.Mesh(new THREE.BoxGeometry(12, 3, 0.12), [glassMat, glassMat, white, white, glassMat, glassMat]);
  wingGlass.position.set(-27, 1.7, -8.45); g.add(wingGlass);
  for (const [w, d, x, z] of [[14, 0.06, -27, -8.5], [0.06, 13, -34, -15], [0.06, 13, -20, -15]]) box(w, 1.1, d, x, 3.6, z, rail, false);
  // pergola terrace on the west side (nv1, left)
  box(12, 0.35, 10, -27, 3.4, -2, white);
  for (const [x, z] of [[-32.6, 2.6], [-21.4, 2.6], [-32.6, -6.6]]) box(0.25, 3.4, 0.25, x, 0, z, std({ color: '#2a2c2e', metalness: 0.6 }));
  // soffit downlights under the cantilever
  const dl = [];
  for (let x = -12; x <= 16; x += 4) for (const z of [-9, -12]) dl.push(mat4(x, 4.18, z));
  const dlGeo = new THREE.CircleGeometry(0.12, 12); dlGeo.rotateX(Math.PI / 2);
  g.add(instanced(dlGeo, nightEmissive(std({ color: '#ddd', emissive: '#fff2d8' }), 6), dl, { cast: false, receive: false }));

  // infinity pool along the city edge (nova_home_ref): turquoise mosaic lit from below at night,
  // a stone coping on three sides and a dark mosaic spill wall on the city side
  const pool = { x: 6, z: 14, w: 28, d: 7 };
  const poolTex = (lit) => canvasTex(512, 128, (c, w, h) => {
    // deeper toward the city edge: the floor darkens, the mosaic grid shows through
    const grd = c.createLinearGradient(0, 0, 0, h);
    grd.addColorStop(0, lit ? '#2fb9d6' : '#3aa9c0'); grd.addColorStop(1, lit ? '#0a5f86' : '#156a88');
    c.fillStyle = grd; c.fillRect(0, 0, w, h);
    c.strokeStyle = lit ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.16)'; c.lineWidth = 1;
    for (let x = 0; x < w; x += 3) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, h); c.stroke(); }
    for (let y = 0; y < h; y += 3) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); }
    // caustic ripples
    c.strokeStyle = lit ? 'rgba(200,250,255,0.22)' : 'rgba(255,255,255,0.18)'; c.lineWidth = 0.8;
    const r = rng(77);
    for (let k = 0; k < 900; k++) { const x = r() * w, y = r() * h; c.beginPath(); c.ellipse(x, y, 1.5 + r() * 3, 1 + r() * 2, r() * 3, 0, Math.PI * 2); c.stroke(); }
    // lane of underwater lights along the house-side wall
    if (lit) for (let x = 36; x < w; x += 72) { const q = c.createRadialGradient(x, 4, 1, x, 4, 26); q.addColorStop(0, 'rgba(230,255,255,0.8)'); q.addColorStop(1, 'rgba(120,230,255,0)'); c.fillStyle = q; c.fillRect(x - 26, 0, 52, 32); }
  });
  const waterMat = std({ map: poolTex(false), emissiveMap: poolTex(true), emissive: '#ffffff', roughness: 0.03, metalness: 0.15 });
  nightEmissive(waterMat, 0.85);
  const water = new THREE.Mesh(new THREE.PlaneGeometry(pool.w, pool.d), waterMat);
  water.rotation.x = -Math.PI / 2; water.position.set(pool.x, 0.13, pool.z); water.receiveShadow = true; g.add(water);
  // the water moves: drift the ripples slowly
  onUpdate((dt) => { for (const t of [waterMat.map, waterMat.emissiveMap]) { t.offset.x += dt * 0.004; t.offset.y = Math.sin(performance.now() * 0.0003) * 0.01; } });
  const coping = std({ map: TX.concrete().map, color: '#efe9de', roughness: 0.7 });
  for (const [w, d, x, z] of [[pool.w + 1.2, 0.6, pool.x, pool.z - pool.d / 2 - 0.3], [0.6, pool.d + 0.6, pool.x - pool.w / 2 - 0.3, pool.z + 0.3],
    [0.6, pool.d + 0.6, pool.x + pool.w / 2 + 0.3, pool.z + 0.3]]) box(w, 0.2, d, x, 0, z, coping);
  // infinity edge: the water spills over a dark mosaic wall on the city side
  const mosaic = std({ map: canvasTex(256, 64, (c, w, h) => {
    c.fillStyle = '#123a4c'; c.fillRect(0, 0, w, h);
    const r = rng(9);
    for (let y = 0; y < h; y += 4) for (let x = 0; x < w; x += 4) { c.fillStyle = `hsl(${195 + r() * 20},${50 + r() * 30}%,${14 + r() * 18}%)`; c.fillRect(x, y, 3, 3); }
  }, { repeat: [6, 1] }), roughness: 0.25, metalness: 0.2 });
  nightEmissive(Object.assign(mosaic, { emissive: new THREE.Color('#0b6f8f') }), 0.6);
  box(pool.w + 1.2, 3.35, 0.5, pool.x, -3.2, pool.z + pool.d / 2 + 0.25, mosaic);
  box(pool.w + 1.2, 0.04, 0.5, pool.x, 0.13, pool.z + pool.d / 2 + 0.25, waterMat, false);   // the sheet of water at the lip
  addLight(g, pool.x - 7, 0.6, pool.z, '#7fe8ff', 14, 14);
  addLight(g, pool.x + 7, 0.6, pool.z, '#7fe8ff', 14, 14);
  // loungers: a steel frame, a cushioned seat and a raised back, facing the pool
  const lounger = mergeParts([
    part(new THREE.BoxGeometry(0.72, 0.08, 1.4), '#d9d3c6', 0, 0.34, 0.2),
    part(new THREE.BoxGeometry(0.72, 0.08, 0.75), '#d9d3c6', 0, 0.52, -0.72, 0.55),
    part(new THREE.BoxGeometry(0.76, 0.05, 2.0), '#3a3c3f', 0, 0.27, 0),
    ...[[-0.33, 0.85], [0.33, 0.85], [-0.33, -0.85], [0.33, -0.85]].map(([x, z]) => part(new THREE.BoxGeometry(0.05, 0.27, 0.05), '#3a3c3f', x, 0.135, z)),
  ]);
  const lounge = [];
  for (let k = 0; k < 4; k++) lounge.push(mat4(-4 + k * 3.2, 0.06, 7.6, 0));   // backs to the house, facing the water
  g.add(instanced(lounger, std({ vertexColors: true, roughness: 0.75 }), lounge));
  // a low table between each pair
  g.add(instanced(new THREE.CylinderGeometry(0.28, 0.28, 0.4, 16), std({ color: '#2f3134', roughness: 0.4, metalness: 0.4 }), [mat4(-2.4, 0.26, 7.8), mat4(4, 0.26, 7.8)]));
  // stone retaining wall where the pad drops toward the city
  const ret = new THREE.Mesh(new THREE.CylinderGeometry(58.5, 60, 14, 64, 1, true, -Math.PI * 0.42, Math.PI * 0.84), stone);
  ret.position.y = -6.8; ret.rotation.y = 0; g.add(ret);

  // garden beds around the terrace (nova_home_ref): stone-edged beds of shrubs, ferny fronds and
  // agaves, warm uplights at their feet; after dark the foliage glows where the lights hit it
  const leafMat = (map, color, glowColor) => nightEmissive(cardMaterial(map, { color, emissive: glowColor, emissiveMap: map }), 0.22);
  const shrubMat = leafMat(TX.bushCard(), '#6f8f50', '#ffd9a0');
  const frondMat = leafMat(TX.canopyCard(), '#5e8a45', '#ffd9a0');
  const agaveMat = leafMat(TX.spikeCard(), '#9fb890', '#ffe2b0');
  const bedEdge = std({ map: TX.rock().map, color: '#9a8f82', roughness: 0.9 });
  const mulch = std({ map: TX.gravel().map, color: '#4a3d32', roughness: 1 });
  const beds = [
    { x: 24, z: -6, w: 10, d: 22, n: 26 },     // east of the house, the lush corner on the right of the still
    { x: -18, z: -3, w: 5, d: 9, n: 10 },      // between the living room and the pergola
    { x: -13.4, z: -8.2, w: 3.2, d: 1.4, n: 3 }, { x: 15.6, z: -8.2, w: 3.2, d: 1.4, n: 3 },   // planters at the glass corners
    { x: -14, z: 18.8, w: 9, d: 1.6, n: 5 },   // along the city edge, west of the pool
  ];
  const br = rng(31);
  const shrubs = [], fronds = [], agaves = [], uplights = [];
  for (const b of beds) {
    box(b.w, 0.32, b.d, b.x, 0, b.z, bedEdge);
    flat(b.w - 0.3, b.d - 0.3, b.x, b.z, mulch, 0.33, 1.5);
    for (let k = 0; k < b.n; k++) {
      const x = b.x + (br() - 0.5) * (b.w - 0.8), z = b.z + (br() - 0.5) * (b.d - 0.8), u = br(), s = 0.7 + br() * 0.7;
      if (u < 0.45) shrubs.push(mat4(x, 0.33, z, br() * 6, s * 1.3, s, s * 1.3));
      else if (u < 0.75) fronds.push(mat4(x, 0.33, z, br() * 6, s, s * 1.2, s));
      else agaves.push(mat4(x, 0.33, z, br() * 6, s * 0.8, s * 0.7, s * 0.8));
      if (k % 3 === 0) uplights.push(mat4(x + 0.4, 0.33, z + 0.4));
    }
  }
  g.add(instanced(crossCards(1.4, 1.2, 3), shrubMat, shrubs, { receive: false }));
  g.add(instanced(crossCards(1.7, 1.6, 3), frondMat, fronds, { receive: false }));
  g.add(instanced(crossCards(1.3, 1.1, 3), agaveMat, agaves, { receive: false }));
  g.add(instanced(new THREE.CylinderGeometry(0.07, 0.09, 0.14, 8), nightEmissive(std({ color: '#2b2b2b', emissive: '#ffd59a' }), 9), uplights, { cast: false }));
  addLight(g, 24, 1.2, -10, '#ffb866', 22, 14);
  addLight(g, 24, 1.2, 2, '#ffb866', 22, 14);
  addLight(g, -18, 1.2, -3, '#ffb866', 18, 12);
  // two small olive trees in the east bed, lit from below
  g.add(buildTrees([{ x: 21.5, z: -12, s: 0.7 }, { x: 26.5, z: 0, s: 0.8, ry: 1.3 }]));

  // planting and landscape lights
  g.add(buildPalms([[-14, 2, 9.5], [22, 3, 10.5], [-38, -2, 8]].map(([x, z, h], i) => ({ x, z, h, ry: i }))));
  g.add(buildTrees([{ x: 30, z: -20, s: 1.2 }, { x: -44, z: -24, s: 1.0, ry: 2 }]));
  const ag = [];
  for (let k = 0; k < 14; k++) { const a = (k / 14) * Math.PI * 2; ag.push(mat4(Math.cos(a) * 46, 0, Math.sin(a) * 40 - 4, a, 0.7, 0.6, 0.7)); }
  g.add(instanced(crossCards(1.6, 1.6, 3, -0.6), cardMaterial(TX.spikeCard(), { color: '#b9c9a8' }), ag, { receive: false }));
  const up2 = [];
  for (let k = 0; k < 16; k++) { const a = (k / 16) * Math.PI * 2; up2.push(mat4(Math.cos(a) * 44, 0.1, Math.sin(a) * 38 - 4)); }
  g.add(instanced(new THREE.CylinderGeometry(0.1, 0.12, 0.2, 8), nightEmissive(std({ color: '#333', emissive: '#ffd59a' }), 8), up2, { cast: false }));
  g.add(contactShadows([{ x: 0, z: -18, w: 38, d: 22 }, { x: -27, z: -15, w: 18, d: 17 }]));

  // Nova's car on the drive by the garage
  // where Nova's car is parked (the loaded model is added by placeVehicle)
  g.userData.spots = { nova_car: { x: -41, y: 0.05, z: -10, ry: 0.35 } };
  g.userData.cast = {
    nova: { x: -2.4, y: LIV.y, z: -15.2, ry: 0.55 },             // living room by the sectional
  };
  g.userData.views = { living: [[-4, LIV.y + 1.7, -23.4], [2.5, 1.0, -11]] };
  return g;
}

// ---------- the living room (nova_home_ref, nv2): grey sectional, wood floor, art, warm light ----------
const LIV = { x0: -14, x1: 14, z0: -25, z1: -11, h: 4.2, y: 0.07 };
function artTex(seed) {
  const r = rng(seed);
  return canvasTex(256, 320, (c, w, h) => {
    c.fillStyle = '#efe9df'; c.fillRect(0, 0, w, h);
    for (let k = 0; k < 7; k++) {
      c.fillStyle = ['#c8743a', '#2f3e46', '#d9b26a', '#8a3a2a', '#e8dcc8', '#4a5a50', '#1e1e1e'][Math.floor(r() * 7)];
      c.globalAlpha = 0.6 + r() * 0.4;
      if (r() < 0.5) { c.beginPath(); c.arc(r() * w, r() * h, 20 + r() * 90, 0, Math.PI * 2); c.fill(); } else c.fillRect(r() * w * 0.7, r() * h * 0.7, 30 + r() * 140, 10 + r() * 120);
    }
    c.globalAlpha = 1;
  }, { srgb: true });
}
function buildLiving(g, box, white) {
  const { x0, x1, z0, z1, h, y } = LIV;
  const oak = canvasTex(512, 512, (c, w, hh) => {
    for (let k = 0; k < 16; k++) { c.fillStyle = `hsl(30, ${30 + Math.random() * 10}%, ${42 + Math.random() * 10}%)`; c.fillRect(k * 32, 0, 31, hh); c.fillStyle = 'rgba(0,0,0,.3)'; c.fillRect(k * 32 + 31, 0, 1, hh); c.fillRect(k * 32, Math.random() * hh, 31, 1); }
    for (let k = 0; k < 900; k++) { c.fillStyle = `rgba(60,30,10,${Math.random() * 0.12})`; c.fillRect(Math.random() * w, Math.random() * hh, 1, 10 + Math.random() * 40); }
  });
  plane(g, x1 - x0, z1 - z0, 0, y, (z0 + z1) / 2, istd({ map: oak, roughness: 0.45 }), { rx: -Math.PI / 2, tile: 5 });
  plane(g, x1 - x0, z1 - z0, 0, h - 0.01, (z0 + z1) / 2, istd({ color: '#f2efe8', roughness: 0.9 }), { rx: Math.PI / 2 });
  box(x1 - x0, h, 0.3, 0, 0, z0 + 0.15, white);
  // glass to the city and the east lawn, with slim black mullions; faintly warm at night
  const glass = nightEmissive(clearGlass({ color: '#b9cdd6', emissive: '#ffcf96', opacity: 0.14 }), 0.12);
  const frame = istd({ color: '#16181a', roughness: 0.4, metalness: 0.6 });
  for (const [w, x, z, ry] of [[x1 - x0, 0, z1, 0], [z1 - z0, x1, (z0 + z1) / 2, Math.PI / 2]]) {
    const p = plane(g, w, h, x, h / 2, z, glass, { ry, receive: false }); p.renderOrder = 2;
    const n = Math.round(w / 3.5), m = [];
    for (let k = 0; k <= n; k++) { const a = -w / 2 + (w * k) / n; m.push(ry ? mat4(x, h / 2, z + a) : mat4(x + a, h / 2, z)); }
    g.add(instanced(new THREE.BoxGeometry(0.07, h, 0.07), frame, m));
  }
  // modular sectional with its back to the glass (nv2), a chaise on the east end
  const fabric = istd({ color: '#8d8a84', roughness: 1 });
  const cushion = istd({ color: '#9a978f', roughness: 1 });
  const sofa = new THREE.Group(); sofa.position.set(-2.5, y, -14.6); sofa.rotation.y = Math.PI; g.add(sofa);
  for (let k = 0; k < 4; k++) {
    box(1.05, 0.42, 1.1, -1.6 + k * 1.07, 0, 0, fabric, true, sofa);
    box(0.95, 0.16, 0.95, -1.6 + k * 1.07, 0.42, 0.05, cushion, true, sofa);
    box(1.0, 0.5, 0.28, -1.6 + k * 1.07, 0.5, -0.48, cushion, true, sofa);
  }
  box(1.05, 0.42, 1.9, -1.6 - 1.07, 0, 0.4, fabric, true, sofa);
  box(0.95, 0.16, 1.75, -1.6 - 1.07, 0.42, 0.45, cushion, true, sofa);
  box(1.0, 0.5, 0.28, -1.6 - 1.07, 0.5, -0.48, cushion, true, sofa);
  box(0.3, 0.62, 1.1, 2.75, 0, 0, fabric, true, sofa);
  plane(g, 6.5, 4.4, -2.5, y + 0.005, -17.4, istd({ color: '#d8d0c2', roughness: 1 }), { rx: -Math.PI / 2 });
  const stoneTop = istd({ color: '#d9d2c4', roughness: 0.35 });
  for (const [x, z, rad, ht] of [[-3.4, -17.2, 0.7, 0.38], [-1.6, -17.8, 0.5, 0.3]]) {
    const t = new THREE.Mesh(new THREE.CylinderGeometry(rad, rad, ht, 32), stoneTop); t.position.set(x, y + ht / 2, z); t.castShadow = t.receiveShadow = true; g.add(t);
  }
  // two lounge chairs facing the sofa, art and a credenza on the back wall, a stone hearth
  for (const x of [-4.6, -0.6]) {
    const c = new THREE.Group(); c.position.set(x, y, -20.2); c.rotation.y = x < -2 ? 0.25 : -0.25; g.add(c);
    box(0.85, 0.4, 0.85, 0, 0, 0, istd({ color: '#c9b9a0', roughness: 0.9 }), true, c);
    box(0.85, 0.45, 0.18, 0, 0.4, -0.34, istd({ color: '#c9b9a0', roughness: 0.9 }), true, c);
  }
  box(4.2, 0.6, 0.5, -2.5, y, z0 + 0.55, istd({ color: '#4a3424', roughness: 0.6 }));
  for (const [x, w, hh, seed] of [[-4.2, 1.6, 2.0, 3], [-1.0, 2.2, 1.5, 8]]) {
    box(w + 0.06, hh + 0.06, 0.04, x, 1.25 - 0.03, z0 + 0.32, istd({ color: '#1a1a1a' }), false);
    plane(g, w, hh, x, 1.25 + hh / 2, z0 + 0.345, istd({ map: artTex(seed), roughness: 0.8 }));
  }
  const hearth = box(0.2, 0.5, 2.4, x0 + 0.1, y + 0.4, -18, istd({ color: '#1a1614', roughness: 0.8 }));
  hearth.castShadow = false;
  box(0.05, 0.12, 2.1, x0 + 0.2, y + 0.55, -18, glow('#ff8a3a', 4), false);
  // dining at the east end under a linear pendant, a walnut kitchen run on the back wall
  const walnut = istd({ color: '#4f3726', roughness: 0.55 });
  box(3.0, 0.06, 1.1, 8.2, y + 0.72, -18.8, walnut);
  for (const [dx, dz] of [[-1.3, -0.4], [1.3, -0.4], [-1.3, 0.4], [1.3, 0.4]]) box(0.06, 0.72, 0.06, 8.2 + dx, y, -18.8 + dz, istd({ color: '#1a1a1a', metalness: 0.5 }));
  const chairs = [];
  for (const dx of [-0.9, 0, 0.9]) for (const s of [-1, 1]) chairs.push(mat4(8.2 + dx, y, -18.8 + s * 0.85, s > 0 ? Math.PI : 0));
  const chairGeo = mergeParts([part(new THREE.BoxGeometry(0.45, 0.05, 0.45), '#d8cfc0', 0, 0.45, 0), part(new THREE.BoxGeometry(0.45, 0.45, 0.05), '#d8cfc0', 0, 0.7, -0.2), ...[[-0.2, -0.2], [0.2, -0.2], [-0.2, 0.2], [0.2, 0.2]].map(([a, b]) => part(new THREE.CylinderGeometry(0.015, 0.015, 0.45, 6), '#1a1a1a', a, 0.22, b))]);
  g.add(instanced(chairGeo, istd({ vertexColors: true, roughness: 0.7 }), chairs));
  box(2.6, 0.04, 0.12, 8.2, h - 1.3, -18.8, glow('#ffd8a0', 3), false);
  box(8.5, 0.9, 0.65, 8.5, y, z0 + 0.62, walnut);
  box(8.5, 0.04, 0.68, 8.5, y + 0.9, z0 + 0.62, istd({ color: '#e8e4dc', roughness: 0.3 }));
  box(8.5, 0.8, 0.4, 8.5, 2.1, z0 + 0.5, walnut);
  // fiddle-leaf trees in big pots and an arc lamp over the sofa
  const trees = [];
  for (const [x, z, s] of [[-12.8, -12.2, 1.2], [12.8, -12.3, 1.0], [-12.8, -23.8, 1.1], [4.2, -23.8, 0.9]]) trees.push(mat4(x, y, z, Math.random() * 3, s, s, s));
  g.add(instanced(mergeParts([part(new THREE.CylinderGeometry(0.32, 0.26, 0.6, 16), '#e8e4dc', 0, 0.3, 0), part(new THREE.CylinderGeometry(0.03, 0.03, 1.2, 6), '#5a4030', 0, 1.1, 0), part(new THREE.IcosahedronGeometry(0.55, 1), '#3f6a34', 0, 1.9, 0), part(new THREE.IcosahedronGeometry(0.4, 1), '#4a7a3c', 0.25, 2.3, 0.1)]), istd({ vertexColors: true, roughness: 0.85 }), trees));
  const arc = new THREE.Mesh(new THREE.TorusGeometry(1.4, 0.025, 6, 24, Math.PI * 0.6), istd({ color: '#c9a86a', metalness: 0.9, roughness: 0.3 }));
  arc.position.set(-6.4, y + 1.0, -15.5); arc.rotation.y = Math.PI / 2; g.add(arc);
  const lampShade = new THREE.Mesh(new THREE.SphereGeometry(0.22, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2), glow('#ffd59a', 3)); lampShade.rotation.x = Math.PI; lampShade.position.set(-6.4, y + 1.95, -16.6); g.add(lampShade);
  // recessed downlights
  const dl = [];
  for (let x = -11; x <= 11; x += 3.6) for (const z of [-14, -18.5, -22.5]) dl.push(mat4(x, h - 0.02, z));
  const dlGeo = new THREE.CircleGeometry(0.09, 12); dlGeo.rotateX(Math.PI / 2);
  g.add(instanced(dlGeo, glow('#fff1d8', 5), dl, { cast: false, receive: false }));
  addLight(g, -3, h - 0.5, -17, '#ffd8a8', 40, 16);
  addLight(g, 8, h - 0.6, -19.5, '#ffd8a8', 30, 12);
  addLight(g, -9.5, h - 0.6, -15.5, '#ffcf96', 22, 12);
  registerRoom({ id: 'nova_living', name: "Nova's living room", minX: x0, maxX: x1, minZ: z0, maxZ: z1, floorY: y, frame: g });
}
