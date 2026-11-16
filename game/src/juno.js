import * as THREE from 'three';
import { IRONWOOD, JUNO_PAD } from './heightfield.js';
import * as HF from './heightfield.js';
import { rng, canvasTex, speckle, mat4, instanced, nightEmissive, part, mergeParts } from './util.js';
import * as TX from './textures.js';
import { contactShadows } from './props.js';
import { registerRoom, std as istd, glow, glassMat, plane, loadRefTex, addLight } from './interiors.js';

// Juno's place (juno_loft_ref, ji1): a concrete-block garage with a big roll-up door, wide open
// on a workshop full of tool chests, engines and bikes, and a corrugated-steel loft above with
// big windows and a deck, reached by an outside stair. On the rocky edge of Ironwood.
// Local frame: +z faces down the hill toward town.
const std = (o) => new THREE.MeshStandardMaterial(o);

const W = 18, D = 12, H1 = 4.4, H2 = 3.6, LOFT = H1 + 0.4;

function drawerTex() {
  return canvasTex(128, 128, (c, w, h) => {
    c.fillStyle = '#b8261c'; c.fillRect(0, 0, w, h);
    speckle(c, w, h, 600, 0.08);
    for (let y = 6; y < h; y += 18) {
      c.fillStyle = 'rgba(0,0,0,.45)'; c.fillRect(4, y + 15, w - 8, 2);
      c.fillStyle = '#c9ccd0'; c.fillRect(14, y + 4, w - 28, 3);
    }
  });
}
function pegboardTex() {
  return canvasTex(512, 256, (c, w, h) => {
    c.fillStyle = '#8a6a48'; c.fillRect(0, 0, w, h);
    c.fillStyle = 'rgba(40,28,18,.55)';
    for (let x = 6; x < w; x += 12) for (let y = 6; y < h; y += 12) c.fillRect(x, y, 3, 3);
    // tool outlines and the tools on them
    const r = rng(11);
    for (let k = 0; k < 34; k++) {
      const x = 14 + r() * (w - 40), y = 14 + r() * (h - 70), l = 30 + r() * 50;
      c.fillStyle = ['#2a2a2a', '#6a6f75', '#b8261c', '#c9a215', '#3a3a3a'][Math.floor(r() * 5)];
      if (r() < 0.5) { c.fillRect(x, y, 5, l); c.fillRect(x - 5, y, 15, 9); } else { c.fillRect(x, y, 4, l); c.beginPath(); c.arc(x + 2, y + l, 8, 0, Math.PI * 2); c.fill(); }
    }
  });
}
function rugTex() {
  return canvasTex(256, 256, (c, w, h) => {
    c.fillStyle = '#7a2e22'; c.fillRect(0, 0, w, h);
    c.strokeStyle = '#d8b26a'; c.lineWidth = 6; c.strokeRect(14, 14, w - 28, h - 28);
    c.strokeStyle = '#1e3a4a'; c.lineWidth = 10; c.strokeRect(30, 30, w - 60, h - 60);
    c.fillStyle = '#d8b26a';
    for (let k = 0; k < 5; k++) { c.beginPath(); c.moveTo(w / 2, 60 + k * 30); c.lineTo(w / 2 + 40, 75 + k * 30); c.lineTo(w / 2, 90 + k * 30); c.lineTo(w / 2 - 40, 75 + k * 30); c.fill(); }
    speckle(c, w, h, 3000, 0.12);
  });
}

