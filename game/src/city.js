import * as THREE from 'three';
import { HALCYON, CITY_GRID, FREEWAY_Z, NOVA_PAD } from './heightfield.js';
import { heightAt, halcyonE } from './terrain.js';
import { rng, fbm, part, mergeParts, mat4, instanced, nightEmissive, signTex, globalUniforms } from './util.js';
import * as TX from './textures.js';
import { facadeMaterial } from './facade.js';
import { buildCars, buildTrucks, buildLightPoles, buildPalms } from './props.js';
import { ribbon } from './road.js';
import { HOMES } from './homes.js';

// Halcyon: Nova's city. A metropolis on a flat basin floor ringed by chaparral hills.
// Downtown towers at the center, a midtown ring of mid-rises, suburbs of single-family
// homes, warehouses at the edges, an elevated freeway in from the east, and hillside homes
// looking down over it all.
const C = HALCYON, G = CITY_GRID;
const std = (o) => new THREE.MeshStandardMaterial(o);

// Instances grouped into 3 km sectors so whole districts are culled together.
export class Batches {
  constructor(sector = 3000) { this.sector = sector; this.types = new Map(); this.p = new THREE.Vector3(); }
  type(name, geo, mat, opts = {}) { this.types.set(name, { geo, mat, opts, cells: new Map() }); }
  add(name, m, color) {
    const t = this.types.get(name);
    this.p.setFromMatrixPosition(m);
    const k = `${Math.floor(this.p.x / this.sector)},${Math.floor(this.p.z / this.sector)}`;
    if (!t.cells.has(k)) t.cells.set(k, { m: [], c: [] });
    const cell = t.cells.get(k);
    cell.m.push(m);
    if (color !== undefined) cell.c.push(color);
  }
  build(group) {
    for (const t of this.types.values()) for (const cell of t.cells.values())
      group.add(instanced(t.geo, t.mat, cell.m, { ...t.opts, colors: cell.c.length ? cell.c : null }));
  }
}

// Ground materials sampled in world space so instanced lots of any size tile cleanly.
export function worldUV(set, tile, extra = {}) {
  const m = std({ map: set.map, roughness: 0.9, ...extra });
  m.userData.cacheKey = 'worldUV' + tile;
  m.userData.extraShader = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', `diffuseColor *= texture2D(map, vWPos.xz / ${tile.toFixed(1)});`);
  };
  return m;
}

