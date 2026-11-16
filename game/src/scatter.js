import * as THREE from 'three';
import { getHeight, roadX, TOWN_Z, ROAD_START, roadDistance, halcyonE, ironwoodE, roadPolyline, NOVA_PAD, JUNO_PAD } from './terrain.js';
import { rng, hash2, fbm, noise2, part, mergeParts, mat4, instanced } from './util.js';
import { bushCard, grassCard, spikeCard, shaggyBark, rock } from './textures.js';

// Places where nothing grows: the highways, Vira's campus and solar fields, the towns and Halcyon.
export function blocked(x, z, roadPad = 13) {
  if (x > -12 && x < 665 && z > -720 && z < 575) return true;   // Vira campus, approach and perimeter road
  if (x > -210 && x < 1550 && z > -610 && z < 1690) return true; // solar fields
  if (x > 440 && x < 16100 && Math.abs(z + 705) < 14) return true; // transmission line footings
  if (Math.abs(x) < 520 && Math.abs(z - TOWN_Z) < 560) return true; // Saltbrush
  if (halcyonE(x, z) < 1.0) return true;                          // Halcyon's basin floor
  if (ironwoodE(x, z) < 1.0) return true;                         // Ironwood
  if (Math.hypot(x - NOVA_PAD.x, z - NOVA_PAD.z) < 90 || Math.hypot(x - JUNO_PAD.x, z - JUNO_PAD.z) < 60) return true;
  return roadDistance(x, z) < roadPad;
}

// Points along every desert highway, for scattering things out across the valleys.
const corridor = (() => {
  const pts = [];
  for (const id of ['saltbrush', 'halcyon', 'ironwood']) for (const p of roadPolyline(id, 200)) pts.push(p);
  return pts;
})();

// Crossed alpha cards. Each plane is doubled back-to-back (instead of DoubleSide) so both
// faces keep the same up-leaning normal and light evenly.
export function crossCards(w, h, planes = 3, y0 = 0) {
  const parts = [];
  for (let k = 0; k < planes * 2; k++) {
    const g = new THREE.PlaneGeometry(w, h);
    g.translate(0, h / 2 + y0, 0);
    g.rotateY((k % planes) * Math.PI / planes + (k >= planes ? Math.PI : 0));
    const n = g.attributes.normal;
    for (let i = 0; i < n.count; i++) { const v = new THREE.Vector3(n.getX(i) * 0.35, 1, n.getZ(i) * 0.35).normalize(); n.setXYZ(i, v.x, v.y, v.z); }
    parts.push(g.toNonIndexed());
  }
  return mergeParts(parts.map((p) => { p.deleteAttribute('color'); return p; }));
}

export function cardMaterial(map, extra = {}) {
  return new THREE.MeshStandardMaterial({ map, alphaTest: 0.45, alphaToCoverage: true, roughness: 0.95, ...extra });
}

// Irregular boulder: an icosphere pushed around by noise.
function boulderGeo(seed, detail = 1) {
  const g = new THREE.IcosahedronGeometry(1, detail);
  const p = g.attributes.position, v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const n = noise2(v.x * 1.7 + seed, v.z * 1.7 + v.y * 1.3 - seed);
    v.multiplyScalar(0.75 + n * 0.5);
    v.y *= 0.7;
    p.setXYZ(i, v.x, v.y, v.z);
  }
  g.computeVertexNormals();
  return g;
}