// A chopper after the one in ji1: fat rear tyre, raked fork, black tank, chrome V-twin.
function bikeGeo() {
  const chrome = '#c9ced3', black = '#141414';
  return mergeParts([
    part(new THREE.TorusGeometry(0.34, 0.1, 10, 28), black, -0.82, 0.44, 0, 0, Math.PI / 2, 0),
    part(new THREE.TorusGeometry(0.33, 0.07, 10, 28), black, 0.92, 0.4, 0, 0, Math.PI / 2, 0),
    part(new THREE.CylinderGeometry(0.24, 0.24, 0.08, 18), chrome, -0.82, 0.44, 0, 0, 0, Math.PI / 2),
    part(new THREE.CylinderGeometry(0.24, 0.24, 0.05, 18), chrome, 0.92, 0.4, 0, 0, 0, Math.PI / 2),
    part(new THREE.CylinderGeometry(0.025, 0.025, 1.0, 8), chrome, 0.72, 0.82, 0.08, 0, 0, 0.5),
    part(new THREE.CylinderGeometry(0.025, 0.025, 1.0, 8), chrome, 0.72, 0.82, -0.08, 0, 0, 0.5),
    part(new THREE.CylinderGeometry(0.03, 0.03, 1.3, 8), black, -0.05, 0.62, 0, 0, 0, Math.PI / 2 + 0.15),
    part(new THREE.CylinderGeometry(0.03, 0.03, 0.9, 8), black, 0.2, 0.92, 0, 0, 0, Math.PI / 2 - 0.25),
    part(new THREE.SphereGeometry(0.22, 16, 10).scale(1.6, 0.75, 0.9), black, 0.22, 1.02, 0),
    part(new THREE.BoxGeometry(0.55, 0.08, 0.3), '#5a3a22', -0.38, 0.9, 0),
    part(new THREE.CylinderGeometry(0.11, 0.12, 0.38, 14), chrome, 0.05, 0.72, 0, 0, 0, 0.45),
    part(new THREE.CylinderGeometry(0.11, 0.12, 0.38, 14), chrome, 0.32, 0.72, 0, 0, 0, -0.45),
    part(new THREE.BoxGeometry(0.4, 0.22, 0.24), '#6a6e72', 0.18, 0.5, 0),
    part(new THREE.CylinderGeometry(0.018, 0.018, 0.8, 8), chrome, 0.55, 1.22, 0, Math.PI / 2, 0, 0),
    part(new THREE.CylinderGeometry(0.035, 0.035, 0.9, 8), chrome, -0.35, 0.36, 0.17, 0, 0, Math.PI / 2 - 0.12),
  ]);
}
function engineGeo() {
  const chrome = '#bfc4c8';
  return mergeParts([
    part(new THREE.BoxGeometry(0.8, 0.06, 0.6), '#3a3a3a', 0, 0.45, 0),
    ...[[-0.35, -0.25], [0.35, -0.25], [-0.35, 0.25], [0.35, 0.25]].map(([x, z]) => part(new THREE.CylinderGeometry(0.03, 0.03, 0.42, 6), '#3a3a3a', x, 0.21, z)),
    part(new THREE.BoxGeometry(0.42, 0.3, 0.3), '#6a6e72', 0, 0.63, 0),
    part(new THREE.CylinderGeometry(0.13, 0.14, 0.42, 14), chrome, -0.12, 0.92, 0, 0, 0, 0.45),
    part(new THREE.CylinderGeometry(0.13, 0.14, 0.42, 14), chrome, 0.12, 0.92, 0, 0, 0, -0.45),
    part(new THREE.CylinderGeometry(0.16, 0.16, 0.12, 16), '#9a9fa4', 0, 0.62, 0.2, Math.PI / 2, 0, 0),
  ]);
}
function chestGeo() {
  return mergeParts([
    part(new THREE.BoxGeometry(1.3, 0.95, 0.6), '#b8261c', 0, 0.55, 0),
    part(new THREE.BoxGeometry(1.25, 0.5, 0.5), '#b8261c', 0, 1.27, -0.04),
    part(new THREE.BoxGeometry(1.32, 0.04, 0.62), '#1a1a1a', 0, 1.03, 0),
    ...[[-0.55, -0.22], [0.55, -0.22], [-0.55, 0.22], [0.55, 0.22]].map(([x, z]) => part(new THREE.CylinderGeometry(0.04, 0.04, 0.05, 8), '#111', x, 0.04, z, Math.PI / 2, 0, 0)),
  ]);
}