// Asphalt for a whole street grid, with procedural lane lines and crosswalks.
export function streetMaterial(cx = C.x, cz = C.z, grid = G, dense = 3200) {
  const a = TX.asphalt();
  const m = std({ map: a.map, roughness: 0.92 });
  m.userData.cacheKey = `streets${cx}`;
  m.userData.extraShader = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', /* glsl */`
      {
        vec2 rel = vWPos.xz - vec2(${cx.toFixed(1)}, ${cz.toFixed(1)});
        vec2 sd = rel - ${grid.toFixed(1)} * floor(rel / ${grid.toFixed(1)} + 0.5);
        float inNS = step(abs(sd.x), 10.0), inEW = step(abs(sd.y), 10.0);
        vec3 col = texture2D(map, vWPos.xz / 10.0).rgb;
        float dense = 1.0 - step(${dense.toFixed(1)}, length(rel));
        float dashNS = inNS * (1.0 - inEW) * step(abs(sd.x), 0.13) * step(fract(vWPos.z / 9.0), 0.45);
        float dashEW = inEW * (1.0 - inNS) * step(abs(sd.y), 0.13) * step(fract(vWPos.x / 9.0), 0.45);
        float cwNS = inNS * step(10.6, abs(sd.y)) * step(abs(sd.y), 13.6) * step(0.5, fract(vWPos.x / 1.1)) * dense;
        float cwEW = inEW * step(10.6, abs(sd.x)) * step(abs(sd.x), 13.6) * step(0.5, fract(vWPos.z / 1.1)) * dense;
        float stopNS = inNS * step(abs(sd.y - 14.2 * sign(sd.y)), 0.25) * step(0.0, sd.x * sign(sd.y) * -1.0) * dense;
        col = mix(col, vec3(0.78, 0.6, 0.18), max(dashNS, dashEW));
        col = mix(col, vec3(0.86, 0.86, 0.82), max(max(cwNS, cwEW), stopNS));
        diffuseColor.rgb *= col;
      }`);
  };
  return m;
}

const TOWER_COLORS = ['#d9dcdf', '#bfc5ca', '#8e969d', '#5d646b', '#c8b9a3', '#e6e2da', '#3e444a', '#9aa7b0', '#b7a68e', '#d0d4d8'];
const MID_COLORS = ['#e2d6c2', '#cdbfa8', '#d9d2c6', '#b9b2a6', '#e8e2d8', '#c9a98a', '#a9b1b8', '#d7c3a6', '#b98f73', '#e6dccb'];
const STUCCO = ['#efe2c8', '#e2c8a2', '#d3a882', '#f3ebdc', '#c9b394', '#e0bea0', '#b9c3ad', '#d2d6d8', '#ead6ae', '#dcae8c'];
const ROOFS = ['#b0583a', '#8f4630', '#6b6560', '#7d7b76', '#b86b48', '#9a8a74', '#5c5550'];

export function buildHalcyon() {
  const g = new THREE.Group();
  const r = rng(2024);
  const B = new Batches();
  const unit = new THREE.BoxGeometry(1, 1, 1); unit.translate(0, 0.5, 0);
  const concrete = TX.concrete();
  B.type('office', unit, facadeMaterial('office'));
  B.type('glass', unit, facadeMaterial('glass'));
  B.type('res', unit, facadeMaterial('residential'));
  B.type('house', unit, facadeMaterial('house'));
  B.type('lot', unit, worldUV(concrete, 6), { cast: false });
  B.type('grass', unit, worldUV(TX.sand(), 4, { color: '#6f8a45' }), { cast: false });
  B.type('mech', unit, std({ map: TX.chillerSide().map, roughness: 0.5, metalness: 0.5 }));
  B.type('warehouse', unit, std({ map: TX.chillerSide().map, color: '#d6d4cf', roughness: 0.55, metalness: 0.45 }));
  const tiles = TX.roofTiles();
  const hipT = tiles.map.clone(); hipT.repeat.set(8, 2.5); hipT.needsUpdate = true;
  const hipGeo = new THREE.ConeGeometry(1, 1, 4, 1); hipGeo.rotateY(Math.PI / 4); hipGeo.translate(0, 0.5, 0);
  B.type('hip', hipGeo, std({ map: hipT, roughness: 0.8, flatShading: true }));
  const poolGeo = new THREE.PlaneGeometry(1, 1); poolGeo.rotateX(-Math.PI / 2);
  B.type('pool', poolGeo, std({ color: '#3fb6c9', roughness: 0.05, metalness: 0.1, emissive: '#0a3a44', emissiveIntensity: 0.6 }), { cast: false });
  const treeGeo = mergeParts([
    part(new THREE.CylinderGeometry(0.18, 0.28, 3, 6), '#6a5442', 0, 1.5, 0),
    part(new THREE.IcosahedronGeometry(2.2, 1), '#5e7a3a', 0, 4.4, 0),
    part(new THREE.IcosahedronGeometry(1.5, 1), '#6d8a44', 1.1, 5.3, 0.4),
  ]);
  B.type('tree', treeGeo, std({ vertexColors: true, roughness: 0.9, flatShading: true }));
  const spireGeo = new THREE.CylinderGeometry(0.15, 1.2, 1, 8); spireGeo.translate(0, 0.5, 0);
  B.type('spire', spireGeo, std({ color: '#c9ced3', metalness: 0.8, roughness: 0.3 }));

  const cars = [], trucks = [], palms = [], lamps = [], signals = [], beacons = [];
  const glowPts = [], glowCol = [];
  const nearHillRoad = (x, z) => Math.hypot(x - (C.x + 600), z - (C.z - 5640)) < 120;

  // ---------- blocks ----------
  for (let i = -54; i < 54; i++) for (let j = -44; j < 44; j++) {
    const bx = C.x + (i + 0.5) * G, bz = C.z + (j + 0.5) * G;
    if (halcyonE(bx, bz) > 0.93 || nearHillRoad(bx, bz)) continue;
    const r0 = Math.hypot(bx - C.x, bz - C.z);
    const rr = r0 * (0.85 + 0.3 * fbm(bx * 0.0004, bz * 0.0004, 2));
    const underFreeway = (j === 1 || j === 2) && bx > C.x + 1000;
    const park = (i >= 2 && i <= 4 && j >= -7 && j <= -5);
    const stadium = (i >= -16 && i <= -14 && j >= 4 && j <= 6);
    if (stadium) continue;

    if (park || (rr > 3000 && r() < 0.035)) {
      B.add('grass', mat4(bx, 0, bz, 0, 120, 0.2, 120));
      for (let k = 0; k < (park ? 28 : 12); k++) B.add('tree', mat4(bx + (r() - 0.5) * 108, 0, bz + (r() - 0.5) * 108, r() * 6, 0.9 + r() * 0.6, 0.9 + r() * 0.5, 0.9 + r() * 0.6), new THREE.Color().setHSL(0.2 + r() * 0.08, 0.3, 0.8 + r() * 0.2));
      continue;
    }
    B.add('lot', mat4(bx, 0, bz, 0, 120, 0.18, 120), rr < 3000 ? '#ffffff' : rr < 5300 ? '#d9c9a8' : '#e8dcc6');

    if (rr < 1300 && !underFreeway) {
      // downtown
      const landmark = i === 0 && j === -1;
      const H = landmark ? 330 : 70 + 240 * Math.pow(Math.max(0, 1 - rr / 1300), 1.2) * (0.45 + 0.55 * r());
      const roll = r();
      const col = TOWER_COLORS[Math.floor(r() * TOWER_COLORS.length)];
      const type = r() < 0.55 ? 'glass' : 'office';
      if (landmark || roll < 0.55) {
        const ph = 12 + r() * 8;
        B.add('office', mat4(bx, 0, bz, 0, 104, ph, 104), MID_COLORS[Math.floor(r() * MID_COLORS.length)]);
        const fw = landmark ? 64 : 44 + r() * 28, fd = landmark ? 64 : 44 + r() * 28;
        const ox = (r() - 0.5) * (100 - fw) * 0.6, oz = (r() - 0.5) * (100 - fd) * 0.6;
        B.add(type, mat4(bx + ox, ph, bz + oz, 0, fw, H - ph, fd), col);
        let top = H;
        if (landmark || r() < 0.55) { B.add(type, mat4(bx + ox, H, bz + oz, 0, fw * 0.72, H * 0.1, fd * 0.72), col); top = H * 1.1; }
        if (landmark || (r() < 0.25 && H > 150)) { B.add(type, mat4(bx + ox, top, bz + oz, 0, fw * 0.45, H * 0.06, fd * 0.45), col); top += H * 0.06; }
        B.add('mech', mat4(bx + ox, top, bz + oz, 0, fw * 0.3, 4, fd * 0.3));
        if (landmark || (H > 200 && r() < 0.5)) { B.add('spire', mat4(bx + ox, top + 4, bz + oz, 0, 1, landmark ? 70 : 25, 1)); top += landmark ? 74 : 29; }
        if (top > 140) beacons.push([bx + ox, top + 0.5, bz + oz]);
      } else if (roll < 0.85) {
        for (const s of [-1, 1]) {
          const h2 = H * (0.55 + r() * 0.35);
          B.add(type, mat4(bx + s * 27, 0, bz - s * 20, 0, 44, h2, 44), col);
          B.add('mech', mat4(bx + s * 27, h2, bz - s * 20, 0, 14, 4, 14));
          if (h2 > 140) beacons.push([bx + s * 27, h2 + 4.5, bz - s * 20]);
        }
      } else {
        B.add('office', mat4(bx, 0, bz + 30, 0, 90, 9, 40), MID_COLORS[Math.floor(r() * MID_COLORS.length)]);
        for (let k = 0; k < 8; k++) B.add('tree', mat4(bx + (r() - 0.5) * 90, 0.2, bz - 25 + (r() - 0.5) * 40, r() * 6, 0.8, 0.8, 0.8), '#ffffff');
      }
      for (let k = 0; k < 4; k++) if (r() < 0.6) cars.push({ x: bx + (r() < 0.5 ? -1 : 1) * 61.5, z: bz + (r() - 0.5) * 100, ry: r() < 0.5 ? 0 : Math.PI });
    } else if (rr < 3000 || underFreeway) {
      // midtown: up to four mid-rises per block
      const hMax = underFreeway ? 9 : 12 + 46 * Math.max(0, 1 - (rr - 1300) / 1700);
      for (const ox of [-30, 30]) for (const oz of [-30, 30]) {
        const roll = r();
        if (roll < 0.12) { for (let k = 0; k < 5; k++) if (r() < 0.7) cars.push({ x: bx + ox + (k - 2) * 2.9, z: bz + oz, ry: 0 }); continue; }
        const w = 40 + r() * 14, d = 40 + r() * 14;
        const h = Math.max(7, Math.round((8 + r() * r() * hMax) / 3.6) * 3.6);
        const type = r() < 0.5 ? 'res' : 'office';
        B.add(type, mat4(bx + ox, 0, bz + oz, 0, w, h, d), MID_COLORS[Math.floor(r() * MID_COLORS.length)]);
        if (r() < 0.5) B.add('mech', mat4(bx + ox + (r() - 0.5) * 10, h, bz + oz + (r() - 0.5) * 10, 0, 6, 2.4, 4));
      }
      for (let k = 0; k < 3; k++) if (r() < 0.5) cars.push({ x: bx + (r() < 0.5 ? -1 : 1) * 61.5, z: bz + (r() - 0.5) * 100, ry: r() < 0.5 ? 0 : Math.PI });
    } else if (rr < 5300) {
      // suburbs: two rows of five houses facing the east-west streets
      for (const row of [-1, 1]) for (let k = -2; k <= 2; k++) {
        if (r() < 0.06) continue;
        const lx = bx + k * 23.5, w = 11 + r() * 3, d = 10 + r() * 2.5, h = 3.2 + r() * 0.4;
        const lz = bz + row * (60 - 8 - d / 2);
        const col = STUCCO[Math.floor(r() * STUCCO.length)];
        B.add('house', mat4(lx, 0, lz, 0, w, h, d), col);
        B.add('hip', mat4(lx, h, lz, 0, (w / 2 + 0.6) / 0.7071, 1.6 + r() * 0.9, (d / 2 + 0.6) / 0.7071), ROOFS[Math.floor(r() * ROOFS.length)]);
        if (r() < 0.22) B.add('pool', mat4(lx, 0.22, lz - row * (d / 2 + 9), 0, 7, 1, 3.6));
        if (r() < 0.38) B.add('tree', mat4(lx + (r() - 0.5) * 16, 0, lz - row * (d / 2 + 12 + r() * 8), r() * 6, 0.8 + r() * 0.5, 0.8 + r() * 0.4, 0.8 + r() * 0.5), new THREE.Color().setHSL(0.18 + r() * 0.1, 0.3, 0.75 + r() * 0.25));
        if (r() < 0.05) cars.push({ x: lx + w / 2 + 3, z: lz + row * (d / 2 + 4), ry: 0 });
        else HOMES.halcyon.push({ city: 'halcyon', drive: [lx + w / 2 + 3, lz + row * (d / 2 + 4)], street: bz + row * 70 });
      }
    } else {
      // industrial edge: warehouses and yards
      const n = r() < 0.5 ? 1 : 2;
      for (let k = 0; k < n; k++) {
        const w = n === 1 ? 70 + r() * 30 : 46 + r() * 10, d = 50 + r() * 40, h = 8 + r() * 6;
        B.add('warehouse', mat4(bx + (n === 1 ? 0 : (k ? 28 : -28)), 0, bz, 0, w, h, d), ['#d6d4cf', '#c8c2b6', '#b9bec2', '#e2ddd2'][Math.floor(r() * 4)]);
      }
      if (r() < 0.3) trucks.push({ x: bx + (r() - 0.5) * 80, z: bz + 52, ry: Math.PI / 2, kind: r() < 0.6 ? 'semi' : 'box' });
    }
  }

  // ---------- intersections: street lights, signals, night glow along every street ----------
  for (let i = -54; i <= 54; i++) for (let j = -44; j <= 44; j++) {
    const x = C.x + i * G, z = C.z + j * G;
    if (halcyonE(x, z) > 0.93) continue;
    const rr = Math.hypot(x - C.x, z - C.z);
    lamps.push({ x: x + 11.6, z: z + 11.6, ry: 3 * Math.PI / 4 });
    if (rr < 2400) signals.push(mat4(x - 11.4, 0, z - 11.4, -Math.PI / 4));
    const warm = rr > 2400;
    for (let k = 1; k < 6; k++) {
      for (const [px, pz] of [[x + k * G / 6, z + (k % 2 ? 9 : -9)], [x + (k % 2 ? 9 : -9), z + k * G / 6]]) {
        if (halcyonE(px, pz) > 0.93) continue;
        glowPts.push(px, 7, pz);
        const c = warm ? [1.0, 0.62, 0.28] : [0.95, 0.93, 0.85];
        glowCol.push(...c);
      }
    }
    if (rr < 1400 && (i % 3 === 0)) for (const s of [-1, 1]) palms.push({ x: x + s * 12.5, z: z + G / 2, h: 9 + r() * 4, ry: r() * 6 });
  }

  B.build(g);
  g.add(buildLightPoles(lamps, 9));
  g.add(buildCars(cars, 77));
  g.add(buildTrucks(trucks, 9));
  g.add(buildPalms(palms));

  // traffic signals: mast arm with three heads; lenses always lit
  const sigGeo = mergeParts([
    part(new THREE.CylinderGeometry(0.14, 0.18, 6.4, 8), '#5a5f64', 0, 3.2, 0),
    part(new THREE.BoxGeometry(8, 0.16, 0.16), '#5a5f64', 4, 6.1, 0),
    ...[2.6, 5.2, 7.6].map((x) => part(new THREE.BoxGeometry(0.4, 1.1, 0.35), '#2a2c2e', x, 5.4, 0)),
  ]);
  g.add(instanced(sigGeo, std({ vertexColors: true, roughness: 0.5, metalness: 0.5 }), signals, { receive: false }));
  const lensGeo = mergeParts([2.6, 5.2, 7.6].map((x) => { const l = new THREE.CircleGeometry(0.12, 10); l.translate(x, 5.1, 0.18); return l; }));
  const lens = instanced(lensGeo, new THREE.MeshBasicMaterial({ toneMapped: false }), signals, { cast: false, receive: false, colors: signals.map(() => (r() < 0.5 ? '#ff2a1a' : '#2aff7a')) });
  g.add(lens);

  // night glow: a carpet of street lights, so the city reads from the hills like the film
  const gg = new THREE.BufferGeometry();
  gg.setAttribute('position', new THREE.Float32BufferAttribute(glowPts, 3));
  gg.setAttribute('color', new THREE.Float32BufferAttribute(glowCol, 3));
  const glow = new THREE.Points(gg, new THREE.ShaderMaterial({
    uniforms: { night: globalUniforms.night },
    vertexShader: /* glsl */`
      #include <common>
      #include <logdepthbuf_pars_vertex>
      attribute vec3 color; varying vec3 vC; uniform float night;
      void main() {
        vC = color;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        gl_Position = projectionMatrix * mv;
        gl_PointSize = night < 0.02 ? 0.0 : clamp(2600.0 / -mv.z, 1.4, 5.0);
        #include <logdepthbuf_vertex>
      }`,
    fragmentShader: /* glsl */`
      #include <common>
      #include <logdepthbuf_pars_fragment>
      varying vec3 vC; uniform float night;
      void main() {
        #include <logdepthbuf_fragment>
        float d = length(gl_PointCoord - 0.5);
        float a = smoothstep(0.5, 0.1, d) * night;
        if (a < 0.02) discard;
        gl_FragColor = vec4(vC * 2.2, a);
      }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  }));
  glow.frustumCulled = false;
  g.add(glow);

  // aviation beacons on the tall towers
  g.add(instanced(new THREE.SphereGeometry(0.6, 8, 6), std({ color: '#400', emissive: '#ff2a1a', emissiveIntensity: 5 }), beacons.map(([x, y, z]) => mat4(x, y, z)), { cast: false }));

  // city floor: asphalt with procedural lane lines and crosswalks
  const floor = new THREE.Mesh(new THREE.CircleGeometry(1, 96), streetMaterial());
  floor.geometry.rotateX(-Math.PI / 2);
  floor.scale.set(C.rx * 0.95, 1, C.rz * 0.95);
  floor.position.set(C.x, 0.06, C.z);
  floor.receiveShadow = true;
  g.add(floor);

  g.add(buildStadium(C.x - 2030, C.z + 770));
  g.add(buildFreeway());
  g.add(buildHillHomes(r));
  return g;
}

