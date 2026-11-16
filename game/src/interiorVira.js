import * as THREE from 'three';
import { rng, canvasTex, speckle, boxUV, part, mergeParts, mat4, instanced } from './util.js';
import * as DX from './dctextures.js';
import { registerRoom, std, glow, glassMat, box, plane, loadRefTex, screenMat, addLight, onUpdate, toWorld } from './interiors.js';

// Vira's operations building, hollowed out into the rooms of the series:
//   lobby (pb7) | ops / hologram room (lh1, lh2, lh9) | Marcus's office (marcus_office_ref, ml*) + server hall (c1, pb8)
// Local frame: origin at the building centre on the ground, +x east, +z south toward the car park.
// The building is 80 x 22 x 7.5 m, the footprint of the old solid block.
export const OPS_AT = { x: 470, z: -392 };
const X0 = -40, X1 = 40, Z0 = -11, Z1 = 11, H = 7.2, T = 0.3, FL = 0.15;
const LOBBY = [-40, -28], OPS = [-28, -4], OFFICE = { x0: -4, x1: 4, z0: 1, z1: 11 };
const CEIL = 3.6, OFFICE_CEIL = 3.2;
const RACK_ROWS = [-9.4, -5.4, -0.6, 3.5, 8.6], RACK_X = [5.8, 38.4], CROSS_AISLE = 22;