// Joshua trees and boulders, sprinkled along the whole valley (visible from far away).
export function buildScatter() {
  const g = new THREE.Group();
  const r = rng(77);

  const trunk = (x, y, z, rx, rz, len, rad) => {
    const c = new THREE.CylinderGeometry(rad * 0.75, rad, len, 7);
    c.translate(0, len / 2, 0);
    c.applyMatrix4(mat4(x, y, z, 0, 1, 1, 1, rx, rz));
    return c.toNonIndexed();
  };
  // a few branching forms, each made of wood + leaf-cluster tips
  const forms = [];
  for (let f = 0; f < 3; f++) {
    const R = rng(100 + f);
    const wood = [trunk(0, 0, 0, 0, 0, 2.6 + R(), 0.32)];
    const tips = [];
    const nArms = 2 + Math.floor(R() * 3);
    for (let a = 0; a < nArms; a++) {
      const ang = (a / nArms) * Math.PI * 2 + R(), tilt = 0.5 + R() * 0.5, len = 1.4 + R() * 1.6;
      const y0 = 2.2 + R() * 0.5;
      const rx = Math.sin(ang) * tilt, rz = -Math.cos(ang) * tilt;
      wood.push(trunk(0, y0, 0, rx, rz, len, 0.2));
      const tip = new THREE.Vector3(0, len, 0).applyEuler(new THREE.Euler(rx, 0, rz, 'YXZ')).add(new THREE.Vector3(0, y0, 0));
      if (R() < 0.5) {
        const len2 = 0.8 + R();
        wood.push(trunk(tip.x, tip.y - 0.1, tip.z, rx * 0.3, rz * 0.3 + (R() - 0.5), len2, 0.14));
        tip.add(new THREE.Vector3(0, len2, 0).applyEuler(new THREE.Euler(rx * 0.3, 0, rz * 0.3, 'YXZ')));
      }
      tips.push(tip);
    }
    const leaves = tips.map((t) => { const c = crossCards(1.9, 1.9, 3, -0.95); c.translate(t.x, t.y, t.z); return c; });
    forms.push({ wood: mergeParts(wood.map((w) => { w.deleteAttribute('color'); return w; })), leaves: mergeParts(leaves) });
  }
  const bark = shaggyBark();
  const woodMat = new THREE.MeshStandardMaterial({ map: bark.map, normalMap: bark.normal, roughness: 1 });
  const leafMat = cardMaterial(spikeCard());

  const R2 = rng(5);
  const per = [[], [], []];
  let tries = 0;
  while (per[0].length + per[1].length + per[2].length < 9000 && tries++ < 90000) {
    const c = corridor[Math.floor(R2() * corridor.length)];
    const x = c[0] + (R2() - 0.5) * 2 * (300 + R2() * 6000), z = c[1] + (R2() - 0.5) * 2 * (300 + R2() * 6000);
    if (blocked(x, z, 18) || halcyonE(x, z) < 2.4 || fbm(x * 0.0008, z * 0.0008, 3) < 0.47) continue;
    const s = 0.75 + R2() * 0.8;
    per[Math.floor(R2() * 3)].push(mat4(x, getHeight(x, z) - 0.1, z, R2() * 6.28, s, s * (0.85 + R2() * 0.4), s));
  }
  forms.forEach((f, i) => {
    g.add(instanced(f.wood, woodMat, per[i]));
    g.add(instanced(f.leaves, leafMat, per[i]));
  });

  const rk = rock();
  const rockMat = new THREE.MeshStandardMaterial({ map: rk.map, normalMap: rk.normal, roughness: 0.92 });
  for (let v = 0; v < 3; v++) {
    const list = [], cols = [];
    let n = 0;
    while (list.length < 4500 && n++ < 40000) {
      const c = corridor[Math.floor(r() * corridor.length)];
      const x = c[0] + (r() - 0.5) * 2 * (200 + r() * 6000), z = c[1] + (r() - 0.5) * 2 * (200 + r() * 6000);
      if (blocked(x, z, 16)) continue;
      const s = 0.5 + Math.pow(r(), 3) * 7;
      list.push(mat4(x, getHeight(x, z) + s * 0.1, z, r() * 6.28, s * (0.8 + r() * 0.6), s * (0.6 + r() * 0.5), s, (r() - 0.5) * 0.4, (r() - 0.5) * 0.4));
      cols.push(['#a77c60', '#94705a', '#b38f6e', '#7d5d4a'][Math.floor(r() * 4)]);
    }
    g.add(instanced(boulderGeo(v * 3.1), rockMat, list, { colors: cols, cast: false }));
  }
  return g;
}

