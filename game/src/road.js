import * as THREE from 'three';
import { roadX, TOWN_Z, GATE_Z, MILE, roadPolyline } from './terrain.js';
import { localRoadProfile, HALCYON_JUNCTION, IRONWOOD_JUNCTION, RAIL_Z } from './heightfield.js';
import { signTex, part, mergeParts, mat4, instanced } from './util.js';
import { highway, highway4, gravel } from './textures.js';

export function roadPath(step = 8) { return roadPolyline('saltbrush', step); }

// Normal (pointing to +x when travelling +z) at path index i.
function frame(pts, i) {
  const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
  let tx = b[0] - a[0], tz = b[1] - a[1];
  const l = Math.hypot(tx, tz); tx /= l; tz /= l;
  return { tx, tz, nx: tz, nz: -tx };
}

// y: a constant height, or an array with one height per point
export function ribbon(pts, width, y, vLen) {
  const n = pts.length;
  const pos = new Float32Array(n * 6), nor = new Float32Array(n * 6), uv = new Float32Array(n * 4);
  const idx = [];
  let s = 0;
  for (let i = 0; i < n; i++) {
    const { nx, nz } = frame(pts, i);
    if (i > 0) s += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    const [x, z] = pts[i], hw = width / 2;
    const yy = typeof y === 'number' ? y : y[i];
    pos.set([x - nx * hw, yy, z - nz * hw, x + nx * hw, yy, z + nz * hw], i * 6);
    nor.set([0, 1, 0, 0, 1, 0], i * 6);
    uv.set([0, s / vLen, 1, s / vLen], i * 4);
    if (i < n - 1) { const L = 2 * i, R = L + 1; idx.push(L, L + 2, R, R, L + 2, L + 3); }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  g.setIndex(idx);
  return g;
}

// Walks the path and calls fn(x, z, nx, nz) every `every` meters (optionally only within [z0, z1]).
function along(pts, every, fn, z0 = -Infinity, z1 = Infinity) {
  let s = 0, next = 0;
  for (let i = 0; i < pts.length; i++) {
    if (i > 0) s += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    if (s < next) continue;
    next += every;
    if (pts[i][1] < z0 || pts[i][1] > z1) continue;
    const { nx, nz } = frame(pts, i);
    fn(pts[i][0], pts[i][1], nx, nz);
  }
}


// Ranch fence well off both shoulders (steel T-posts, three strands) and delineator posts.
function roadside(pts, wire, fenceOff, delinOff, z0, z1, group, x0 = -Infinity, x1 = Infinity) {
  const tposts = [];
  const inRange = (x, z) => z > z0 && z < z1 && x > x0 && x < x1;
  for (const side of [-1, 1]) {
    let prev = null, count = 0;
    along(pts, 6, (px, pz, nx, nz) => {
      if (!inRange(px, pz)) { prev = null; return; }
      const x = px + side * nx * fenceOff, z = pz + side * nz * fenceOff;
      tposts.push(mat4(x, 0.6, z, Math.atan2(-nz, nx), 1, 0.9 + (count % 3) * 0.05, 1, (count * 0.37 % 1 - 0.5) * 0.08));
      if (count++ % 8 === 0) {
        if (prev) for (const y of [0.55, 0.85, 1.1]) wire.push(prev[0], y, prev[1], x, y, z);
        prev = [x, z];
      }
    });
  }
  group.add(instanced(new THREE.BoxGeometry(0.05, 1.3, 0.05), new THREE.MeshStandardMaterial({ color: '#4a4f3a', metalness: 0.5, roughness: 0.6 }), tposts, { receive: false }));
  const delin = [], refl = [];
  for (const side of [-1, 1]) along(pts, 160, (px, pz, nx, nz) => {
    if (!inRange(px, pz)) return;
    const x = px + side * nx * delinOff, z = pz + side * nz * delinOff;
    const ry = Math.atan2(nx, nz) + (side > 0 ? 0 : Math.PI) + Math.PI / 2;
    delin.push(mat4(x, 0.6, z, ry));
    refl.push(mat4(x, 1.0, z, ry));
  });
  group.add(instanced(new THREE.BoxGeometry(0.1, 1.2, 0.05), new THREE.MeshStandardMaterial({ color: '#f0f0ea', roughness: 0.5 }), delin, { receive: false }));
  group.add(instanced(new THREE.BoxGeometry(0.08, 0.16, 0.07), new THREE.MeshStandardMaterial({ color: '#ffb02e', emissive: '#ff9a1a', emissiveIntensity: 0.3, metalness: 0.4, roughness: 0.2 }), refl, { cast: false }));
}

function boardSign(lines, w, h, opts, ry) {
  const g = new THREE.Group();
  const back = new THREE.MeshStandardMaterial({ color: '#7c8186', metalness: 0.6, roughness: 0.5 });
  const face = new THREE.MeshStandardMaterial({ map: signTex(lines, { w: 512, h: Math.round(512 * h / w), ...opts }), roughness: 0.5 });
  const board = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.08), [back, back, back, back, face, back]);
  board.position.y = 2.2 + h / 2;
  board.castShadow = true;
  g.add(board);
  for (const sx of w > 2 ? [-w * 0.3, w * 0.3] : [0]) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.1, 2.2 + h, 0.1), back);
    post.position.set(sx, (2.2 + h) / 2, -0.09);
    post.castShadow = true;
    g.add(post);
  }
  g.rotation.y = ry;
  return g;
}

