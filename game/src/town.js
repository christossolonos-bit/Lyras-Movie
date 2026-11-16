import * as THREE from 'three';
import { TOWN_Z } from './terrain.js';
import { rng, canvasTex, signTex, speckle, boxUV, part, mergeParts, mat4, instanced, flatRect, nightEmissive } from './util.js';
import * as TX from './textures.js';
import { buildCars, buildLightPoles, buildPalms, buildTrees, contactShadows } from './props.js';
import { crossCards, cardMaterial } from './scatter.js';
import { HOMES } from './homes.js';

// A small desert town, 40 miles north of Vira. The highway becomes Main Street (x = 0).
const T = TOWN_Z;
const CROSS = [-4, -3, -2, -1, 0, 1, 2, 3, 4].map((c) => T + c * 110);
const NS_STREETS = [160, 320, 480];
const STUCCO = ['#efe2c8', '#e2c8a2', '#d3a882', '#f3ebdc', '#c9b394', '#e0bea0', '#b9c3ad', '#d2d6d8', '#ead6ae', '#dcae8c'];
const ROOFS = ['#b0583a', '#8f4630', '#6b6560', '#7d7b76', '#b86b48', '#9a8a74', '#5c5550'];
const SHOPS = ['DINER', 'HARDWARE', 'CAFE', 'SALOON', 'PHARMACY', 'GROCERY', 'POST OFFICE', 'BARBER', 'THRIFT', 'LAUNDRY', 'BANK', 'PIZZA', 'AUTO PARTS', 'TACOS', 'BOOKS', 'FEED & SEED'];
const SIGN_COLORS = [['#7a1f1f', '#f6e7c8'], ['#1f3a5a', '#ffffff'], ['#f2e3c2', '#5a2a1a'], ['#2f4a2a', '#f0e6c8'], ['#111111', '#ffcf5a']];
const AWNINGS = ['#8b2d2d', '#2d5a6b', '#3f6b3a', '#b07a2a', '#5a3a6b', '#6b6b6b'];

const reserved = [
  [-310, -170, T - 220, T - 110], // church
  [330, 470, T + 110, T + 220],   // water tower
  [170, 310, T - 330, T - 220],   // school
];
const isReserved = (x, z) => reserved.some(([a, b, c, d]) => x > a && x < b && z > c && z < d);

const std = (o) => new THREE.MeshStandardMaterial(o);
function rep(set, rx, ry) {
  const map = set.map.clone(); map.repeat.set(rx, ry); map.needsUpdate = true;
  const normal = set.normal.clone(); normal.repeat.set(rx, ry); normal.needsUpdate = true;
  return { map, normal };
}

const plainCache = new Map();
function stuccoMat(color) {
  if (!plainCache.has(color)) {
    const s = rep(TX.stucco(), 6, 3);
    plainCache.set(color, std({ color, map: s.map, normalMap: s.normal, roughness: 0.92 }));
  }
  return plainCache.get(color);
}

const facadeCache = new Map();
function facade(wallColor, stories, brickFront) {
  const key = wallColor + stories + brickFront;
  if (facadeCache.has(key)) return facadeCache.get(key);
  const lit = Math.random();
  const brickImg = TX.brick().map.image;
  const draw = (emiss) => (c, w, h) => {
    if (emiss) { c.fillStyle = '#000'; c.fillRect(0, 0, w, h); }
    else if (brickFront) { c.fillStyle = c.createPattern(brickImg, 'repeat'); c.fillRect(0, 0, w, h); }
    else { c.fillStyle = wallColor; c.fillRect(0, 0, w, h); speckle(c, w, h, 1500, 0.06, 2); }
    if (!emiss) { c.fillStyle = 'rgba(0,0,0,.22)'; c.fillRect(0, 0, w, h * 0.04); }
    const g0 = stories === 2 ? 0.55 : 0.12, gh = 1 - g0;
    // display windows with mullions, transom, kickplate, recessed door
    const wy = h * (g0 + gh * 0.3), wh = gh * h * 0.5;
    if (!emiss) {
      const grd = c.createLinearGradient(0, wy, 0, wy + wh);
      grd.addColorStop(0, '#5c7480'); grd.addColorStop(0.5, '#25333b'); grd.addColorStop(1, '#1a2329');
      c.fillStyle = grd;
    } else c.fillStyle = '#ffd08a';
    c.fillRect(w * 0.06, wy, w * 0.6, wh);
    c.fillRect(w * 0.06, h * (g0 + gh * 0.18), w * 0.6, h * gh * 0.09);
    c.fillStyle = emiss ? '#e6b06c' : '#2a1f18';
    c.fillRect(w * 0.72, h * (g0 + gh * 0.22), w * 0.18, h * gh * 0.78);
    if (!emiss) {
      c.fillStyle = '#3a3027';
      for (const fx of [0.06, 0.26, 0.46, 0.66]) c.fillRect(w * fx - 2, wy, 4, wh);
      c.fillRect(w * 0.06, wy - 2, w * 0.6, 4); c.fillRect(w * 0.06, wy + wh - 2, w * 0.6, 4);
      c.fillStyle = '#5a4a3c'; c.fillRect(w * 0.06, wy + wh, w * 0.6, h * gh * 0.12);
    }
    if (stories === 2) for (let k = 0; k < 3; k++) {
      if (emiss && (k + lit * 3) % 3 < 1.2) continue;
      const x = w * (0.1 + k * 0.3), y = h * 0.16, ww = w * 0.16, hh = h * 0.25;
      if (!emiss) { c.fillStyle = '#e8e2d4'; c.fillRect(x - 3, y - 3, ww + 6, hh + 8); }
      c.fillStyle = emiss ? '#ffd59a' : '#26323a';
      c.fillRect(x, y, ww, hh);
    }
  };
  const mat = nightEmissive(std({
    map: canvasTex(256, 256, draw(false)), emissiveMap: canvasTex(256, 256, draw(true)), emissive: '#ffffff', roughness: 0.85,
  }), 1.0);
  facadeCache.set(key, mat);
  return mat;
}