// ---------- stadium ----------
function buildStadium(x, z) {
  const g = new THREE.Group();
  const prof = [[60, 0], [62, 0], [86, 22], [92, 30], [93, 30], [93, 0]].map(([a, b]) => new THREE.Vector2(a, b));
  const bowl = new THREE.Mesh(new THREE.LatheGeometry(prof, 64), std({ color: '#cfcac0', roughness: 0.8, side: THREE.DoubleSide }));
  bowl.scale.set(1.35, 1, 1);
  bowl.position.set(x, 0, z);
  bowl.castShadow = bowl.receiveShadow = true;
  const field = new THREE.Mesh(new THREE.CircleGeometry(60, 48), std({ color: '#3f7a35', roughness: 0.9 }));
  field.rotation.x = -Math.PI / 2; field.scale.set(1.35, 1, 1);
  field.position.set(x, 0.3, z);
  const lot = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), std({ map: TX.asphalt().map, roughness: 0.95 }));
  lot.rotation.x = -Math.PI / 2; lot.position.set(x, 0.2, z);
  lot.receiveShadow = true;
  g.add(lot, field, bowl);
  const towerGeo = mergeParts([part(new THREE.BoxGeometry(1, 48, 1), '#9aa0a5', 0, 24, 0), part(new THREE.BoxGeometry(10, 4, 1), '#9aa0a5', 0, 48, 0)]);
  const towers = [[-110, -70], [110, -70], [-110, 70], [110, 70]].map(([dx, dz]) => mat4(x + dx, 0, z + dz, Math.atan2(-dx, -dz)));
  g.add(instanced(towerGeo, std({ vertexColors: true, metalness: 0.6, roughness: 0.4 }), towers));
  const lamps = new THREE.PlaneGeometry(9.5, 3.5); lamps.translate(0, 48, 0.55);
  g.add(instanced(lamps, nightEmissive(std({ color: '#888', emissive: '#f4f6ff' }), 4), towers, { cast: false }));
  return g;
}