// Low brush, dry grass and stones in windows that follow the camera.
class LocalLayer {
  constructor(geo, mat, N, cell, seed, place) {
    Object.assign(this, { N, cell, seed, place, cx: null, cz: null });
    this.mesh = new THREE.InstancedMesh(geo, mat, N * N);
    this.mesh.frustumCulled = false;
    this.mesh.castShadow = false; // thousands of alpha cards in four shadow cascades cost ~15 ms
    this.mesh.receiveShadow = true;
    this.zero = new THREE.Matrix4().makeScale(0, 0, 0);
  }
  update(pos) {
    const cx = Math.floor(pos.x / this.cell), cz = Math.floor(pos.z / this.cell);
    if (cx === this.cx && cz === this.cz) return;
    this.cx = cx; this.cz = cz;
    const { N, cell, seed } = this, h = N / 2;
    for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
      const gx = cx - h + i, gz = cz - h + j;
      // slot keyed by world cell, so an instance keeps its slot while in view
      const k = (((gx % N) + N) % N) * N + (((gz % N) + N) % N);
      const a = hash2(gx + seed, gz), b = hash2(gz + 911, gx - seed), c = hash2(gx * 3 + 5, gz * 7 - seed);
      const x = (gx + a) * cell, z = (gz + b) * cell;
      const m = blocked(x, z) ? null : this.place(x, z, a, b, c);
      this.mesh.setMatrixAt(k, m || this.zero);
    }
    this.mesh.instanceMatrix.needsUpdate = true;
  }
}

export class LocalScatter {
  constructor() {
    this.group = new THREE.Group();
    const tint = (mesh, palette) => { for (let i = 0; i < mesh.count; i++) mesh.setColorAt(i, new THREE.Color(palette[i % palette.length])); };

    const bush = new LocalLayer(crossCards(2.4, 1.8, 3), cardMaterial(bushCard()), 128, 7, 0, (x, z, a, b, c) => {
      const eH = halcyonE(x, z);
      const dens = 0.2 + 0.6 * fbm(x * 0.004, z * 0.004, 2) + (eH < 2.4 ? 0.3 : 0) + (ironwoodE(x, z) < 2.2 ? 0.15 : 0);
      if (c > dens) return null;
      const s = 0.45 + a * 0.9;
      return mat4(x, getHeight(x, z) - 0.05, z, b * 6.28, s, s * (0.75 + c * 0.6), s);
    });
    tint(bush.mesh, ['#ffffff', '#e8eadc', '#f4efd8', '#d9dccb', '#fff8e8']);

    const grass = new LocalLayer(crossCards(1.0, 0.7, 2), cardMaterial(grassCard()), 100, 4.5, 31, (x, z, a, b, c) => {
      const dens = 0.15 + 0.5 * fbm(x * 0.006 + 3, z * 0.006, 2);
      if (c > dens) return null;
      const s = 0.6 + a * 0.9;
      return mat4(x, getHeight(x, z) - 0.03, z, b * 6.28, s, s, s);
    });
    grass.mesh.castShadow = false;
    tint(grass.mesh, ['#ffffff', '#efe6cf', '#e6dcc0']);

    const rk = rock();
    const stones = new LocalLayer(boulderGeo(7.7), new THREE.MeshStandardMaterial({ map: rk.map, normalMap: rk.normal, roughness: 0.9 }), 70, 6, 57, (x, z, a, b, c) => {
      if (c > 0.35) return null;
      const s = 0.12 + a * a * 0.6;
      return mat4(x, getHeight(x, z), z, b * 6.28, s * (0.8 + c), s * 0.7, s, a, b);
    });
    stones.mesh.castShadow = false;
    tint(stones.mesh, ['#a77c60', '#94705a', '#c4a184', '#7d5d4a', '#b9a690']);

    this.layers = [bush, grass, stones];
    for (const l of this.layers) this.group.add(l.mesh);
  }
  update(pos) { for (const l of this.layers) l.update(pos); }
}