export function buildTown() {
  const g = new THREE.Group();
  const r = rng(1979);
  const cars = [], palms = [], trees = [], lamps = [];

  // ---------- streets, curbs, sidewalks ----------
  const asphalt = std({ map: TX.asphalt().map, normalMap: TX.asphalt().normal, roughness: 0.95 });
  const concreteT = TX.concrete();
  const walk = std({ map: concreteT.map, normalMap: concreteT.normal, roughness: 0.9 });
  const curbMat = std({ color: '#cfc9bd', roughness: 0.9, map: concreteT.map });
  g.add(flatRect(22, 940, 0, T, 0.3, asphalt, 10));
  const yellow = std({ color: '#d9ad2b', roughness: 0.7 });
  g.add(flatRect(0.15, 940, -0.15, T, 0.32, yellow), flatRect(0.15, 940, 0.15, T, 0.32, yellow));
  for (const s of [-1, 1]) g.add(flatRect(4, 680, s * 13, T, 0.38, walk, 3));
  for (const z of CROSS) g.add(flatRect(1000, 10, 0, z, 0.22, asphalt, 10));
  for (const x of NS_STREETS) for (const s of [-1, 1]) g.add(flatRect(9, 890, s * x, T, 0.23, asphalt, 10));

  const curbs = [];
  const curbRun = (ax, az, bx, bz) => {
    const len = Math.hypot(bx - ax, bz - az);
    if (len < 1) return;
    curbs.push(mat4((ax + bx) / 2, 0.2, (az + bz) / 2, Math.atan2(bx - ax, bz - az), 0.3, 0.3, len));
  };
  // E-W streets: curbs broken at each N-S street
  const xsBreaks = [-480, -320, -160, 0, 160, 320, 480];
  const halfW = (x) => (x === 0 ? 11 : 4.5);
  for (const z of CROSS) for (const s of [-1, 1]) {
    let x0 = -500;
    for (const bx of xsBreaks) { curbRun(x0, z + s * 5.15, bx - halfW(bx), z + s * 5.15); x0 = bx + halfW(bx); }
    curbRun(x0, z + s * 5.15, 500, z + s * 5.15);
  }
  for (const x of [...NS_STREETS, ...NS_STREETS.map((v) => -v), 0]) for (const s of [-1, 1]) {
    const off = x === 0 ? 11.15 : 4.65;
    let z0 = T - (x === 0 ? 470 : 445);
    for (const bz of CROSS) { curbRun(x + s * off, z0, x + s * off, bz - 5); z0 = bz + 5; }
    curbRun(x + s * off, z0, x + s * off, T + (x === 0 ? 470 : 445));
  }
  g.add(instanced(new THREE.BoxGeometry(1, 1, 1), curbMat, curbs, { cast: false }));

  // crosswalks on Main Street
  const zebra = [];
  for (const z of CROSS) if (Math.abs(z - T) <= 330) for (const s of [-1, 1]) for (let x = -10; x <= 10; x += 1.2) zebra.push(mat4(x, 0.33, z + s * 7.5));
  g.add(instanced(new THREE.BoxGeometry(0.6, 0.02, 3), std({ color: '#ecebe4', roughness: 0.7 }), zebra, { cast: false }));

  // ---------- downtown storefronts ----------
  let shop = 0;
  const rtu = [], skirts = [];
  for (const s of [-1, 1]) for (let c = -3; c <= 2; c++) {
    const zs = T + c * 110 + 6, ze = T + (c + 1) * 110 - 6;
    let z = zs;
    while (z < ze - 8) {
      const width = Math.min(12 + r() * 12, ze - z);
      if (r() < 0.12) {
        for (let k = 0; k < 2; k++) cars.push({ x: s * (24 + r() * 14), z: z + 3 + r() * (width - 6), ry: Math.PI / 2 + (r() < 0.5 ? 0 : Math.PI) });
        z += width; continue;
      }
      const depth = 16 + r() * 12, two = r() < 0.35, h = two ? 9 : 5.2 + r();
      const wallC = STUCCO[Math.floor(r() * STUCCO.length)];
      const brickFront = r() < 0.3;
      const side = stuccoMat(wallC), roofM = std({ color: '#8f8a82', roughness: 0.9 });
      const front = facade(wallC, two ? 2 : 1, brickFront);
      const mats = s > 0 ? [side, front, roofM, roofM, side, side] : [front, side, roofM, roofM, side, side];
      const b = new THREE.Mesh(new THREE.BoxGeometry(depth, h, width - 0.4), mats);
      const cx = s * (15 + depth / 2), cz = z + width / 2;
      b.position.set(cx, h / 2, cz);
      b.castShadow = b.receiveShadow = true;
      g.add(b);
      skirts.push({ x: cx, z: cz, w: depth + 3, d: width + 2 });
      const tall = r() < 0.45 ? 1.6 : 0.5;
      const ff = new THREE.Mesh(new THREE.BoxGeometry(0.5, h + tall, width - 0.4), brickFront ? std({ map: TX.brick().map, normalMap: TX.brick().normal, roughness: 0.9 }) : side);
      ff.position.set(s * 15.25, (h + tall) / 2, cz);
      ff.castShadow = true;
      g.add(ff);
      const cornice = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.35, width - 0.2), stuccoMat('#e9e2d2'));
      cornice.position.set(s * 15.05, h + tall - 0.2, cz);
      g.add(cornice);
      const aw = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.12, (width - 0.4) * 0.86), std({ color: AWNINGS[Math.floor(r() * AWNINGS.length)], roughness: 0.85 }));
      aw.position.set(s * 13.8, 3.3, cz);
      aw.rotation.z = s * 0.22;
      aw.castShadow = true;
      g.add(aw);
      if (r() < 0.6) rtu.push(mat4(cx + s * depth * 0.2, h, cz + (r() - 0.5) * width * 0.4, r() < 0.5 ? 0 : Math.PI / 2));
      if (shop < SHOPS.length && r() < 0.7) {
        const [bg, fg] = SIGN_COLORS[Math.floor(r() * SIGN_COLORS.length)];
        const sw = Math.min(10, (width - 0.4) * 0.8);
        const sm = nightEmissive(std({ map: signTex([SHOPS[shop++]], { w: 512, h: 96, bg, fg, border: fg, font: 'bold 60px Georgia' }), emissive: '#ffffff', roughness: 0.7 }), 0.6);
        sm.emissiveMap = sm.map;
        const sign = new THREE.Mesh(new THREE.PlaneGeometry(sw, sw * 96 / 512), sm);
        sign.position.set(s * 14.7, Math.min(h - 0.7, 4.4), cz);
        sign.rotation.y = -s * Math.PI / 2;
        g.add(sign);
      }
      z += width;
    }
    for (let zz = zs; zz < ze; zz += 6.5) if (r() < 0.45) cars.push({ x: s * 9.2, z: zz + 3, ry: s > 0 ? Math.PI : 0 });
  }
  const rtuGeo = new THREE.BoxGeometry(2.2, 1.2, 1.6); rtuGeo.translate(0, 0.6, 0);
  g.add(instanced(rtuGeo, std({ color: '#c7c9c6', roughness: 0.5, metalness: 0.5 }), rtu));

  // ---------- houses ----------
  const B = { body: [], bodyCol: [], garage: [], garageCol: [], hip: [], hipCol: [], gable: [], gableCol: [], gdoor: [], door: [], cooler: [], wall: [], drive: [], mail: [], agave: [], pool: [], deck: [] };
  const walls = [];
  const bands = [[50, 152], [168, 314], [328, 474]];
  for (const s of [-1, 1]) for (let c = -4; c < 4; c++) for (const [a, b] of bands) {
    const mid = T + c * 110 + 55;
    if (a === 50 && Math.abs(mid - T) < 330) {
      for (let k = 0; k < 4; k++) if (r() < 0.6) cars.push({ x: s * (60 + r() * 80), z: mid + (r() - 0.5) * 80, ry: r() * Math.PI });
      continue;
    }
    if (!isReserved(s * (a + b) / 2, mid)) walls.push(mat4(s * (a + b) / 2, 0.9, mid, 0, b - a, 1.8, 0.22));
    for (const row of [-1, 1]) {
      const edge = row < 0 ? T + c * 110 + 5 : T + (c + 1) * 110 - 5;
      const lots = [];
      for (let lx = a + 12; lx <= b - 10; lx += 24) lots.push(lx);
      lots.forEach((lx, li) => {
        const x = s * lx;
        if (isReserved(x, edge - row * 20) || r() < 0.1) return;
        const w = 10 + r() * 3, d = 9 + r() * 3, h = 3.0 + r() * 0.5;
        const gs = r() < 0.5 ? -1 : 1;
        const xb = x - gs * 3.25, xg = xb + gs * (w / 2 + 3.25);
        const zc = edge - row * (7 + d / 2);
        const zg = edge - row * (6 + 3.5);
        const col = STUCCO[Math.floor(r() * STUCCO.length)];
        const roofC = ROOFS[Math.floor(r() * ROOFS.length)];
        B.body.push(mat4(xb, h / 2, zc, 0, w, h, d)); B.bodyCol.push(col);
        B.garage.push(mat4(xg, 1.45, zg, 0, 6.5, 2.9, 7)); B.garageCol.push(col);
        const rh = 1.5 + r() * 1.0;
        if (r() < 0.55) { B.hip.push(mat4(xb, h, zc, 0, (w / 2 + 0.6) / 0.7071, rh, (d / 2 + 0.6) / 0.7071)); B.hipCol.push(roofC); }
        else { B.gable.push(mat4(xb, h, zc, 0, w + 1.2, rh, d + 1.2)); B.gableCol.push(roofC); }
        B.hip.push(mat4(xg, 2.9, zg, 0, 4.2 / 0.7071, 1.1, 4.0 / 0.7071)); B.hipCol.push(roofC);
        const face = row < 0 ? Math.PI : 0;
        B.gdoor.push(mat4(xg, 1.15, zg + row * 3.52, face));
        B.door.push(mat4(xb - gs * (w * 0.15), 1.05, zc + row * (d / 2 + 0.02), face));
        B.cooler.push(mat4(xb + gs * 1.5, h + rh * 0.45, zc - row * d * 0.18, r() * 0.3));
        B.drive.push(mat4(xg, 0.08, edge - row * 3, 0, 5.5, 0.05, 6));
        B.mail.push(mat4(xg + gs * 3.6, 0, edge - row * 0.7, face));
        // block walls enclosing the back yard (left edge of every lot, right edge of the last)
        const zRear = zc - row * d / 2, len = Math.abs(mid - zRear);
        B.wall.push(mat4(x - 12, 0.9, (mid + zRear) / 2, 0, 0.22, 1.8, len));
        if (li === lots.length - 1) B.wall.push(mat4(x + 12, 0.9, (mid + zRear) / 2, 0, 0.22, 1.8, len));
        for (let k = 0; k < 3; k++) if (r() < 0.6) B.agave.push(mat4(xb + (r() - 0.5) * w, 0, zc + row * (d / 2 + 1.2 + r() * 2.5), r() * 6, 0.5 + r() * 0.4, 0.5 + r() * 0.3, 0.5 + r() * 0.4));
        if (r() < 0.28) {
          const pz = zRear - row * 7;
          B.pool.push(mat4(xb, 0.1, pz, 0, 7, 1, 3.8)); B.deck.push(mat4(xb, 0.07, pz, 0, 10, 0.06, 6.5));
        }
        if (r() < 0.4) cars.push({ x: xg + (r() - 0.5) * 0.6, z: edge - row * 3.4, ry: 0 });
        else HOMES.saltbrush.push({ city: 'saltbrush', drive: [xg, edge - row * 3.4], street: edge + row * 5 });
        if (r() < 0.35) trees.push({ x: xb - gs * (w / 2 - 1.5), z: edge - row * 3.2, s: 0.7 + r() * 0.5, ry: r() * 6 });
        if (r() < 0.25) palms.push({ x: x + (r() - 0.5) * 18, z: zRear - row * (10 + r() * 8), h: 7 + r() * 7, ry: r() * 6 });
        else if (r() < 0.3) trees.push({ x: x + (r() - 0.5) * 16, z: zRear - row * (9 + r() * 8), s: 0.9 + r() * 0.5, ry: r() * 6 });
        skirts.push({ x: xb, z: zc, w: w + 2, d: d + 2 });
      });
    }
  }
  const houseTex = canvasTex(256, 128, (c, w, h) => {
    c.fillStyle = '#ffffff'; c.fillRect(0, 0, w, h); speckle(c, w, h, 900, 0.07, 2);
    for (const x of [0.14, 0.62]) {
      c.fillStyle = '#ffffff'; c.fillRect(w * x - 4, h * 0.28 - 4, w * 0.24 + 8, h * 0.36 + 10);
      const grd = c.createLinearGradient(0, h * 0.28, 0, h * 0.64); grd.addColorStop(0, '#6f8794'); grd.addColorStop(1, '#202a30');
      c.fillStyle = grd; c.fillRect(w * x, h * 0.28, w * 0.24, h * 0.36);
      c.fillStyle = '#e9e9e9'; c.fillRect(w * x + w * 0.12 - 1, h * 0.28, 2, h * 0.36);
    }
    c.fillStyle = 'rgba(0,0,0,.12)'; c.fillRect(0, h * 0.94, w, h * 0.06);
  });
  const houseLit = canvasTex(256, 128, (c, w, h) => { c.fillStyle = '#000'; c.fillRect(0, 0, w, h); c.fillStyle = '#ffcf86'; c.fillRect(w * 0.14, h * 0.28, w * 0.24, h * 0.36); });
  const stuccoN = rep(TX.stucco(), 4, 2).normal;
  const unitBox = new THREE.BoxGeometry(1, 1, 1);
  g.add(instanced(unitBox, nightEmissive(std({ map: houseTex, normalMap: stuccoN, emissiveMap: houseLit, emissive: '#ffffff', roughness: 0.9 }), 0.8), B.body, { colors: B.bodyCol }));
  const st = rep(TX.stucco(), 3, 2);
  g.add(instanced(unitBox, std({ map: st.map, normalMap: st.normal, roughness: 0.9 }), B.garage, { colors: B.garageCol }));

  const tiles = TX.roofTiles();
  const hipGeo = new THREE.ConeGeometry(1, 1, 4, 1);
  hipGeo.rotateY(Math.PI / 4); hipGeo.translate(0, 0.5, 0);
  const hipT = rep(tiles, 8, 2.5);
  g.add(instanced(hipGeo, std({ map: hipT.map, normalMap: hipT.normal, roughness: 0.8, flatShading: true }), B.hip, { colors: B.hipCol }));
  const gableT = rep(tiles, 6, 3);
  g.add(instanced(gableGeometry(), std({ map: gableT.map, normalMap: gableT.normal, roughness: 0.8 }), B.gable, { colors: B.gableCol }));

  const gdoorTex = canvasTex(128, 96, (c, w, h) => {
    c.fillStyle = '#efefea'; c.fillRect(0, 0, w, h);
    for (let y = 0; y < h; y += 24) { c.fillStyle = '#c9c9c2'; c.fillRect(0, y, w, 2); }
    for (let x = 0; x < w; x += 32) for (let y = 0; y < h; y += 24) { c.strokeStyle = '#d6d6cf'; c.strokeRect(x + 4, y + 5, 24, 15); }
  });
  g.add(instanced(new THREE.PlaneGeometry(4.8, 2.3), std({ map: gdoorTex, roughness: 0.6, metalness: 0.2 }), B.gdoor, { cast: false }));
  g.add(instanced(new THREE.PlaneGeometry(1.0, 2.1), std({ color: '#5a3a28', roughness: 0.7 }), B.door, { cast: false }));
  const coolerGeo = new THREE.BoxGeometry(1.1, 0.9, 1.1); coolerGeo.translate(0, 0.45, 0);
  const cs = TX.chillerSide();
  g.add(instanced(coolerGeo, std({ map: cs.map, normalMap: cs.normal, color: '#d9d2c2', roughness: 0.6, metalness: 0.4 }), B.cooler));
  const block = TX.blockWall();
  const wallT = rep(block, 9, 1.1);
  const wallMat = std({ map: wallT.map, normalMap: wallT.normal, color: '#d8c8aa', roughness: 0.95 });
  g.add(instanced(unitBox, wallMat, [...B.wall, ...walls]));
  const driveT = rep(concreteT, 1, 1);
  g.add(instanced(unitBox, std({ map: driveT.map, normalMap: driveT.normal, roughness: 0.9 }), B.drive, { cast: false }));
  const mailGeo = mergeParts([
    part(new THREE.BoxGeometry(0.08, 1.1, 0.08), '#5d5d5d', 0, 0.55, 0),
    part(new THREE.BoxGeometry(0.26, 0.24, 0.5), '#2f3236', 0, 1.2, 0),
  ]);
  g.add(instanced(mailGeo, std({ vertexColors: true, roughness: 0.6, metalness: 0.5 }), B.mail, { receive: false }));
  const agaveMat = cardMaterial(TX.spikeCard(), { color: '#b9c9a8' });
  g.add(instanced(crossCards(1.6, 1.6, 3, -0.6), agaveMat, B.agave, { receive: false }));
  const poolGeo = new THREE.PlaneGeometry(1, 1); poolGeo.rotateX(-Math.PI / 2);
  g.add(instanced(poolGeo, std({ color: '#3fb6c9', roughness: 0.05, metalness: 0.1, emissive: '#0a3a44', emissiveIntensity: 0.6 }), B.pool, { cast: false }));
  g.add(instanced(unitBox, std({ map: driveT.map, color: '#efe8da', roughness: 0.9 }), B.deck, { cast: false }));

  g.add(contactShadows(skirts.map((s) => ({ ...s, w: s.w * 1.15, d: s.d * 1.15 }))));

  // ---------- alley power lines along the rear lot lines ----------
  const poles = [], wire = [];
  for (const s of [-1, 1]) for (let c = -4; c < 4; c++) for (const [a, b] of bands) {
    const mid = T + c * 110 + 55;
    if (a === 50 && Math.abs(mid - T) < 330) continue;
    let prev = null;
    for (let x = a + 4; x <= b; x += 36) {
      const px = s * x, pz = mid + 0.6;
      poles.push(mat4(px, 0, pz, Math.PI / 2));
      const top = [[px, 9.6, pz - 0.9], [px, 9.6, pz + 0.9], [px, 10.6, pz]];
      if (prev) for (let w = 0; w < 3; w++) for (let k = 0; k < 6; k++) for (const t of [k / 6, (k + 1) / 6])
        wire.push(prev[w][0] + (top[w][0] - prev[w][0]) * t, prev[w][1] - 4 * 0.5 * t * (1 - t), prev[w][2]);
      prev = top;
    }
  }
  const poleGeo = mergeParts([
    part(new THREE.CylinderGeometry(0.12, 0.16, 10.5, 6), '#5c4632', 0, 5.25, 0),
    part(new THREE.BoxGeometry(2.2, 0.12, 0.12), '#4a3828', 0, 9.4, 0),
    part(new THREE.CylinderGeometry(0.28, 0.28, 0.9, 8), '#8a8f93', 0.35, 8.3, 0),
  ]);
  g.add(instanced(poleGeo, std({ vertexColors: true, roughness: 1 }), poles, { receive: false }));
  const wg = new THREE.BufferGeometry();
  wg.setAttribute('position', new THREE.Float32BufferAttribute(wire, 3));
  g.add(new THREE.LineSegments(wg, new THREE.LineBasicMaterial({ color: '#1d1a17' })));

  // ---------- stop signs at residential intersections ----------
  const stops = [];
  for (const z of CROSS) for (const x of [...NS_STREETS, ...NS_STREETS.map((v) => -v)]) {
    stops.push(mat4(x - 6, 0, z - 7, Math.PI), mat4(x + 6, 0, z + 7, 0));
  }
  const stopTex = canvasTex(128, 128, (c, w, h) => {
    c.clearRect(0, 0, w, h);
    const oct = (rad, color) => { c.fillStyle = color; c.beginPath(); for (let i = 0; i < 8; i++) { const a = Math.PI / 8 + i * Math.PI / 4; c.lineTo(64 + Math.cos(a) * rad, 64 + Math.sin(a) * rad); } c.fill(); };
    oct(63, '#ffffff'); oct(57, '#b5121b');
    c.fillStyle = '#fff'; c.font = 'bold 34px Arial'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('STOP', 64, 66);
  });
  const stopFace = new THREE.CircleGeometry(0.42, 8, Math.PI / 8); stopFace.translate(0, 2.2, 0.04);
  const stopPost = mergeParts([part(new THREE.BoxGeometry(0.06, 2.4, 0.06), '#8a8f93', 0, 1.2, 0), part(new THREE.CircleGeometry(0.42, 8, Math.PI / 8).rotateY(Math.PI), '#8a8f93', 0, 2.2, 0.03)]);
  g.add(instanced(stopPost, std({ vertexColors: true, metalness: 0.5, roughness: 0.5 }), stops, { receive: false }));
  g.add(instanced(stopFace, std({ map: stopTex, alphaTest: 0.5, roughness: 0.5 }), stops, { cast: false }));

  // ---------- main street lights & palms ----------
  for (let z = T - 450; z <= T + 450; z += 32) for (const s of [-1, 1]) {
    lamps.push({ x: s * 11.6, z, ry: s > 0 ? Math.PI : 0 });
    if (Math.abs(z - T) < 340) palms.push({ x: s * 12.6, z: z + 16, h: 8 + r() * 4, ry: r() * 6 });
  }
  for (const z of CROSS) for (const x of [...NS_STREETS, ...NS_STREETS.map((v) => -v)]) lamps.push({ x: x + 5.5, z: z - 6, ry: Math.PI });
  g.add(buildLightPoles(lamps, 8.5));

  g.add(buildGasStation(cars));
  g.add(buildMotel(cars));
  g.add(buildChurch());
  g.add(buildWaterTower());
  g.add(buildSchool(trees));

  // ---------- outskirts: sheds and trailers ----------
  const sheds = [], shedCol = [];
  for (let i = 0; i < 26; i++) {
    const s = r() < 0.5 ? -1 : 1, x = s * (540 + r() * 380), z = T + (r() - 0.5) * 1100;
    const big = r() < 0.4;
    sheds.push(mat4(x, big ? 3 : 1.6, z, r() * Math.PI, big ? 18 : 14, big ? 6 : 3.2, big ? 12 : 4.5));
    shedCol.push(big ? '#9aa1a6' : ['#e9e6dc', '#cfd3d6', '#d8c9a8'][i % 3]);
    if (r() < 0.6) cars.push({ x: x + 10, z: z + (r() - 0.5) * 10, ry: r() * Math.PI, kind: 'pickup' });
  }
  const ribs = canvasTex(256, 64, (c, w, h) => { c.fillStyle = '#e8e8e8'; c.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 12) { c.fillStyle = '#b8b8b8'; c.fillRect(x, 0, 3, h); } speckle(c, w, h, 600, 0.12, 2); }, { repeat: [3, 1] });
  g.add(instanced(unitBox, std({ map: ribs, roughness: 0.55, metalness: 0.5 }), sheds, { colors: shedCol }));

  g.add(buildPalms(palms));
  g.add(buildTrees(trees));
  g.add(buildCars(cars, 11));
  return g;
}

