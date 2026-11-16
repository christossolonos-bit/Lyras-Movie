import * as THREE from 'three';
import { globalUniforms } from './util.js';

// Procedural building facades for instanced boxes. Windows are laid out in world space, so
// any box at any scale gets a consistent grid of floors and bays. Each building picks its
// style (curtain wall vs punched windows, bay width, glass tint) from a hash of its position,
// and at night a random share of windows lights up. Instance color is the wall color.
//
// style: 'office' (mixed curtain/punched), 'glass' (all curtain wall), 'residential' (punched),
// 'house' (punched, no ground-floor storefront glass), 'brick' (punched, running-bond brick walls)
export function facadeMaterial(style = 'office') {
  const m = new THREE.MeshStandardMaterial({ roughness: 0.7, metalness: 0.1 });
  const forced = { office: -1, glass: 0, residential: 1, house: 1, brick: 1 }[style];
  const brick = style === 'brick' ? `{
          vec2 bp = f / vec2(0.24, 0.075);
          float row = floor(bp.y), bxv = bp.x + 0.5 * mod(row, 2.0);
          float mortar = max(step(fract(bxv), 0.07), step(fract(bp.y), 0.16));
          float fade = smoothstep(0.3, 0.8, max(fwidth(bp.x), fwidth(bp.y)));
          float jitter = mix(0.86 + 0.28 * fh1(floor(vec2(bxv, row))), 1.0, fade);
          wallC *= mix(jitter, 1.4, mix(mortar, 0.18, fade));
        }` : '';
  const lobbyExpr = style === 'house' ? '0.0' : '1.0 - step(floorH * 1.25, vWPos.y)';
  m.userData.cacheKey = 'facade-' + style;
  m.userData.extraShader = (shader) => {
    shader.uniforms.cityNight = globalUniforms.night;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec2 vOrigin;')
      .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
        #ifdef USE_INSTANCING
          vOrigin = (modelMatrix * instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xz;
        #else
          vOrigin = (modelMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xz;
        #endif`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
        uniform float cityNight;
        varying vec2 vOrigin;
        float fh1(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
        float fh3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }`)
      .replace('#include <color_fragment>', '')
      .replace('#include <map_fragment>', /* glsl */`
        vec3 nW = normalize(vWNorm);
        vec2 key = floor(vOrigin / 7.0);
        float seed = fh1(key), seed2 = fh1(key + 17.3), seed3 = fh1(key + 41.9);
        float curtain = ${forced < 0 ? 'step(seed, 0.5)' : forced === 0 ? '1.0' : '0.0'};
        float isRoof = step(0.5, nW.y);
        vec2 f = abs(nW.x) > abs(nW.z) ? vec2(vWPos.z, vWPos.y) : vec2(vWPos.x, vWPos.y);
        float floorH = mix(3.3, 4.1, seed2);
        float bay = curtain > 0.5 ? mix(1.5, 2.4, seed3) : mix(2.4, 3.6, seed3);
        vec2 cell = f / vec2(bay, floorH);
        vec2 cf = fract(cell), ci = floor(cell);
        float winC = step(cf.x, 0.93) * step(cf.y, 0.88);
        float winP = step(0.2, cf.x) * step(cf.x, 0.8) * step(0.3, cf.y) * step(cf.y, 0.82);
        float win = mix(winP, winC, curtain);
        float lobby = ${lobbyExpr};
        win = mix(win, step(0.05, cf.x) * step(cf.x, 0.95) * step(cf.y, 0.85), lobby);
        // fade the grid to its average where it gets smaller than a pixel (no moire on distant towers)
        float px = max(fwidth(cell.x), fwidth(cell.y));
        win = mix(win, mix(0.36, 0.8, curtain), smoothstep(0.35, 0.9, px));
        win *= 1.0 - isRoof;
        vec3 wallC = vColor;
        ${brick}
        vec3 glassC = mix(vec3(0.06, 0.09, 0.12), vec3(0.16, 0.22, 0.28), seed2) * (0.8 + 0.4 * fh3(vec3(ci, seed)));
        vec3 roofC = vec3(0.42, 0.42, 0.4) * (0.9 + 0.2 * seed);
        diffuseColor.rgb = mix(mix(wallC, glassC, win), roofC, isRoof);
        float fWin = win;
      `)
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = mix(roughness, 0.08, fWin);')
      .replace('#include <metalnessmap_fragment>', 'float metalnessFactor = mix(metalness, 0.8, fWin);')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        {
          float share = mix(0.15, 0.5, seed3) + lobby * 0.4;
          float lit = step(1.0 - share, fh3(vec3(ci, seed * 91.0)));
          lit = mix(lit, share, smoothstep(0.35, 0.9, px));
          vec3 warm = mix(vec3(1.0, 0.74, 0.45), vec3(0.82, 0.9, 1.0), step(0.6, fh1(ci + seed)));
          totalEmissiveRadiance += warm * lit * fWin * cityNight * mix(1.6, 0.7, smoothstep(0.35, 0.9, px));
        }`);
  };
  return m;
}