// ---------- elevated freeway from the interstate into downtown ----------
export const FREEWAY_X0 = -71500, FREEWAY_X1 = C.x + 8 * G; // east end meets the interstate; west end is a street line
export function freewayY(x) {
  if (x > -72300) return 13 * smoothstepJS(FREEWAY_X0, -72300, x);
  if (x < C.x + 1900) return 13 * smoothstepJS(FREEWAY_X1, C.x + 1900, x);
  return 13;
}

function buildFreeway() {
  const g = new THREE.Group();
  const x0 = FREEWAY_X0, x1 = FREEWAY_X1;
  const elev = freewayY;
  const pts = [], ys = [];
  for (let x = x0; x >= x1; x -= 10) { pts.push([x, FREEWAY_Z]); ys.push(elev(x) + 0.3); }
  const h4 = TX.highway4();
  const map = h4.map.clone(); map.repeat.set(2, 1); map.needsUpdate = true;
  const deckTop = new THREE.Mesh(ribbon(pts, 32, ys, 48), std({ map, roughness: 0.9 }));
  deckTop.receiveShadow = true;
  g.add(deckTop);
  const deck = [], cols = [], walls = [], lamps = [];
  for (let x = x0 - 17.5; x > x1; x -= 35) {
    const ya = elev(x + 17.5), yb = elev(x - 17.5), y = (ya + yb) / 2;
    const slope = Math.atan2(ya - yb, 35);
    deck.push(mat4(x, y - 0.8, FREEWAY_Z, 0, 35.2, 1.6, 32, 0, slope));
    for (const s of [-1, 1]) walls.push(mat4(x, y + 0.55, FREEWAY_Z + s * 15.8, 0, 35.2, 1.1, 0.45, 0, slope));
    if (y > 2.5) for (const s of [-1, 1]) cols.push(mat4(x, 0, FREEWAY_Z + s * 8, 0, 2.2, y - 1.6, 2.2));
    if (Math.round(x) % 70 < 35) lamps.push({ x, y: y + 0.3, z: FREEWAY_Z - 15.4, ry: -Math.PI / 2 });
  }
  const conc = std({ ...{ map: TX.concrete().map }, color: '#cfcbc3', roughness: 0.85 });
  const unit = new THREE.BoxGeometry(1, 1, 1);
  g.add(instanced(unit, conc, deck));
  g.add(instanced(unit, conc, walls));
  const colGeo = new THREE.CylinderGeometry(0.5, 0.5, 1, 12); colGeo.translate(0, 0.5, 0);
  g.add(instanced(colGeo, conc, cols));
  g.add(buildLightPoles(lamps, 10));
  // overhead sign gantry
  const gx = C.x + 3800;
  const gy = elev(gx);
  const steel = std({ color: '#9aa1a8', metalness: 0.7, roughness: 0.4 });
  for (const s of [-1, 1]) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.5, 8, 0.5), steel); p.position.set(gx, gy + 4, FREEWAY_Z + s * 16.2); g.add(p); }
  const beam = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.8, 33), steel); beam.position.set(gx, gy + 7.8, FREEWAY_Z); g.add(beam);
  const face = std({ map: signTex(['DOWNTOWN', 'HALCYON  1 MI'], { w: 512, h: 220 }), roughness: 0.5 });
  const board = new THREE.Mesh(new THREE.BoxGeometry(0.2, 3.4, 8), [face, steel, steel, steel, steel, steel]);
  board.position.set(gx + 0.5, gy + 6.4, FREEWAY_Z - 8); g.add(board);
  const face2 = std({ map: signTex(['HILLS', 'EXIT 2B'], { w: 512, h: 220 }), roughness: 0.5 });
  const board2 = new THREE.Mesh(new THREE.BoxGeometry(0.2, 3.4, 8), [face2, steel, steel, steel, steel, steel]);
  board2.position.set(gx + 0.5, gy + 6.4, FREEWAY_Z + 1); g.add(board2);
  return g;
}

