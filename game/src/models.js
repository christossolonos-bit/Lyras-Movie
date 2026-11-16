import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

// Hero vehicles from Meshy (converted to Draco GLB in game/assets/vehicles).
// Each is normalized on load: real-world length, long axis along +z, wheels on y = 0.
// `yaw` turns the model so its nose points +z (checked by eye against the vehicle card).
export const VEHICLES = {
  nova_car: { file: 'assets/vehicles/nova_car.glb', length: 4.7, yaw: Math.PI / 2 },
  juno_trike: { file: 'assets/vehicles/juno_trike.glb', length: 3.4, yaw: Math.PI / 2 },
  james_rover: { file: 'assets/vehicles/james_rover.glb', length: 6.4, yaw: Math.PI / 2 },
};

const draco = new DRACOLoader();
draco.setDecoderPath('https://unpkg.com/three@0.169.0/examples/jsm/libs/draco/gltf/');
const loader = new GLTFLoader();
loader.setDRACOLoader(draco);
const cache = new Map();

async function loadNormalized(name) {
  const cfg = VEHICLES[name];
  const gltf = await loader.loadAsync(cfg.file);
  const model = gltf.scene;
  model.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = o.receiveShadow = true;
    const m = o.material;
    if (m.map) m.map.anisotropy = 8;
    m.envMapIntensity = 1.0;
  });
  // turn so the long axis runs along z, then scale to real length and sit it on the ground
  const inner = new THREE.Group();
  inner.add(model);
  model.rotation.y = cfg.yaw;
  inner.updateMatrixWorld(true);
  let box = new THREE.Box3().setFromObject(inner);
  const size = box.getSize(new THREE.Vector3());
  const s = cfg.length / Math.max(size.x, size.z);
  model.scale.setScalar(s);
  inner.updateMatrixWorld(true);
  box = new THREE.Box3().setFromObject(inner);
  const c = box.getCenter(new THREE.Vector3());
  model.position.set(-c.x, -box.min.y, -c.z);
  return inner;
}

// Returns a fresh copy (shares geometry and materials with other copies).
export async function loadVehicle(name) {
  if (!cache.has(name)) cache.set(name, loadNormalized(name));
  const proto = await cache.get(name);
  const g = new THREE.Group();
  g.add(proto.clone(true));
  g.userData.vehicle = name;
  return g;
}
