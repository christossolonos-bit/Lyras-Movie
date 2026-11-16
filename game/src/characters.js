import * as THREE from 'three';

// Full-body cast figures from the series character sheets (cropped + regenerated isolates
// in game/assets/characters/). Without a Meshy pipeline these are high-detail textured
// volumetric impostors (crossed alpha planes) scaled to real height — the same approach
// the desert uses for Joshua trees, at character resolution.

const loader = new THREE.TextureLoader();
const cache = new Map();

export const CHARACTERS = {
  lyra:   { file: 'assets/characters/lyra_body.png',   height: 1.72, kind: 'hologram' },
  marcus: { file: 'assets/characters/marcus_body.png', height: 1.80, kind: 'human' },
  juno:   { file: 'assets/characters/juno_body.png',   height: 1.68, kind: 'human' },
  nova:   { file: 'assets/characters/nova_body.png',   height: 1.70, kind: 'human' },
  james:  { file: 'assets/characters/james_body.png',  height: 1.78, kind: 'human' },
  patch:  { file: 'assets/characters/patch_body.png',  height: 0.62, kind: 'dog',
            side: 'assets/characters/patch_side.png' },
};

function loadTex(url) {
  return new Promise((resolve, reject) => {
    loader.load(url, (t) => {
      t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = 8;
      t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
      resolve(t);
    }, undefined, reject);
  });
}

async function getMaps(name) {
  if (!cache.has(name)) {
    const cfg = CHARACTERS[name];
    cache.set(name, Promise.all([
      loadTex(cfg.file),
      cfg.side ? loadTex(cfg.side) : Promise.resolve(null),
    ]).then(([front, side]) => ({ front, side, cfg })));
  }
  return cache.get(name);
}

function humanMaterial(map, kind) {
  if (kind === 'hologram') {
    return new THREE.MeshBasicMaterial({
      map,
      color: new THREE.Color('#7af0ff'),
      transparent: true,
      opacity: 0.82,
      alphaTest: 0.08,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
  }
  return new THREE.MeshStandardMaterial({
    map,
    alphaTest: 0.35,
    alphaToCoverage: true,
    roughness: 0.72,
    metalness: 0.05,
    side: THREE.DoubleSide,
  });
}

// Crossed full-body cards: 4 radial planes (8 faces) so the figure reads from every angle.
function figureGeometry(w, h, planes = 4) {
  const geos = [];
  for (let k = 0; k < planes; k++) {
    const g = new THREE.PlaneGeometry(w, h);
    g.translate(0, h / 2, 0);
    g.rotateY((k / planes) * Math.PI);
    geos.push(g);
  }
  // merge into one BufferGeometry
  const positions = [], normals = [], uvs = [], indices = [];
  let base = 0;
  for (const g of geos) {
    const p = g.attributes.position, n = g.attributes.normal, u = g.attributes.uv, idx = g.index;
    for (let i = 0; i < p.count; i++) {
      positions.push(p.getX(i), p.getY(i), p.getZ(i));
      // bias normals upward so they catch indoor light evenly
      const nx = n.getX(i) * 0.4, ny = 1, nz = n.getZ(i) * 0.4;
      const len = Math.hypot(nx, ny, nz) || 1;
      normals.push(nx / len, ny / len, nz / len);
      uvs.push(u.getX(i), u.getY(i));
    }
    for (let i = 0; i < idx.count; i++) indices.push(idx.getX(i) + base);
    base += p.count;
    g.dispose();
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  out.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  out.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  out.setIndex(indices);
  out.computeBoundingSphere();
  return out;
}

// Dog: front card + side card for volume (matches dog_ref front/side panels).
function dogGeometry(w, h) {
  const front = new THREE.PlaneGeometry(w, h); front.translate(0, h / 2, 0);
  const side = new THREE.PlaneGeometry(w * 1.15, h); side.translate(0, h / 2, 0); side.rotateY(Math.PI / 2);
  const geos = [front, side];
  const positions = [], normals = [], uvs = [], indices = [];
  let base = 0;
  for (const g of geos) {
    const p = g.attributes.position, n = g.attributes.normal, u = g.attributes.uv, idx = g.index;
    for (let i = 0; i < p.count; i++) {
      positions.push(p.getX(i), p.getY(i), p.getZ(i));
      normals.push(n.getX(i), n.getY(i), n.getZ(i));
      uvs.push(u.getX(i), u.getY(i));
    }
    for (let i = 0; i < idx.count; i++) indices.push(idx.getX(i) + base);
    base += p.count;
    g.dispose();
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  out.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  out.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  out.setIndex(indices);
  out.computeBoundingSphere();
  return out;
}

export async function loadCharacter(name) {
  const { front, side, cfg } = await getMaps(name);
  const aspect = front.image ? front.image.width / front.image.height : 0.45;
  const h = cfg.height;
  const w = h * aspect * (cfg.kind === 'dog' ? 1.05 : 0.92);

  const root = new THREE.Group();
  root.userData.character = name;

  if (cfg.kind === 'dog' && side) {
    // two materials: front + side textures on separate meshes
    const frontMesh = new THREE.Mesh(
      (() => { const g = new THREE.PlaneGeometry(w, h); g.translate(0, h / 2, 0); return g; })(),
      humanMaterial(front, 'human'),
    );
    const sideMesh = new THREE.Mesh(
      (() => { const g = new THREE.PlaneGeometry(w * 1.2, h); g.translate(0, h / 2, 0); g.rotateY(Math.PI / 2); return g; })(),
      humanMaterial(side, 'human'),
    );
    frontMesh.castShadow = sideMesh.castShadow = true;
    root.add(frontMesh, sideMesh);
  } else {
    const mesh = new THREE.Mesh(figureGeometry(w, h, cfg.kind === 'hologram' ? 6 : 4), humanMaterial(front, cfg.kind));
    mesh.castShadow = cfg.kind !== 'hologram';
    mesh.renderOrder = cfg.kind === 'hologram' ? 3 : 0;
    root.add(mesh);

    if (cfg.kind === 'hologram') {
      // soft cyan ground glow on the projector plate
      const glow = new THREE.Mesh(
        new THREE.CircleGeometry(0.55, 32),
        new THREE.MeshBasicMaterial({ color: '#36e0ff', transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false }),
      );
      glow.rotation.x = -Math.PI / 2;
      glow.position.y = 0.02;
      root.add(glow);
    }
  }

  // soft contact shadow (skip for hologram)
  if (cfg.kind !== 'hologram') {
    const shadow = new THREE.Mesh(
      new THREE.CircleGeometry(w * 0.28, 24),
      new THREE.MeshBasicMaterial({ color: '#000', transparent: true, opacity: 0.28, depthWrite: false }),
    );
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.y = 0.015;
    shadow.renderOrder = -1;
    root.add(shadow);
  }

  return root;
}

// Place a character in a parent group's local frame.
export async function placeCharacter(parent, name, spot) {
  let fig;
  try { fig = await loadCharacter(name); }
  catch (e) { console.warn('character failed', name, e); return null; }
  fig.position.set(spot.x, spot.y || 0, spot.z);
  fig.rotation.y = spot.ry || 0;
  if (spot.scale) fig.scale.setScalar(spot.scale);
  parent.add(fig);
  return fig;
}