export function buildRoad() {
  const group = new THREE.Group();
  const pts = roadPath(8);

  const gv = gravel();
  const sMap = gv.map.clone(); sMap.repeat.set(17 / 1.6, 1); sMap.needsUpdate = true;
  const sNor = gv.normal.clone(); sNor.repeat.set(17 / 1.6, 1); sNor.needsUpdate = true;
  const shoulder = new THREE.Mesh(ribbon(pts, 17, 0.12, 1.6), new THREE.MeshStandardMaterial({ map: sMap, normalMap: sNor, color: '#d8c4a6', roughness: 1 }));
  shoulder.receiveShadow = true;
  const hw = highway();
  const road = new THREE.Mesh(ribbon(pts, 10, 0.25, 48), new THREE.MeshStandardMaterial({ map: hw.map, normalMap: hw.normal, roughness: 0.9 }));
  road.receiveShadow = true;
  group.add(shoulder, road);

  // Wooden utility poles along the east side, with sagging wires.
  const poleGeo = mergeParts([
    part(new THREE.CylinderGeometry(0.13, 0.17, 11.5, 7), '#5c4632', 0, 5.75, 0),
    part(new THREE.BoxGeometry(2.6, 0.14, 0.14), '#4a3828', 0, 10.3, 0),
    part(new THREE.BoxGeometry(1.2, 0.08, 0.08), '#4a3828', 0.6, 9.9, 0, 0, 0, 0.6),
    part(new THREE.CylinderGeometry(0.06, 0.06, 0.25, 5), '#cfd6d8', -1.1, 10.5, 0),
    part(new THREE.CylinderGeometry(0.06, 0.06, 0.25, 5), '#cfd6d8', 1.1, 10.5, 0),
    part(new THREE.CylinderGeometry(0.06, 0.06, 0.25, 5), '#cfd6d8', 0, 11.6, 0),
  ]);
  const poles = [], anchors = [];
  along(pts, 80, (x0, z0, nx, nz) => {
    const x = x0 + nx * 13, z = z0 + nz * 13;
    poles.push(mat4(x, 0, z, Math.atan2(-nz, nx)));
    anchors.push([[x - nx * 1.1, 10.6, z - nz * 1.1], [x + nx * 1.1, 10.6, z + nz * 1.1], [x, 11.7, z]]);
  });
  group.add(instanced(poleGeo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1 }), poles, { receive: false }));

  const wire = [];
  const SEG = 8;
  for (let p = 0; p < anchors.length - 1; p++) for (let w = 0; w < 3; w++) {
    const A = anchors[p][w], B = anchors[p + 1][w];
    for (let k = 0; k < SEG; k++) for (const t of [k / SEG, (k + 1) / SEG])
      wire.push(A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t - 4 * 0.9 * t * (1 - t), A[2] + (B[2] - A[2]) * t);
  }

  roadside(pts, wire, 32, 7, TOWN_Z + 1500, GATE_Z - 700, group);

  // Mile markers counting down to Vira, on the right for southbound drivers.
  const mmGeo = new THREE.PlaneGeometry(0.6, 1.0); mmGeo.translate(0, 1.6, 0);
  const postMat = new THREE.MeshStandardMaterial({ color: '#8a8f93', metalness: 0.5 });
  for (let m = 1; m < 40; m++) {
    const z = TOWN_Z + m * MILE;
    const mk = new THREE.Group();
    const plate = new THREE.Mesh(mmGeo,
      new THREE.MeshStandardMaterial({ map: signTex([{ text: 'MILE', font: 'bold 34px Arial' }, { text: String(40 - m), font: 'bold 72px Arial' }], { w: 128, h: 212 }), side: THREE.DoubleSide }));
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.06, 1.3, 0.06), postMat);
    post.position.y = 0.65;
    mk.add(plate, post);
    mk.position.set(roadX(z) - 8, 0, z);
    mk.rotation.y = Math.PI;
    group.add(mk);
  }

  // Leaving town, heading south toward Vira.
  const green = { bg: '#1f6b3a', fg: '#ffffff', border: '#ffffff', font: 'bold 64px Arial' };
  const white = { bg: '#f4f4f0', fg: '#111111', border: '#111111', font: 'bold 70px Arial' };
  const place = (sign, z, side) => { sign.position.set(roadX(z) + side * 11, 0, z); group.add(sign); };
  place(boardSign(['VIRA DATA CENTER', '39 MILES'], 7, 2.6, green, Math.PI), TOWN_Z + 1400, -1);
  place(boardSign([{ text: 'SPEED', font: 'bold 70px Arial' }, { text: 'LIMIT', font: 'bold 70px Arial' }, { text: '65', font: 'bold 150px Arial' }], 0.9, 1.15, { ...white, h: 655 }, Math.PI), TOWN_Z + 1650, -1);
  place(boardSign(['NO SERVICES', 'NEXT 39 MILES'], 6, 2.4, green, Math.PI), TOWN_Z + 1900, -1);
  // approaching Vira
  place(boardSign([{ text: 'SPEED', font: 'bold 70px Arial' }, { text: 'LIMIT', font: 'bold 70px Arial' }, { text: '25', font: 'bold 150px Arial' }], 0.9, 1.15, { ...white, h: 655 }, Math.PI), GATE_Z - 900, -1);
  place(boardSign(['PRIVATE ROAD', 'VIRA FACILITY'], 4.5, 2, { ...white, font: 'bold 60px Arial' }, Math.PI), GATE_Z - 1300, -1);
  // heading north into town
  place(boardSign([{ text: 'SPEED', font: 'bold 70px Arial' }, { text: 'LIMIT', font: 'bold 70px Arial' }, { text: '35', font: 'bold 150px Arial' }], 0.9, 1.15, { ...white, h: 655 }, 0), TOWN_Z + 900, 1);

  // Interstate to Halcyon: four lanes, wide gravel shoulders, fencing and delineators.
  const hp = roadPolyline('halcyon', 8);
  const hs = new THREE.Mesh(ribbon(hp, 26, 0.12, 1.6), shoulder.material);
  const h4 = highway4();
  const hr = new THREE.Mesh(ribbon(hp, 16, 0.26, 48), new THREE.MeshStandardMaterial({ map: h4.map, normalMap: h4.normal, roughness: 0.9 }));
  hs.receiveShadow = hr.receiveShadow = true;
  group.add(hs, hr);
  roadside(hp, wire, 38, 10, -Infinity, Infinity, group, -68500, HALCYON_JUNCTION[0] - 900);

  // Switchback road up to Nova's house, graded into the hill.
  const prof = localRoadProfile('novahill');
  const nr = new THREE.Mesh(ribbon(prof.pts, 8, prof.elev.map((e) => e + 0.35), 12), new THREE.MeshStandardMaterial({ map: road.material.map, normalMap: hw.normal, roughness: 0.9 }));
  const ns = new THREE.Mesh(ribbon(prof.pts, 12, prof.elev.map((e) => e + 0.2), 1.6), shoulder.material);
  nr.receiveShadow = ns.receiveShadow = true;
  nr.material.polygonOffset = ns.material.polygonOffset = true;
  group.add(ns, nr);

  // Signs at the junction and along the interstate.
  const [jx, jz] = HALCYON_JUNCTION;
  place(boardSign(['HALCYON  →', 'NEXT RIGHT'], 6, 2.4, green, Math.PI), jz - 700, -1);
  const westSign = (lines, along, w = 7, h = 2.6) => {
    const p = hp[Math.min(hp.length - 1, Math.round(along / 8))];
    const q = hp[Math.min(hp.length - 1, Math.round(along / 8) + 2)];
    const ry = Math.atan2(p[0] - q[0], p[1] - q[1]);
    const sg = boardSign(lines, w, h, green, ry);
    const nx = -(q[1] - p[1]), nz = q[0] - p[0], l = Math.hypot(nx, nz);
    sg.position.set(p[0] + nx / l * 14, 0, p[1] + nz / l * 14);
    group.add(sg);
  };
  westSign(['HALCYON', '49 MILES'], 1500);
  westSign(['HALCYON', '25 MILES'], 40000);
  westSign(['WELCOME TO', 'HALCYON'], hp.length * 8 - 2500, 8, 3);
  // Saltbrush town limit
  place(boardSign(['WELCOME TO', 'SALTBRUSH'], 6, 2.4, green, 0), TOWN_Z + 1100, 1);

  // ---------- state highway to Ironwood (Juno's route), with Lyra's numbered highway cameras ----------
  const ip = roadPolyline('ironwood', 8);
  const is = new THREE.Mesh(ribbon(ip, 17, 0.12, 1.6), shoulder.material);
  const ir = new THREE.Mesh(ribbon(ip, 10, 0.25, 48), road.material);
  is.receiveShadow = ir.receiveShadow = true;
  group.add(is, ir);
  const ipoles = [], ianch = [];
  along(ip, 80, (x0, z0, nx, nz) => {
    if (x0 > 48200 || Math.hypot(x0 - IRONWOOD_JUNCTION[0], z0 - IRONWOOD_JUNCTION[1]) < 300) return;
    const x = x0 - nx * 13, z = z0 - nz * 13;
    ipoles.push(mat4(x, 0, z, Math.atan2(-nz, nx)));
    ianch.push([[x - nx * 1.1, 10.6, z - nz * 1.1], [x + nx * 1.1, 10.6, z + nz * 1.1], [x, 11.7, z]]);
  });
  group.add(instanced(poleGeo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1 }), ipoles, { receive: false }));
  for (let p = 0; p < ianch.length - 1; p++) for (let w = 0; w < 3; w++) {
    const A = ianch[p][w], B = ianch[p + 1][w];
    if (Math.hypot(A[0] - B[0], A[2] - B[2]) > 200) continue;
    for (let k = 0; k < SEG; k++) for (const t of [k / SEG, (k + 1) / SEG])
      wire.push(A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t - 4 * 0.9 * t * (1 - t), A[2] + (B[2] - A[2]) * t);
  }
  roadside(ip, wire, 30, 7, -Infinity, Infinity, group, IRONWOOD_JUNCTION[0] + 1200, 47500);

  const camGeo = mergeParts([
    part(new THREE.CylinderGeometry(0.1, 0.15, 8, 8), '#9aa0a5', 0, 4, 0),
    part(new THREE.BoxGeometry(0.1, 0.1, 1.4), '#9aa0a5', 0, 7.7, -0.6),
    part(new THREE.BoxGeometry(0.3, 0.3, 0.7), '#e9eaea', 0, 7.45, -1.25),
    part(new THREE.BoxGeometry(0.36, 0.06, 0.8), '#e9eaea', 0, 7.63, -1.25),
    part(new THREE.BoxGeometry(0.5, 0.7, 0.35), '#6a6f74', 0, 2.2, 0.2),
  ]);
  const cams = [];
  let camNo = 0;
  along(ip, 4600, (x0, z0, nx, nz) => {
    if (camNo++ === 0) return;
    const x = x0 + nx * 9, z = z0 + nz * 9;
    cams.push(mat4(x, 0, z, Math.atan2(nx, nz)));
    const plate = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.45), new THREE.MeshStandardMaterial({ map: signTex([`HWY CAM ${camNo - 1}`], { w: 256, h: 128, bg: '#f2f2ee', fg: '#111', border: '#111', font: 'bold 44px Arial' }), side: THREE.DoubleSide }));
    plate.position.set(x - nx * 0.2, 3.2, z - nz * 0.2);
    plate.rotation.y = Math.atan2(-nx, -nz);
    group.add(plate);
  });
  group.add(instanced(camGeo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.4, metalness: 0.5 }), cams, { receive: false }));
  const camLed = new THREE.SphereGeometry(0.04, 6, 4); camLed.translate(0.1, 7.5, -1.62);
  group.add(instanced(camLed, new THREE.MeshBasicMaterial({ color: '#ff2a1a', toneMapped: false }), cams, { cast: false }));

  const pathSign = (pts, lines, at, w = 7, h = 2.6) => {
    const i = Math.min(pts.length - 3, Math.round(at / 8));
    const p = pts[i], q = pts[i + 2];
    const sg = boardSign(lines, w, h, green, Math.atan2(p[0] - q[0], p[1] - q[1]));
    const nx = -(q[1] - p[1]), nz = q[0] - p[0], l = Math.hypot(nx, nz);
    sg.position.set(p[0] + nx / l * 14, 0, p[1] + nz / l * 14);
    group.add(sg);
  };
  place(boardSign(['IRONWOOD  ←', 'NEXT LEFT'], 6, 2.4, green, Math.PI), IRONWOOD_JUNCTION[1] - 700, -1);
  pathSign(ip, ['IRONWOOD', '40 MILES'], 1500);
  pathSign(ip, ['WELCOME TO', 'IRONWOOD'], ip.length * 8 - 1500, 8, 3);

  // ---------- railroad: ballast, ties, rails, and the crossing on the Ironwood highway ----------
  const rp = roadPolyline('rail', 10);
  const ballast = new THREE.Mesh(ribbon(rp, 6, 0.18, 1.6), new THREE.MeshStandardMaterial({ map: sMap, normalMap: sNor, color: '#a39a8c', roughness: 1 }));
  const tieTex = signTex([''], { w: 64, h: 64, bg: '#00000000', border: null, clear: true });
  const tieCanvas = tieTex.image.getContext('2d');
  tieCanvas.fillStyle = '#8e8476'; tieCanvas.fillRect(0, 0, 64, 64);
  tieCanvas.fillStyle = '#4a3a2c'; tieCanvas.fillRect(0, 8, 64, 22);
  tieTex.wrapS = tieTex.wrapT = THREE.RepeatWrapping; tieTex.needsUpdate = true;
  const ties = new THREE.Mesh(ribbon(rp, 2.7, 0.3, 0.6), new THREE.MeshStandardMaterial({ map: tieTex, roughness: 1 }));
  ballast.receiveShadow = ties.receiveShadow = true;
  group.add(ballast, ties);
  const railMat = new THREE.MeshStandardMaterial({ color: '#6d6a66', metalness: 0.85, roughness: 0.35 });
  const rails = [];
  for (let i = 0; i < rp.length - 1; i += 200) {
    const a = rp[i], b = rp[Math.min(rp.length - 1, i + 200)];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    for (const s of [-0.72, 0.72]) rails.push(mat4((a[0] + b[0]) / 2, 0.42, (a[1] + b[1]) / 2 + s, Math.atan2(b[0] - a[0], b[1] - a[1]), 0.08, 0.16, len));
  }
  group.add(instanced(new THREE.BoxGeometry(1, 1, 1), railMat, rails, { receive: false }));
  // crossbucks where the highway crosses the tracks
  for (let i = 1; i < ip.length; i++) {
    const [ax, az] = ip[i - 1], [bx, bz] = ip[i];
    if ((az - RAIL_Z) * (bz - RAIL_Z) > 0) continue;
    const cx = ax + (bx - ax) * (RAIL_Z - az) / (bz - az);
    const xb = new THREE.Group();
    const white = new THREE.MeshStandardMaterial({ map: signTex(['RAILROAD CROSSING'], { w: 512, h: 64, bg: '#f4f4f0', fg: '#111', border: '#111', font: 'bold 38px Arial' }), roughness: 0.5 });
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.12, 4, 0.12), railMat); post.position.y = 2; xb.add(post);
    for (const r of [0.6, -0.6]) { const b = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.3, 0.04), white); b.position.y = 3.6; b.rotation.z = r; xb.add(b); }
    const lamp = new THREE.MeshBasicMaterial({ color: '#ff3020', toneMapped: false });
    for (const s of [-0.35, 0.35]) { const l = new THREE.Mesh(new THREE.CircleGeometry(0.14, 12), lamp); l.position.set(s, 2.7, 0.08); xb.add(l); }
    for (const [dx, dz, ry] of [[-8, -9, Math.PI], [8, 9, 0]]) { const c = xb.clone(); c.position.set(cx + dx, 0, RAIL_Z + dz); c.rotation.y = ry; group.add(c); }
    break;
  }

  // dirt drive up to Juno's loft
  const jp = localRoadProfile('junodrive');
  const dirt = new THREE.Mesh(ribbon(jp.pts, 6, jp.elev.map((e) => e + 0.25), 1.6), new THREE.MeshStandardMaterial({ map: sMap, normalMap: sNor, color: '#c9b48e', roughness: 1, polygonOffset: true, polygonOffsetFactor: -1 }));
  dirt.receiveShadow = true;
  group.add(dirt);

  const wg = new THREE.BufferGeometry();
  wg.setAttribute('position', new THREE.Float32BufferAttribute(wire, 3));
  group.add(new THREE.LineSegments(wg, new THREE.LineBasicMaterial({ color: '#1d1a17' })));
  return group;
}