// Gable roof prism: ridge along x, slopes facing +z/-z, unit size, base at y = 0.
function gableGeometry() {
  const P = [], U = [];
  const quad = (a, b, c, d, ua, ub, uc, ud) => { P.push(...a, ...b, ...c, ...a, ...c, ...d); U.push(...ua, ...ub, ...uc, ...ua, ...uc, ...ud); };
  quad([-0.5, 0, 0.5], [0.5, 0, 0.5], [0.5, 1, 0], [-0.5, 1, 0], [0, 0], [1, 0], [1, 1], [0, 1]);
  quad([0.5, 0, -0.5], [-0.5, 0, -0.5], [-0.5, 1, 0], [0.5, 1, 0], [0, 0], [1, 0], [1, 1], [0, 1]);
  P.push(-0.5, 0, -0.5, -0.5, 0, 0.5, -0.5, 1, 0, 0.5, 0, 0.5, 0.5, 0, -0.5, 0.5, 1, 0);
  U.push(0, 0, 1, 0, 0.5, 0.4, 0, 0, 1, 0, 0.5, 0.4);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(U, 2));
  g.computeVertexNormals();
  return g;
}

function buildGasStation(cars) {
  const g = new THREE.Group();
  const z0 = T + 500;
  const ct = TX.concrete();
  g.add(flatRect(84, 76, 62, z0, 0.28, std({ map: ct.map, normalMap: ct.normal, roughness: 0.9 }), 6));
  const canopyMat = nightEmissive(std({ color: '#f4f4f2', emissive: '#fff6e0', roughness: 0.5 }), 0.8);
  const canopy = new THREE.Mesh(new THREE.BoxGeometry(16, 1, 30), canopyMat);
  canopy.position.set(48, 5.6, z0 - 6);
  canopy.castShadow = true;
  const fascia = new THREE.Mesh(new THREE.BoxGeometry(16.2, 0.55, 30.2), std({ color: '#b3201c', roughness: 0.5 }));
  fascia.position.set(48, 5.3, z0 - 6);
  g.add(canopy, fascia);
  for (const dx of [-5, 5]) for (const dz of [-11, -1, 11]) {
    const col = new THREE.Mesh(new THREE.BoxGeometry(0.5, 5.1, 0.5), stuccoMat('#e8e8e4'));
    col.position.set(48 + dx, 2.55, z0 - 6 + dz);
    g.add(col);
  }
  for (const dz of [-11, -1, 9]) {
    const island = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.3, 6), stuccoMat('#d8d8d2'));
    island.position.set(48, 0.43, z0 - 6 + dz);
    g.add(island);
    for (const pz of [-1.6, 1.6]) {
      const pump = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.8, 0.7), std({ color: '#c42a24', roughness: 0.4, metalness: 0.3 }));
      pump.position.set(48, 1.48, z0 - 6 + dz + pz);
      pump.castShadow = true;
      g.add(pump);
    }
  }
  const wallC = '#ece6d8';
  const front = facade(wallC, 1, false), side = stuccoMat(wallC);
  const store = new THREE.Mesh(new THREE.BoxGeometry(14, 4.6, 22), [side, front, std({ color: '#8f8a82' }), side, side, side]);
  store.position.set(88, 2.3, z0 + 6);
  store.castShadow = store.receiveShadow = true;
  g.add(store);
  const mart = new THREE.Mesh(new THREE.PlaneGeometry(9, 1.3), new THREE.MeshBasicMaterial({ map: signTex(['MINI MART'], { w: 512, h: 74, bg: '#b3201c', border: null, font: 'bold 54px Arial' }) }));
  mart.position.set(80.9, 3.9, z0 + 6);
  mart.rotation.y = -Math.PI / 2;
  g.add(mart);
  const pole = new THREE.Mesh(new THREE.BoxGeometry(0.5, 9, 0.5), std({ color: '#777', metalness: 0.5 }));
  pole.position.set(26, 4.5, z0 + 30);
  const priceMat = nightEmissive(std({
    map: signTex([{ text: 'GAS', font: 'bold 110px Arial', color: '#ffffff' }, { text: 'REG  4.19', font: 'bold 80px Arial', color: '#ffcf3a' }], { w: 384, h: 384, bg: '#1b1b1b', border: '#b3201c' }),
    emissive: '#ffffff',
  }), 0.9);
  priceMat.emissiveMap = priceMat.map;
  const dark = std({ color: '#333' });
  const price = new THREE.Mesh(new THREE.BoxGeometry(0.4, 4, 4), [priceMat, priceMat, dark, dark, dark, dark]);
  price.position.set(26, 9.5, z0 + 30);
  g.add(pole, price);
  cars.push({ x: 45.5, z: z0 - 10, ry: 0 }, { x: 50.5, z: z0 + 4, ry: Math.PI, kind: 'pickup' }, { x: 78, z: z0 + 22, ry: Math.PI / 2 });
  return g;
}

