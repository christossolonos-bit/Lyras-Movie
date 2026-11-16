import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// ---------- randomness & noise (shared with workers) ----------

export { rng, hash2, noise2, fbm, ridged, clamp, smoothstep } from './noise.js';
import { clamp, smoothstep } from './noise.js';

// ---------- textures ----------

export function canvasTex(w, h, draw, { repeat = [1, 1], srgb = true } = {}) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat[0], repeat[1]);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

export function speckle(g, w, h, n, alpha = 0.08, size = 2) {
  for (let i = 0; i < n; i++) {
    g.fillStyle = Math.random() < 0.5 ? `rgba(0,0,0,${Math.random() * alpha})` : `rgba(255,255,255,${Math.random() * alpha})`;
    g.fillRect(Math.random() * w, Math.random() * h, size, size);
  }
}

// Text sign. lines: array of strings or {text, font, color}.
export function signTex(lines, { w = 512, h = 128, bg = '#1f6b3a', fg = '#ffffff', font = 'bold 64px Arial', border = '#ffffff', clear = false } = {}) {
  const t = canvasTex(w, h, (g) => {
    if (!clear) { g.fillStyle = bg; g.fillRect(0, 0, w, h); }
    if (border && !clear) { g.strokeStyle = border; g.lineWidth = Math.max(3, h * 0.04); g.strokeRect(h * 0.06, h * 0.06, w - h * 0.12, h * 0.88); }
    g.textAlign = 'center'; g.textBaseline = 'middle';
    const L = lines.map((l) => (typeof l === 'string' ? { text: l } : l));
    L.forEach((l, i) => {
      g.font = l.font || font; g.fillStyle = l.color || fg;
      g.fillText(l.text, w / 2, h * (i + 0.5) / L.length);
    });
  });
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  return t;
}

// ---------- geometry helpers ----------

// Box whose UVs are in world units (u along the face width / unit) so textures don't stretch.
export function boxUV(w, h, d, unit = 1, vUnit = 0) {
  const g = new THREE.BoxGeometry(w, h, d);
  const uv = g.attributes.uv;
  for (let k = 0; k < uv.count; k++) {
    const face = Math.floor(k / 4);
    let u = uv.getX(k), v = uv.getY(k);
    if (face < 2) { u *= d / unit; if (vUnit) v *= h / vUnit; }
    else if (face < 4) { u *= w / unit; v *= d / unit; }
    else { u *= w / unit; if (vUnit) v *= h / vUnit; }
    uv.setXY(k, u, v);
  }
  return g;
}

export function colored(geo, color) {
  const c = new THREE.Color(color);
  const n = geo.attributes.position.count;
  const arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { arr[i * 3] = c.r; arr[i * 3 + 1] = c.g; arr[i * 3 + 2] = c.b; }
  geo.setAttribute('color', new THREE.BufferAttribute(arr, 3));
  return geo;
}

const _q = new THREE.Quaternion(), _e = new THREE.Euler(), _p = new THREE.Vector3(), _s = new THREE.Vector3();

// A colored, positioned piece of a merged prop.
export function part(geo, color, x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0) {
  const m = new THREE.Matrix4().compose(_p.set(x, y, z), _q.setFromEuler(_e.set(rx, ry, rz)), _s.set(1, 1, 1));
  geo.applyMatrix4(m);
  return colored(geo, color);
}

export function mergeParts(parts) {
  const g = mergeGeometries(parts.map((p) => (p.index ? p.toNonIndexed() : p)));
  g.computeBoundingSphere();
  return g;
}

export function mat4(x, y, z, ry = 0, sx = 1, sy = 1, sz = 1, rx = 0, rz = 0) {
  return new THREE.Matrix4().compose(_p.set(x, y, z), _q.setFromEuler(_e.set(rx, ry, rz, 'YXZ')), _s.set(sx, sy, sz));
}

export function instanced(geo, mat, matrices, { cast = true, receive = true, colors = null } = {}) {
  const m = new THREE.InstancedMesh(geo, mat, Math.max(1, matrices.length));
  if (!matrices.length) m.count = 0;
  matrices.forEach((t, i) => m.setMatrixAt(i, t));
  if (colors) colors.forEach((c, i) => m.setColorAt(i, c instanceof THREE.Color ? c : new THREE.Color(c)));
  m.castShadow = cast; m.receiveShadow = receive;
  m.instanceMatrix.needsUpdate = true;
  m.computeBoundingSphere();
  return m;
}

// Flat ground patch. With `tile`, UVs are in world units / tile so shared textures don't stretch.
export function flatRect(w, d, x, z, y, mat, tile = 0) {
  const g = new THREE.PlaneGeometry(w, d);
  if (tile) {
    const uv = g.attributes.uv;
    for (let k = 0; k < uv.count; k++) uv.setXY(k, uv.getX(k) * w / tile, uv.getY(k) * d / tile);
  }
  g.rotateX(-Math.PI / 2);
  const m = new THREE.Mesh(g, mat);
  m.position.set(x, y, z);
  m.receiveShadow = true;
  return m;
}

// ---------- night lighting registry ----------

export const nightMats = [];
export function nightEmissive(mat, intensity = 1) {
  mat.userData.nightBase = intensity;
  mat.emissiveIntensity = 0;
  nightMats.push(mat);
  return mat;
}
// Shared shader uniforms (procedural city facades read the night level from here).
export const globalUniforms = { night: { value: 0 } };
export function setNight(f) {
  for (const m of nightMats) m.emissiveIntensity = m.userData.nightBase * f;
  globalUniforms.night.value = f;
}
