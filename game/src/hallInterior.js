import * as THREE from 'three';
import { HALL, HALL_X, HALL_Z } from './datacenter.js';
import { canvasTex, mat4, instanced } from './util.js';
import { std, glow, box, plane, registerRoom, addLight } from './interiors.js';
import * as TX from './textures.js';

// The inside of a data hall. All sixteen halls share one layout, so a single interior is
// built and moved into whichever hall the camera is in (the hall's outer box faces only
// outward, so from inside you see this instead). Every hall is still registered as a room
// for walking and gets its own light entries.
//
// Hall-local frame: origin at the hall centre on the ground, x across (62 m), z along (230 m).
export const HL = {
  floor: 0.3,                         // raised floor height
  ceil: 6.5,
  inX: HALL.W / 2 - 0.3, inZ: HALL.L / 2 - 0.3,
  corridorX: 27.3,                     // service corridors along both long walls
  crossX: 0,                           // cross aisle down the middle
  halfX: [1.5, 24],                    // rack rows span these |x|
  firstPair: -104, pairPitch: 5.4, pairs: 38,
  doorZ: -28.5,                        // the personnel doors used by staff (west and east walls)
  stagingZ: [-110, 110],
};
// Cold aisle centres (rack fronts face these) and rack slot x positions, for workers.
export const COLD_AISLES = Array.from({ length: HL.pairs }, (_, k) => HL.firstPair + k * HL.pairPitch + 1.5);
export const RACK_SLOTS = (() => {
  const s = [];
  for (let x = HL.halfX[0] + 0.3; x <= HL.halfX[1] - 0.3; x += 0.6) s.push(x, -x);
  return s;
})();
const labels = (i) => `${'ABCD'[Math.floor(i / 4)]}${(i % 4) + 1}`;
export const hallIndexOf = (col, row) => col * 4 + row; // col: block (HALL_Z), row: HALL_X
export const hallCenter = (i) => ({ x: HALL_X[i % 4], z: HALL_Z[Math.floor(i / 4)] });
export const hallName = (i) => `Hall ${labels(i)}`;

// Hall-local <-> world (halls are axis-aligned).
export const hallToWorld = (i, lx, lz) => { const c = hallCenter(i); return [c.x + lx, c.z + lz]; };

function rackFrontTex(lit) {
  return canvasTex(64, 256, (c, w, h) => {
    c.fillStyle = lit ? '#000' : '#16191c'; c.fillRect(0, 0, w, h);
    if (!lit) { c.strokeStyle = '#2c3136'; for (let y = 0; y < h; y += 3) { c.beginPath(); c.moveTo(4, y); c.lineTo(w - 4, y); c.stroke(); } }
    for (let u = 0; u < 22; u++) {
      const y = 12 + u * 10.5;
      for (let k = 0; k < 6; k++) {
        if (Math.random() < 0.35) continue;
        c.fillStyle = lit ? (Math.random() < 0.12 ? '#ffb020' : Math.random() < 0.5 ? '#3cff9a' : '#3aa8ff') : '#3a4046';
        c.fillRect(8 + k * 8, y, 3, 2);
      }
    }
  });
}