function smoothstepJS(a, b, x) { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); }

// ---------- homes on the hills above the city ----------
function buildHillHomes(r) {
  const g = new THREE.Group();
  const glass = facadeMaterial('glass');
  const unit = new THREE.BoxGeometry(1, 1, 1); unit.translate(0, 0.5, 0);
  const plinth = std({ map: TX.concrete().map, color: '#d6d0c4', roughness: 0.9 });
  const homes = [], upper = [], bases = [], pools = [], colors = [], upColors = [];
  let tries = 0;
  while (homes.length < 70 && tries++ < 4000) {
    const a = r() * Math.PI * 2, e = 1.07 + r() * 0.45;
    const x = C.x + Math.cos(a) * C.rx * e, z = C.z + Math.sin(a) * C.rz * e;
    if (Math.hypot(x - NOVA_PAD.x, z - NOVA_PAD.z) < 260) continue;
    if (Math.abs(z - FREEWAY_Z) < 600 && x > C.x) continue;
    const h = heightAt(x, z), hx = heightAt(x + 15, z), hz = heightAt(x, z + 15);
    if (Math.hypot(hx - h, hz - h) / 15 > 0.4 || h < 40) continue;
    const ry = Math.atan2(C.x - x, C.z - z);
    const w = 18 + r() * 12, d = 13 + r() * 6;
    homes.push(mat4(x, h, z, ry, w, 3.8, d)); colors.push('#f2f0ea');
    upper.push(mat4(x + Math.sin(ry) * 2, h + 3.8, z + Math.cos(ry) * 2, ry, w * 0.8, 3.6, d * 0.85)); upColors.push(r() < 0.5 ? '#f2f0ea' : '#3b3f44');
    bases.push(mat4(x, h - 12, z, ry, w + 6, 12.2, d + 10));
    pools.push(mat4(x + Math.sin(ry) * (d / 2 + 4), h + 0.25, z + Math.cos(ry) * (d / 2 + 4), ry, w * 0.7, 1, 3.6));
  }
  g.add(instanced(unit, glass, homes, { colors }));
  g.add(instanced(unit, glass, upper, { colors: upColors }));
  g.add(instanced(unit, plinth, bases));
  const poolGeo = new THREE.PlaneGeometry(1, 1); poolGeo.rotateX(-Math.PI / 2);
  g.add(instanced(poolGeo, std({ color: '#3fb6c9', roughness: 0.05, emissive: '#0d6a7a', emissiveIntensity: 0.6 }), pools, { cast: false }));
  return g;
}