function buildMotel(cars) {
  const g = new THREE.Group();
  const z0 = T + 500;
  g.add(flatRect(100, 90, -70, z0, 0.28, std({ map: TX.asphalt().map, normalMap: TX.asphalt().normal, roughness: 0.95 }), 10));
  const room = (emiss) => (c, w, h) => {
    c.fillStyle = emiss ? '#000' : '#eadcbf'; c.fillRect(0, 0, w, h);
    if (!emiss) { speckle(c, w, h, 300, 0.07, 2); c.fillStyle = '#6b3a2a'; c.fillRect(w * 0.12, h * 0.35, w * 0.24, h * 0.65); c.fillStyle = '#d4b26a'; c.fillRect(w * 0.31, h * 0.66, 4, 4); }
    const grd = c.createLinearGradient(0, h * 0.38, 0, h * 0.68); grd.addColorStop(0, emiss ? '#ffc979' : '#5f7783'); grd.addColorStop(1, emiss ? '#ffb85a' : '#1f292f');
    c.fillStyle = grd; c.fillRect(w * 0.5, h * 0.38, w * 0.36, h * 0.3);
  };
  const front = nightEmissive(std({ map: canvasTex(128, 128, room(false)), emissiveMap: canvasTex(128, 128, room(true)), emissive: '#ffffff', roughness: 0.9 }), 0.9);
  const side = stuccoMat('#eadcbf'), roofM = std({ color: '#7d6a58', roughness: 0.9 });
  const a = new THREE.Mesh(boxUV(11, 3.8, 70, 4.5), [front, side, roofM, roofM, side, side]);
  a.position.set(-108, 1.9, z0);
  const b = new THREE.Mesh(boxUV(40, 3.8, 11, 4.5), [side, side, roofM, roofM, front, side]);
  b.position.set(-82.5, 1.9, z0 - 29.5);
  for (const m of [a, b]) { m.castShadow = m.receiveShadow = true; g.add(m); }
  const over1 = new THREE.Mesh(new THREE.BoxGeometry(3, 0.3, 70), roofM);
  over1.position.set(-101, 3.6, z0);
  const over2 = new THREE.Mesh(new THREE.BoxGeometry(40, 0.3, 3), roofM);
  over2.position.set(-82.5, 3.6, z0 - 22.5);
  over1.castShadow = over2.castShadow = true;
  g.add(over1, over2);
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 10, 8), std({ color: '#777', metalness: 0.5 }));
  pole.position.set(-20, 5, z0 + 25);
  const neon = std({
    map: signTex([{ text: 'MOTEL', font: 'bold 120px Georgia', color: '#ff4a3a' }, { text: 'VACANCY', font: 'bold 70px Arial', color: '#3affd2' }], { w: 512, h: 320, bg: '#1d2430', border: '#ffcf5a' }),
    emissive: '#ffffff',
  });
  neon.emissiveMap = neon.map;
  nightEmissive(neon, 2.2);
  const dark = std({ color: '#333' });
  const sign = new THREE.Mesh(new THREE.BoxGeometry(0.5, 4, 6.4), [neon, neon, dark, dark, dark, dark]);
  sign.position.set(-20, 11, z0 + 25);
  g.add(pole, sign);
  for (let i = 0; i < 6; i++) cars.push({ x: -93, z: z0 - 20 + i * 9 + (i % 2) * 3, ry: Math.PI / 2 });
  return g;
}

