import * as THREE from 'three';
import { IRONWOOD, IRON_GRID, RAIL_Z, JUNO_PAD } from './heightfield.js';
import { ironwoodE, heightAt } from './terrain.js';
import { rng, part, mergeParts, mat4, instanced, nightEmissive, signTex, canvasTex, globalUniforms } from './util.js';
import * as TX from './textures.js';
import { facadeMaterial } from './facade.js';
import { Batches, worldUV, streetMaterial } from './city.js';
import { buildCars, buildTrucks, buildLightPoles, buildPalms, buildTrees, contactShadows } from './props.js';
import { ribbon } from './road.js';
import { HOMES } from './homes.js';

// Ironwood: Juno's city. An old railroad town that turned into a repair town: a brick main
// street, a rail yard with freight cars, silos and a water tower, auto shops, junkyards and
// warehouses south of the tracks, small houses and a trailer park, a highway strip of motels
// and gas stations, all ringed by granite boulder hills with pinyon and juniper.
const I = IRONWOOD, G = IRON_GRID;
const std = (o) => new THREE.MeshStandardMaterial(o);

const BRICK = ['#9a4a35', '#a5583e', '#7d3b2c', '#b8705a', '#8c5a44', '#c49a76', '#a07858', '#6e3a2e'];
const STUCCO = ['#efe2c8', '#e2c8a2', '#d3a882', '#f3ebdc', '#c9b394', '#e0bea0', '#b9c3ad', '#d2d6d8', '#ead6ae', '#dcae8c'];
const ROOFS = ['#6b6560', '#7d7b76', '#8a7f72', '#5c5550', '#9a8a74', '#b0583a'];
const SHOPS = ['HARDWARE', 'DINER', 'PAWN', 'AUTO PARTS', 'SALOON', 'FEED & SUPPLY', 'BARBER', 'TATTOO', 'CAFE', 'MACHINE SHOP', 'THRIFT', 'TIRES', 'LIQUOR', 'BAKERY', 'BAIT & TACKLE', 'LAUNDROMAT'];
const SIGN_COLORS = [['#7a1f1f', '#f6e7c8'], ['#1f3a5a', '#ffffff'], ['#f2e3c2', '#5a2a1a'], ['#2f4a2a', '#f0e6c8'], ['#111111', '#ffcf5a']];
const YARD_X = [I.x - 1300, I.x + 700];

