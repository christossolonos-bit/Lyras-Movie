import { hash2, smoothstep } from './util.js';
import { canvas, tex, pixels, normalMap, tfbm } from './textures.js';

// Textures specific to the Vira campus, matched to the film's stills.

const cache = new Map();
const once = (key, make) => { if (!cache.has(key)) cache.set(key, make()); return cache.get(key); };
const set = (o, r, g, b) => { o.r = r; o.g = g; o.b = b; };

// Hall wall: one 4 m wide strip (u) by the full 16 m height (v).
// Grey plinth, white vertical-rib cladding, grey louvered upper band, grey coping.
export const hallCladding = () => once('cladding', () => {
  const W = 128, H = 1024, m = H / 16;
  const t = pixels(W, H, (x, y, u, v, o) => {
    const z = 16 - y / m;
    const rib = (x % 16) / 16; // 0.5 m ribs
    const ribShape = Math.sin(rib * Math.PI) ** 0.6;
    let c, h = 0;
    if (z < 1.1) { c = [0.62, 0.63, 0.64]; h = 0; }
    else if (z < 11.6) { const l = 0.86 + ribShape * 0.08; c = [l, l, l * 0.985]; h = ribShape; }
    else if (z < 14.6) {
      const slat = (y % 8) < 3;
      c = slat ? [0.38, 0.4, 0.42] : [0.6, 0.62, 0.64];
      h = slat ? -0.6 : 0.3;
      if (Math.abs(z - 11.6) < 0.08 || Math.abs(z - 14.6) < 0.08) { c = [0.45, 0.47, 0.49]; h = 1; }
    } else { c = [0.7, 0.71, 0.72]; h = 0.4; }
    const n = (tfbm(u, v, 4, 3) - 0.5) * 0.05 + (hash2(x, y) - 0.5) * 0.025;
    const dust = smoothstep(2.4, 0, z) * (0.55 + 0.45 * tfbm(u, v * 4, 6, 2));
    const streakSeed = hash2(Math.floor(x / 4), 7);
    const streak = streakSeed > 0.7 && z < 11.6 ? smoothstep(11.6 - streakSeed * 8, 11.6, z) * (streakSeed - 0.7) * 0.35 : 0;
    let r = c[0] + n - streak, g = c[1] + n - streak, b = c[2] + n - streak * 0.9;
    r = r * (1 - dust * 0.16) + dust * 0.05; g = g * (1 - dust * 0.2) + dust * 0.03; b *= 1 - dust * 0.28;
    set(o, r, g, b);
    o.h = h;
  });
  return { map: tex(t.c), normal: normalMap(t, 2.5) };
});

// Grey louvered panel for the projecting louver columns and penthouses (tiles 2 m).
export const louver = () => once('louver', () => {
  const t = pixels(128, 128, (x, y, u, v, o) => {
    const slat = (y % 8);
    const l = slat < 2 ? 0.34 : 0.52 + (slat / 8) * 0.12;
    const frame = x < 3 || x > 124;
    const n = (hash2(x, y) - 0.5) * 0.03;
    if (frame) set(o, 0.58, 0.6, 0.62); else set(o, l + n, l + 0.01 + n, l + 0.025 + n);
    o.h = frame ? 1 : slat < 2 ? -0.8 : slat / 8;
  });
  return { map: tex(t.c), normal: normalMap(t, 3) };
});

