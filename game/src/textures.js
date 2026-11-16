import * as THREE from 'three';
import { hash2, rng, smoothstep, clamp } from './util.js';

// Procedural texture library. Every surface texture tiles seamlessly and most come with a
// normal map derived from the same height field.

const cache = new Map();
const once = (key, make) => { if (!cache.has(key)) cache.set(key, make()); return cache.get(key); };

// ---------- tileable noise ----------

function thash(x, y, p) { return hash2(((x % p) + p) % p, ((y % p) + p) % p); }
export function tnoise(x, y, p) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  const a = thash(xi, yi, p), b = thash(xi + 1, yi, p), c = thash(xi, yi + 1, p), d = thash(xi + 1, yi + 1, p);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
// x, y in [0,1) texture space; p = base cells per tile
export function tfbm(x, y, p, oct = 4) {
  let s = 0, a = 0.5, n = 0, f = p;
  for (let i = 0; i < oct; i++) { s += a * tnoise(x * f, y * f, f); n += a; a *= 0.5; f *= 2; }
  return s / n;
}
// Cellular noise: returns [F1, F2, cellHash] for jittered grid with `cells` per tile.
function cellular(x, y, cells) {
  const X = x * cells, Y = y * cells, xi = Math.floor(X), yi = Math.floor(Y);
  let f1 = 9, f2 = 9, id = 0;
  for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++) {
    const cx = xi + i, cy = yi + j;
    const px = cx + thash(cx, cy, cells), py = cy + thash(cx + 17, cy + 31, cells);
    const d = Math.hypot(px - X, py - Y);
    if (d < f1) { f2 = f1; f1 = d; id = thash(cx + 5, cy + 3, cells); } else if (d < f2) f2 = d;
  }
  return [f1, f2, id];
}

// ---------- canvas plumbing ----------

function canvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

function tex(c, { srgb = true, repeat = null, clampEdge = false } = {}) {
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = clampEdge ? THREE.ClampToEdgeWrapping : THREE.RepeatWrapping;
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.anisotropy = 8;
  if (repeat) t.repeat.set(repeat[0], repeat[1]);
  return t;
}

// fn(x, y, u, v, o) fills o.r/g/b (0..1), o.a (0..1), o.h (height)
function pixels(w, h, fn) {
  const c = canvas(w, h), g = c.getContext('2d');
  const img = g.createImageData(w, h), d = img.data;
  const H = new Float32Array(w * h);
  const o = { r: 0, g: 0, b: 0, a: 1, h: 0 };
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    o.a = 1; o.h = 0;
    fn(x, y, x / w, y / h, o);
    const i = (y * w + x) * 4;
    d[i] = clamp(o.r, 0, 1) * 255; d[i + 1] = clamp(o.g, 0, 1) * 255; d[i + 2] = clamp(o.b, 0, 1) * 255; d[i + 3] = clamp(o.a, 0, 1) * 255;
    H[y * w + x] = o.h;
  }
  g.putImageData(img, 0, 0);
  return { c, g, H, w, h };
}