export function buildJunoHome() {
  HF.heightAt(JUNO_PAD.x, JUNO_PAD.z);
  const g = new THREE.Group();
  g.position.set(JUNO_PAD.x, HF.JUNO_ELEV, JUNO_PAD.z);
  g.rotation.y = Math.atan2(IRONWOOD.x - JUNO_PAD.x, IRONWOOD.z - JUNO_PAD.z);
  const r = rng(7);

  const block = std({ map: TX.blockWall().map, normalMap: TX.blockWall().normal, color: '#a9a49a', roughness: 0.95 });
  const ribs = canvasTex(256, 128, (c, w, h) => { c.fillStyle = '#5d564e'; c.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 10) { c.fillStyle = 'rgba(255,255,255,.08)'; c.fillRect(x, 0, 3, h); c.fillStyle = 'rgba(0,0,0,.2)'; c.fillRect(x + 6, 0, 2, h); } for (let k = 0; k < 40; k++) { c.fillStyle = `rgba(120,60,30,${Math.random() * 0.25})`; c.fillRect(Math.random() * w, Math.random() * h, 8 + Math.random() * 30, 4 + Math.random() * 20); } }, { repeat: [4, 1] });
  const steel = std({ map: ribs, roughness: 0.7, metalness: 0.45 });
  const dark = std({ color: '#2a2724', roughness: 0.8, metalness: 0.3 });
  const concrete = std({ map: TX.concrete().map, color: '#bdb6aa', roughness: 0.9 });
  const box = (w, h, d, x, y, z, m, cast = true, parent = g) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
    mesh.position.set(x, y + h / 2, z);
    mesh.castShadow = cast; mesh.receiveShadow = true;
    parent.add(mesh);
    return mesh;
  };

  // driveway and yard
  const flat = (w, d, x, z, m, y = 0.05) => { const p = new THREE.Mesh(new THREE.PlaneGeometry(w, d), m); p.rotation.x = -Math.PI / 2; p.position.set(x, y, z); p.receiveShadow = true; g.add(p); };
  flat(20, 16, 0, 12, concrete);
  flat(40, 34, 0, 0, std({ map: TX.gravel().map, color: '#cbb894', roughness: 1 }), 0.03);

  // ground floor: block garage with the door rolled up on the workshop. The door piers are
  // only at the front; the shop runs the full width behind them.
  box(0.4, H1, D, -W / 2 + 0.2, 0, 0, block);        // side walls
  box(0.4, H1, D, W / 2 - 0.2, 0, 0, block);
  box(4, H1, 0.6, -W / 2 + 2, 0, D / 2 - 0.3, block); // piers either side of the door
  box(4, H1, 0.6, W / 2 - 2, 0, D / 2 - 0.3, block);
  box(W, 1.0, 0.6, 0, H1 - 1.0, D / 2 - 0.3, block);  // header over the door
  box(W, H1, 0.4, 0, 0, -D / 2 + 0.2, block);        // back wall
  const roll = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, W - 8, 12), dark); roll.rotation.z = Math.PI / 2; roll.position.set(0, H1 - 0.6, D / 2 - 0.3); g.add(roll);
  buildWorkshop(g, box, r);

  // loft: corrugated steel box with big windows, cantilevered deck, shed roof
  box(W + 2, 0.4, D + 2, 0, H1, 0, concrete);
  box(0.3, H2, D, -W / 2 - 0.5, LOFT, 0, steel);
  box(0.3, H2, D, W / 2 + 0.5, LOFT, 0, steel);
  box(W + 1.3, H2, 0.3, 0, LOFT, -D / 2, steel);
  // glass front with steel mullions: the loft is lived in, and reads from the drive (jn1)
  const glass = glassMat({ color: '#c8b89a', opacity: 0.12 });
  const pane = new THREE.Mesh(new THREE.PlaneGeometry(W + 1, H2), glass);
  pane.position.set(0, LOFT + H2 / 2, D / 2 - 0.2); pane.renderOrder = 2; g.add(pane);
  const mull = [];
  for (let k = 0; k <= 6; k++) mull.push(mat4(-(W + 1) / 2 + k * (W + 1) / 6, LOFT + H2 / 2, D / 2 - 0.2));
  g.add(instanced(new THREE.BoxGeometry(0.12, H2, 0.14), dark, mull));
  box(W + 1, 0.12, 0.16, 0, LOFT + H2 - 0.12, D / 2 - 0.2, dark);
  box(W + 1, 0.12, 0.16, 0, LOFT, D / 2 - 0.2, dark);
  box(W + 1, 0.06, 0.1, 0, LOFT + 2.5, D / 2 - 0.2, dark, false);
  const roof = new THREE.Mesh(new THREE.BoxGeometry(W + 4, 0.25, D + 4), dark);
  roof.position.set(0, LOFT + H2 + 0.5, 0.5); roof.rotation.x = -0.06; roof.castShadow = true; g.add(roof);
  buildLoft(g, box, r);
  // deck along the front with railings, plants and string lights
  box(W + 2, 0.25, 3.2, 0, H1 + 0.15, D / 2 + 1.4, std({ color: '#6a5442', roughness: 0.9 }));
  const rail = [];
  for (let x = -W / 2 - 0.8; x <= W / 2 + 0.8; x += 1.2) rail.push(mat4(x, H1 + 0.4, D / 2 + 2.9));
  g.add(instanced(new THREE.BoxGeometry(0.05, 1.05, 0.05), dark, rail, { receive: false }));
  box(W + 2, 0.06, 0.06, 0, H1 + 1.4, D / 2 + 2.9, dark, false);
  const bulbs = [];
  for (let x = -W / 2; x <= W / 2; x += 1.1) bulbs.push(mat4(x, H1 + 2.6 - Math.abs(Math.sin(x * 0.6)) * 0.3, D / 2 + 2.85));
  g.add(instanced(new THREE.SphereGeometry(0.06, 6, 4), nightEmissive(std({ color: '#ddd', emissive: '#ffd9a0' }), 8), bulbs, { cast: false }));
  const pots = [];
  for (let k = 0; k < 7; k++) pots.push(mat4(-W / 2 + 1 + k * 2.6 + r(), H1 + 0.3, D / 2 + 2.3));
  g.add(instanced(mergeParts([part(new THREE.CylinderGeometry(0.3, 0.22, 0.5, 10), '#8a4a30', 0, 0.25, 0), part(new THREE.IcosahedronGeometry(0.45, 1), '#5a7a3a', 0, 0.75, 0)]), std({ vertexColors: true, roughness: 0.9 }), pots));

  // outside steel stair up the right side
  const steps = [];
  for (let k = 0; k < 16; k++) steps.push(mat4(W / 2 + 1.6, k * (H1 / 16), D / 2 - 1 - k * 0.6));
  g.add(instanced(new THREE.BoxGeometry(1.2, 0.08, 0.5), dark, steps));
  for (const s of [-0.6, 0.6]) {
    const stringer = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.25, 11.5), dark);
    stringer.position.set(W / 2 + 1.6 + s, H1 / 2, D / 2 - 5.6); stringer.rotation.x = Math.atan2(H1, 9.6); g.add(stringer);
  }

  // yard junk: drums, tire stacks, an engine block, a scrap-metal sculpture
  const drums = [], tires = [];
  for (let k = 0; k < 6; k++) drums.push(mat4(-W / 2 - 3 + (k % 3) * 1.1, 0, D / 2 + 3 + Math.floor(k / 3) * 1.1, r()));
  for (let k = 0; k < 4; k++) for (let s = 0; s < 3 + (k % 2); s++) tires.push(mat4(W / 2 + 4 + k * 1.4, s * 0.32 + 0.16, 4 + (k % 2) * 1.2, r(), 1, 1, 1, Math.PI / 2));
  g.add(instanced(new THREE.CylinderGeometry(0.3, 0.3, 0.9, 14).translate(0, 0.45, 0), std({ roughness: 0.6, metalness: 0.4 }), drums, { colors: drums.map((_, k) => ['#2a4a7a', '#8a2a1e', '#3a3a3a', '#b8902a'][k % 4]) }));
  g.add(instanced(new THREE.TorusGeometry(0.42, 0.16, 8, 18), std({ color: '#151515', roughness: 0.9 }), tires));
  const sculpt = mergeParts([
    part(new THREE.BoxGeometry(0.12, 3.2, 0.12), '#6a5a4a', 0, 1.6, 0, 0, 0, 0.3),
    part(new THREE.BoxGeometry(0.12, 2.6, 0.12), '#6a5a4a', 0.4, 1.3, 0, 0, 0, -0.5),
    part(new THREE.TorusGeometry(0.6, 0.07, 6, 16), '#7a6a5a', 0.3, 2.6, 0),
    part(new THREE.CylinderGeometry(0.35, 0.35, 0.5, 12), '#5a5550', 0, 0.25, 0),
  ]);
  const sc = new THREE.Mesh(sculpt, std({ vertexColors: true, roughness: 0.6, metalness: 0.6 }));
  sc.position.set(-W / 2 - 5, 0, 9); sc.castShadow = true; g.add(sc);
  g.add(contactShadows([{ x: 0, z: 0, w: W + 6, d: D + 6 }]));

  // walkable floors: the shop, the loft and deck, and the outside stair between them
  registerRoom({ id: 'juno_shop', name: "Juno's workshop", minX: -W / 2 + 0.4, maxX: W / 2 - 0.4, minZ: -D / 2 + 0.4, maxZ: D / 2, floorY: 0.06, frame: g });
  registerRoom({ id: 'juno_loft', name: "Juno's loft", minX: -W / 2 - 0.65, maxX: W / 2 + 1.05, minZ: -D / 2 + 0.15, maxZ: D / 2 + 3.0, floorY: LOFT, frame: g });
  registerRoom({ id: 'juno_stair', name: "Juno's stair", minX: W / 2 + 1.0, maxX: W / 2 + 2.2, minZ: -D / 2 + 1.4, maxZ: D / 2 - 0.4, floorY: (lx, lz) => Math.min(H1, Math.max(0, (D / 2 - 1 - lz) * (H1 / 16) / 0.6)) + 0.04, frame: g });

  // where Juno's trike is parked, nose out of the workshop
  g.userData.spots = { juno_trike: { x: 2.5, y: 0.05, z: 10.5, ry: 0.4 } };
  g.userData.cast = {
    juno: { x: -2.8, y: 0.06, z: -2.2, ry: 0.35 },               // workshop floor (ji1)
  };
  g.userData.views = {
    shop: [[-6.8, 1.76, 4.6], [2.5, 1.2, -5.5]],
    loft: [[7.6, LOFT + 1.7, 4.4], [-6, LOFT + 1.0, -4.5]],
  };
  return g;
}