function buildChurch() {
  const g = new THREE.Group();
  const white = stuccoMat('#f1ede4');
  const x = -240, z = T - 160;
  const nave = new THREE.Mesh(new THREE.BoxGeometry(16, 7, 30), white);
  nave.position.set(x, 3.5, z);
  const rt = rep(TX.roofTiles(), 6, 4);
  const roof = new THREE.Mesh(gableGeometry(), std({ map: rt.map, normalMap: rt.normal, color: '#8a5a44', roughness: 0.85 }));
  roof.rotation.y = Math.PI / 2;
  roof.scale.set(31, 5, 17.5);
  roof.position.set(x, 7, z);
  const tower = new THREE.Mesh(new THREE.BoxGeometry(5.5, 15, 5.5), white);
  tower.position.set(x, 7.5, z + 17);
  const spireGeo = new THREE.ConeGeometry(4, 9, 4);
  spireGeo.rotateY(Math.PI / 4);
  const spire = new THREE.Mesh(spireGeo, std({ color: '#6b4a3a', roughness: 0.8 }));
  spire.position.set(x, 19.5, z + 17);
  const gold = std({ color: '#d8c27a', metalness: 0.8, roughness: 0.3 });
  const cross1 = new THREE.Mesh(new THREE.BoxGeometry(0.3, 2.6, 0.3), gold);
  cross1.position.set(x, 25.2, z + 17);
  const cross2 = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.3, 0.3), gold);
  cross2.position.set(x, 25.6, z + 17);
  for (const m of [nave, roof, tower, spire]) { m.castShadow = m.receiveShadow = true; }
  g.add(nave, roof, tower, spire, cross1, cross2);
  g.add(contactShadows([{ x, z, w: 20, d: 40 }]));
  return g;
}

