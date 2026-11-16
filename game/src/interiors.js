import * as THREE from 'three';

// Walkable interiors: a registry of rooms (floor overrides for walk mode), a loader for the
// series stills used on screens and key surfaces, and a small pool of point lights that
// follows the camera between interiors. The pool has a fixed size so the scene's light count
// (and so every shader) never changes.

// ---------- rooms ----------
// Bounds are in the local x/z of `frame` (an Object3D placed directly in the world, rotated
// only about y), or in world coordinates when there is no frame. floorY is local too: a number,
// or a function (lx, lz) for ramps and stairs.
const rooms = [];

function frameOf(frame) {
  if (!frame) return { x: 0, y: 0, z: 0, c: 1, s: 0 };
  return { x: frame.position.x, y: frame.position.y, z: frame.position.z, c: Math.cos(frame.rotation.y), s: Math.sin(frame.rotation.y) };
}
const toLocal = (f, x, z) => {
  const dx = x - f.x, dz = z - f.z;
  return [dx * f.c - dz * f.s, dx * f.s + dz * f.c];
};
export function toWorld(frame, lx, ly, lz) {
  const f = frameOf(frame);
  return new THREE.Vector3(f.x + lx * f.c + lz * f.s, f.y + ly, f.z - lx * f.s + lz * f.c);
}

export function registerRoom({ id, name, minX, maxX, minZ, maxZ, floorY = 0, frame = null }) {
  rooms.push({ id, name: name || id, minX, maxX, minZ, maxZ, floorY, f: frameOf(frame), area: (maxX - minX) * (maxZ - minZ) });
}

// Rooms under (x, z) whose floor is no more than a step above the feet.
function candidates(x, z, feetY) {
  const out = [];
  for (const r of rooms) {
    const [lx, lz] = toLocal(r.f, x, z);
    if (lx < r.minX || lx > r.maxX || lz < r.minZ || lz > r.maxZ) continue;
    const y = r.f.y + (typeof r.floorY === 'function' ? r.floorY(lx, lz) : r.floorY);
    if (y <= feetY + 0.6) out.push({ r, y });
  }
  return out;
}

// Walk height: the highest interior floor reachable from the feet, else the terrain.
export function floorAt(x, z, terrainY, feetY = Infinity) {
  let best = -Infinity;
  for (const c of candidates(x, z, feetY)) best = Math.max(best, c.y);
  return best > -Infinity ? best : terrainY;
}

// The room the camera is in (the topmost reachable floor; the smallest room on ties).
export function roomAt(x, z, feetY = Infinity) {
  let best = null;
  for (const c of candidates(x, z, feetY)) {
    if (!best || c.y > best.y + 0.01 || (Math.abs(c.y - best.y) <= 0.01 && c.r.area < best.r.area)) best = c;
  }
  return best ? best.r : null;
}

// ---------- materials & geometry helpers ----------
// Indoors sees little of the sky: the sky's ambient and reflections are damped. three ignores
// envMapIntensity under scene.environment, so this is a shader edit (applied by render.js
// patchMaterial through userData.extraShader).
// Rooms keep their lights on after dark: indoor ambient never drops below indoorFill, so a
// windowless room looks the same at midnight as at noon.
export const indoorFill = { value: new THREE.Color(0.62, 0.62, 0.64) };
const indoorShader = (shader) => {
  shader.uniforms.indoorFill = indoorFill;
  shader.fragmentShader = shader.fragmentShader.replace('#include <common>', '#include <common>\nuniform vec3 indoorFill;');
  shader.fragmentShader = shader.fragmentShader.replace('#include <lights_fragment_maps>', `#include <lights_fragment_maps>
    irradiance = max(irradiance * 0.45, indoorFill); iblIrradiance *= 0.2;
    #if defined( RE_IndirectSpecular )
      radiance *= 0.2;
    #endif`);
};
export const std = (o) => {
  const m = new THREE.MeshStandardMaterial(o);
  m.userData.extraShader = indoorShader;
  m.userData.cacheKey = 'indoor';
  return m;
};
export const glow = (color, intensity = 2) => new THREE.MeshStandardMaterial({ color: '#111', emissive: color, emissiveIntensity: intensity });
export const glassMat = (o = {}) => new THREE.MeshStandardMaterial({ color: '#9fc4d2', roughness: 0.04, metalness: 0.3, transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide, ...o });