export function buildIronwood() {
  const g = new THREE.Group();
  const r = rng(1891);
  const B = new Batches(2000);
  const unit = new THREE.BoxGeometry(1, 1, 1); unit.translate(0, 0.5, 0);
  B.type('brick', unit, facadeMaterial('brick'));
  B.type('office', unit, facadeMaterial('office'));
  B.type('house', unit, facadeMaterial('house'));
  B.type('lot', unit, worldUV(TX.concrete(), 6), { cast: false });
  B.type('dirt', unit, worldUV(TX.gravel(), 2, { color: '#d8c6a6' }), { cast: false });
  B.type('warehouse', unit, std({ map: TX.chillerSide().map, color: '#d6d4cf', roughness: 0.6, metalness: 0.45 }));
  B.type('rust', unit, std({ map: TX.chillerSide().map, color: '#9a6a4a', roughness: 0.8, metalness: 0.3 }));
  B.type('mech', unit, std({ map: TX.chillerSide().map, roughness: 0.5, metalness: 0.5 }));
  const tiles = TX.roofTiles();
  const hipT = tiles.map.clone(); hipT.repeat.set(8, 2.5); hipT.needsUpdate = true;
  const hipGeo = new THREE.ConeGeometry(1, 1, 4, 1); hipGeo.rotateY(Math.PI / 4); hipGeo.translate(0, 0.5, 0);
  B.type('hip', hipGeo, std({ map: hipT, roughness: 0.85, flatShading: true }));
  const juniper = mergeParts([
    part(new THREE.CylinderGeometry(0.15, 0.25, 1.4, 6), '#5a4636', 0, 0.7, 0),
    part(new THREE.IcosahedronGeometry(1.6, 1), '#3f4c2c', 0, 2.0, 0),
    part(new THREE.IcosahedronGeometry(1.2, 1), '#4a5834', 0.7, 2.7, 0.3),
    part(new THREE.IcosahedronGeometry(1.0, 1), '#44522f', -0.6, 2.5, -0.4),
  ]);
  B.type('juniper', juniper, std({ vertexColors: true, roughness: 0.95, flatShading: true }));
  const rollTex = canvasTex(128, 128, (c, w, h) => { c.fillStyle = '#b4b6b2'; c.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 6) { c.fillStyle = '#8a8c88'; c.fillRect(0, y, w, 1); } c.fillStyle = 'rgba(80,60,40,.35)'; c.fillRect(0, h * 0.7, w, h * 0.3); });
  const rollGeo = new THREE.PlaneGeometry(1, 1); rollGeo.translate(0, 0.5, 0);
  B.type('rollup', rollGeo, std({ map: rollTex, roughness: 0.6, metalness: 0.4 }), { cast: false });

  const cars = [], wrecks = [], trucks = [], lamps = [], trees = [], palms = [], signs = [];
  const glowPts = [], glowCol = [];
  let shop = 0;
  const nearDrive = (x, z) => Math.hypot(x - (I.x + 1700), z - (I.z - 2400)) < 110;

  for (let i = -38; i < 38; i++) for (let j = -30; j < 30; j++) {
    const bx = I.x + (i + 0.5) * G, bz = I.z + (j + 0.5) * G;
    if (ironwoodE(bx, bz) > 0.93 || nearDrive(bx, bz)) continue;
    const dx = Math.abs(bx - I.x), rr = Math.hypot(bx - I.x, (bz - I.z) * 1.2);
    const onMain = j === -1 || j === 0;
    const inYard = j === 4 && bx > YARD_X[0] && bx < YARD_X[1];
    const depot = j === 3 && Math.abs(bx - (I.x - 50)) < 60;
    if (inYard) continue;
    if (depot) { B.add('lot', mat4(bx, 0, bz, 0, 80, 0.18, 80), '#ffffff'); continue; }

    if (onMain && dx < 700) {
      // downtown: brick storefronts shoulder to shoulder along Main Street
      B.add('lot', mat4(bx, 0, bz, 0, 80, 0.18, 80), '#ffffff');
      const side = j === -1 ? -1 : 1; // -1: north side of Main
      let x = bx - 40;
      while (x < bx + 38) {
        const w = Math.min(10 + r() * 9, bx + 40 - x);
        const stories = r() < 0.45 ? 1 : r() < 0.75 ? 2 : 3;
        const h = 4.6 + (stories - 1) * 3.8 + r() * 0.6, d = 24 + r() * 10;
        const fz = I.z + side * 12.5;
        B.add('brick', mat4(x + w / 2, 0, fz + side * d / 2, 0, w - 0.3, h, d), BRICK[Math.floor(r() * BRICK.length)]);
        B.add('mech', mat4(x + w / 2, h, fz + side * (d / 2 + 4), 0, 2.4, 1.2, 1.8));
        if (shop < SHOPS.length && r() < 0.55) signs.push({ text: SHOPS[shop++], x: x + w / 2, z: fz - side * 0.06, w: Math.min(8, w * 0.8), y: Math.min(h - 0.8, 3.9), side });
        x += w;
      }
      for (let k = 0; k < 4; k++) if (r() < 0.6) cars.push({ x: bx + (r() - 0.5) * 70, z: I.z + side * 8.6, ry: side < 0 ? 0 : Math.PI });
      for (let k = 0; k < 3; k++) if (r() < 0.6) cars.push({ x: bx + (r() - 0.5) * 60, z: bz + side * 30, ry: Math.PI / 2 });
    } else if (onMain) {
      // highway strip: motels, gas, fast food, a truck stop at the east end
      B.add('lot', mat4(bx, 0, bz, 0, 80, 0.18, 80), '#f2ece0');
      const side = j === -1 ? -1 : 1;
      const kind = r();
      if (kind < 0.3) {
        B.add('office', mat4(bx, 0, bz + side * 20, 0, 60, 4, 12), STUCCO[Math.floor(r() * STUCCO.length)]);
        signs.push({ pole: true, text: 'MOTEL', sub: 'VACANCY', x: bx - 32, z: I.z + side * 14, color: '#ff4a3a' });
        for (let k = 0; k < 6; k++) cars.push({ x: bx - 25 + k * 10, z: bz + side * 6, ry: Math.PI / 2 * side });
      } else if (kind < 0.55) {
        B.add('office', mat4(bx + 15, 0, bz + side * 22, 0, 22, 4.4, 14), '#ece6d8');
        B.add('warehouse', mat4(bx - 14, 5.2, bz, 0, 26, 0.9, 16), '#f4f4f2');
        signs.push({ pole: true, text: 'GAS', sub: 'REG 4.39', x: bx - 36, z: I.z + side * 14, color: '#ffcf3a' });
        cars.push({ x: bx - 17, z: bz - 3, ry: Math.PI / 2 }, { x: bx - 11, z: bz + 4, ry: -Math.PI / 2 });
      } else if (kind < 0.75) {
        B.add('office', mat4(bx, 0, bz + side * 12, 0, 22, 5, 18), STUCCO[Math.floor(r() * STUCCO.length)]);
        signs.push({ pole: true, text: ['BURGERS', 'TACOS', 'CHICKEN', 'DONUTS'][Math.floor(r() * 4)], sub: 'OPEN 24 HRS', x: bx + 30, z: I.z + side * 14, color: '#ff8a2a' });
        for (let k = 0; k < 5; k++) if (r() < 0.7) cars.push({ x: bx - 30 + k * 3, z: bz - side * 20, ry: 0 });
      } else if (bx > I.x) {
        B.add('office', mat4(bx + 20, 0, bz + side * 25, 0, 30, 5, 18), '#d8cfc0');
        for (let k = 0; k < 3; k++) trucks.push({ x: bx - 25, z: bz - side * 5 + (k - 1) * 9, ry: Math.PI / 2, kind: 'semi' });
      }
    } else if (j >= 4 && j <= 8) {
      // south of the tracks: auto shops, junkyards, warehouses
      const kind = r();
      B.add('dirt', mat4(bx, 0, bz, 0, 80, 0.15, 80));
      if (kind < 0.12) {
        // junkyard: corrugated fence and stacked wrecks
        B.add('rust', mat4(bx, 0, bz - 39, 0, 80, 2.4, 0.3)); B.add('rust', mat4(bx, 0, bz + 39, 0, 80, 2.4, 0.3));
        B.add('rust', mat4(bx - 39, 0, bz, 0, 0.3, 2.4, 80)); B.add('rust', mat4(bx + 39, 0, bz, 0, 0.3, 2.4, 80));
        for (let a = -30; a <= 30; a += 7.5) for (let b = -30; b <= 30; b += 10) {
          if (r() < 0.35) continue;
          const stack = r() < 0.3 ? 2 : 1;
          for (let s = 0; s < stack; s++) wrecks.push({ x: bx + a + (r() - 0.5) * 2, y: s * 1.45, z: bz + b, ry: r() < 0.5 ? 0 : Math.PI + (r() - 0.5) * 0.3 });
        }
      } else if (kind < 0.55) {
        // auto / machine shops: low buildings with open roll-up doors
        for (const ox of [-20, 20]) {
          const h = 5 + r() * 2;
          B.add('warehouse', mat4(bx + ox, 0, bz - 10, 0, 34, h, 26), ['#d6d4cf', '#c8c2b6', '#e2ddd2', '#b9bec2'][Math.floor(r() * 4)]);
          for (const dx2 of [-10, 0, 10]) B.add('rollup', mat4(bx + ox + dx2, 0, bz - 10 + 13.02, 0, 4, 4, 1));
          for (let k = 0; k < 3; k++) if (r() < 0.7) cars.push({ x: bx + ox + (k - 1) * 9, z: bz + 12, ry: 0, kind: r() < 0.5 ? 'pickup' : undefined });
        }
      } else {
        B.add('warehouse', mat4(bx, 0, bz, 0, 64 + r() * 10, 9 + r() * 5, 50 + r() * 16), ['#d6d4cf', '#c8c2b6', '#e2ddd2', '#b9bec2'][Math.floor(r() * 4)]);
        if (r() < 0.4) trucks.push({ x: bx + (r() - 0.5) * 40, z: bz + 34, ry: Math.PI / 2, kind: r() < 0.6 ? 'semi' : 'box' });
      }
    } else if (j <= -14 && rr > 1500 && r() < 0.35) {
      // trailer park
      B.add('dirt', mat4(bx, 0, bz, 0, 80, 0.15, 80));
      for (let a = -30; a <= 30; a += 10) for (const b of [-18, 18]) {
        if (r() < 0.15) continue;
        B.add('house', mat4(bx + a, 0, bz + b, 0, 4.4, 3.2, 16), ['#f2f0ea', '#e8e2d2', '#dfe6ea', '#efe0c4'][Math.floor(r() * 4)]);
        if (r() < 0.4) cars.push({ x: bx + a + 4.2, z: bz + b + (b > 0 ? -5 : 5), ry: 0, kind: r() < 0.6 ? 'pickup' : undefined });
      }
    } else {
      // neighborhoods: small houses, chain-link and block-wall yards
      if (r() < 0.12) { B.add('dirt', mat4(bx, 0, bz, 0, 80, 0.15, 80)); continue; }
      B.add('dirt', mat4(bx, 0, bz, 0, 80, 0.12, 80), '#e6d6b6');
      for (const row of [-1, 1]) for (let k = -1.5; k <= 1.5; k += 1) {
        if (r() < 0.12) continue;
        const lx = bx + k * 20, w = 9 + r() * 3, d = 8.5 + r() * 2.5, h = 3.0 + r() * 0.4;
        const lz = bz + row * (40 - 7 - d / 2);
        B.add('house', mat4(lx, 0, lz, 0, w, h, d), STUCCO[Math.floor(r() * STUCCO.length)]);
        B.add('hip', mat4(lx, h, lz, 0, (w / 2 + 0.5) / 0.7071, 1.3 + r() * 0.8, (d / 2 + 0.5) / 0.7071), ROOFS[Math.floor(r() * ROOFS.length)]);
        if (r() < 0.14) cars.push({ x: lx + w / 2 + 2.5, z: lz + row * (d / 2 + 3), ry: 0, kind: r() < 0.5 ? 'pickup' : undefined });
        else HOMES.ironwood.push({ city: 'ironwood', drive: [lx + w / 2 + 2.5, lz + row * (d / 2 + 3)], street: bz + row * 50 });
        if (r() < 0.3) trees.push({ x: lx + (r() - 0.5) * 12, z: lz - row * (d / 2 + 7), s: 0.7 + r() * 0.4, ry: r() * 6 });
      }
    }
  }

  // ---------- intersections: lights and night glow ----------
  for (let i = -38; i <= 38; i++) for (let j = -30; j <= 30; j++) {
    const x = I.x + i * G, z = I.z + j * G;
    if (ironwoodE(x, z) > 0.93) continue;
    if ((i + j) % 2 === 0 || j === 0) lamps.push({ x: x + 11.6, z: z + 11.6, ry: 3 * Math.PI / 4 });
    for (let k = 1; k < 4; k++) for (const [px, pz] of [[x + k * G / 4, z + 9], [x + 9, z + k * G / 4]]) {
      if (ironwoodE(px, pz) > 0.93) continue;
      glowPts.push(px, 7, pz);
      glowCol.push(1.0, 0.6, 0.26);
    }
  }
  // pinyon and juniper on the hills around town
  for (let k = 0; k < 2600; k++) {
    const a = r() * Math.PI * 2, e = 1.03 + r() * 0.9;
    const x = I.x + Math.cos(a) * I.rx * e, z = I.z + Math.sin(a) * I.rz * e;
    if (Math.hypot(x - JUNO_PAD.x, z - JUNO_PAD.z) < 60) continue;
    if (Math.abs(z - RAIL_Z) < 25) continue;
    B.add('juniper', mat4(x, heightAt(x, z) - 0.2, z, r() * 6, 0.7 + r() * 0.9, 0.7 + r() * 0.8, 0.7 + r() * 0.9), new THREE.Color().setHSL(0.22 + r() * 0.06, 0.25, 0.7 + r() * 0.3));
  }

  B.build(g);
  g.add(buildLightPoles(lamps, 8.5));
  g.add(buildCars(cars, 12));
  g.add(buildCars(wrecks.map((w) => ({ ...w, color: ['#6b4a3a', '#7a6a55', '#5a5f63', '#8a3a2a', '#9a8a6a', '#3d4a3a', '#4a4a50'][Math.floor(r() * 7)] })), 13));
  g.add(buildTrucks(trucks, 14));
  g.add(buildTrees(trees));
  g.add(buildPalms(palms));
  g.add(buildSigns(signs));

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
        float a = smoothstep(0.5, 0.1, length(gl_PointCoord - 0.5)) * night;
        if (a < 0.02) discard;
        gl_FragColor = vec4(vC * 2.2, a);
      }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  }));
  glow.frustumCulled = false;
  g.add(glow);

  const floor = new THREE.Mesh(new THREE.CircleGeometry(1, 96), streetMaterial(I.x, I.z, G, 800));
  floor.geometry.rotateX(-Math.PI / 2);
  floor.scale.set(I.rx * 0.95, 1, I.rz * 0.95);
  floor.position.set(I.x, 0.06, I.z);
  floor.receiveShadow = true;
  g.add(floor);

  g.add(buildRailYard(r));
  return g;
}