function buildWaterTower() {
  const g = new THREE.Group();
  const m = std({ color: '#d9dee1', metalness: 0.5, roughness: 0.4 });
  const x = 400, z = T + 165;
  for (const dx of [-5, 5]) for (const dz of [-5, 5]) {
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.45, 27, 8), m);
    leg.position.set(x + dx * 0.85, 13.5, z + dz * 0.85);
    leg.rotation.set(dz * 0.012, 0, -dx * 0.012);
    leg.castShadow = true;
    g.add(leg);
  }
  const tank = new THREE.Mesh(new THREE.CylinderGeometry(7.5, 7.5, 8, 48), m);
  tank.position.set(x, 31, z);
  const bottom = new THREE.Mesh(new THREE.SphereGeometry(7.5, 48, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), m);
  bottom.position.set(x, 27, z);
  const top = new THREE.Mesh(new THREE.ConeGeometry(7.8, 3.2, 48), m);
  top.position.set(x, 36.6, z);
  const rail = new THREE.Mesh(new THREE.TorusGeometry(7.9, 0.06, 4, 48), m);
  rail.rotation.x = Math.PI / 2; rail.position.set(x, 28.2, z);
  for (const p of [tank, bottom, top]) { p.castShadow = true; g.add(p); }
  g.add(rail);
  return g;
}