// ---------- the workshop (ji1, jn1, jn2) ----------
function buildWorkshop(g, box, r) {
  const floorTex = canvasTex(512, 512, (c, w, h) => {
    c.fillStyle = '#8f877c'; c.fillRect(0, 0, w, h);
    for (let k = 0; k < 40; k++) { const x = Math.random() * w, y = Math.random() * h, rr = 10 + Math.random() * 60; const gr = c.createRadialGradient(x, y, 0, x, y, rr); gr.addColorStop(0, 'rgba(30,24,18,.35)'); gr.addColorStop(1, 'rgba(30,24,18,0)'); c.fillStyle = gr; c.fillRect(x - rr, y - rr, rr * 2, rr * 2); }
    speckle(c, w, h, 8000, 0.08);
  });
  plane(g, W - 0.8, D - 0.4, 0, 0.06, 0, istd({ map: floorTex, roughness: 0.75 }), { rx: -Math.PI / 2, tile: 6 });
  // open joists under the loft slab
  const joists = [];
  for (let z = -D / 2 + 0.6; z < D / 2 - 0.5; z += 0.8) joists.push(mat4(0, H1 - 0.15, z));
  g.add(instanced(new THREE.BoxGeometry(W - 0.8, 0.3, 0.12), istd({ color: '#4a3a2c', roughness: 0.9 }), joists, { cast: false }));
  plane(g, W - 0.8, D - 0.4, 0, H1 - 0.01, 0, istd({ color: '#3b342e', roughness: 0.95 }), { rx: Math.PI / 2 });

  // inside, the block shell is lined with weathered corrugated steel (ji1): ribs, seams, rust runs
  const corr = (rep) => canvasTex(256, 256, (c, w, h) => {
    c.fillStyle = '#6f6a62'; c.fillRect(0, 0, w, h);
    for (let x = 0; x < w; x += 8) {
      const g2 = c.createLinearGradient(x, 0, x + 8, 0);
      g2.addColorStop(0, 'rgba(255,255,255,.10)'); g2.addColorStop(0.45, 'rgba(255,255,255,.02)'); g2.addColorStop(0.6, 'rgba(0,0,0,.28)'); g2.addColorStop(1, 'rgba(0,0,0,.05)');
      c.fillStyle = g2; c.fillRect(x, 0, 8, h);
    }
    for (let x = 0; x < w; x += 64) { c.fillStyle = 'rgba(0,0,0,.35)'; c.fillRect(x, 0, 2, h); }     // panel laps
    for (let k = 0; k < 30; k++) { const x = Math.random() * w, y = Math.random() * h * 0.6; c.fillStyle = `rgba(110,55,25,${0.08 + Math.random() * 0.18})`; c.fillRect(x, y, 2 + Math.random() * 5, 20 + Math.random() * 90); }
    speckle(c, w, h, 3000, 0.06);
  }, { repeat: rep });
  const lining = (w, h) => istd({ map: corr([w / 2.4, h / 2.4]), roughness: 0.6, metalness: 0.45 });
  plane(g, D - 1.2, H1 - 0.3, -W / 2 + 0.405, (H1 - 0.3) / 2, 0, lining(D - 1.2, H1 - 0.3), { ry: Math.PI / 2 });
  plane(g, D - 1.2, H1 - 0.3, W / 2 - 0.405, (H1 - 0.3) / 2, 0, lining(D - 1.2, H1 - 0.3), { ry: -Math.PI / 2 });
  plane(g, W - 0.82, H1 - 0.3, 0, (H1 - 0.3) / 2, -D / 2 + 0.405, lining(W - 0.82, H1 - 0.3));
  plane(g, W - 0.82, 1.0, 0, H1 - 0.5, D / 2 - 0.605, lining(W - 0.82, 1.0), { ry: Math.PI });   // inside of the door header

  // the back wall from the still: shelves of parts, tools, little windows, all of it (ji1)
  const backZ = -D / 2 + 0.41;
  const shelfWall = (crop, w, x) => {
    const t = loadRefTex('ji1_workshop_floor.png', crop);
    const m = nightEmissive(istd({ map: t, emissiveMap: t, emissive: '#ffffff', roughness: 0.9 }), 0.5);
    plane(g, w, 3.0, x, 2.75, backZ, m);
  };
  shelfWall([0.40, 0.15, 0.62, 0.44], 4.2, -2.4);
  shelfWall([0.62, 0.13, 0.84, 0.43], 4.2, 1.8);
  shelfWall([0.83, 0.12, 0.98, 0.46], 3.0, 5.4);
  // pegboard and bench on the left wall, shelving on the right
  plane(g, 5.5, 1.6, -W / 2 + 0.41, 2.2, -1.5, istd({ map: pegboardTex(), roughness: 0.9 }), { ry: Math.PI / 2 });
  plane(g, 3.6, 1.6, -6.0, 1.9, backZ, istd({ map: pegboardTex(), roughness: 0.9 }));
  const wood = istd({ color: '#6e5136', roughness: 0.85 });
  const steelLeg = istd({ color: '#3a3c3e', roughness: 0.5, metalness: 0.7 });
  box(1.0, 0.08, 4.2, -W / 2 + 1.0, 0.92, -1.5, wood);
  for (const z of [-3.4, 0.4]) for (const x of [-W / 2 + 0.6, -W / 2 + 1.4]) box(0.07, 0.92, 0.07, x, 0, z, steelLeg);
  box(0.9, 0.05, 4.0, -W / 2 + 1.0, 0.3, -1.5, wood);
  const vise = new THREE.Mesh(mergeParts([part(new THREE.BoxGeometry(0.22, 0.16, 0.3), '#2f4a6a', 0, 0.08, 0), part(new THREE.CylinderGeometry(0.015, 0.015, 0.3, 6), '#bbb', 0.12, 0.08, 0, 0, 0, Math.PI / 2)]), istd({ vertexColors: true, metalness: 0.5, roughness: 0.5 }));
  vise.position.set(-W / 2 + 1.3, 1.0, 0.2); g.add(vise);
  const shelves = [], junk = [];
  for (const y of [0.4, 1.2, 2.0, 2.8]) for (const z of [-4.2, -1.8]) {
    shelves.push(mat4(W / 2 - 0.75, y, z));
    for (let k = 0; k < 4; k++) junk.push(mat4(W / 2 - 0.75 + (r() - 0.5) * 0.4, y + 0.05, z + (r() - 0.5) * 2, r() * 3, 0.6 + r() * 0.8, 0.6 + r() * 1.2, 0.6 + r() * 0.8));
  }
  g.add(instanced(new THREE.BoxGeometry(0.7, 0.04, 2.3), steelLeg, shelves));
  g.add(instanced(new THREE.BoxGeometry(0.25, 0.25, 0.3).translate(0, 0.125, 0), istd({ roughness: 0.7 }), junk, { colors: junk.map(() => ['#6a6e72', '#2a2a2a', '#b8261c', '#3a5a7a', '#c9a215', '#8a7a62'][Math.floor(r() * 6)]) }));

  // red tool chests (ji1): drawer fronts on the +z face
  const chest = new THREE.Mesh(chestGeo(), istd({ vertexColors: true, roughness: 0.4, metalness: 0.3 }));
  const drawers = istd({ map: drawerTex(), roughness: 0.4, metalness: 0.3 });
  for (const [x, z, ry] of [[-3.6, -5.15, 0], [-2.1, -5.15, 0], [3.9, -5.15, 0], [-W / 2 + 0.75, 2.6, Math.PI / 2], [W / 2 - 0.75, 1.8, -Math.PI / 2]]) {
    const c = chest.clone(); c.position.set(x, 0.06, z); c.rotation.y = ry; c.castShadow = c.receiveShadow = true; g.add(c);
    const f = new THREE.Mesh(new THREE.PlaneGeometry(1.24, 1.55), drawers); f.position.set(0, 0.86, 0.305); c.add(f);
  }

  // the chopper on the floor, an engine on a cart by the door, wheels and tyres, a welder
  const bike = new THREE.Mesh(bikeGeo(), istd({ vertexColors: true, roughness: 0.3, metalness: 0.7 }));
  bike.position.set(0.6, 0.06, -1.2); bike.rotation.y = 0.35; bike.castShadow = true; g.add(bike);
  const eng = new THREE.Mesh(engineGeo(), istd({ vertexColors: true, roughness: 0.35, metalness: 0.75 }));
  eng.position.set(-2.4, 0.06, 3.6); eng.rotation.y = -0.3; eng.castShadow = true; g.add(eng);
  const tyres = [];
  for (let k = 0; k < 5; k++) tyres.push(mat4(5.8 + (k > 2 ? 1.1 : 0), 0.2 + (k % 3) * 0.33, -2.6 + (k > 2 ? 0.8 : 0), r(), 1, 1, 1, Math.PI / 2));
  tyres.push(mat4(3.2, 0.5, 1.6, 0.4, 1.1, 1.1, 1.1, 0, 0.1));
  g.add(instanced(new THREE.TorusGeometry(0.42, 0.17, 10, 22), istd({ color: '#121212', roughness: 0.85 }), tyres));
  const welder = new THREE.Mesh(mergeParts([
    part(new THREE.BoxGeometry(0.5, 0.45, 0.7), '#2a4a7a', 0, 0.55, 0),
    part(new THREE.CylinderGeometry(0.12, 0.12, 1.2, 12), '#3a6a3a', 0, 0.9, -0.42),
    part(new THREE.BoxGeometry(0.55, 0.05, 0.9), '#333', 0, 0.3, -0.1),
    part(new THREE.CylinderGeometry(0.1, 0.1, 0.05, 12), '#111', 0, 0.1, 0.3, 0, 0, Math.PI / 2),
  ]), istd({ vertexColors: true, roughness: 0.5, metalness: 0.4 }));
  welder.position.set(4.6, 0.06, -0.6); welder.castShadow = true; g.add(welder);

  // string lights zig-zagging across the ceiling, and two hanging shop lights
  const bulbs = [], wire = [];
  for (let k = 0; k < 6; k++) {
    const z = -D / 2 + 1 + k * 1.9, x0 = -W / 2 + 0.6, x1 = W / 2 - 0.6;
    for (let s = 0; s <= 24; s++) {
      const t = s / 24, x = x0 + (x1 - x0) * t, y = H1 - 0.35 - Math.sin(t * Math.PI) * 0.45;
      if (s % 2 === 0) bulbs.push(mat4(x, y - 0.06, z));
      if (s < 24) { const t2 = (s + 1) / 24; wire.push(x, y, z, x0 + (x1 - x0) * t2, H1 - 0.35 - Math.sin(t2 * Math.PI) * 0.45, z); }
    }
  }
  g.add(instanced(new THREE.SphereGeometry(0.05, 6, 4), glow('#ffd9a0', 7), bulbs, { cast: false, receive: false }));
  const wg = new THREE.BufferGeometry(); wg.setAttribute('position', new THREE.Float32BufferAttribute(wire, 3));
  g.add(new THREE.LineSegments(wg, new THREE.LineBasicMaterial({ color: '#1a1714' })));
  for (const x of [-3.5, 3.5]) {
    box(1.4, 0.08, 0.25, x, H1 - 0.85, -1.5, istd({ color: '#555', metalness: 0.5 }), false);
    box(1.3, 0.02, 0.18, x, H1 - 0.87, -1.5, glow('#fff4e0', 3), false);
  }
  addLight(g, 0, H1 - 0.7, 0.5, '#ffd9a0', 45, 16);
  addLight(g, -4.5, H1 - 0.9, -3.5, '#ffe6c0', 22, 10);
  addLight(g, 4.5, H1 - 0.9, -3.5, '#ffe6c0', 22, 10);
}