// ---------- storefront and pole signs ----------
function buildSigns(signs) {
  const g = new THREE.Group();
  for (const s of signs) {
    const [bg, fg] = SIGN_COLORS[Math.floor(Math.abs(Math.sin(s.x)) * SIGN_COLORS.length)];
    if (!s.pole) {
      const m = nightEmissive(std({ map: signTex([s.text], { w: 512, h: 96, bg, fg, border: fg, font: 'bold 58px Georgia' }), emissive: '#ffffff', roughness: 0.7 }), 0.6);
      m.emissiveMap = m.map;
      const p = new THREE.Mesh(new THREE.PlaneGeometry(s.w, s.w * 96 / 512), m);
      p.position.set(s.x, s.y, s.z);
      p.rotation.y = s.side < 0 ? 0 : Math.PI;
      g.add(p);
      continue;
    }
    const m = std({ map: signTex([{ text: s.text, font: 'bold 110px Arial', color: s.color }, { text: s.sub, font: 'bold 56px Arial', color: '#ffffff' }], { w: 512, h: 320, bg: '#1d2430', border: s.color }), emissive: '#ffffff', emissiveIntensity: 0.2 });
    m.emissiveMap = m.map;
    nightEmissive(m, 1.6);
    const dark = std({ color: '#333' });
    const board = new THREE.Mesh(new THREE.BoxGeometry(6.4, 4, 0.5), [dark, dark, dark, dark, m, m]);
    board.position.set(s.x, 11, s.z);
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 10, 8), std({ color: '#777', metalness: 0.5 }));
    pole.position.set(s.x, 5, s.z);
    g.add(board, pole);
  }
  return g;
}