function normalMap({ H, w, h }, strength) {
  const c = canvas(w, h), g = c.getContext('2d');
  const img = g.createImageData(w, h), d = img.data;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const l = H[y * w + ((x - 1 + w) % w)], r = H[y * w + ((x + 1) % w)];
    const u = H[((y - 1 + h) % h) * w + x], dn = H[((y + 1) % h) * w + x];
    let nx = (l - r) * strength, ny = (dn - u) * strength, nz = 1;
    const len = Math.hypot(nx, ny, nz); nx /= len; ny /= len; nz /= len;
    const i = (y * w + x) * 4;
    d[i] = (nx * 0.5 + 0.5) * 255; d[i + 1] = (ny * 0.5 + 0.5) * 255; d[i + 2] = (nz * 0.5 + 0.5) * 255; d[i + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  return tex(c, { srgb: false });
}

const set = (o, r, g, b) => { o.r = r; o.g = g; o.b = b; };
const hex = (s) => { const c = new THREE.Color(s); return [c.r, c.g, c.b]; }; // NB: linear; we use these as display values below
const sv = (s) => { const n = parseInt(s.slice(1), 16); return [(n >> 16 & 255) / 255, (n >> 8 & 255) / 255, (n & 255) / 255]; };

// ---------- ground ----------

// Grayscale sand detail (multiplied over the terrain's vertex tint): wind ripples, grains, pebbles.
export const sand = () => once('sand', () => {
  const S = 512, R = rng(5);
  const P = new Float32Array(S * S), PC = new Float32Array(S * S);
  for (let i = 0; i < 450; i++) {
    const px = R() * S, py = R() * S, r = 1.2 + R() * R() * 4, c = R();
    for (let dy = -Math.ceil(r); dy <= r; dy++) for (let dx = -Math.ceil(r); dx <= r; dx++) {
      const d2 = (dx * dx + dy * dy) / (r * r); if (d2 > 1) continue;
      const k = (((Math.floor(py) + dy) % S + S) % S) * S + (((Math.floor(px) + dx) % S + S) % S);
      const hh = Math.sqrt(1 - d2) * r * 0.35;
      if (hh > P[k]) { P[k] = hh; PC[k] = c; }
    }
  }
  const t = pixels(S, S, (x, y, u, v, o) => {
    const warp = tfbm(u, v, 4, 3);
    const rip = Math.sin((u * 0.8 + v * 0.6 + warp * 0.3) * Math.PI * 2 * 14) * 0.5 + 0.5;
    const mask = smoothstep(0.45, 0.65, tfbm(u + 0.3, v, 2, 2));
    const grain = hash2(x, y);
    const k = y * S + x, pb = P[k];
    let l = 0.84 + grain * 0.1 + (rip - 0.5) * 0.08 * mask + (tfbm(u, v, 16, 2) - 0.5) * 0.16;
    if (pb > 0) {
      const c = PC[k], s = 0.85 + pb * 0.08;
      const col = c < 0.45 ? [0.74, 0.62, 0.52] : c < 0.75 ? [0.95, 0.92, 0.86] : [0.62, 0.56, 0.5];
      set(o, col[0] * s, col[1] * s, col[2] * s);
    } else set(o, l, l * 0.99, l * 0.97);
    o.h = rip * 0.5 * mask + pb + grain * 0.25;
  });
  return { map: tex(t.c), normal: normalMap(t, 1.6) };
});

export const rock = () => once('rock', () => {
  const S = 512;
  const t = pixels(S, S, (x, y, u, v, o) => {
    const strata = Math.sin((v * 7 + tfbm(u, v, 3, 3) * 1.6) * Math.PI * 2) * 0.5 + 0.5;
    const cr = 1 - Math.abs(2 * tnoise(u * 9 + tfbm(u, v, 4, 2), v * 9, 9) - 1);
    const crack = smoothstep(0.9, 0.99, cr);
    const n = tfbm(u, v, 12, 3);
    const l = 0.72 + strata * 0.14 + (n - 0.5) * 0.35 - crack * 0.4 + (hash2(x, y) - 0.5) * 0.06;
    set(o, l * 1.04, l, l * 0.95);
    o.h = strata * 0.6 + n * 1.6 - crack * 1.2;
  });
  return { map: tex(t.c), normal: normalMap(t, 2.2) };
});

export const macro = () => once('macro', () => {
  const t = pixels(256, 256, (x, y, u, v, o) => { const n = tfbm(u, v, 4, 5); set(o, n, n, n); });
  return tex(t.c, { srgb: false });
});

export const cloudNoise = () => once('cloud', () => {
  const t = pixels(512, 512, (x, y, u, v, o) => {
    const n = tfbm(u, v, 4, 6);
    const [f1] = cellular(u, v, 8);
    const m = n * 0.75 + (1 - f1) * 0.25;
    set(o, m, m, m);
  });
  return tex(t.c, { srgb: false });
});

export const gravel = () => once('gravel', () => {
  const S = 512;
  const pal = [sv('#b9a88f'), sv('#9c8c78'), sv('#c9bba4'), sv('#8a7867'), sv('#a3988c'), sv('#d6cbb8'), sv('#8f6f5a')];
  const t = pixels(S, S, (x, y, u, v, o) => {
    const [f1, f2, id] = cellular(u, v, 40);
    const edge = smoothstep(0.0, 0.18, f2 - f1);
    const c = pal[Math.floor(id * pal.length)];
    const s = 0.72 + 0.28 * edge + (hash2(x, y) - 0.5) * 0.06;
    set(o, c[0] * s, c[1] * s, c[2] * s);
    o.h = edge * 1.5;
  });
  return { map: tex(t.c), normal: normalMap(t, 2.5) };
});

export const concrete = () => once('concrete', () => {
  const S = 512;
  const t = pixels(S, S, (x, y, u, v, o) => {
    const joint = (x % 256 < 2) || (y % 256 < 2);
    const n = tfbm(u, v, 6, 4), stain = smoothstep(0.55, 0.8, tfbm(u + 0.5, v, 3, 3));
    let l = 0.74 + (n - 0.5) * 0.12 - stain * 0.1 + (hash2(x, y) - 0.5) * 0.05;
    if (joint) l *= 0.55;
    set(o, l, l * 0.99, l * 0.96);
    o.h = joint ? -1 : n * 0.3;
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});

// Bleached desert highway, 10 m wide (u) by 48 m long (v): wheel paths, oil streak, cracks, worn paint.
export const highway = () => once('highway', () => {
  const W = 256, Hh = 1024;
  const t = pixels(W, Hh, (x, y, u, v, o) => {
    const vm = v * 48;
    let l = 0.4 + (tfbm(u * 0.25, v, 8, 4) - 0.5) * 0.08 + (hash2(x, y) - 0.5) * 0.09;
    if (hash2(x + 7, y * 3) > 0.94) l += 0.12;
    for (const c of [0.32, 0.68]) {
      for (const off of [-0.09, 0.09]) l += 0.05 * Math.exp(-(((u - c - off) / 0.03) ** 2));
      l -= 0.07 * Math.exp(-(((u - c) / 0.035) ** 2)) * (0.5 + tfbm(u, v, 16, 2));
    }
    const cr = 1 - Math.abs(2 * tnoise(u * 5, v * 20 + tfbm(u, v, 6, 2) * 2, 20) - 1);
    const crack = smoothstep(0.95, 0.995, cr) * smoothstep(0.5, 0.65, tfbm(u, v + 0.2, 3, 2));
    const snake = smoothstep(0.012, 0.0, Math.abs(u - 0.5 - (tfbm(0.3, v, 6, 3) - 0.5) * 0.1)) * 0.8;
    l = l * (1 - crack * 0.6) * (1 - snake * 0.55);
    set(o, l * 1.02, l, l * 0.97);
    o.h = (hash2(x, y) > 0.9 ? 0.4 : 0) - crack * 1.5;
    const worn = hash2(x * 3, y + 11) < 0.18 + tfbm(u, v, 12, 2) * 0.25;
    if (!worn && ((u > 0.128 && u < 0.145) || (u > 0.855 && u < 0.872))) set(o, 0.86, 0.85, 0.8);
    if (!worn && u > 0.493 && u < 0.507 && (vm % 12) < 3) set(o, 0.85, 0.66, 0.16);
  });
  return { map: tex(t.c), normal: normalMap(t, 1.5) };
});

// Four-lane interstate, 16 m wide (u) by 48 m (v): double yellow center, dashed white lane lines.
export const highway4 = () => once('highway4', () => {
  const W = 384, Hh = 1024;
  const t = pixels(W, Hh, (x, y, u, v, o) => {
    const vm = v * 48, m = u * 16;
    let l = 0.37 + (tfbm(u * 0.25, v, 8, 4) - 0.5) * 0.08 + (hash2(x, y) - 0.5) * 0.09;
    if (hash2(x + 7, y * 3) > 0.94) l += 0.12;
    for (const c of [2.85, 6.35, 9.65, 13.15]) {
      for (const off of [-0.85, 0.85]) l += 0.05 * Math.exp(-(((m - c - off) / 0.45) ** 2));
      l -= 0.06 * Math.exp(-(((m - c) / 0.5) ** 2)) * (0.5 + tfbm(u, v, 16, 2));
    }
    const cr = 1 - Math.abs(2 * tnoise(u * 8, v * 20 + tfbm(u, v, 6, 2) * 2, 20) - 1);
    const crack = smoothstep(0.96, 0.995, cr) * smoothstep(0.5, 0.65, tfbm(u, v + 0.2, 3, 2));
    l *= 1 - crack * 0.5;
    set(o, l * 1.02, l, l * 0.97);
    o.h = (hash2(x, y) > 0.9 ? 0.4 : 0) - crack * 1.5;
    const worn = hash2(x * 3, y + 11) < 0.15 + tfbm(u, v, 12, 2) * 0.2;
    if (worn) return;
    if ((m > 0.95 && m < 1.1) || (m > 14.9 && m < 15.05)) set(o, 0.86, 0.85, 0.8);
    if ((m > 7.82 && m < 7.95) || (m > 8.05 && m < 8.18)) set(o, 0.85, 0.66, 0.16);
    if (((m > 4.55 && m < 4.67) || (m > 11.33 && m < 11.45)) && (vm % 12) < 3) set(o, 0.86, 0.85, 0.8);
  });
  return { map: tex(t.c), normal: normalMap(t, 1.5) };
});

export const asphalt = () => once('asphalt', () => {
  const S = 512, R = rng(9);
  const patches = Array.from({ length: 5 }, () => [R(), R(), 0.05 + R() * 0.15, 0.05 + R() * 0.2]);
  const t = pixels(S, S, (x, y, u, v, o) => {
    let l = 0.36 + (tfbm(u, v, 8, 4) - 0.5) * 0.1 + (hash2(x, y) - 0.5) * 0.08;
    if (hash2(x + 3, y * 7) > 0.95) l += 0.1;
    for (const [px, py, pw, ph] of patches) {
      const dx = Math.min(Math.abs(u - px), 1 - Math.abs(u - px)), dy = Math.min(Math.abs(v - py), 1 - Math.abs(v - py));
      if (dx < pw && dy < ph) l *= 0.9;
    }
    const cr = 1 - Math.abs(2 * tnoise(u * 7 + tfbm(u, v, 4, 2), v * 7, 7) - 1);
    const crack = smoothstep(0.982, 0.997, cr) * smoothstep(0.55, 0.7, tfbm(u, v, 3, 2));
    l *= 1 - crack * 0.35;
    set(o, l * 1.02, l, l * 0.98);
    o.h = (hash2(x, y) > 0.9 ? 0.4 : 0) - crack * 1.5;
  });
  return { map: tex(t.c), normal: normalMap(t, 1.5) };
});

// ---------- walls & roofs ----------

export const stucco = () => once('stucco', () => {
  const t = pixels(256, 256, (x, y, u, v, o) => {
    const n = tfbm(u, v, 16, 3), b = tfbm(u, v, 3, 3);
    const l = 0.9 + (n - 0.5) * 0.12 + (b - 0.5) * 0.1;
    set(o, l, l, l);
    o.h = n;
  });
  return { map: tex(t.c), normal: normalMap(t, 3) };
});

// Precast concrete hall wall: one 3 m panel wide (u) by the full 16 m height (v).
export const hallWall = () => once('hallWall', () => {
  const W = 256, Hh = 1024, m = Hh / 16; // px per meter vertically
  const t = pixels(W, Hh, (x, y, u, v, o) => {
    const z = 16 - y / m; // height above ground in meters
    let c = [0.9, 0.9, 0.88];
    if (z < 2.3) c = [0.72, 0.73, 0.74];
    if (z > 12.6 && z < 13.9) { const slat = (y % 6) < 2; c = slat ? [0.2, 0.22, 0.24] : [0.36, 0.39, 0.42]; }
    if (z > 15.5) c = [0.62, 0.64, 0.66];
    const n = (tfbm(u, v, 4, 3) - 0.5) * 0.06 + (hash2(x, y) - 0.5) * 0.03;
    const dust = smoothstep(2.2, 0, z) * (0.6 + 0.4 * tfbm(u, v, 8, 2));
    const streakSeed = hash2(Math.floor(x / 5), 99);
    const streak = streakSeed > 0.6 ? smoothstep(15.5 - streakSeed * 9, 15.5, z) * (streakSeed - 0.6) * 0.5 : 0;
    const joint = x < 2;
    const reveal = Math.abs(z - 8) < 0.04 || Math.abs(z - 2.3) < 0.04;
    let r = c[0] + n, g = c[1] + n, b = c[2] + n;
    r = r * (1 - dust * 0.18) + dust * 0.05; g = g * (1 - dust * 0.22) + dust * 0.03; b = b * (1 - dust * 0.3);
    r -= streak; g -= streak; b -= streak * 0.9;
    if (joint || reveal) { r *= 0.6; g *= 0.6; b *= 0.6; }
    set(o, r, g, b);
    o.h = joint || reveal ? -1 : (z > 12.6 && z < 13.9 ? ((y % 6) < 2 ? -0.6 : 0.2) : 0);
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});

export const membrane = () => once('membrane', () => {
  const S = 512;
  const t = pixels(S, S, (x, y, u, v, o) => {
    const seam = (x % 128) < 3;
    const dirt = smoothstep(0.5, 0.8, tfbm(u, v, 4, 4));
    let l = 0.86 - dirt * 0.18 + (hash2(x, y) - 0.5) * 0.03;
    if (seam) l *= 0.9;
    set(o, l, l, l * 0.98);
    o.h = seam ? 0.6 : 0;
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});

export const roofTiles = () => once('roofTiles', () => {
  const S = 256;
  const t = pixels(S, S, (x, y, u, v, o) => {
    const row = Math.floor(y / 32), off = row % 2 ? 16 : 0;
    const col = Math.floor((x + off) / 32), fx = ((x + off) % 32) / 32, fy = (y % 32) / 32;
    const barrel = Math.sin(Math.PI * fx);
    const vary = (thash(col, row, 8) - 0.5) * 0.18;
    const shadow = smoothstep(0.75, 1.0, fy) * 0.35;
    const l = 0.62 + barrel * 0.3 + vary - shadow + (hash2(x, y) - 0.5) * 0.05;
    set(o, l, l, l);
    o.h = barrel - fy * 0.5;
  });
  return { map: tex(t.c), normal: normalMap(t, 3) };
});

export const blockWall = () => once('block', () => {
  const W = 256, Hh = 128; // 3.2 m x 1.6 m, 40 x 20 cm blocks
  const t = pixels(W, Hh, (x, y, u, v, o) => {
    const row = Math.floor(y / 16), off = row % 2 ? 16 : 0;
    const mortar = (y % 16) < 2 || ((x + off) % 32) < 2;
    const id = thash(Math.floor((x + off) / 32), row, 64);
    const l = mortar ? 0.7 : 0.82 + (id - 0.5) * 0.1 + (hash2(x, y) - 0.5) * 0.1;
    set(o, l, l * 0.98, l * 0.94);
    o.h = mortar ? -0.8 : (hash2(x, y) - 0.5) * 0.3;
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});

export const brick = () => once('brick', () => {
  const W = 256, Hh = 256;
  const t = pixels(W, Hh, (x, y, u, v, o) => {
    const row = Math.floor(y / 10), off = row % 2 ? 13 : 0;
    const mortar = (y % 10) < 2 || ((x + off) % 26) < 2;
    const id = thash(Math.floor((x + off) / 26), row, 64);
    const base = [0.62 + id * 0.12, 0.33 + id * 0.06, 0.24 + id * 0.04];
    const n = (hash2(x, y) - 0.5) * 0.06;
    if (mortar) set(o, 0.72, 0.68, 0.6); else set(o, base[0] + n, base[1] + n, base[2] + n);
    o.h = mortar ? -1 : 0;
  });
  return { map: tex(t.c), normal: normalMap(t, 2.5) };
});

// ---------- equipment ----------

export const chillerSide = () => once('chillerSide', () => {
  const W = 256, Hh = 96;
  const t = pixels(W, Hh, (x, y, u, v, o) => {
    let l = 0.68;
    const coil = y > 14 && y < 80 && (x % 64) > 4 && (x % 64) < 60;
    if (coil) l = (y % 3) ? 0.32 : 0.48;
    if ((x % 64) < 2) l = 0.45;
    l += (hash2(x, y) - 0.5) * 0.04;
    set(o, l, l * 1.01, l * 1.03);
    o.h = coil ? ((y % 3) ? -0.5 : 0) : 0;
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});

export const chillerTop = () => once('chillerTop', () => {
  const c = canvas(256, 128), g = c.getContext('2d');
  g.fillStyle = '#9fa5aa'; g.fillRect(0, 0, 256, 128);
  for (const cx of [64, 192]) {
    g.fillStyle = '#1d2024'; g.beginPath(); g.arc(cx, 64, 52, 0, Math.PI * 2); g.fill();
    g.strokeStyle = '#5c6268'; g.lineWidth = 1.5;
    for (let r = 10; r <= 52; r += 6) { g.beginPath(); g.arc(cx, 64, r, 0, Math.PI * 2); g.stroke(); }
    for (let a = 0; a < 8; a++) { g.beginPath(); g.moveTo(cx, 64); g.lineTo(cx + Math.cos(a * Math.PI / 4) * 52, 64 + Math.sin(a * Math.PI / 4) * 52); g.stroke(); }
    g.fillStyle = '#3a3f44'; g.beginPath(); g.arc(cx, 64, 8, 0, Math.PI * 2); g.fill();
  }
  g.strokeStyle = '#6b7177'; g.lineWidth = 3; g.strokeRect(1, 1, 254, 126);
  return tex(c);
});

export const genSide = () => once('genSide', () => {
  const W = 256, Hh = 72;
  const t = pixels(W, Hh, (x, y, u, v, o) => {
    let c = [0.78, 0.76, 0.7];
    const louver = (x < 40 || x > 216) && y > 10 && y < 62;
    if (louver) c = (y % 4) < 2 ? [0.3, 0.3, 0.3] : [0.55, 0.54, 0.5];
    const door = ((x > 70 && x < 100) || (x > 156 && x < 186)) && y > 8 && y < 68;
    const edge = door && (x === 71 || x === 99 || x === 157 || x === 185 || y === 9);
    if (edge) c = [0.45, 0.44, 0.4];
    if (y > 66) c = [0.5, 0.5, 0.48];
    const n = (hash2(x, y) - 0.5) * 0.04 - smoothstep(30, 72, y) * 0.06;
    set(o, c[0] + n, c[1] + n, c[2] + n);
    o.h = louver ? ((y % 4) < 2 ? -0.5 : 0) : edge ? -0.6 : 0;
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});

export const solarPanel = () => once('solar', () => {
  const W = 512, Hh = 64; // 20 m x 2.3 m: cells
  const t = pixels(W, Hh, (x, y, u, v, o) => {
    const frame = (x % 51) < 2 || y < 2 || y > 61;
    const cell = (x % 8) === 0 || (y % 8) === 0;
    const n = (hash2(x, y) - 0.5) * 0.02;
    if (frame) set(o, 0.5, 0.52, 0.55); else if (cell) set(o, 0.2, 0.24, 0.33); else set(o, 0.07 + n, 0.1 + n, 0.2 + n);
    o.h = frame ? 0.6 : 0;
  });
  return { map: tex(t.c), normal: normalMap(t, 1) };
});

// ---------- vegetation cards (RGBA) ----------

function card(w, h, draw) { const c = canvas(w, h); const g = c.getContext('2d'); draw(g, w, h); return tex(c); }

export const bushCard = () => once('bush', () => card(256, 256, (g, w, h) => {
  const R = rng(3);
  const tips = [];
  for (let i = 0; i < 26; i++) {
    const a = (R() - 0.5) * 2.4, len = 90 + R() * 130;
    const ex = w / 2 + Math.sin(a) * len, ey = h - 4 - Math.cos(a) * len * 0.9;
    const cx = w / 2 + Math.sin(a) * len * 0.3 + (R() - 0.5) * 30, cy = h - 4 - Math.cos(a) * len * 0.6;
    g.strokeStyle = R() < 0.5 ? '#5d4c3c' : '#6e5c49'; g.lineWidth = 1.5 + R() * 1.5;
    g.beginPath(); g.moveTo(w / 2 + (R() - 0.5) * 10, h - 2); g.quadraticCurveTo(cx, cy, ex, ey); g.stroke();
    for (let k = 0; k < 6; k++) { const t = 0.45 + R() * 0.55; tips.push([(1 - t) * (1 - t) * (w / 2) + 2 * (1 - t) * t * cx + t * t * ex, (1 - t) * (1 - t) * (h - 2) + 2 * (1 - t) * t * cy + t * t * ey]); }
  }
  const greens = ['#6b7a3a', '#7d8a46', '#5b6a31', '#8b9152', '#717d40', '#9a9a5c'];
  for (let i = 0; i < 2600; i++) {
    const [tx, ty] = tips[Math.floor(R() * tips.length)];
    const x = tx + (R() - 0.5) * 34, y = ty + (R() - 0.5) * 30;
    const shade = 0.75 + 0.25 * (1 - y / h);
    g.fillStyle = greens[Math.floor(R() * greens.length)];
    g.globalAlpha = 1; g.filter = `brightness(${shade})`;
    g.beginPath(); g.ellipse(x, y, 1.5 + R() * 2, 1 + R() * 1.5, R() * 3, 0, Math.PI * 2); g.fill();
  }
  g.filter = 'none';
}));

export const grassCard = () => once('grass', () => card(256, 256, (g, w, h) => {
  const R = rng(8);
  const cols = ['#cbb57c', '#b8a066', '#ddc994', '#a99060', '#8f8a58', '#c2ab70'];
  for (let i = 0; i < 90; i++) {
    const x0 = w / 2 + (R() - 0.5) * 70, a = (R() - 0.5) * 1.6, len = 90 + R() * 150;
    g.strokeStyle = cols[Math.floor(R() * cols.length)]; g.lineWidth = 1 + R() * 2;
    g.beginPath(); g.moveTo(x0, h);
    g.quadraticCurveTo(x0 + Math.sin(a) * len * 0.4, h - len * 0.6, x0 + Math.sin(a) * len, h - Math.cos(a) * len); g.stroke();
  }
}));

export const frondCard = () => once('frond', () => card(512, 128, (g, w, h) => {
  const R = rng(4);
  for (let i = 0; i < 120; i++) {
    const t = i / 120, x = 10 + t * (w - 20), len = (0.25 + 0.75 * Math.sin(Math.PI * Math.min(1, t * 1.3))) * 58;
    for (const s of [-1, 1]) {
      g.strokeStyle = ['#4d6a2c', '#5e7a35', '#6e8a40', '#45602a'][Math.floor(R() * 4)]; g.lineWidth = 2.2;
      g.beginPath(); g.moveTo(x, h / 2); g.lineTo(x + len * 0.55, h / 2 + s * len); g.stroke();
    }
  }
  g.strokeStyle = '#8a8a4a'; g.lineWidth = 4; g.beginPath(); g.moveTo(0, h / 2); g.lineTo(w, h / 2); g.stroke();
}));

export const spikeCard = () => once('spike', () => card(256, 256, (g, w, h) => {
  const R = rng(6);
  for (let i = 0; i < 70; i++) { // dead skirt hanging down
    const a = Math.PI / 2 + (R() - 0.5) * 1.6, len = 40 + R() * 50;
    g.strokeStyle = ['#8a7556', '#6e5c44', '#9c8664'][Math.floor(R() * 3)]; g.lineWidth = 2;
    g.beginPath(); g.moveTo(w / 2, h / 2); g.lineTo(w / 2 + Math.cos(a) * len, h / 2 + Math.sin(a) * len); g.stroke();
  }
  for (let i = 0; i < 160; i++) {
    const a = -Math.PI / 2 + (R() - 0.5) * 3.6, len = 50 + R() * 70;
    const grd = g.createLinearGradient(w / 2, h / 2, w / 2 + Math.cos(a) * len, h / 2 + Math.sin(a) * len);
    grd.addColorStop(0, '#3e4f2a'); grd.addColorStop(0.8, '#62743f'); grd.addColorStop(1, '#a3a070');
    g.strokeStyle = grd; g.lineWidth = 2.5;
    g.beginPath(); g.moveTo(w / 2, h / 2); g.lineTo(w / 2 + Math.cos(a) * len, h / 2 + Math.sin(a) * len); g.stroke();
  }
}));

export const canopyCard = () => once('canopy', () => card(256, 256, (g, w, h) => {
  const R = rng(12);
  g.strokeStyle = '#5a4a3a'; g.lineWidth = 3;
  for (let i = 0; i < 7; i++) { g.beginPath(); g.moveTo(w / 2, h - 10); g.quadraticCurveTo(w / 2 + (R() - 0.5) * 120, h / 2, w / 2 + (R() - 0.5) * 200, 40 + R() * 80); g.stroke(); }
  const greens = ['#7b8a42', '#8f9a4e', '#6a7a38', '#a2a65e', '#5f6d33'];
  for (let i = 0; i < 4200; i++) {
    const a = R() * Math.PI * 2, r = Math.sqrt(R()) * 110;
    const x = w / 2 + Math.cos(a) * r, y = h * 0.42 + Math.sin(a) * r * 0.7;
    if (tfbm(x / w, y / h, 4, 2) < 0.38) continue;
    g.fillStyle = greens[Math.floor(R() * greens.length)];
    g.filter = `brightness(${0.7 + 0.4 * (1 - y / h)})`;
    g.beginPath(); g.ellipse(x, y, 2 + R() * 2, 1.2 + R(), R() * 3, 0, Math.PI * 2); g.fill();
  }
  g.filter = 'none';
}));

export const palmBark = () => once('palmBark', () => {
  const t = pixels(128, 256, (x, y, u, v, o) => {
    const ring = Math.abs(Math.sin((v * 24 + Math.sin(u * Math.PI * 2 * 3) * 0.15) * Math.PI));
    const l = 0.32 + ring * 0.22 + (hash2(x, y) - 0.5) * 0.08;
    set(o, l * 1.15, l, l * 0.8);
    o.h = ring;
  });
  return { map: tex(t.c), normal: normalMap(t, 3) };
});

export const shaggyBark = () => once('shaggy', () => {
  const t = pixels(128, 256, (x, y, u, v, o) => {
    const s = tfbm(u * 6, v * 0.5, 4, 3);
    const l = 0.28 + s * 0.3 + (hash2(x, y) - 0.5) * 0.08;
    set(o, l * 1.1, l, l * 0.85);
    o.h = s;
  });
  return { map: tex(t.c), normal: normalMap(t, 3) };
});

// Soft round shadow for contact darkening under objects.
export const blob = () => once('blob', () => {
  const c = canvas(128, 128), g = c.getContext('2d');
  const grd = g.createRadialGradient(64, 64, 8, 64, 64, 64);
  grd.addColorStop(0, 'rgba(0,0,0,0.55)'); grd.addColorStop(0.6, 'rgba(0,0,0,0.25)'); grd.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = grd; g.fillRect(0, 0, 128, 128);
  return tex(c, { clampEdge: true });
});

// Rectangular contact shadow (dark inside, soft fade at the edges) for building footprints.
export const skirt = () => once('skirt', () => {
  const c = canvas(128, 128), g = c.getContext('2d');
  const img = g.createImageData(128, 128);
  for (let y = 0; y < 128; y++) for (let x = 0; x < 128; x++) {
    const dx = Math.min(x, 127 - x) / 24, dy = Math.min(y, 127 - y) / 24;
    const a = smoothstep(0, 1, Math.min(dx, dy));
    const i = (y * 128 + x) * 4; img.data[i + 3] = a * 150;
  }
  g.putImageData(img, 0, 0);
  return tex(c, { clampEdge: true });
});

export { hex, sv, canvas, tex, pixels, normalMap };
