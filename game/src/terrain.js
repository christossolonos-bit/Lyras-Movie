import * as THREE from 'three';
import { sand, rock, macro } from './textures.js';
import { heightAt, TILE, WORLD } from './heightfield.js';

export {
  MILE, TOWN_Z, GATE_Z, ROAD_START, ROAD_END, roadX, heightAt, WORLD,
  HALCYON, NOVA_PAD, NOVA_ELEV, roadPolyline, roadDistance, halcyonE,
  IRONWOOD, JUNO_PAD, JUNO_ELEV, ironwoodE, RAIL_Z, IRON_GRID,
} from './heightfield.js';
export const BOUNDS = { X0: WORLD.x0, X1: WORLD.x1, Z0: WORLD.z0, Z1: WORLD.z1 };

// Streaming terrain: a 7 x 7 block of 4 km tiles around the camera (finest in the middle),
// built by worker threads, over a coarse 500 m mesh of the whole world for the distance.
const RING_SEGS = [128, 128, 64, 32];
const RING_SKIRT = [8, 8, 25, 120];
const RADIUS = 3;
const FAR_STEP = 500;

export const nearSquare = { value: new THREE.Vector4(1e9, 1e9, -1e9, -1e9) };

function terrainMaterial(far) {
  const S = sand(), R = rock();
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, map: S.map, normalMap: S.normal, roughness: 0.96 });
  mat.normalScale.set(0.9, 0.9);
  mat.userData.extraShader = (shader) => {
    shader.uniforms.rockMap = { value: R.map };
    shader.uniforms.macroMap = { value: macro() };
    shader.uniforms.nearSquare = nearSquare;
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D rockMap;\nuniform sampler2D macroMap;\nuniform vec4 nearSquare;')
      .replace('#include <map_fragment>', /* glsl */`
        ${far ? 'if (vWPos.x > nearSquare.x && vWPos.z > nearSquare.y && vWPos.x < nearSquare.z && vWPos.z < nearSquare.w) discard;' : ''}
        {
          vec2 wxz = vWPos.xz;
          vec3 s1 = texture2D(map, wxz / 6.0).rgb;
          vec3 s2 = texture2D(map, wxz / 37.0 + vec2(0.37, 0.71)).rgb;
          float m1 = texture2D(macroMap, wxz / 1500.0).r;
          float m2 = texture2D(macroMap, wxz / 230.0 + 0.5).r;
          vec3 sandD = s1 * mix(vec3(1.0), s2, 0.5) * (0.8 + 0.4 * m1) * (0.9 + 0.2 * m2);
          vec3 n0 = normalize(vWNorm);
          vec3 bw = pow(abs(n0), vec3(4.0)); bw /= (bw.x + bw.y + bw.z);
          vec3 rk = texture2D(rockMap, vWPos.zy / 31.0).rgb * bw.x + texture2D(rockMap, wxz / 31.0).rgb * bw.y + texture2D(rockMap, vWPos.xy / 31.0).rgb * bw.z;
          rk *= texture2D(rockMap, wxz / 230.0).rgb * 0.6 + 0.5;
          float rockF = smoothstep(0.2, 0.42, 1.0 - n0.y);
          diffuseColor.rgb *= mix(sandD, rk * (0.8 + 0.4 * m1), rockF);
        }`);
  };
  mat.userData.cacheKey = far ? 'terrainFar' : 'terrain';
  return mat;
}

function geometryFrom(d) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(d.pos, 3));
  g.setAttribute('normal', new THREE.BufferAttribute(d.nor, 3));
  g.setAttribute('color', new THREE.BufferAttribute(d.col, 3));
  g.setAttribute('uv', new THREE.BufferAttribute(d.uv, 2));
  g.setIndex(new THREE.BufferAttribute(d.idx, 1));
  g.computeBoundingSphere();
  return g;
}

export class Terrain {
  constructor() {
    this.group = new THREE.Group();
    this.material = terrainMaterial(false);
    this.farMaterial = terrainMaterial(true);
    const n = Math.max(2, Math.min(4, (navigator.hardwareConcurrency || 4) - 1));
    this.workers = Array.from({ length: n }, () => new Worker(new URL('./terrainWorker.js', import.meta.url), { type: 'module' }));
    this.pending = new Map();
    this.nextId = 1;
    this.rr = 0;
    this.cache = new Map();   // key -> { mesh, heights, n, s, x0, z0, used }
    this.shown = new Map();   // tile "tx,tz" -> cache entry currently displayed
    this.center = null;
    this.loading = null;
    for (const w of this.workers) w.onmessage = (e) => { const cb = this.pending.get(e.data.id); this.pending.delete(e.data.id); cb(e.data); };
  }