// ---------- rail yard: sidings, freight cars, depot, silos, water tower ----------
function buildRailYard(r) {
  const g = new THREE.Group();
  const gv = TX.gravel();
  const ballastMap = gv.map.clone(); ballastMap.repeat.set(6 / 1.6, 1); ballastMap.needsUpdate = true;
  const ballastMat = std({ map: ballastMap, color: '#a39a8c', roughness: 1 });
  const tieTex = canvasTex(64, 64, (c) => { c.fillStyle = '#8e8476'; c.fillRect(0, 0, 64, 64); c.fillStyle = '#4a3a2c'; c.fillRect(0, 8, 64, 22); });
  const tieMat = std({ map: tieTex, roughness: 1 });
  const railMat = std({ color: '#6d6a66', metalness: 0.85, roughness: 0.35 });
  const rails = [];
  const sidings = [RAIL_Z + 10, RAIL_Z + 20, RAIL_Z + 30, RAIL_Z + 40];
  for (const z of sidings) {
    const pts = []; for (let x = YARD_X[0]; x <= YARD_X[1]; x += 10) pts.push([x, z]);
    const b = new THREE.Mesh(ribbon(pts, 6, 0.17, 1.6), ballastMat);
    const t = new THREE.Mesh(ribbon(pts, 2.7, 0.29, 0.6), tieMat);
    b.receiveShadow = t.receiveShadow = true;
    g.add(b, t);
    for (const s of [-0.72, 0.72]) rails.push(mat4((YARD_X[0] + YARD_X[1]) / 2, 0.41, z + s, Math.PI / 2, 0.08, 0.16, YARD_X[1] - YARD_X[0]));
  }
  g.add(instanced(new THREE.BoxGeometry(1, 1, 1), railMat, rails, { receive: false }));

  // freight cars: boxcars, covered hoppers and tank cars, plus two locomotives
  const truck = (x) => [part(new THREE.BoxGeometry(2.6, 0.7, 2.6), '#1d1d1d', 0, 0.7, x), ...[-0.9, 0.9].flatMap((zz) => [-0.72, 0.72].map((sx) => part(new THREE.CylinderGeometry(0.46, 0.46, 0.15, 12), '#222222', sx, 0.46, x + zz, 0, 0, Math.PI / 2)))];
  const boxcar = mergeParts([part(new THREE.BoxGeometry(3.0, 3.8, 15.5), '#ffffff', 0, 3.2, 0), part(new THREE.BoxGeometry(3.05, 0.25, 15.6), '#2a2a2a', 0, 1.2, 0), part(new THREE.BoxGeometry(0.06, 2.8, 3.2), '#5a5a5a', 1.54, 2.8, 0), ...truck(-5.6), ...truck(5.6)]);
  const hopper = mergeParts([part(new THREE.BoxGeometry(3.1, 3.4, 16), '#ffffff', 0, 3.4, 0), part(new THREE.CylinderGeometry(1.55, 1.55, 16, 16, 1, false, 0, Math.PI), '#ffffff', 0, 5.1, 0, Math.PI / 2, 0, -Math.PI / 2), ...truck(-6), ...truck(6)]);
  const tank = mergeParts([part(new THREE.CylinderGeometry(1.5, 1.5, 15, 18), '#ffffff', 0, 3.0, 0, Math.PI / 2, 0, 0), part(new THREE.SphereGeometry(1.5, 14, 8), '#ffffff', 0, 3.0, 7.5), part(new THREE.SphereGeometry(1.5, 14, 8), '#ffffff', 0, 3.0, -7.5), part(new THREE.BoxGeometry(2.8, 0.3, 17), '#2a2a2a', 0, 1.3, 0), ...truck(-6), ...truck(6)]);
  const loco = mergeParts([part(new THREE.BoxGeometry(3.0, 3.4, 20), '#ffffff', 0, 3.0, 0), part(new THREE.BoxGeometry(3.0, 1.2, 4.2), '#ffffff', 0, 5.3, 7.4), part(new THREE.BoxGeometry(3.02, 0.6, 4.0), '#1b2329', 0, 5.2, 7.4), part(new THREE.BoxGeometry(3.1, 0.35, 20.4), '#222222', 0, 1.2, 0), ...truck(-7), ...truck(7)]);
  const lists = { boxcar: [], hopper: [], tank: [], loco: [] }, cols = { boxcar: [], hopper: [], tank: [], loco: [] };
  const palette = { boxcar: ['#8a3a2a', '#6b3a2a', '#7a5a3a', '#2f4a6a', '#b88a2a', '#5a5f63'], hopper: ['#9aa0a5', '#b9a98a', '#7a6a5a', '#c9c2b2'], tank: ['#1d1d1f', '#e6e6e2', '#2a2a2c'], loco: ['#e2b52a', '#2a3a6a', '#1d1d1f'] };
  for (const z of [RAIL_Z, ...sidings]) {
    let x = YARD_X[0] + 40 + r() * 80;
    const end = z === RAIL_Z ? YARD_X[0] + 900 : YARD_X[1] - 40;
    while (x < end) {
      if (r() < 0.12) { x += 30 + r() * 60; continue; }
      const kind = z === RAIL_Z && x < YARD_X[0] + 80 ? 'loco' : ['boxcar', 'boxcar', 'hopper', 'tank'][Math.floor(r() * 4)];
      const len = kind === 'loco' ? 21 : 17.5;
      lists[kind].push(mat4(x + len / 2, 0.42, z, Math.PI / 2));
      cols[kind].push(palette[kind][Math.floor(r() * palette[kind].length)]);
      x += len + 0.8;
    }
  }
  lists.loco.push(mat4(YARD_X[0] + 60, 0.42, RAIL_Z, Math.PI / 2)); cols.loco.push('#e2b52a');
  const carMat = std({ vertexColors: true, roughness: 0.75, metalness: 0.35 });
  for (const [k, geo] of [['boxcar', boxcar], ['hopper', hopper], ['tank', tank], ['loco', loco]]) g.add(instanced(geo, carMat, lists[k], { colors: cols[k] }));

  // depot: two-story brick station with a platform canopy
  const brickMat = facadeMaterial('brick');
  const dep = instanced(new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0), brickMat, [mat4(I.x - 50, 0, RAIL_Z - 28, 0, 46, 9, 12)], { colors: ['#9a4a35'] });
  g.add(dep);
  const roof = new THREE.Mesh(new THREE.BoxGeometry(50, 0.6, 16), std({ color: '#4a3a32', roughness: 0.8 }));
  roof.position.set(I.x - 50, 9.3, RAIL_Z - 28); roof.castShadow = true; g.add(roof);
  const canopy = new THREE.Mesh(new THREE.BoxGeometry(80, 0.4, 7), std({ color: '#3d4a44', roughness: 0.7, metalness: 0.3 }));
  canopy.position.set(I.x - 50, 4.2, RAIL_Z - 15); canopy.castShadow = true; g.add(canopy);
  const plat = new THREE.Mesh(new THREE.BoxGeometry(90, 0.9, 7), std({ map: TX.concrete().map, color: '#cfc9bd' }));
  plat.position.set(I.x - 50, 0.45, RAIL_Z - 15); plat.receiveShadow = true; g.add(plat);
  const name = new THREE.Mesh(new THREE.PlaneGeometry(14, 2), std({ map: signTex(['IRONWOOD'], { w: 512, h: 72, bg: '#1d2a22', fg: '#e8d9a8', border: '#e8d9a8', font: 'bold 54px Georgia' }) }));
  name.position.set(I.x - 50, 6.6, RAIL_Z - 21.95); g.add(name);

  // grain and cement silos south of the yard
  const siloMat = std({ map: TX.concrete().map, color: '#d8d4cc', roughness: 0.85 });
  for (let k = 0; k < 6; k++) {
    const s = new THREE.Mesh(new THREE.CylinderGeometry(4.2, 4.2, 32, 28), siloMat);
    s.position.set(I.x - 1100 + (k % 3) * 8.6, 16, RAIL_Z + 70 + Math.floor(k / 3) * 8.6);
    s.castShadow = s.receiveShadow = true; g.add(s);
  }
  const head = new THREE.Mesh(new THREE.BoxGeometry(26, 6, 6), std({ color: '#a7a39a', roughness: 0.7, metalness: 0.3 }));
  head.position.set(I.x - 1091.4, 35, RAIL_Z + 74.3); head.castShadow = true; g.add(head);

  // water tower with the town's name
  const wt = new THREE.Group();
  const tm = std({ color: '#c9ced1', metalness: 0.4, roughness: 0.5 });
  for (const dx of [-5, 5]) for (const dz of [-5, 5]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.45, 30, 8), tm); l.position.set(dx * 0.85, 15, dz * 0.85); wt.add(l); }
  const nameTex = canvasTex(1024, 128, (c, w, h) => { c.fillStyle = '#c9ced1'; c.fillRect(0, 0, w, h); c.fillStyle = '#1f3a5a'; c.font = 'bold 84px Arial'; c.textAlign = 'center'; c.textBaseline = 'middle'; for (const x of [w * 0.25, w * 0.75]) c.fillText('IRONWOOD', x, h / 2); });
  const tankM = new THREE.Mesh(new THREE.CylinderGeometry(8, 8, 9, 48), std({ map: nameTex, metalness: 0.4, roughness: 0.5 }));
  tankM.position.y = 34.5; wt.add(tankM);
  const capM = new THREE.Mesh(new THREE.ConeGeometry(8.3, 3.4, 48), tm); capM.position.y = 40.7; wt.add(capM);
  const bot = new THREE.Mesh(new THREE.SphereGeometry(8, 48, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), tm); bot.position.y = 30; wt.add(bot);
  wt.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  wt.position.set(I.x + 350, 0, RAIL_Z - 45);
  g.add(wt);
  g.add(contactShadows([{ x: I.x - 50, z: RAIL_Z - 28, w: 52, d: 18 }]));
  return g;
}