// Air-cooled chiller module side: framed V-coil fins. One 12 m x 2.4 m face.
export const coilSide = () => once('coil', () => {
  const W = 512, H = 96;
  const t = pixels(W, H, (x, y, u, v, o) => {
    const bay = x % 64;
    const frame = bay < 3 || y < 5 || y > 88;
    const fin = (x % 3) === 0;
    let l = frame ? 0.66 : fin ? 0.3 : 0.44;
    if (!frame && y > 70) l -= 0.06;
    l += (hash2(x, y) - 0.5) * 0.03;
    set(o, l, l * 1.01, l * 1.03);
    o.h = frame ? 1 : fin ? 0.2 : 0;
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});

// Chiller module top deck (fans are separate geometry).
export const unitTop = () => once('unitTop', () => {
  const t = pixels(256, 64, (x, y, u, v, o) => {
    const seam = (x % 43) < 2;
    const l = (seam ? 0.6 : 0.78) + (hash2(x, y) - 0.5) * 0.03 - smoothstep(0.3, 0.8, tfbm(u, v, 4, 2)) * 0.06;
    set(o, l, l, l * 1.01);
  });
  return tex(t.c);
});

// Fan with finger guard, seen from above.
export const fanDisk = () => once('fan', () => {
  const c = canvas(128, 128), g = c.getContext('2d');
  g.fillStyle = '#16181b'; g.fillRect(0, 0, 128, 128);
  g.fillStyle = '#2c3034';
  for (let k = 0; k < 6; k++) {
    g.save(); g.translate(64, 64); g.rotate(k * Math.PI / 3);
    g.beginPath(); g.ellipse(30, 0, 30, 11, 0.35, 0, Math.PI * 2); g.fill(); g.restore();
  }
  g.fillStyle = '#4a4f54'; g.beginPath(); g.arc(64, 64, 10, 0, Math.PI * 2); g.fill();
  g.strokeStyle = 'rgba(165,170,175,0.85)'; g.lineWidth = 1.2;
  for (let r = 14; r <= 62; r += 6) { g.beginPath(); g.arc(64, 64, r, 0, Math.PI * 2); g.stroke(); }
  for (let a = 0; a < 4; a++) { g.beginPath(); g.moveTo(64 + Math.cos(a * Math.PI / 4) * 62, 64 + Math.sin(a * Math.PI / 4) * 62); g.lineTo(64 - Math.cos(a * Math.PI / 4) * 62, 64 - Math.sin(a * Math.PI / 4) * 62); g.stroke(); }
  return tex(c);
});

// Steel bar grating for rooftop walkways (1 m tile).
export const grating = () => once('grating', () => {
  const t = pixels(64, 64, (x, y, u, v, o) => {
    const bar = (x % 4) < 1, cross = (y % 16) < 1;
    const l = bar || cross ? 0.55 : 0.2;
    set(o, l, l, l * 1.02);
    o.h = bar || cross ? 1 : 0;
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});

// Cable tray full of cables, viewed from above (u across the tray, v along it).
export const cables = (base, alt) => once('cables' + base, () => {
  const c = canvas(64, 256), g = c.getContext('2d');
  g.fillStyle = '#6c7177'; g.fillRect(0, 0, 64, 256);
  for (let x = 3; x < 61; x += 4) {
    const grd = g.createLinearGradient(x, 0, x + 4, 0);
    const col = (x * 7) % 5 === 0 ? alt : base;
    grd.addColorStop(0, '#000'); grd.addColorStop(0.35, col); grd.addColorStop(1, '#000');
    g.globalAlpha = 0.95; g.fillStyle = grd; g.fillRect(x, 0, 4, 256);
  }
  g.globalAlpha = 1; g.fillStyle = '#8a8f94';
  for (let y = 0; y < 256; y += 64) g.fillRect(0, y, 64, 3);
  return tex(c);
});

// Cooling tower casing: corrugated panels with an air-inlet louver band near the bottom.
export const towerSide = () => once('towerSide', () => {
  const t = pixels(128, 256, (x, y, u, v, o) => {
    const z = 1 - v;
    const rib = Math.sin(((x % 10) / 10) * Math.PI);
    let l = 0.72 + rib * 0.08, h = rib;
    if (z < 0.42 && z > 0.06) { const s = (y % 6) < 2; l = s ? 0.28 : 0.46; h = s ? -1 : 0; }
    l += (hash2(x, y) - 0.5) * 0.03 - smoothstep(0.25, 0, z) * 0.08;
    set(o, l, l * 1.01, l * 1.02);
    o.h = h;
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});

// Generator enclosure in the dark green seen along the hall walls.
export const gensetSide = () => once('genset', () => {
  const W = 256, H = 72;
  const t = pixels(W, H, (x, y, u, v, o) => {
    let c = [0.14, 0.32, 0.27];
    const louverBox = (x < 44 || x > 212) && y > 10 && y < 60;
    if (louverBox) c = (y % 4) < 2 ? [0.07, 0.15, 0.13] : [0.12, 0.27, 0.23];
    const door = ((x > 70 && x < 102) || (x > 154 && x < 186)) && y > 8 && y < 66;
    const edge = door && (x === 71 || x === 101 || x === 155 || x === 185 || y === 9);
    if (edge) c = [0.08, 0.18, 0.16];
    if (y > 66) c = [0.25, 0.26, 0.26];
    const n = (hash2(x, y) - 0.5) * 0.03 - smoothstep(30, 72, y) * 0.03;
    set(o, c[0] + n, c[1] + n, c[2] + n);
    o.h = louverBox ? ((y % 4) < 2 ? -0.5 : 0) : edge ? -0.6 : 0;
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});

// White ribbed trailer / box-truck body side.
export const trailerSide = () => once('trailer', () => {
  const t = pixels(256, 64, (x, y, u, v, o) => {
    const post = (x % 16) < 2;
    const rail = y < 3 || y > 60;
    const l = (post || rail ? 0.8 : 0.92) + (hash2(x, y) - 0.5) * 0.02 - smoothstep(30, 64, y) * 0.05;
    set(o, l, l, l * 0.98);
    o.h = post || rail ? 1 : 0;
  });
  return { map: tex(t.c), normal: normalMap(t, 1.5) };
});

// Substation pad: dark crushed rock with faint painted bay lines baked in later.
export const darkGravel = () => once('darkGravel', () => {
  const t = pixels(256, 256, (x, y, u, v, o) => {
    const n = hash2(x, y), m = tfbm(u, v, 16, 3);
    const l = 0.24 + n * 0.12 + (m - 0.5) * 0.1;
    set(o, l, l * 0.99, l * 0.98);
    o.h = n;
  });
  return { map: tex(t.c), normal: normalMap(t, 2) };
});