// ---------- the loft (juno_loft_ref, jn1, jn3, ji7) ----------
function buildLoft(g, box, r) {
  const planks = canvasTex(256, 256, (c, w, h) => {
    for (let y = 0; y < h; y += 32) { c.fillStyle = `hsl(28, 35%, ${30 + Math.random() * 10}%)`; c.fillRect(0, y, w, 31); c.fillStyle = 'rgba(0,0,0,.4)'; c.fillRect(0, y + 31, w, 1); c.fillRect(Math.random() * w, y, 1, 31); }
    speckle(c, w, h, 3000, 0.08);
  });
  const IW = W + 0.7, ID = D - 0.6;
  plane(g, IW, ID, 0, LOFT + 0.01, -0.2, istd({ map: planks, roughness: 0.7 }), { rx: -Math.PI / 2, tile: 2.5 });
  plane(g, IW, ID, 0, LOFT + H2 - 0.02, -0.2, istd({ map: planks, color: '#a08a70', roughness: 0.9 }), { rx: Math.PI / 2, tile: 3 });
  // warm wood lining on the back wall: it glows at night, which is what the drive sees (jn1)
  const lining = nightEmissive(istd({ map: planks, color: '#c8a888', emissive: '#ffb56b', roughness: 0.85 }), 0.35);
  plane(g, IW, H2 - 0.05, 0, LOFT + H2 / 2, -D / 2 + 0.16, lining, { tile: 2.5 });

  // sitting area: a worn leather sofa, armchair, rug, low table
  plane(g, 4.6, 3.2, -3.2, LOFT + 0.015, 0.4, istd({ map: rugTex(), roughness: 1 }), { rx: -Math.PI / 2 });
  const leather = istd({ color: '#6a3f24', roughness: 0.55 });
  const sofa = new THREE.Group(); sofa.position.set(-3.2, LOFT, -1.6); g.add(sofa);
  box(3.0, 0.42, 0.95, 0, 0, 0, leather, true, sofa);
  box(3.0, 0.55, 0.22, 0, 0.42, -0.37, leather, true, sofa);
  for (const s of [-1, 1]) box(0.22, 0.62, 0.95, s * 1.4, 0, 0, leather, true, sofa);
  for (const x of [-0.7, 0.7]) box(1.3, 0.12, 0.8, x, 0.42, 0.05, istd({ color: '#7a4a2a', roughness: 0.6 }), true, sofa);
  const arm = new THREE.Group(); arm.position.set(-0.4, LOFT, 1.2); arm.rotation.y = -1.9; g.add(arm);
  box(1.0, 0.42, 0.9, 0, 0, 0, leather, true, arm); box(1.0, 0.5, 0.2, 0, 0.42, -0.35, leather, true, arm);
  box(1.4, 0.08, 0.7, -3.2, LOFT + 0.38, 0.4, istd({ color: '#3a2a1e', roughness: 0.6 }));
  box(0.08, 0.38, 0.6, -3.8, LOFT, 0.4, istd({ color: '#2a2a2a', metalness: 0.6 })); box(0.08, 0.38, 0.6, -2.6, LOFT, 0.4, istd({ color: '#2a2a2a', metalness: 0.6 }));

  // shelves of salvage along the back wall, two framed prints of the place (jn1, juno_loft_ref)
  const shelf = istd({ color: '#4a3826', roughness: 0.8 });
  const items = [];
  for (const x0 of [2.2, 6.0]) for (const y of [0.4, 1.1, 1.8, 2.5]) {
    box(3.2, 0.05, 0.4, x0, LOFT + y, -D / 2 + 0.4, shelf, false);
    for (let k = 0; k < 6; k++) items.push(mat4(x0 - 1.4 + k * 0.55 + r() * 0.2, LOFT + y + 0.05, -D / 2 + 0.42, r() * 3, 0.5 + r(), 0.6 + r() * 1.2, 0.5 + r() * 0.6));
  }
  g.add(instanced(new THREE.BoxGeometry(0.3, 0.3, 0.3).translate(0, 0.15, 0), istd({ roughness: 0.7 }), items, { colors: items.map(() => ['#8a4a30', '#2a4a5a', '#c9a215', '#5a7a3a', '#d8d0c0', '#3a3a3a', '#7a2a22'][Math.floor(r() * 7)]) }));
  for (const [name, x, w, h] of [['jn1_loft_night.png', -4.4, 1.7, 0.95], ['juno_loft_ref.png', -1.8, 1.2, 0.67]]) {
    box(w + 0.1, h + 0.1, 0.04, x, LOFT + 2.0 - 0.05, -D / 2 + 0.18, istd({ color: '#1a1410' }), false);
    plane(g, w, h, x, LOFT + 2.0 + h / 2, -D / 2 + 0.21, istd({ map: loadRefTex(name), roughness: 0.5 }));
  }

  // workbench by the window with a lamp, a guitar on a stand (ji7), Lyra's little speaker (jn3)
  box(2.4, 0.06, 0.8, 5.6, LOFT + 0.9, 3.8, istd({ color: '#7a5a3a', roughness: 0.7 }));
  for (const [x, z] of [[4.5, 3.5], [6.7, 3.5], [4.5, 4.1], [6.7, 4.1]]) box(0.06, 0.9, 0.06, x, LOFT, z, istd({ color: '#2a2a2a', metalness: 0.6 }));
  const speaker = new THREE.Group(); speaker.position.set(5.0, LOFT + 0.96, 3.7); g.add(speaker);
  box(0.16, 0.24, 0.16, 0, 0, 0, istd({ color: '#202224', roughness: 0.4 }), true, speaker);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.008, 8, 24), glow('#36e0ff', 4)); ring.position.set(0, 0.14, 0.082); speaker.add(ring);
  const guitar = new THREE.Mesh(mergeParts([
    part(new THREE.CylinderGeometry(0.2, 0.2, 0.09, 20), '#a86a32', 0, 0.35, 0, Math.PI / 2, 0, 0),
    part(new THREE.CylinderGeometry(0.15, 0.15, 0.09, 20), '#a86a32', 0, 0.62, 0, Math.PI / 2, 0, 0),
    part(new THREE.BoxGeometry(0.05, 0.6, 0.03), '#3a2414', 0, 1.0, 0),
    part(new THREE.BoxGeometry(0.08, 0.14, 0.03), '#2a1a10', 0, 1.36, 0),
  ]), istd({ vertexColors: true, roughness: 0.4 }));
  guitar.position.set(8.4, LOFT + 0.05, -2.0); guitar.rotation.set(-0.2, -0.9, 0); g.add(guitar);
  // plants in tins and pots everywhere (juno_loft_ref)
  const plants = [];
  for (const [x, z, s] of [[-8.6, 4.6, 1.2], [-8.6, -4.8, 1.0], [-6.2, 4.8, 0.8], [8.6, 4.8, 1.1], [3.0, 4.8, 0.7], [-0.8, -4.8, 0.9]]) plants.push(mat4(x, LOFT, z, r() * 3, s, s, s));
  g.add(instanced(mergeParts([part(new THREE.CylinderGeometry(0.25, 0.2, 0.45, 12), '#8a4a30', 0, 0.22, 0), part(new THREE.IcosahedronGeometry(0.45, 1), '#4f7a36', 0, 0.85, 0), part(new THREE.IcosahedronGeometry(0.3, 1), '#5f8a3e', 0.15, 1.2, 0.1)]), istd({ vertexColors: true, roughness: 0.9 }), plants));
  // pendant lamps and a floor lamp
  for (const [x, z] of [[-3.2, 0.2], [2.5, 0.5], [5.6, 3.6]]) {
    const cord = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 1.2, 4), istd({ color: '#111' })); cord.position.set(x, LOFT + H2 - 0.6, z); g.add(cord);
    const sh = new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.25, 16, 1, true), istd({ color: '#2a2724', metalness: 0.5, side: THREE.DoubleSide })); sh.position.set(x, LOFT + H2 - 1.25, z); g.add(sh);
    const bl = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 8), glow('#ffcf8a', 6)); bl.position.set(x, LOFT + H2 - 1.36, z); g.add(bl);
  }
  addLight(g, -3.2, LOFT + 2.1, 0.2, '#ffcf8a', 26, 10);
  addLight(g, 3.8, LOFT + 2.1, 1.5, '#ffcf8a', 22, 10);
}