// Box with its base at y.
export function box(parent, w, h, d, x, y, z, mat, { ry = 0, cast = true, receive = true } = {}) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y + h / 2, z);
  m.rotation.y = ry;
  m.castShadow = cast; m.receiveShadow = receive;
  parent.add(m);
  return m;
}

// Vertical plane centred at (x, y, z) facing +z rotated by ry; rx tilts it (−π/2 makes a floor).
// With `tile`, UVs are in world units / tile so repeating textures keep their scale.
export function plane(parent, w, h, x, y, z, mat, { ry = 0, rx = 0, receive = true, tile = 0 } = {}) {
  const g = new THREE.PlaneGeometry(w, h);
  if (tile) {
    const uv = g.attributes.uv;
    for (let k = 0; k < uv.count; k++) uv.setXY(k, uv.getX(k) * w / tile, uv.getY(k) * h / tile);
  }
  const m = new THREE.Mesh(g, mat);
  m.position.set(x, y, z);
  m.rotation.set(rx, ry, 0, 'YXZ');
  m.receiveShadow = receive;
  parent.add(m);
  return m;
}

// ---------- series stills ----------
// crop = [u0, v0, u1, v1] as fractions of the image, measured from its top-left corner.
const loader = new THREE.TextureLoader();
const stills = new Map();
export function loadRefTex(name, crop = [0, 0, 1, 1]) {
  if (!stills.has(name)) {
    const entry = { base: null, copies: [] };
    entry.base = loader.load(`assets/refs/${name}`, () => { for (const t of entry.copies) t.needsUpdate = true; }, undefined,
      () => console.warn('missing still', name));
    entry.base.colorSpace = THREE.SRGBColorSpace;
    stills.set(name, entry);
  }
  const entry = stills.get(name);
  const t = entry.base.clone();
  const [u0, v0, u1, v1] = crop;
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  t.repeat.set(u1 - u0, v1 - v0);
  t.offset.set(u0, 1 - v1);
  t.anisotropy = 8;
  entry.copies.push(t);
  return t;
}

// A lit screen showing a still (or canvas). gain > 1 pushes it toward the bloom threshold.
export function screenMat(map, gain = 1.15) {
  const m = new THREE.MeshBasicMaterial({ map });
  m.color.setScalar(gain);
  return m;
}

// ---------- interior lights ----------
const lights = [];      // { pos, color, intensity, distance }
const animators = [];
const POOL = 6, RANGE = 90;
let pool = [], poolT = 1;

export function addLight(frame, lx, ly, lz, color = '#fff2dc', intensity = 40, distance = 16) {
  lights.push({ pos: toWorld(frame, lx, ly, lz), color: new THREE.Color(color), intensity, distance });
}
export function onUpdate(fn) { animators.push(fn); }

export function initInteriorLights(scene) {
  pool = [];
  for (let i = 0; i < POOL; i++) {
    const l = new THREE.PointLight('#ffffff', 0, 10, 2);
    l.castShadow = false;
    scene.add(l);
    pool.push(l);
  }
}

const _near = [];
export function updateInteriors(cam, dt, t) {
  for (const fn of animators) fn(dt, t, cam);
  poolT += dt;
  if (poolT < 0.2 || !pool.length) return;
  poolT = 0;
  _near.length = 0;
  for (const L of lights) {
    const d = L.pos.distanceToSquared(cam);
    if (d < RANGE * RANGE) _near.push([d, L]);
  }
  _near.sort((a, b) => a[0] - b[0]);
  pool.forEach((l, i) => {
    const L = _near[i] && _near[i][1];
    if (!L) { l.intensity = 0; return; }
    l.position.copy(L.pos); l.color.copy(L.color); l.intensity = L.intensity; l.distance = L.distance;
  });
}