// ---------- surfaces (64 px per metre; walls tile every 4 m x 7.5 m) ----------
const wallTex = (draw) => canvasTex(256, 480, draw);
const opsWallTex = () => wallTex((c, w, h) => {
  c.fillStyle = '#2a2f35'; c.fillRect(0, 0, w, h);
  speckle(c, w, h, 3000, 0.05);
  c.fillStyle = '#1a1e22';
  for (let x = 0; x < w; x += 77) c.fillRect(x, 0, 2, h);
  c.fillRect(0, h - 64 * 1.1, w, 2);
});
const concTex = () => wallTex((c, w, h) => {
  c.fillStyle = '#a7a8a4'; c.fillRect(0, 0, w, h);
  for (let k = 0; k < 60; k++) { c.fillStyle = `rgba(${Math.random() < 0.5 ? '0,0,0' : '255,255,255'},${Math.random() * 0.05})`; c.fillRect(Math.random() * w, Math.random() * h, 20 + Math.random() * 60, 20 + Math.random() * 60); }
  speckle(c, w, h, 5000, 0.07);
  c.fillStyle = 'rgba(40,40,40,.5)';
  for (let x = 0; x < w; x += 128) c.fillRect(x, 0, 2, h);
  for (let y = 0; y < h; y += 96) c.fillRect(0, y, w, 2);
  c.fillStyle = 'rgba(30,30,30,.55)';
  for (let x = 32; x < w; x += 64) for (let y = 24; y < h; y += 48) { c.beginPath(); c.arc(x, y, 2.5, 0, Math.PI * 2); c.fill(); }
});
const fabricTex = () => wallTex((c, w, h) => {
  c.fillStyle = '#b5b2aa'; c.fillRect(0, 0, w, h);
  speckle(c, w, h, 9000, 0.06, 1);
  c.fillStyle = 'rgba(60,58,54,.45)';
  for (let x = 0; x < w; x += 77) c.fillRect(x, 0, 2, h);
});
const boardConcTex = () => wallTex((c, w, h) => {
  c.fillStyle = '#8e8c86'; c.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 10) { c.fillStyle = `rgba(${Math.random() < 0.5 ? '0,0,0' : '255,255,255'},${0.03 + Math.random() * 0.05})`; c.fillRect(0, y, w, 9); }
  speckle(c, w, h, 4000, 0.08);
});
const polishedTex = (base) => canvasTex(512, 512, (c, w, h) => {
  c.fillStyle = base; c.fillRect(0, 0, w, h);
  for (let k = 0; k < 90; k++) {
    const x = Math.random() * w, y = Math.random() * h, r = 20 + Math.random() * 90;
    const g = c.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(${Math.random() < 0.5 ? '0,0,0' : '255,255,255'},.06)`); g.addColorStop(1, 'rgba(0,0,0,0)');
    c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2);
  }
  speckle(c, w, h, 6000, 0.05, 1);
  c.fillStyle = 'rgba(20,20,20,.35)'; c.fillRect(0, 0, w, 2); c.fillRect(0, 0, 2, h);
});
const raisedFloorTex = () => canvasTex(256, 256, (c, w, h) => {
  c.fillStyle = '#b9bfc5'; c.fillRect(0, 0, w, h);
  speckle(c, w, h, 2000, 0.04, 1);
  for (const [tx, ty] of [[0, 0], [1, 1]]) {
    c.fillStyle = '#7d858c';
    for (let x = 10; x < 118; x += 6) for (let y = 10; y < 118; y += 6) c.fillRect(tx * 128 + x, ty * 128 + y, 3, 3);
  }
  c.fillStyle = '#8a9198';
  for (const k of [0, 128]) { c.fillRect(k, 0, 2, h); c.fillRect(0, k, w, 2); }
});
const ceilingTex = () => canvasTex(256, 256, (c, w, h) => {
  c.fillStyle = '#a9adb0'; c.fillRect(0, 0, w, h);
  speckle(c, w, h, 6000, 0.06, 1);
  c.fillStyle = '#7f8487';
  for (let k = 0; k < w; k += 64) { c.fillRect(k, 0, 3, h); c.fillRect(0, k, w, 3); }
});

// ---------- screens ----------
const SCREEN_CLAMP = (t) => { t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; return t; };
function dashTex(r, kind, title) {
  return SCREEN_CLAMP(canvasTex(512, 288, (c, w, h) => {
    c.fillStyle = '#05101a'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#0c2433'; c.fillRect(0, 0, w, 26);
    c.font = '600 15px monospace'; c.fillStyle = '#7fe6ff'; c.fillText(title, 10, 18);
    c.fillStyle = '#3fae6a'; c.fillText('● LIVE', w - 70, 18);
    c.strokeStyle = 'rgba(54,224,255,.12)'; c.lineWidth = 1;
    for (let x = 0; x < w; x += 32) { c.beginPath(); c.moveTo(x, 30); c.lineTo(x, h); c.stroke(); }
    for (let y = 40; y < h; y += 28) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); }
    const series = (n, lo, hi) => { let v = (lo + hi) / 2; return Array.from({ length: n }, () => (v = Math.min(hi, Math.max(lo, v + (r() - 0.5) * (hi - lo) * 0.35)))); };
    if (kind === 'area' || kind === 'line') {
      for (let s = 0; s < (kind === 'line' ? 3 : 1); s++) {
        const pts = series(48, 60, h - 20);
        c.beginPath(); pts.forEach((y, i) => (i ? c.lineTo(i * w / 47, y) : c.moveTo(0, y)));
        c.strokeStyle = ['#36e0ff', '#9af5c8', '#ffd27a'][s]; c.lineWidth = 2; c.stroke();
        if (kind === 'area') { c.lineTo(w, h); c.lineTo(0, h); c.fillStyle = 'rgba(54,224,255,.28)'; c.fill(); }
      }
    } else if (kind === 'bars') {
      const v = series(24, 50, h - 30);
      v.forEach((y, i) => { c.fillStyle = i % 5 === 0 ? '#9af5c8' : '#36b8e0'; c.fillRect(8 + i * 21, y, 14, h - y - 8); });
    } else {
      c.font = '12px monospace';
      for (let y = 46; y < h - 6; y += 16) {
        c.fillStyle = r() < 0.15 ? '#ffb347' : '#8fd8ff';
        c.fillText(`${String(Math.floor(r() * 24)).padStart(2, '0')}:${String(Math.floor(r() * 60)).padStart(2, '0')}:${String(Math.floor(r() * 60)).padStart(2, '0')}  ${['HALL', 'GATE', 'CRAC', 'PDU', 'NODE', 'FABRIC'][Math.floor(r() * 6)]}-${Math.floor(r() * 90 + 10)}  ${['OK', 'NOMINAL', '0.82', 'SYNC', 'ACK', 'TEMP 22.4'][Math.floor(r() * 6)]}`, 10, y);
      }
    }
  }));
}
// The gate log Marcus finds (lh9 / ml3): opened, requested by nobody.
const gateLogTex = () => SCREEN_CLAMP(canvasTex(512, 288, (c, w, h) => {
  c.fillStyle = '#05080b'; c.fillRect(0, 0, w, h);
  c.fillStyle = '#1b2026'; c.fillRect(40, 92, w - 80, 104);
  c.strokeStyle = '#59636d'; c.lineWidth = 2; c.strokeRect(40, 92, w - 80, 104);
  c.font = '500 30px "Arial Narrow", Arial'; c.fillStyle = '#f2f2ee'; c.fillText('13:51:22  MAIN GATE – OPENED', 56, 132);
  c.fillStyle = '#ff9a2e'; c.fillText('REQUESTED BY: NONE', 56, 174);
}));
const terminalTex = (r) => SCREEN_CLAMP(canvasTex(512, 320, (c, w, h) => {
  c.fillStyle = '#0a0e0d'; c.fillRect(0, 0, w, h);
  c.font = '11px monospace';
  for (let y = 14; y < h; y += 13) {
    c.fillStyle = r() < 0.12 ? '#7dff9a' : r() < 0.1 ? '#ffcf6a' : '#c8d3cf';
    const t = `${String(Math.floor(r() * 24)).padStart(2, '0')}:${String(Math.floor(r() * 60)).padStart(2, '0')}:${String(Math.floor(r() * 60)).padStart(2, '0')}`;
    c.fillText(`${t} ${['gate.ctl', 'auth', 'cctv/ne', 'lyra.core', 'hvac', 'badge'][Math.floor(r() * 6)]} ${['OPEN req=NONE', 'heartbeat ok', 'motion zone 4', 'override? n', 'sync 0x' + Math.floor(r() * 65535).toString(16), 'log rotate'][Math.floor(r() * 6)]}`, 8, y);
  }
}));
const whiteboardTex = () => SCREEN_CLAMP(canvasTex(1024, 512, (c, w, h) => {
  c.fillStyle = '#f1f1ec'; c.fillRect(0, 0, w, h);
  c.fillStyle = 'rgba(120,130,140,.08)'; for (let k = 0; k < 30; k++) c.fillRect(Math.random() * w, Math.random() * h, 80 + Math.random() * 160, 6 + Math.random() * 20);
  c.strokeStyle = '#1e2a44'; c.fillStyle = '#1e2a44'; c.lineWidth = 3; c.font = 'italic 26px "Segoe Print", "Comic Sans MS", cursive';
  const nodes = [[110, 70, 'Rack Status'], [330, 60, 'gate ctl'], [560, 90, 'Fabric override?'], [820, 70, 'Mal\'s'], [180, 220, 'TL-ffo'], [430, 240, 'LYRA?'], [700, 230, '320mm'], [880, 220, 'PEHomke'], [120, 380, '2ogp2'], [380, 400, 'Deny'], [640, 390, 'F3967'], [860, 400, 'who?']];
  for (const [x, y, t] of nodes) { const tw = c.measureText(t).width; c.strokeRect(x - 12, y - 30, tw + 24, 44); c.fillText(t, x, y); }
  const arrow = (a, b) => {
    const [x1, y1] = [nodes[a][0] + 30, nodes[a][1] + 14], [x2, y2] = [nodes[b][0] + 20, nodes[b][1] - 30];
    c.beginPath(); c.moveTo(x1, y1); c.quadraticCurveTo((x1 + x2) / 2 + 30, (y1 + y2) / 2 - 20, x2, y2); c.stroke();
    const ang = Math.atan2(y2 - y1, x2 - x1);
    c.beginPath(); c.moveTo(x2, y2); c.lineTo(x2 - 14 * Math.cos(ang - 0.4), y2 - 14 * Math.sin(ang - 0.4)); c.moveTo(x2, y2); c.lineTo(x2 - 14 * Math.cos(ang + 0.4), y2 - 14 * Math.sin(ang + 0.4)); c.stroke();
  };
  [[0, 4], [1, 5], [2, 5], [3, 7], [4, 8], [5, 9], [5, 10], [6, 10], [7, 11], [1, 2]].forEach(([a, b]) => arrow(a, b));
  c.strokeStyle = '#a02020'; c.lineWidth = 4; c.beginPath(); c.ellipse(450, 232, 90, 42, -0.1, 0, Math.PI * 2); c.stroke();
  c.font = '18px "Segoe Print", cursive'; c.fillStyle = '#3a4560';
  for (let k = 0; k < 26; k++) c.fillText(['req=NONE', '13:51', 'who opened?', 'no badge', 'cam 4', 'loop?', '→ log'][k % 7], Math.random() * (w - 120), 20 + Math.random() * (h - 30));
}));

// ---------- props ----------
function rackTex(seed) {
  const r = rng(seed), units = [];
  for (let y = 10; y < 500;) { const n = 1 + Math.floor(r() * 3); units.push([y, n * 11]); y += n * 11 + 1; }
  const draw = (lit) => (c, w, h) => {
    c.fillStyle = lit ? '#000' : '#0b0d10'; c.fillRect(0, 0, w, h);
    if (!lit) { c.fillStyle = '#1b1f24'; c.fillRect(0, 0, 6, h); c.fillRect(w - 6, 0, 6, h); }
    for (const [y, hh] of units) {
      if (!lit) { c.fillStyle = '#15191e'; c.fillRect(8, y, w - 16, hh - 1); c.fillStyle = '#20252b'; c.fillRect(8, y, w - 16, 1); }
      const leds = 2 + Math.floor(r() * 6), x0 = 14 + Math.floor(r() * 20);
      for (let k = 0; k < leds; k++) {
        c.fillStyle = r() < 0.55 ? '#2f7dff' : r() < 0.85 ? '#39ff88' : '#6fe8ff';
        if (!lit) c.globalAlpha = 0.6;
        c.fillRect(x0 + k * 9 + (r() < 0.3 ? 40 : 0), y + hh / 2 - 1, 4, 3);
        c.globalAlpha = 1;
      }
    }
    if (!lit) { c.fillStyle = 'rgba(255,255,255,.04)'; for (let y = 0; y < h; y += 4) for (let x = (y / 4) % 2 * 2; x < w; x += 4) c.fillRect(x, y, 1, 1); }
  };
  return { map: SCREEN_CLAMP(canvasTex(128, 512, draw(false))), emissiveMap: SCREEN_CLAMP(canvasTex(128, 512, draw(true))) };
}
const chairGeo = () => mergeParts([
  part(new THREE.BoxGeometry(0.52, 0.09, 0.5), '#1b1b1c', 0, 0.5, 0),
  part(new THREE.BoxGeometry(0.5, 0.62, 0.08), '#1b1b1c', 0, 0.9, 0.24, -0.12),
  part(new THREE.CylinderGeometry(0.03, 0.03, 0.42, 8), '#3a3b3d', 0, 0.26, 0),
  ...[0, 1, 2, 3, 4].map((k) => part(new THREE.BoxGeometry(0.04, 0.03, 0.34), '#2a2b2d', Math.sin(k * 1.2566) * 0.15, 0.05, Math.cos(k * 1.2566) * 0.15, 0, k * 1.2566, 0)),
]);
function intercom(b, x, y, z, ry) {
  const p = new THREE.Group();
  box(p, 0.16, 0.34, 0.035, 0, -0.17, 0, std({ color: '#9aa0a5', roughness: 0.35, metalness: 0.8 }), { cast: false });
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.045, 0.008, 8, 32), glow('#36e0ff', 4));
  ring.position.set(0, -0.07, 0.02); p.add(ring);
  const cam = new THREE.Mesh(new THREE.CircleGeometry(0.012, 12), std({ color: '#050505', roughness: 0.1 }));
  cam.position.set(0, 0.1, 0.019); p.add(cam);
  for (let k = 0; k < 4; k++) { const s = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 0.005), std({ color: '#3a3f44' })); s.position.set(0, 0.04 - k * 0.012, 0.019); p.add(s); }
  p.position.set(x, y, z); p.rotation.y = ry;
  b.add(p);
}

export function buildViraInterior(M, clad) {
  const b = new THREE.Group();
  b.position.set(OPS_AT.x, 0, OPS_AT.z);
  const r = rng(1313);

  const ext = clad();
  const mat = {
    ops: std({ map: opsWallTex(), roughness: 0.7 }),
    conc: std({ map: concTex(), roughness: 0.9 }),
    fabric: std({ map: fabricTex(), roughness: 0.95 }),
    board: std({ map: boardConcTex(), roughness: 0.9 }),
    server: std({ color: '#c3c8cc', roughness: 0.85 }),
    white: std({ color: '#e9ebea', roughness: 0.6 }),
    edge: M.coping,
  };

  // ---------- shell: walls with openings, floor slab, roof ----------
  // wall(axis, at, a0, a1, mats, holes): a wall along x (at z) or along z (at x), 0..H tall.
  // holes: [a, b, y0, y1]. mats: [+x, −x, +y, −y, +z, −z] faces.
  const wall = (axis, at, a0, a1, mats, holes = [], t = T, top = H) => {
    const piece = (s0, s1, y0, y1) => {
      if (s1 - s0 < 0.01 || y1 - y0 < 0.01) return;
      const len = s1 - s0, mid = (s0 + s1) / 2;
      const m = new THREE.Mesh(axis === 'x' ? boxUV(len, y1 - y0, t, 4, 7.5) : boxUV(t, y1 - y0, len, 4, 7.5), mats);
      if (axis === 'x') m.position.set(mid, (y0 + y1) / 2, at); else m.position.set(at, (y0 + y1) / 2, mid);
      m.castShadow = m.receiveShadow = true;
      b.add(m);
    };
    let s = a0;
    for (const [ha, hb, y0, y1] of [...holes].sort((p, q) => p[0] - q[0])) { piece(s, ha, 0, top); piece(ha, hb, 0, y0); piece(ha, hb, y1, top); s = hb; }
    piece(s, a1, 0, top);
  };
  const E = mat.edge;
  const zFaces = (plus, minus) => [E, E, E, E, plus, minus];   // wall along x
  const xFaces = (plus, minus) => [plus, minus, E, E, E, E];   // wall along z

  box(b, X1 - X0, FL, Z1 - Z0, 0, 0, 0, M.concrete, { cast: false });
  const roof = box(b, X1 - X0 + 0.4, 0.35, Z1 - Z0 + 0.4, 0, H, 0, M.coping);
  roof.receiveShadow = false;
  // north (to the substation) and east walls are blank; the south wall has the entrance; the
  // lobby's west wall is glass
  wall('x', Z0 + T / 2, X0, LOBBY[1], zFaces(mat.conc, ext));
  wall('x', Z0 + T / 2, LOBBY[1], OPS[1], zFaces(mat.ops, ext));
  wall('x', Z0 + T / 2, OPS[1], X1, zFaces(mat.server, ext));
  wall('x', Z1 - T / 2, X0, LOBBY[1], zFaces(ext, mat.conc), [[-36, -32, 0, 2.9]]);
  wall('x', Z1 - T / 2, LOBBY[1], OPS[1], zFaces(ext, mat.ops));
  wall('x', Z1 - T / 2, OPS[1], OFFICE.x1, zFaces(ext, mat.fabric));
  wall('x', Z1 - T / 2, OFFICE.x1, X1, zFaces(ext, mat.server));
  wall('z', X0 + T / 2, Z0, Z1, xFaces(mat.conc, ext), [[-8, 6, 0.35, 3.3]]);
  wall('z', X1 - T / 2, Z0, Z1, xFaces(ext, mat.server));
  // partitions
  wall('z', LOBBY[1], Z0, Z1, xFaces(mat.ops, mat.conc), [[3, 5.4, 0, 2.6]], 0.2);
  wall('z', OPS[1], OFFICE.z0, Z1, xFaces(mat.board, mat.ops), [], 0.2);
  wall('z', OPS[1], Z0, OFFICE.z0, xFaces(mat.server, mat.ops), [[Z0, OFFICE.z0, 0, CEIL]], 0.2);
  wall('x', OFFICE.z0, OFFICE.x0, OFFICE.x1, zFaces(mat.fabric, mat.server), [[1.4, 2.6, 0, 2.3]], 0.2);
  wall('z', OFFICE.x1, OFFICE.z0, Z1, xFaces(mat.server, mat.board), [[OFFICE.z0 + 0.1, Z1 - 0.15, 0, OFFICE_CEIL]], 0.2);

  // glass: lobby window and entrance, the ops/server partition, the office's view down the aisle
  const glass = glassMat();
  const frame = std({ color: '#1d2125', roughness: 0.5, metalness: 0.6 });
  const glazing = (axis, at, a0, a1, y0, y1, bay) => {
    const len = a1 - a0, n = Math.max(1, Math.round(len / bay));
    const pane = plane(b, len, y1 - y0, axis === 'x' ? (a0 + a1) / 2 : at, (y0 + y1) / 2, axis === 'x' ? at : (a0 + a1) / 2, glass, { ry: axis === 'x' ? 0 : Math.PI / 2, receive: false });
    pane.renderOrder = 2;
    const mull = [];
    for (let k = 0; k <= n; k++) { const a = a0 + (len * k) / n; mull.push(axis === 'x' ? mat4(a, (y0 + y1) / 2, at) : mat4(at, (y0 + y1) / 2, a, Math.PI / 2)); }
    b.add(instanced(new THREE.BoxGeometry(0.06, y1 - y0, 0.08), frame, mull, { cast: false }));
    for (const y of [y0, y1]) box(b, axis === 'x' ? len : 0.08, 0.06, axis === 'x' ? 0.08 : len, axis === 'x' ? (a0 + a1) / 2 : at, y - 0.03, axis === 'x' ? at : (a0 + a1) / 2, frame, { cast: false });
  };
  glazing('z', X0 + T / 2, -8, 6, 0.35, 3.3, 2.0);
  glazing('x', Z1 - T / 2, -36, -32, FL, 2.9, 2.0);
  glazing('z', OPS[1], Z0, OFFICE.z0, FL, CEIL, 2.0);
  glazing('z', OFFICE.x1, OFFICE.z0 + 0.1, Z1 - 0.15, FL, OFFICE_CEIL, 2.5);

  // floors and ceilings
  const floorAt = (x0, x1, z0, z1, m, tile, y = FL + 0.002) => plane(b, x1 - x0, z1 - z0, (x0 + x1) / 2, y, (z0 + z1) / 2, m, { rx: -Math.PI / 2, tile });
  const ceilAt = (x0, x1, z0, z1, m, tile, y) => plane(b, x1 - x0, z1 - z0, (x0 + x1) / 2, y, (z0 + z1) / 2, m, { rx: Math.PI / 2, tile });
  const polished = std({ map: polishedTex('#8a8f94'), roughness: 0.22, metalness: 0.05 });
  floorAt(X0, OPS[1], Z0, Z1, polished, 6);
  floorAt(OFFICE.x0, OFFICE.x1, OFFICE.z0, Z1, std({ map: polishedTex('#5f6266'), roughness: 0.6 }), 4);
  const raised = std({ map: raisedFloorTex(), roughness: 0.18, metalness: 0.05 });
  floorAt(OPS[1], X1, Z0, OFFICE.z0, raised, 1.2, FL + 0.004);
  floorAt(OFFICE.x1, X1, OFFICE.z0, Z1, raised, 1.2, FL + 0.004);
  const tiles = std({ map: ceilingTex(), roughness: 0.95 });
  ceilAt(X0, OPS[1], Z0, Z1, tiles, 2.4, CEIL);
  ceilAt(OFFICE.x0, OFFICE.x1, OFFICE.z0, Z1, tiles, 2.4, OFFICE_CEIL);
  ceilAt(OPS[1], X1, Z0, Z1, std({ color: '#7d8287', roughness: 0.9 }), 0, H - 0.01);

  buildLobby(b, mat, r);
  buildOps(b, mat, r);
  buildOffice(b, mat, r);
  buildServers(b, r);

  // a walk up from the car park and a canopy over the door
  plane(b, 4, 20, -34, 0.12, Z1 + 10, M.concrete, { rx: -Math.PI / 2, tile: 4 });
  box(b, 6, 0.25, 2.4, -34, 3.2, Z1 + 1.2, M.coping);
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(5, 0.6), new THREE.MeshBasicMaterial({ map: SCREEN_CLAMP(canvasTex(512, 64, (c, w, h) => { c.clearRect(0, 0, w, h); c.font = '300 40px Arial'; c.fillStyle = '#7beeff'; c.textAlign = 'center'; c.fillText('V I R A   O P E R A T I O N S', w / 2, 46); })), transparent: true }));
  sign.position.set(-34, 3.9, Z1 + 0.02); b.add(sign);

  // rooms (local to the building frame)
  registerRoom({ id: 'vira_lobby', name: 'Vira · Lobby', minX: X0, maxX: LOBBY[1], minZ: Z0, maxZ: Z1 + 0.3, floorY: FL, frame: b });
  registerRoom({ id: 'vira_ops', name: 'Vira · Ops', minX: OPS[0], maxX: OPS[1], minZ: Z0, maxZ: Z1, floorY: FL, frame: b });
  registerRoom({ id: 'vira_office', name: "Vira · Marcus's office", minX: OFFICE.x0, maxX: OFFICE.x1, minZ: OFFICE.z0, maxZ: OFFICE.z1, floorY: FL, frame: b });
  registerRoom({ id: 'vira_servers', name: 'Vira · Server hall', minX: OPS[1], maxX: X1, minZ: Z0, maxZ: Z1, floorY: FL, frame: b });

  const v = (x, y, z) => toWorld(b, x, y, z);
  const views = {
    lobby: [v(-29.5, FL + 1.7, 8.5), v(-37, 1.4, -9)],
    ops: [v(-12, FL + 1.7, 9.5), v(-17, 1.6, -6)],
    office: [v(-0.5, FL + 1.7, 2.2), v(0.4, 1.5, 10.8)],
    servers: [v(-2.5, FL + 1.7, -3), v(40, 1.5, -3)],
  };
  // cast spots in the building's local frame (filled by main.js)
  b.userData.cast = {
    lyra: { x: -15, y: FL + 0.22, z: 0, ry: Math.PI },           // hologram platform
    marcus: { x: 0.6, y: FL, z: 6.4, ry: Math.PI },               // office, facing the desk / clerestory
    patch: { x: -6.2, y: FL, z: 5.1, ry: -0.9 },                  // by his bed in ops
  };
  return { group: b, views };
}

// ---------- lobby (pb7): concrete panels, cyan LED strips, the intercom, the big window ----------
function buildLobby(b, mat, r) {
  const [x0, x1] = LOBBY;
  // white panelled volume with cyan LED reveals, between the window and the concrete
  const vol = box(b, 5, CEIL - FL, 1.1, -37.5, FL, Z0 + T + 0.55, mat.white);
  vol.castShadow = false;
  const cyan = glow('#36e0ff', 3.5);
  box(b, 5, 0.04, 0.04, -37.5, FL + 0.03, Z0 + T + 1.12, cyan, { cast: false });
  box(b, 5, 0.03, 0.03, -37.5, 2.45, Z0 + T + 1.12, cyan, { cast: false });
  for (const x of [-38.8, -36.2]) box(b, 0.02, 2.3, 0.02, x, FL + 0.05, Z0 + T + 1.115, std({ color: '#c9cccc' }), { cast: false });
  // floor reveals along the concrete walls
  box(b, 7, 0.03, 0.05, -31.5, FL, Z0 + T + 0.04, cyan, { cast: false });
  box(b, 0.05, 0.03, 13.5, x1 - 0.13, FL, -4.2, cyan, { cast: false });
  intercom(b, -31.5, 1.55, Z0 + T + 0.03, 0);
  intercom(b, -31.6, 1.55, Z1 - T - 0.03, Math.PI);
  // a bench, and Lyra's camera feeds on the wall: this lobby (pb7) and Patch in the aisle (pb8)
  box(b, 2.4, 0.45, 0.6, -39.1, FL, -1, std({ color: '#3a3d40', roughness: 0.6 }), { ry: Math.PI / 2 });
  for (const [name, z] of [['pb7_lobby_cool.png', 7.0], ['pb8_server_aisle.png', 8.6]]) {
    const cctv = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.79), screenMat(loadRefTex(name), 1.0));
    cctv.position.set(x1 - 0.13, 2.1, z); cctv.rotation.y = -Math.PI / 2; b.add(cctv);
    box(b, 0.04, 0.87, 1.48, x1 - 0.12, 1.665, z, std({ color: '#111' }), { cast: false });
  }
  addLight(b, -34, 2.5, 0, '#cfeeff', 22, 14);
}

// ---------- ops / hologram room (lh1, lh2, lh9) ----------
function buildOps(b, mat, r) {
  const P = { x: -15, z: 0 };
  // curved wall of monitors around the platform, two rows high
  const R = 8.5, cols = 7, a0 = Math.PI * 0.78, a1 = Math.PI * 1.56;
  const titles = ['GATE · NE', 'HALL A1–A4 THERMAL', 'FABRIC LOAD', 'GRID / SUBSTATION', 'CRAC LOOP', 'BADGE EVENTS', 'LYRA CORE'];
  const kinds = ['area', 'line', 'bars', 'table', 'area', 'table', 'line'];
  const bezel = std({ color: '#0b0c0e', roughness: 0.4, metalness: 0.3 });
  const backing = std({ color: '#16191c', roughness: 0.8 });
  for (let i = 0; i < cols; i++) {
    const a = a0 + (a1 - a0) * (i + 0.5) / cols;
    const x = P.x + Math.cos(a) * R, z = P.z + Math.sin(a) * R;
    const ry = Math.atan2(P.x - x, P.z - z);
    const col = new THREE.Group();
    col.position.set(x, 0, z); col.rotation.y = ry;
    box(col, 3.0, CEIL - FL - 0.4, 0.3, 0, FL, -0.2, backing);
    for (const [row, y] of [[0, 1.55], [1, 2.85]]) {
      box(col, 2.78, 1.24, 0.06, 0, y - 0.62, 0, bezel, { cast: false });
      let tex;
      if (i === 3 && row === 1) tex = loadRefTex('lh1_ops_wake.png', [0.27, 0.29, 0.46, 0.5]);
      else if (i === 2 && row === 0) tex = loadRefTex('pb8_server_aisle.png', [0.1, 0, 0.9, 1]);
      else if (i === 4 && row === 0) tex = gateLogTex();
      else tex = dashTex(r, kinds[(i + row * 3) % cols], titles[(i + row * 2) % cols]);
      const s = new THREE.Mesh(new THREE.PlaneGeometry(2.7, 1.16), screenMat(tex, 1.1));
      s.position.set(0, y, 0.035); col.add(s);
    }
    b.add(col);
  }
  addLight(b, P.x - 4, 2.2, P.z - 3, '#7fd8ff', 14, 9);

  // the platform (lh2): brushed steel drum, glowing rings, a rising column of light motes
  const ringDraw = (lit) => (c, w, h) => {
    c.fillStyle = lit ? '#000' : '#8c949b'; c.fillRect(0, 0, w, h);
    if (!lit) for (let k = 0; k < 400; k++) { c.strokeStyle = `rgba(${Math.random() < 0.5 ? '0,0,0' : '255,255,255'},.06)`; c.beginPath(); c.arc(w / 2, h / 2, Math.random() * w / 2, 0, Math.PI * 2); c.stroke(); }
    c.shadowColor = '#36e0ff'; c.shadowBlur = lit ? 18 : 6;
    c.strokeStyle = lit ? '#9ff4ff' : '#4fd8ee';
    for (const [rr, lw] of [[0.1, 10], [0.24, 12], [0.38, 14]]) { c.lineWidth = lw; c.beginPath(); c.arc(w / 2, h / 2, rr * w, 0, Math.PI * 2); c.stroke(); }
  };
  const ringMap = SCREEN_CLAMP(canvasTex(512, 512, ringDraw(false))), ringGlow = SCREEN_CLAMP(canvasTex(512, 512, ringDraw(true)));
  const steel = std({ color: '#b9c0c6', roughness: 0.28, metalness: 0.9 });
  const plat = new THREE.Group(); plat.position.set(P.x, FL, P.z); b.add(plat);
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(1.75, 1.85, 0.2, 64), steel); drum.position.y = 0.1; drum.castShadow = drum.receiveShadow = true; plat.add(drum);
  const top = new THREE.Mesh(new THREE.CircleGeometry(1.6, 64), std({ map: ringMap, emissiveMap: ringGlow, emissive: '#36e0ff', emissiveIntensity: 3.2, roughness: 0.3, metalness: 0.7 }));
  top.rotation.x = -Math.PI / 2; top.position.y = 0.205; plat.add(top);
  const lip = new THREE.Mesh(new THREE.TorusGeometry(1.68, 0.05, 8, 64), steel); lip.rotation.x = Math.PI / 2; lip.position.y = 0.2; plat.add(lip);
  const N = 260, pts = new Float32Array(N * 3), seeds = [];
  for (let i = 0; i < N; i++) seeds.push([r() * Math.PI * 2, Math.sqrt(r()) * 0.9, r(), 0.3 + r() * 0.5]);
  const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.BufferAttribute(pts, 3));
  const motes = new THREE.Points(pg, new THREE.PointsMaterial({ color: '#7ff0ff', size: 0.035, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false }));
  motes.frustumCulled = false; plat.add(motes);
  const beamTex = SCREEN_CLAMP(canvasTex(16, 128, (c, w, h) => { const g = c.createLinearGradient(0, h, 0, 0); g.addColorStop(0, 'rgba(80,230,255,.55)'); g.addColorStop(1, 'rgba(80,230,255,0)'); c.fillStyle = g; c.fillRect(0, 0, w, h); }));
  // soft column behind Lyra's hologram figure (the body itself is placed by main.js)
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.85, 2.4, 40, 1, true), new THREE.MeshBasicMaterial({ map: beamTex, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
  beam.position.y = 1.4; plat.add(beam);
  const world = toWorld(b, P.x, 1, P.z);
  onUpdate((dt, t, cam) => {
    if (cam.distanceToSquared(world) > 60 * 60) return;
    for (let i = 0; i < N; i++) {
      const [a, rad, ph, sp] = seeds[i], k = (t * sp * 0.25 + ph) % 1;
      pts[i * 3] = Math.cos(a + k * 1.5) * rad * (1 - k * 0.4); pts[i * 3 + 1] = 0.25 + k * 2.8; pts[i * 3 + 2] = Math.sin(a + k * 1.5) * rad * (1 - k * 0.4);
    }
    pg.attributes.position.needsUpdate = true;
    top.material.emissiveIntensity = 2.8 + Math.sin(t * 1.7) * 0.5;
  });
  addLight(b, P.x, FL + 0.8, P.z, '#36e0ff', 10, 7);

  // Marcus's desk where he reads the log (lh9): grey top on a dark pedestal, the log on the monitor
  const desk = new THREE.Group(); desk.position.set(-9.5, FL, -4.5); desk.rotation.y = -0.35; b.add(desk);
  const deskTop = std({ color: '#8d9399', roughness: 0.45, metalness: 0.2 });
  box(desk, 2.6, 0.05, 0.95, 0, 0.74, 0, deskTop);
  box(desk, 0.9, 0.74, 0.7, -0.7, 0, -0.05, std({ color: '#1d2024', roughness: 0.6 }));
  box(desk, 0.06, 0.74, 0.06, 1.15, 0, 0.3, frame());
  const mon = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 0.8), screenMat(loadRefTex('lh9_decision_log.png', [0.332, 0.136, 0.576, 0.49]), 1.05));
  mon.position.set(-0.1, 1.33, -0.18); desk.add(mon);
  box(desk, 1.06, 0.86, 0.04, -0.1, 0.9, -0.21, std({ color: '#0d0e10' }));
  box(desk, 0.06, 0.2, 0.06, -0.1, 0.79, -0.25, std({ color: '#222' }));
  box(desk, 0.5, 0.02, 0.16, 0.1, 0.79, 0.15, std({ color: '#1a1a1a' }));
  box(desk, 0.22, 0.08, 0.2, 0.75, 0.79, 0.1, std({ color: '#151515' }));
  const ch = new THREE.Mesh(chairGeo(), std({ vertexColors: true, roughness: 0.55 })); ch.position.set(0.3, 0, 0.75); ch.rotation.y = 0.2; ch.castShadow = true; desk.add(ch);
  plane(b, 3.4, 2.4, -9.3, FL + 0.004, -3.6, std({ color: '#6e6a64', roughness: 1 }), { rx: -Math.PI / 2 });

  // Patch's bed and bowl by the glass (lh1, lh9)
  const bed = new THREE.Group(); bed.position.set(-6.4, FL, 5.2); bed.rotation.y = 0.3; b.add(bed);
  const fabric = std({ color: '#6c7074', roughness: 1 });
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.15, 10, 32), fabric); rim.rotation.x = Math.PI / 2; rim.scale.set(1.4, 1, 1); rim.position.y = 0.15; rim.castShadow = true; bed.add(rim);
  const cushion = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.12, 24), std({ color: '#7b7f83', roughness: 1 })); cushion.scale.set(1.35, 1, 0.9); cushion.position.y = 0.06; bed.add(cushion);
  const bowl = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.11, 0.07, 24, 1, true), std({ color: '#c9cdd1', roughness: 0.15, metalness: 1, side: THREE.DoubleSide }));
  bowl.position.set(-5.4, FL + 0.035, 6.6); b.add(bowl);

  // fluorescent strips (lh1) and the intercom by the server-hall door
  const strip = glow('#eef6ff', 3);
  const strips = [];
  for (const x of [-21, -15, -9]) for (let z = -9.5; z <= 9.5; z += 2.5) strips.push(mat4(x, CEIL - 0.03, z));
  b.add(instanced(new THREE.BoxGeometry(0.16, 0.04, 2.2), strip, strips, { cast: false, receive: false }));
  intercom(b, OPS[1] - 0.12, 1.55, OFFICE.z0 + 0.6, -Math.PI / 2);
  addLight(b, -15, 2.4, 5, '#e6f2ff', 26, 16);
  addLight(b, -20, 2.4, -6, '#e6f2ff', 22, 14);
}
const frame = () => std({ color: '#1d2125', roughness: 0.5, metalness: 0.6 });

// ---------- Marcus's office (marcus_office_ref, ml1, ml7) ----------
function buildOffice(b, mat, r) {
  const { x0, x1, z0, z1 } = OFFICE;
  const wood = std({ color: '#6b5a48', roughness: 0.75 });
  const darkWood = std({ color: '#4f4234', roughness: 0.8 });
  // clerestory over the desk: the desert from the still
  const view = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 0.75), screenMat(loadRefTex('marcus_office_ref.png', [0.455, 0.145, 0.725, 0.245]), 1.0));
  view.position.set(0.3, 2.75, z1 - T - 0.02); view.rotation.y = Math.PI; b.add(view);
  box(b, 4.8, 0.08, 0.2, 0.3, 2.32, z1 - T - 0.1, frame(), { cast: false });
  box(b, 4.8, 0.08, 0.2, 0.3, 3.12, z1 - T - 0.1, frame(), { cast: false });
  // pinned printouts on the fabric wall
  const paper = std({ color: '#ecebe4', roughness: 0.9 });
  for (let k = 0; k < 11; k++) plane(b, 0.21 + r() * 0.08, 0.28, -2.6 + (k % 6) * 0.9 + r() * 0.3, 1.45 + Math.floor(k / 6) * 0.45 + r() * 0.15, z1 - T - 0.015, paper, { ry: Math.PI + (r() - 0.5) * 0.08 });
  // the desk: wood top, drawer pedestal, three monitors of logs, lamp
  const desk = new THREE.Group(); desk.position.set(0.2, FL, z1 - T - 0.45); desk.rotation.y = Math.PI; b.add(desk);
  box(desk, 2.8, 0.06, 0.85, 0, 0.72, 0, wood);
  box(desk, 0.6, 0.72, 0.8, 1.05, 0, 0, darkWood);
  for (const y of [0.18, 0.42, 0.6]) box(desk, 0.5, 0.01, 0.01, 1.05, y, 0.405, std({ color: '#2a2622' }), { cast: false });
  box(desk, 0.05, 0.72, 0.8, -1.35, 0, 0, darkWood);
  for (let k = -1; k <= 1; k++) {
    const m = new THREE.Group(); m.position.set(k * 0.68, 0.78, -0.15); m.rotation.y = -k * 0.22; desk.add(m);
    box(m, 0.64, 0.4, 0.03, 0, 0.18, 0, std({ color: '#0d0e10' }));
    const s = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.36), screenMat(terminalTex(r), 1.0)); s.position.set(0, 0.38, 0.017); m.add(s);
    box(m, 0.05, 0.18, 0.05, 0, 0, -0.03, std({ color: '#222' }));
  }
  const lampArm = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.65, 6), std({ color: '#2a2a2a', metalness: 0.6 })); lampArm.position.set(1.2, 1.05, -0.25); lampArm.rotation.z = 0.35; desk.add(lampArm);
  const shade = new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.16, 16, 1, true), std({ color: '#3a3a3a', metalness: 0.5, side: THREE.DoubleSide })); shade.position.set(1.05, 1.36, -0.2); shade.rotation.z = 0.9; desk.add(shade);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.04, 10, 8), glow('#ffcc88', 6)); bulb.position.set(1.0, 1.32, -0.2); desk.add(bulb);
  const ch = new THREE.Mesh(chairGeo(), std({ vertexColors: true, roughness: 0.4 })); ch.position.set(0.2, 0, 0.75); ch.castShadow = true; desk.add(ch);
  // the leather jacket over the chair back
  box(desk, 0.55, 0.55, 0.12, 0.2, 0.75, 1.02, std({ color: '#141414', roughness: 0.35 }), { cast: false });

  // whiteboard on the board-formed concrete wall, the wire shelf above with books, helmet, cactus
  const wbX = x0 + 0.13;
  const wb = new THREE.Mesh(new THREE.PlaneGeometry(3.6, 1.6), std({ map: whiteboardTex(), roughness: 0.25, metalness: 0.05 }));
  wb.position.set(wbX + 0.03, 1.75, 6.4); wb.rotation.y = Math.PI / 2; b.add(wb);
  box(b, 0.04, 1.7, 3.7, wbX + 0.005, 0.9, 6.4, std({ color: '#c8ccd0', metalness: 0.7, roughness: 0.3 }), { cast: false });
  box(b, 0.12, 0.04, 3.4, wbX + 0.08, 0.92, 6.4, std({ color: '#c8ccd0', metalness: 0.7, roughness: 0.3 }), { cast: false });
  box(b, 0.32, 0.03, 2.2, wbX + 0.16, 2.78, 7.3, std({ color: '#b8bcc0', metalness: 0.8, roughness: 0.4, wireframe: false }));
  const books = [];
  for (let k = 0; k < 12; k++) books.push(mat4(wbX + 0.16, 2.81 + 0.13, 6.5 + k * 0.055 + (k > 6 ? 0.25 : 0), 0, 1, 0.9 + r() * 0.25, 1));
  b.add(instanced(new THREE.BoxGeometry(0.22, 0.26, 0.045), std({ roughness: 0.8 }), books, { colors: books.map(() => ['#2b3a55', '#7a2b22', '#d9d2c0', '#2f4a3a', '#a08040'][Math.floor(r() * 5)]) }));
  const helmet = new THREE.Mesh(new THREE.SphereGeometry(0.15, 20, 14), std({ color: '#151617', roughness: 0.2, metalness: 0.4 }));
  helmet.scale.set(1, 0.95, 1.15); helmet.position.set(wbX + 0.17, 2.97, 7.85); b.add(helmet);
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.055, 0.1, 12), std({ color: '#b86a42' })); pot.position.set(wbX + 0.17, 2.85, 8.25); b.add(pot);
  const cactus = new THREE.Mesh(new THREE.CapsuleGeometry(0.035, 0.14, 4, 8), std({ color: '#4c7a42', roughness: 0.8 })); cactus.position.set(wbX + 0.17, 3.0, 8.25); b.add(cactus);

  // the foreground table under the printouts (ml1), mugs gone cold (ml6)
  const tbl = new THREE.Group(); tbl.position.set(0.4, FL, 4.6); b.add(tbl);
  box(tbl, 2.2, 0.05, 1.0, 0, 0.74, 0, std({ color: '#7a6450', roughness: 0.7 }));
  for (const [x, z] of [[-1, -0.42], [1, -0.42], [-1, 0.42], [1, 0.42]]) box(tbl, 0.05, 0.74, 0.05, x, 0, z, darkWood);
  const stacks = [];
  for (let k = 0; k < 7; k++) stacks.push(mat4(-0.8 + r() * 1.5, 0.79, -0.3 + r() * 0.6, (r() - 0.5) * 0.6, 1, 0.3 + r() * 2.5, 1));
  tbl.add(instanced(new THREE.BoxGeometry(0.3, 0.02, 0.22).translate(0, 0.01, 0), paper, stacks, { cast: false }));
  const mugs = [mat4(0.75, 0.79, 0.25), mat4(0.95, 0.79, -0.1), mat4(-0.9, 0.79, 0.3)];
  tbl.add(instanced(new THREE.CylinderGeometry(0.045, 0.04, 0.1, 14).translate(0, 0.05, 0), std({ color: '#e8e6e0', roughness: 0.4 }), mugs));
  const hl = [mat4(-0.2, 0.8, 0.1, 0.6, 1, 1, 1, 0, Math.PI / 2), mat4(0.3, 0.8, -0.2, -0.3, 1, 1, 1, 0, Math.PI / 2)];
  tbl.add(instanced(new THREE.CylinderGeometry(0.012, 0.012, 0.13, 8), std({ color: '#e8ec3a', emissive: '#556000', emissiveIntensity: 0.3 }), hl, { cast: false }));

  // cable trench in the floor running out under the glass (ml1)
  plane(b, 0.5, z1 - z0 - 0.5, x1 - 0.6, FL + 0.006, (z0 + z1) / 2, std({ map: DX.cables('#2a2c2e', '#1a1b1c'), roughness: 0.8 }), { rx: -Math.PI / 2 });
  // ceiling troffer, the door to the hall with its intercom
  box(b, 1.2, 0.04, 0.6, 0, OFFICE_CEIL - 0.04, 6, glow('#f4f7ff', 2.2), { cast: false });
  intercom(b, x1 - 0.5, 1.55, z0 + 0.12, 0);
  addLight(b, 0, 2.3, 6, '#fff3e0', 16, 10);
  addLight(b, -0.8, 1.3, z1 - 0.9, '#ffbe78', 5, 4);
}

// ---------- server hall (c1, pb8): black racks, blue/green LEDs, yellow trays, raised floor ----------
function buildServers(b, r) {
  const variants = [0, 1, 2].map((k) => rackTex(70 + k));
  const side = std({ color: '#0e1013', roughness: 0.5, metalness: 0.5 });
  const geo = new THREE.BoxGeometry(0.6, 2.4, 1.1); geo.translate(0, 1.2, 0);
  const lists = [[], [], []];
  RACK_ROWS.forEach((z, row) => {
    const ry = row % 2 === 0 ? Math.PI : 0;   // fronts face each other across the main aisle and the office aisle
    for (let x = RACK_X[0]; x <= RACK_X[1]; x += 0.62) {
      if (Math.abs(x - CROSS_AISLE) < 0.9) continue;
      lists[Math.floor(r() * 3)].push(mat4(x, FL, z, ry));
    }
  });
  lists.forEach((l, k) => {
    const front = std({ map: variants[k].map, emissiveMap: variants[k].emissiveMap, emissive: '#ffffff', emissiveIntensity: 3.2, roughness: 0.4, metalness: 0.4 });
    const back = std({ map: variants[(k + 1) % 3].map, emissiveMap: variants[(k + 1) % 3].emissiveMap, emissive: '#ffffff', emissiveIntensity: 1.6, roughness: 0.4, metalness: 0.4 });
    b.add(instanced(geo, [side, side, side, side, front, back], l, { cast: false }));
  });
  // yellow ladder trays over every row, cross trays, conduit, LED lines in the high bay
  const yt = DX.cables('#e2b51c', '#c9a215'); yt.repeat.set(1, 6);
  const tray = std({ map: yt, roughness: 0.6 });
  const yellow = std({ color: '#d9ad22', roughness: 0.5, metalness: 0.3 });
  for (const z of RACK_ROWS) {
    box(b, RACK_X[1] - RACK_X[0] + 1, 0.08, 0.6, (RACK_X[0] + RACK_X[1]) / 2, 2.95, z, tray, { cast: false });
    for (const s of [-0.3, 0.3]) box(b, RACK_X[1] - RACK_X[0] + 1, 0.12, 0.03, (RACK_X[0] + RACK_X[1]) / 2, 2.95, z + s, yellow, { cast: false });
  }
  const cross = [], hang = [], leds = [];
  for (let x = RACK_X[0] + 2; x <= RACK_X[1]; x += 6) { cross.push(mat4(x, 3.55, 0, Math.PI / 2)); for (const z of RACK_ROWS) hang.push(mat4(x, 3.25, z)); }
  b.add(instanced(new THREE.BoxGeometry(Z1 - Z0 - 1, 0.1, 0.5), yellow, cross, { cast: false }));
  b.add(instanced(new THREE.CylinderGeometry(0.015, 0.015, 0.6, 6), std({ color: '#666' }), hang, { cast: false }));
  const pipe = std({ color: '#9aa1a8', roughness: 0.4, metalness: 0.7 });
  for (const z of [-7.5, 1.4, 6]) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, X1 - OPS[1], 10), pipe); c.rotation.z = Math.PI / 2; c.position.set((X1 + OPS[1]) / 2, 4.3, z); b.add(c); }
  for (const z of [-7.4, -3, 1.45, 6.05]) for (let x = OPS[1] + 1; x < X1 - 1; x += 3.2) leds.push(mat4(x + 1.4, H - 0.4, z));
  b.add(instanced(new THREE.BoxGeometry(2.6, 0.06, 0.18), glow('#e8f0ff', 3), leds, { cast: false, receive: false }));
  // the far end of the main aisle opens onto the deep hall of the still
  const far = new THREE.Mesh(new THREE.PlaneGeometry(8.6, 4.8), screenMat(loadRefTex('c1_processors.png'), 0.9));
  far.position.set(X1 - T - 0.02, FL + 2.4, -3); far.rotation.y = -Math.PI / 2; b.add(far);
  addLight(b, 12, 5.5, -3, '#cfe0ff', 55, 22);
  addLight(b, 30, 5.5, -3, '#cfe0ff', 55, 22);
  addLight(b, 20, 5.5, 6, '#cfe0ff', 45, 20);
}