  request(msg) {
    return new Promise((resolve) => {
      const id = this.nextId++;
      this.pending.set(id, resolve);
      this.workers[this.rr++ % this.workers.length].postMessage({ id, ...msg });
    });
  }

  async init(pos) {
    const far = await this.request({ kind: 'far', step: FAR_STEP });
    this.far = new THREE.Mesh(geometryFrom(far), this.farMaterial);
    this.far.receiveShadow = true;
    this.far.frustumCulled = false;
    this.group.add(this.far);
    this.update(pos);
    await this.loading;
  }

  tileKey(tx, tz, segs) { return `${tx},${tz},${segs}`; }

  update(pos) {
    const cx = Math.floor(pos.x / TILE), cz = Math.floor(pos.z / TILE);
    if (this.center && this.center[0] === cx && this.center[1] === cz) return;
    if (this.loading && this.loadingFor && this.loadingFor[0] === cx && this.loadingFor[1] === cz) return;
    this.loadingFor = [cx, cz];
    const want = [];
    for (let dz = -RADIUS; dz <= RADIUS; dz++) for (let dx = -RADIUS; dx <= RADIUS; dx++) {
      const ring = Math.max(Math.abs(dx), Math.abs(dz));
      want.push({ tx: cx + dx, tz: cz + dz, segs: RING_SEGS[ring], skirt: RING_SKIRT[ring], ring });
    }
    want.sort((a, b) => a.ring - b.ring);
    const token = {};
    this.token = token;
    this.loading = Promise.all(want.map(async (w) => {
      const key = this.tileKey(w.tx, w.tz, w.segs);
      if (!this.cache.has(key)) {
        const d = await this.request({ kind: 'tile', tx: w.tx, tz: w.tz, segs: w.segs, skirt: w.skirt });
        const mesh = new THREE.Mesh(geometryFrom(d), this.material);
        mesh.receiveShadow = true;
        mesh.castShadow = w.ring <= 1;
        this.cache.set(key, { mesh, heights: d.heights, n: d.n, s: d.s, x0: d.x0, z0: d.z0, used: 0 });
      }
      return [w, this.cache.get(key)];
    })).then((tiles) => {
      if (this.token !== token) return;
      for (const e of this.shown.values()) this.group.remove(e.mesh);
      this.shown.clear();
      const stamp = performance.now();
      for (const [w, e] of tiles) {
        e.used = stamp;
        e.mesh.castShadow = w.ring <= 1;
        this.group.add(e.mesh);
        this.shown.set(`${w.tx},${w.tz}`, e);
      }
      this.center = [cx, cz];
      nearSquare.value.set((cx - RADIUS) * TILE, (cz - RADIUS) * TILE, (cx + RADIUS + 1) * TILE, (cz + RADIUS + 1) * TILE);
      this.loading = null;
      this.evict();
    });
  }

  evict() {
    if (this.cache.size < 160) return;
    const entries = [...this.cache.entries()].filter(([, e]) => ![...this.shown.values()].includes(e)).sort((a, b) => a[1].used - b[1].used);
    for (const [k, e] of entries.slice(0, this.cache.size - 120)) { e.mesh.geometry.dispose(); this.cache.delete(k); }
  }

  // Height of the displayed mesh where it exists (matches its triangles), analytic elsewhere.
  getHeight(x, z) {
    const e = this.shown.get(`${Math.floor(x / TILE)},${Math.floor(z / TILE)}`);
    if (!e) return heightAt(x, z);
    const fx = (x - e.x0) / e.s, fz = (z - e.z0) / e.s, n = e.n, H = e.heights;
    const i = Math.min(n - 2, Math.max(0, Math.floor(fx))), j = Math.min(n - 2, Math.max(0, Math.floor(fz)));
    const u = fx - i, v = fz - j;
    const ha = H[j * n + i], hb = H[j * n + i + 1], hc = H[(j + 1) * n + i], hd = H[(j + 1) * n + i + 1];
    if (u + v <= 1) return ha + (hb - ha) * u + (hc - ha) * v;
    return hd + (hc - hd) * (1 - u) + (hb - hd) * (1 - v);
  }
}

export let terrain = null;
export function setTerrain(t) { terrain = t; }
export function getHeight(x, z) { return terrain ? terrain.getHeight(x, z) : heightAt(x, z); }