export function buildHallInterior() {
  const g = new THREE.Group();
  g.visible = false;
  const { inX, inZ, floor: FY, ceil: CY } = HL;

  // shell seen from inside: walls and ceiling (inward faces), a raised floor
  const wallMat = std({ color: '#d9dcdc', roughness: 0.85, side: THREE.BackSide });
  const shell = new THREE.Mesh(new THREE.BoxGeometry(inX * 2, CY, inZ * 2), wallMat);
  shell.position.y = CY / 2; g.add(shell);
  const tileTex = canvasTex(128, 128, (c, w, h) => {
    c.fillStyle = '#c9cdd0'; c.fillRect(0, 0, w, h);
    c.strokeStyle = '#8f959a'; c.lineWidth = 3; c.strokeRect(1, 1, w - 2, h - 2);
    for (let k = 0; k < 400; k++) { c.fillStyle = `rgba(0,0,0,${Math.random() * 0.05})`; c.fillRect(Math.random() * w, Math.random() * h, 2, 2); }
  });
  plane(g, inX * 2, inZ * 2, 0, FY, 0, std({ map: tileTex, roughness: 0.3, metalness: 0.05 }), { rx: -Math.PI / 2, tile: 0.6 });
  box(g, inX * 2, FY - 0.01, inZ * 2, 0, 0, 0, std({ color: '#5a5f63' }), { cast: false });
  // dark plenum above a light grid of ceiling tiles
  plane(g, inX * 2, inZ * 2, 0, CY - 0.02, 0, std({ color: '#3c4146', roughness: 0.95 }), { rx: Math.PI / 2 });

  // rack rows: pairs facing across cold aisles, backs closed into hot-aisle containment
  const front = std({ map: rackFrontTex(false), emissiveMap: rackFrontTex(true), emissive: '#ffffff', emissiveIntensity: 1.6, roughness: 0.5, metalness: 0.5 });
  const side = std({ color: '#1d2125', roughness: 0.55, metalness: 0.5 });
  const rackGeo = new THREE.BoxGeometry(0.6, 2.2, 1.2); rackGeo.translate(0, 1.1, 0);
  const racks = [], trays = [], strips = [], hot = [], ends = [];
  for (let k = 0; k < HL.pairs; k++) {
    const zA = HL.firstPair + k * HL.pairPitch, zB = zA + 3.0;
    for (const s of [-1, 1]) {
      for (let x = HL.halfX[0] + 0.3; x <= HL.halfX[1] - 0.3; x += 0.6) {
        racks.push(mat4(s * x, FY, zA, 0));          // fronts face +z (the cold aisle)
        racks.push(mat4(s * x, FY, zB, Math.PI));    // fronts face -z
      }
      const cx = s * (HL.halfX[0] + HL.halfX[1]) / 2, len = HL.halfX[1] - HL.halfX[0];
      trays.push(mat4(cx, 3.1, zA, 0, len, 0.12, 0.5), mat4(cx, 3.1, zB, 0, len, 0.12, 0.5));
      strips.push(mat4(cx, CY - 0.1, zA + 1.5, 0, len, 0.06, 0.25));
      // hot aisle behind row B: roof panel and end doors
      hot.push(mat4(cx, FY + 2.2, zB + 1.2, 0, len, 0.06, 1.2));
      for (const ex of [HL.halfX[0], HL.halfX[1]]) ends.push(mat4(s * ex, FY, zB + 1.2, 0, 0.06, 2.2, 1.2));
    }
  }
  g.add(instanced(rackGeo, [side, side, side, side, front, side], racks));
  g.add(instanced(new THREE.BoxGeometry(1, 1, 1), std({ color: '#d8a92a', roughness: 0.6, metalness: 0.4 }), trays, { cast: false }));
  g.add(instanced(new THREE.BoxGeometry(1, 1, 1), glow('#eef4ff', 3.2), strips, { cast: false, receive: false }));
  g.add(instanced(new THREE.BoxGeometry(1, 1, 1), std({ color: '#7f9aa6', roughness: 0.2, metalness: 0.3, transparent: true, opacity: 0.55 }), hot, { cast: false }));
  const endGeo = new THREE.BoxGeometry(1, 1, 1); endGeo.translate(0, 0.5, 0);
  g.add(instanced(endGeo, std({ color: '#2a2f34', roughness: 0.5, metalness: 0.4 }), ends, { cast: false }));

  // cooling units (CRAH) along both long walls, and the service corridors' light
  const cs = TX.chillerSide();
  const crah = [];
  for (let z = -inZ + 6; z <= inZ - 6; z += 6) for (const s of [-1, 1]) crah.push(mat4(s * (inX - 0.7), FY, z, -s * Math.PI / 2));   // coil faces into the room
  const crahGeo = new THREE.BoxGeometry(2.4, 2.3, 1.2); crahGeo.translate(0, 1.15, 0);
  g.add(instanced(crahGeo, [side, side, std({ color: '#b4b9be' }), side, std({ map: cs.map, normalMap: cs.normal, roughness: 0.5, metalness: 0.5 }), side], crah));
  const lights = [];
  for (let z = -inZ + 4; z <= inZ - 4; z += 8) for (const s of [-1, 1]) lights.push(mat4(s * HL.corridorX, CY - 0.1, z, 0, 0.25, 0.06, 4));
  for (let z = -inZ + 4; z <= inZ - 4; z += 8) lights.push(mat4(0, CY - 0.1, z, 0, 0.25, 0.06, 4));
  g.add(instanced(new THREE.BoxGeometry(1, 1, 1), glow('#f4f6ff', 3), lights, { cast: false, receive: false }));

  // staging areas at both ends: carts and boxed servers waiting to go in
  const crates = [];
  for (const zs of HL.stagingZ) for (let k = 0; k < 14; k++) crates.push(mat4(-20 + (k % 7) * 6.5, FY, zs + (k < 7 ? -2 : 2), (k * 0.7) % 1, 1.2, 0.8 + (k % 3) * 0.4, 1.0));
  const crateGeo = new THREE.BoxGeometry(1, 1, 1); crateGeo.translate(0, 0.5, 0);
  g.add(instanced(crateGeo, std({ map: TX.blockWall().map, color: '#c8b48e', roughness: 0.9 }), crates));

  // a sign on the north end wall with the hall's name (redrawn when the interior moves)
  const signCanvas = document.createElement('canvas'); signCanvas.width = 512; signCanvas.height = 160;
  const signTexture = new THREE.CanvasTexture(signCanvas); signTexture.colorSpace = THREE.SRGBColorSpace;
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(9, 2.8), new THREE.MeshBasicMaterial({ map: signTexture }));
  sign.position.set(0, 4.6, -inZ + 0.05);
  g.add(sign);
  const drawSign = (i) => {
    const c = signCanvas.getContext('2d');
    c.fillStyle = '#e9ebea'; c.fillRect(0, 0, 512, 160);
    c.fillStyle = '#2a2f35'; c.font = '600 92px Arial'; c.textAlign = 'center'; c.textBaseline = 'middle';
    c.fillText(hallName(i).toUpperCase(), 256, 84);
    signTexture.needsUpdate = true;
  };

  // every hall: a walkable room and a few lights for the interior light pool
  for (let i = 0; i < 16; i++) {
    const c = hallCenter(i);
    registerRoom({ id: `hall_${i}`, name: `Vira · ${hallName(i)}`, minX: c.x - inX, maxX: c.x + inX, minZ: c.z - inZ, maxZ: c.z + inZ, floorY: FY });
    for (const z of [-80, -28.5, 28.5, 80]) addLight(null, c.x, 5.5, c.z + z, '#eaf2ff', 30, 30);
  }

  let current = -1;
  return {
    group: g,
    get current() { return current; },
    // Put the interior in the hall containing (x, y, z), or hide it.
    update(p) {
      let found = -1;
      if (p.y < HALL.H) for (let i = 0; i < 16; i++) {
        const c = hallCenter(i);
        if (Math.abs(p.x - c.x) < HALL.W / 2 && Math.abs(p.z - c.z) < HALL.L / 2) { found = i; break; }
      }
      if (found !== current) {
        current = found;
        g.visible = found >= 0;
        if (found >= 0) { const c = hallCenter(found); g.position.set(c.x, 0, c.z); drawSign(found); }
      }
    },
  };
}
