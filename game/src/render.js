import * as THREE from 'three';
import { CSM } from 'three/addons/csm/CSM.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { cloudNoise } from './textures.js';

export const CLOUD_Y = 4200;

// Shared by the cloud layer and every material that receives cloud shadows.
export const cloudUniforms = {
  cloudNoise: { value: null },
  cloudTime: { value: 0 },
  cloudWind: { value: new THREE.Vector2(0.0009, 0.0004) },
  cloudCover: { value: 0.56 },
  cloudShadowAmt: { value: 0.6 },
  sunDirU: { value: new THREE.Vector3(0, 1, 0) },
};

export const CLOUD_GLSL = /* glsl */`
uniform sampler2D cloudNoise;
uniform float cloudTime, cloudCover, cloudShadowAmt;
uniform vec2 cloudWind;
uniform vec3 sunDirU;
float cloudDensity(vec2 xz) {
  vec2 p = xz / 36000.0 + cloudWind * cloudTime;
  float n = texture2D(cloudNoise, p).r * 0.65 + texture2D(cloudNoise, p * 3.7 + 0.31).r * 0.35;
  return smoothstep(cloudCover, cloudCover + 0.22, n);
}
float cloudShadow(vec3 wpos) {
  vec3 sd = normalize(sunDirU);
  float t = (${CLOUD_Y.toFixed(1)} - wpos.y) / max(sd.y, 0.08);
  return 1.0 - cloudDensity(wpos.xz + sd.xz * t) * cloudShadowAmt;
}
`;

// Adds world-position varyings and cloud shadowing on direct light to a built-in material.
// `extra` can further edit the shader (used by the terrain).
export function patchMaterial(mat, extra) {
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (shader, renderer) => {
    if (prev) prev.call(mat, shader, renderer);
    Object.assign(shader.uniforms, cloudUniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWPos;\nvarying vec3 vWNorm;')
      .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
        { vec4 wp = vec4(transformed, 1.0);
          #ifdef USE_INSTANCING
            wp = instanceMatrix * wp;
          #endif
          vWPos = (modelMatrix * wp).xyz; }
        #ifdef USE_INSTANCING
          vWNorm = normalize(mat3(modelMatrix) * mat3(instanceMatrix) * objectNormal);
        #else
          vWNorm = normalize(mat3(modelMatrix) * objectNormal);
        #endif`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWPos;\nvarying vec3 vWNorm;\n' + CLOUD_GLSL)
      .replace('#include <lights_fragment_end>', `#include <lights_fragment_end>
        { float cs = cloudShadow(vWPos); reflectedLight.directDiffuse *= cs; reflectedLight.directSpecular *= cs; }`);
    if (extra) extra(shader);
  };
  mat.customProgramCacheKey = () => (mat.userData.cacheKey || '') + 'cloud';
  mat.needsUpdate = true;
}

export function buildClouds() {
  cloudUniforms.cloudNoise.value = cloudNoise();
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      ...cloudUniforms,
      sunColor: { value: new THREE.Color() },
      ambient: { value: new THREE.Color() },
      hazeColor: { value: new THREE.Color() },
      camPos: { value: new THREE.Vector3() },
    },
    vertexShader: /* glsl */`
      #include <common>
      #include <logdepthbuf_pars_vertex>
      varying vec3 vW;
      void main() {
        vec4 w = modelMatrix * vec4(position, 1.0);
        vW = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
        #include <logdepthbuf_vertex>
      }`,
    fragmentShader: /* glsl */`
      #include <common>
      #include <logdepthbuf_pars_fragment>
      ${CLOUD_GLSL}
      uniform vec3 sunColor, ambient, hazeColor, camPos;
      varying vec3 vW;
      void main() {
        #include <logdepthbuf_fragment>
        float d = cloudDensity(vW.xz);
        if (d < 0.01) discard;
        vec3 sd = normalize(sunDirU);
        float toward = cloudDensity(vW.xz + normalize(sd.xz + 1e-4) * 900.0);
        float lit = clamp(1.0 - toward * 0.7 + (1.0 - d) * 0.4, 0.25, 1.0);
        vec3 col = mix(ambient, sunColor, lit);
        float dist = length(vW.xz - camPos.xz);
        col = mix(col, hazeColor, smoothstep(15000.0, 110000.0, dist) * 0.75);
        float a = d * (1.0 - smoothstep(60000.0, 140000.0, dist)) * 0.95;
        gl_FragColor = vec4(col, a);
      }`,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const geo = new THREE.PlaneGeometry(1, 1);
  geo.rotateX(-Math.PI / 2);
  const mesh = new THREE.Mesh(geo, mat);
  mesh.scale.set(300000, 1, 300000);
  mesh.position.y = CLOUD_Y;
  mesh.frustumCulled = false;
  mesh.renderOrder = 1;
  return mesh;
}

const GradeShader = {
  uniforms: { tDiffuse: { value: null }, time: { value: 0 }, amount: { value: 1 } },
  vertexShader: /* glsl */`varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: /* glsl */`
    uniform sampler2D tDiffuse; uniform float time; uniform float amount; varying vec2 vUv;
    void main() {
      vec3 c = texture2D(tDiffuse, vUv).rgb;
      float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
      c = mix(vec3(l), c, 1.0 + 0.06 * amount);
      c = mix(c, (c - 0.5) * 1.07 + 0.5, amount);
      c *= mix(vec3(1.0), vec3(1.025, 1.0, 0.965), amount);
      vec2 d = vUv - 0.5;
      c *= mix(0.8, 1.0, smoothstep(0.9, 0.3, length(d * vec2(1.0, 0.85))));
      float n = fract(sin(dot(vUv * vec2(1231.0, 1789.0) + time, vec2(12.9898, 78.233))) * 43758.5453);
      c += (n - 0.5) * 0.018;
      gl_FragColor = vec4(c, 1.0);
    }`,
};

export function createPipeline(renderer, scene, camera) {
  const size = renderer.getDrawingBufferSize(new THREE.Vector2());
  const rt = new THREE.WebGLRenderTarget(size.x, size.y, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, rt);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(size.x, size.y), 0.2, 0.3, 3.0);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  const grade = new ShaderPass(GradeShader);
  composer.addPass(grade);

  const csm = new CSM({
    camera, parent: scene, cascades: 4, maxFar: 3200, mode: 'practical',
    shadowMapSize: 2048, lightDirection: new THREE.Vector3(-1, -1, -1).normalize(),
    lightIntensity: 3, lightNear: 1, lightFar: 9000, lightMargin: 500,
  });
  csm.fade = true;
  for (const l of csm.lights) { l.shadow.bias = -0.0002; l.shadow.normalBias = 0.35; }

  return {
    composer, bloom, grade, csm,
    setupMaterials(root) {
      const seen = new Set();
      root.traverse((o) => {
        if (!o.material) return;
        for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
          if (seen.has(m) || !(m.isMeshStandardMaterial || m.isMeshLambertMaterial || m.isMeshPhongMaterial)) continue;
          seen.add(m);
          csm.setupMaterial(m);
          patchMaterial(m, m.userData.extraShader);
        }
      });
    },
    resize(w, h) {
      composer.setSize(w, h);
      csm.updateFrustums();
    },
  };
}