function buildSchool(trees) {
  const g = new THREE.Group();
  const x = 240, z = T - 280;
  const wallC = '#d6b48e';
  const tex = canvasTex(256, 64, (c, w, h) => {
    c.fillStyle = wallC; c.fillRect(0, 0, w, h); speckle(c, w, h, 300, 0.06, 2);
    c.fillStyle = '#26323a'; for (let k = 0; k < 4; k++) c.fillRect(w * (0.05 + k * 0.25), h * 0.35, w * 0.15, h * 0.35);
  });
  const front = std({ map: tex, normalMap: TX.stucco().normal, roughness: 0.9 });
  const bld = new THREE.Mesh(boxUV(70, 6, 24, 16), [front, front, std({ color: '#8f8a82' }), front, front, front]);
  bld.position.set(x, 3, z);
  bld.castShadow = bld.receiveShadow = true;
  g.add(bld);
  g.add(flatRect(60, 40, x, z + 40, 0.2, std({ color: '#b98d5f', roughness: 1 })));
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 11, 6), std({ color: '#cccccc', metalness: 0.7 }));
  pole.position.set(x - 42, 5.5, z - 16);
  g.add(pole);
  g.add(contactShadows([{ x, z, w: 76, d: 30 }]));
  trees.push({ x: x - 30, z: z - 20, s: 1.3 }, { x: x + 10, z: z - 20, s: 1.2, ry: 2 }, { x: x + 34, z: z - 19, s: 1.1, ry: 4 });
  return g;
}
