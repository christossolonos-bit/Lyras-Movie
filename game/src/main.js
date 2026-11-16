import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';
import { Terrain, setTerrain, getHeight, roadX, roadPolyline, TOWN_Z, MILE, BOUNDS, HALCYON, NOVA_PAD, IRONWOOD, JUNO_PAD } from './terrain.js';
import { buildHalcyon } from './city.js';
import { buildNovaHome } from './nova.js';
import { buildIronwood } from './ironwood.js';
import { buildJunoHome } from './juno.js';
import { loadVehicle } from './models.js';
import { placeCharacter } from './characters.js';
import { buildTraffic } from './traffic.js';
import { buildPeople } from './people.js';
import { buildHallInterior, hallCenter, hallName, HL } from './hallInterior.js';
import { buildNovaCar } from './props.js';
import { buildRoad, roadPath } from './road.js';
import { buildDataCenter } from './datacenter.js';
import { buildTown } from './town.js';
import { buildScatter, LocalScatter } from './scatter.js';
import { Controls } from './controls.js';
import { floorAt, roomAt, initInteriorLights, updateInteriors, toWorld, indoorFill } from './interiors.js';
import { createPipeline, buildClouds, cloudUniforms } from './render.js';
import { setNight, smoothstep } from './util.js';
import { sunPosition, moonPosition, localClock, localDate, DEATH_VALLEY } from './sun.js';

const renderer = new THREE.WebGLRenderer({ antialias: false, logarithmicDepthBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.3, 220000);
scene.fog = new THREE.FogExp2(0xc8cdd0, 0.000034);

const sky = new Sky();
sky.scale.setScalar(180000);
scene.add(sky);
const su = sky.material.uniforms;
su.turbidity.value = 4; su.rayleigh.value = 1.1; su.mieCoefficient.value = 0.004; su.mieDirectionalG.value = 0.82;

const hemi = new THREE.HemisphereLight(0xcfe3ff, 0x9a7656, 0.35);
scene.add(hemi);

const pipe = createPipeline(renderer, scene, camera);
const clouds = buildClouds();
scene.add(clouds);

// Star field for night skies.
const stars = (() => {
  const n = 4000, p = new Float32Array(n * 3), c = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const v = new THREE.Vector3().randomDirection();
    v.y = Math.abs(v.y) * 0.95 + 0.02;
    v.normalize().multiplyScalar(150000);
    p.set([v.x, v.y, v.z], i * 3);
    const b = 0.35 + Math.random() ** 3 * 0.65, t = Math.random();
    c.set([b * (t < 0.2 ? 1 : 0.85), b * 0.9, b * (t > 0.8 ? 1 : 0.85)], i * 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
  const pts = new THREE.Points(g, new THREE.PointsMaterial({ size: 1.6, sizeAttenuation: false, vertexColors: true, transparent: true, fog: false, depthWrite: false }));
  pts.frustumCulled = false;
  return pts;
})();
scene.add(stars);

// Environment reflections come from the sky itself; rebuilt when the sun moves.
const pmrem = new THREE.PMREMGenerator(renderer);
const envScene = new THREE.Scene();
const envSky = new Sky();
envSky.scale.setScalar(10000);
envScene.add(envSky);
let envRT = null;

// ---------- build the world ----------
const loadMsg = document.getElementById('loadmsg');
const step = async (msg, fn) => { loadMsg.textContent = msg; await new Promise((r) => setTimeout(r, 30)); return fn(); };

const terrain = new Terrain();
setTerrain(terrain);
scene.add(terrain.group);
const START = [new THREE.Vector3(-200, 210, -840), new THREE.Vector3(300, 0, -40)];
await step('Shaping the desert…', () => terrain.init(START[0]));
await step('Paving 40 miles of highway…', () => scene.add(buildRoad()));
const dc = await step('Raising Vira…', () => buildDataCenter());
scene.add(dc.group);
await step('Building the town…', () => scene.add(buildTown()));
const halcyon = await step('Building Halcyon…', () => buildHalcyon());
scene.add(halcyon);
const novaHome = await step('Up in the hills…', () => buildNovaHome());
scene.add(novaHome);
const ironwood = await step('Building Ironwood…', () => buildIronwood());
scene.add(ironwood);
const junoHome = await step("Juno's place…", () => buildJunoHome());
scene.add(junoHome);

// Hero vehicles (Meshy models). Each parks at a spot its home marks, in that home's frame.
async function park(parent, name, spot, fallback) {
  let v;
  try { v = await loadVehicle(name); } catch (e) { console.warn('vehicle failed to load', name, e); v = fallback ? fallback() : null; }
  if (!v) return null;
  v.position.set(spot.x, spot.y || 0, spot.z);
  v.rotation.y = spot.ry || 0;
  parent.add(v);
  return v;
}
await step('Parking the cars…', () => Promise.all([
  park(novaHome, 'nova_car', novaHome.userData.spots.nova_car, buildNovaCar),
  park(junoHome, 'juno_trike', junoHome.userData.spots.juno_trike),
  park(scene, 'james_rover', { x: 92, y: 0.12, z: -545, ry: Math.PI / 2 }),
]));
// Cast: full-body figures from the series character sheets, posed in their rooms.
await step('Casting the crew…', () => Promise.all([
  placeCharacter(dc.ops, 'lyra', dc.ops.userData.cast.lyra),
  placeCharacter(dc.ops, 'marcus', dc.ops.userData.cast.marcus),
  placeCharacter(dc.ops, 'patch', dc.ops.userData.cast.patch),
  placeCharacter(junoHome, 'juno', junoHome.userData.cast.juno),
  placeCharacter(novaHome, 'nova', novaHome.userData.cast.nova),
  placeCharacter(scene, 'james', { x: 86, y: 0.12, z: -548, ry: Math.PI * 0.15 }),
]));
await step('Growing the desert…', () => scene.add(buildScatter()));
const brush = new LocalScatter();
scene.add(brush.group);
// Vira's staff roster (names, titles, households): game/data/staff/roster.json, built by tools/staff_roster.py
const roster = await fetch('data/staff/roster.json').then((r) => (r.ok ? r.json() : null)).catch(() => null);
const traffic = await step('Sending everyone to work…', () => buildTraffic(roster));
scene.add(traffic.group);
const halls = await step('Fitting out the data halls…', () => buildHallInterior());
scene.add(halls.group);
const people = await step('Clocking everyone in…', () => buildPeople());
people.setStaff(traffic.staff);
scene.add(people.group);
initInteriorLights(scene);
await step('Lighting…', () => pipe.setupMaterials(scene));

// ---------- time of day: the real sky over Death Valley ----------
// The world clock runs on real time. [ and ] scrub it, T runs it 120x, L snaps back to live.
let simMs = Date.now(), timeRate = 1;
let sunElev = 0, sunAzim = 0, lastEnvElev = null;
let moon = { elev: -90, azim: 0, phase: 0 };
const isLive = () => timeRate === 1 && Math.abs(simMs - Date.now()) < 60000;
// azimuth clockwise from north -> spherical theta measured from +z (south) toward +x (east)
const skyTheta = (azim) => THREE.MathUtils.degToRad(180 - azim);
function syncSky() {
  const d = new Date(simMs);
  const s = sunPosition(d);
  moon = moonPosition(d);
  if (Math.abs(s.elev - sunElev) < 0.01 && Math.abs(s.azim - sunAzim) < 0.01) return;
  sunElev = s.elev; sunAzim = s.azim;
  updateSun();
}
const sunDir = new THREE.Vector3();
const C = (h) => new THREE.Color(h);
const FOG_NIGHT = C('#0b1120'), FOG_GOLD = C('#d9b08a'), FOG_DAY = C('#c3ccd3');
const SUN_LOW = C('#ffa860'), SUN_HIGH = C('#fff3e4');
const lightColor = new THREE.Color();
let lightIntensity = 3;

function updateSun() {
  sunDir.setFromSphericalCoords(1, THREE.MathUtils.degToRad(90 - sunElev), skyTheta(sunAzim));
  su.sunPosition.value.copy(sunDir);
  envSky.material.uniforms.sunPosition.value.copy(sunDir);
  for (const k of ['turbidity', 'rayleigh', 'mieCoefficient', 'mieDirectionalG']) envSky.material.uniforms[k].value = su[k].value;

  const day = smoothstep(-4, 8, sunElev);
  const night = 1 - smoothstep(-8, 3, sunElev);
  const warm = smoothstep(2, 35, sunElev);
  lightColor.copy(SUN_LOW).lerp(SUN_HIGH, warm);
  const lightDir = sunDir.clone();
  if (sunElev > -2) {
    lightIntensity = 3.4 * day;
  } else if (moon.elev > 0) {
    // the real moon: brightness from its phase and how high it is
    lightDir.setFromSphericalCoords(1, THREE.MathUtils.degToRad(90 - Math.max(moon.elev, 4)), skyTheta(moon.azim));
    lightColor.set('#8fa8ff');
    lightIntensity = 0.12 + 0.75 * moon.phase * smoothstep(0, 12, moon.elev);
  } else {
    // moonless: faint starlight from overhead
    lightDir.set(0.2, 1, 0.1).normalize();
    lightColor.set('#6f84c8');
    lightIntensity = 0.1;
  }
  moonMesh.visible = moon.elev > -1 && sunElev < 10;
  moonDir.setFromSphericalCoords(1, THREE.MathUtils.degToRad(90 - moon.elev), skyTheta(moon.azim));
  moonMesh.material.opacity = 0.35 + 0.65 * moon.phase;
  pipe.csm.lightDirection.copy(lightDir).negate();
  for (const l of pipe.csm.lights) { l.color.copy(lightColor); l.intensity = lightIntensity; }
  cloudUniforms.sunDirU.value.copy(lightDir);
  cloudUniforms.cloudShadowAmt.value = 0.6 * day;

  hemi.intensity = 0.3 + 0.3 * day;
  hemi.color.set(day > 0.5 ? '#cfe3ff' : '#5a6a9a');
  scene.environmentIntensity = 0.2 + 0.7 * day;
  renderer.toneMappingExposure = 0.62 + 0.55 * night;
  stars.material.opacity = night;
  stars.visible = night > 0.01;
  scene.fog.color.copy(FOG_NIGHT).lerp(FOG_GOLD, day).lerp(FOG_DAY, warm);

  const cu = clouds.material.uniforms;
  cu.sunColor.value.copy(lightColor).multiplyScalar(0.25 + 0.95 * day);
  cu.ambient.value.copy(scene.fog.color).multiplyScalar(0.55 + 0.2 * day);
  cu.hazeColor.value.copy(scene.fog.color);
  setNight(night);
  dc.setDaylight(day);

  if (lastEnvElev === null || Math.abs(sunElev - lastEnvElev) > 2) {
    lastEnvElev = sunElev;
    if (envRT) envRT.dispose();
    envRT = pmrem.fromScene(envScene);
    scene.environment = envRT.texture;
  }
}
// the moon itself, a small disc far out in the sky
const moonDir = new THREE.Vector3(0, -1, 0);
const moonMesh = new THREE.Mesh(new THREE.CircleGeometry(900, 32), new THREE.MeshBasicMaterial({ color: '#f4f1e4', transparent: true, fog: false, depthWrite: false }));
moonMesh.renderOrder = -1;
scene.add(moonMesh);
syncSky();
updateSun();

// ---------- distance culling for whole districts ----------
const farCull = [
  [halcyon, HALCYON.x, HALCYON.z, 32000], [novaHome, NOVA_PAD.x, NOVA_PAD.z, 30000],
  [ironwood, IRONWOOD.x, IRONWOOD.z, 26000], [junoHome, JUNO_PAD.x, JUNO_PAD.z, 26000],
  [dc.group, 300, 0, 30000],
];

// ---------- camera & viewpoints ----------
// walk height: interior floors where there are rooms, the terrain everywhere else
const walkHeight = (x, z, feetY) => floorAt(x, z, getHeight(x, z), feetY);
const controls = new Controls(camera, renderer.domElement, walkHeight);
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const viewpoints = {
  Digit1: [V(-200, 210, -840), V(300, 0, -40)],                  // Vira from above the gate corner (hero aerial)
  Digit2: [V(70, 45, TOWN_Z - 650), V(0, 5, TOWN_Z - 80)],         // town from the north
  Digit3: [V(roadX(-32000) - 6, 1.7, -32000), V(roadX(-32300), 1.7, -32300)], // middle of nowhere
  Digit4: [V(9000, 9000, -16000), V(0, 0, -36000)],                // high over the valley
  Digit5: [V(4, 1.7, -760), V(31, 2, -600)],                       // standing at the front gate
  Digit6: [V(900, 230, -1000), V(380, 0, -300)],                   // over the substation
  Digit7: [V(18, 22, -470), V(40, 14, 120)],                       // along the west wall and cooling towers
  Digit8: [V(200, 48, -520), V(200, 16, -200)],                    // rooftops
  Digit9: [V(HALCYON.x + 5200, 40, HALCYON.z + 300), V(HALCYON.x, 140, HALCYON.z)], // Halcyon skyline from the freeway
  Digit0: [V(NOVA_PAD.x + 10, 0, NOVA_PAD.z + 30), V(HALCYON.x, 40, HALCYON.z)], // Nova's terrace
  Minus: [V(IRONWOOD.x - 2600, 380, IRONWOOD.z + 2600), V(IRONWOOD.x, 0, IRONWOOD.z)],  // Ironwood from above
  Equal: [V(JUNO_PAD.x - 30, 0, JUNO_PAD.z + 45), V(JUNO_PAD.x, 0, JUNO_PAD.z)],      // Juno's place
  Backquote: [V(80, 3, -530), V(92, 1.5, -545)],                                       // James's rover at Vira
  // interiors, on foot
  KeyI: dc.views.lobby,                                                               // Vira lobby (pb7)
  KeyO: dc.views.ops,                                                                 // ops / hologram room (lh1)
  KeyM: dc.views.office,                                                              // Marcus's office (ml1)
  KeyP: dc.views.servers,                                                             // server aisle (pb8, c1)
};
const localView = (home, name) => home.userData.views[name].map(([x, y, z]) => toWorld(home, x, y, z));
viewpoints.KeyJ = localView(junoHome, 'shop');                                         // Juno's workshop (ji1)
viewpoints.KeyK = localView(junoHome, 'loft');                                         // Juno's loft (jn1)
viewpoints.KeyN = localView(novaHome, 'living');                                       // Nova's living room (nv2)
const WALK_VIEWS = ['Digit3', 'Digit5', 'Digit0', 'Equal', 'Backquote', 'KeyI', 'KeyO', 'KeyM', 'KeyP', 'KeyJ', 'KeyK', 'KeyN'];
let hallU = -1;
controls.onKey = (code) => {
  // follow a staff car: V cycles through cars on the road, B grabs the nearest one
  if (code === 'KeyV') traffic.followNext();
  if (code === 'KeyB') traffic.followNearest(camera.position);
  if (code === 'KeyV' || code === 'KeyB') people.unfollow();
  // follow a worker on foot: E grabs the nearest one in sight
  if (code === 'KeyE') { traffic.unfollow(); people.followNearest(camera.position); }
  // U walks into the next data hall
  if (code === 'KeyU') {
    hallU = (hallU + 1) % 16;
    const c = hallCenter(hallU), sd = hallU % 4 < 2 ? -1 : 1;
    controls.place(V(c.x + sd * HL.corridorX, HL.floor + 1.7, c.z - 26.9), V(c.x, HL.floor + 1.5, c.z - 26.9));
    controls.mode = 'walk';
  }
  const leave = /^Key[WASDIOMPJKNU]$|^Digit|^Minus$|^Equal$|^Backquote$|^Escape$/.test(code);
  if (leave) { traffic.unfollow(); if (code !== 'KeyE') people.unfollow(); }
  if (viewpoints[code]) {
    controls.place(...viewpoints[code]);
    controls.mode = WALK_VIEWS.includes(code) ? 'walk' : 'fly';
  }
  if (code === 'KeyG') dc.gate.toggle();
  if (code === 'KeyT') timeRate = timeRate === 1 ? 120 : 1;
  if (code === 'KeyL') { simMs = Date.now(); timeRate = 1; syncSky(); }
  if (code === 'KeyH') document.getElementById('help').classList.toggle('hidden');
  if (code === 'KeyQ') {
    // quality: toggle render resolution
    const pr = renderer.getPixelRatio() > 1.01 ? 1 : Math.min(devicePixelRatio, 1.5);
    renderer.setPixelRatio(pr);
    pipe.composer.setPixelRatio(pr);
    pipe.resize(innerWidth, innerHeight);
  }
};
viewpoints.Digit0[0].y = getHeight(NOVA_PAD.x, NOVA_PAD.z) + 1.7;
viewpoints.Equal[0].y = getHeight(JUNO_PAD.x, JUNO_PAD.z) + 1.7;
viewpoints.Equal[1].y = viewpoints.Equal[0].y + 3;
controls.place(...viewpoints.Digit1);

// ---------- HUD & minimap ----------
const hud = document.getElementById('hud');
const followPanel = document.getElementById('follow');
const mini = document.getElementById('minimap');
const mctx = mini.getContext('2d');
const mapRoads = ['saltbrush', 'halcyon', 'novahill', 'ironwood', 'junodrive'].map((id) => roadPolyline(id, 400));
const MAP = { x0: -95000, x1: 62000, z0: -72000, z1: 8000 };
const toMap = (x, z) => [((x - MAP.x0) / (MAP.x1 - MAP.x0)) * mini.width, ((z - MAP.z0) / (MAP.z1 - MAP.z0)) * mini.height];

function drawMinimap() {
  const { width: w, height: h } = mini;
  mctx.clearRect(0, 0, w, h);
  mctx.fillStyle = 'rgba(6,14,22,.65)'; mctx.fillRect(0, 0, w, h);
  mctx.strokeStyle = '#c8b28a'; mctx.lineWidth = 2; mctx.beginPath();
  for (const pts of mapRoads) { mctx.beginPath(); pts.forEach(([x, z], i) => { const [px, py] = toMap(x, z); i ? mctx.lineTo(px, py) : mctx.moveTo(px, py); }); mctx.stroke(); }
  const [hx, hy] = toMap(HALCYON.x, HALCYON.z);
  mctx.fillStyle = 'rgba(255,207,134,.18)'; mctx.beginPath();
  mctx.ellipse(hx, hy, HALCYON.rx / (MAP.x1 - MAP.x0) * mini.width, HALCYON.rz / (MAP.z1 - MAP.z0) * mini.height, 0, 0, Math.PI * 2); mctx.fill();
  const label = (x, z, text, color) => {
    const [px, py] = toMap(x, z);
    mctx.fillStyle = color; mctx.fillRect(px - 4, py - 4, 8, 8);
    mctx.font = '11px system-ui'; mctx.fillText(text, px + 8, py + 4);
  };
  label(0, 0, 'VIRA', '#36e0ff');
  label(0, TOWN_Z, 'SALTBRUSH', '#ffcf86');
  label(HALCYON.x, HALCYON.z, 'HALCYON', '#ffcf86');
  label(NOVA_PAD.x, NOVA_PAD.z, 'NOVA', '#d8b4ff');
  label(IRONWOOD.x, IRONWOOD.z, 'IRONWOOD', '#ffcf86');
  label(JUNO_PAD.x, JUNO_PAD.z, 'JUNO', '#d8b4ff');
  const [px, py] = toMap(camera.position.x, camera.position.z);
  mctx.save(); mctx.translate(px, py); mctx.rotate(-controls.yaw);
  mctx.fillStyle = '#fff'; mctx.beginPath(); mctx.moveTo(0, -7); mctx.lineTo(5, 6); mctx.lineTo(-5, 6); mctx.fill();
  mctx.restore();
}

function clockText() {
  const d = new Date(simMs);
  const tag = isLive() ? '<span style="color:#ff5a4a">● LIVE</span>' : timeRate > 1 ? '▶▶ ×' + timeRate : 'scrubbed (L = live)';
  return `${localDate(d)} ${localClock(d)} &nbsp;${tag}`;
}

let hudT = 0;
function updateHud(dt) {
  hudT += dt;
  if (hudT < 0.1) return;
  hudT = 0;
  const p = camera.position;
  const toVira = Math.hypot(p.x, p.z) / MILE, toTown = Math.hypot(p.x, p.z - TOWN_Z) / MILE;
  const mph = controls.vel.length() * 2.23694;
  const room = roomAt(p.x, p.z, p.y - 1.7);
  hud.innerHTML =
    `<b>LYRA // WORLD</b><br>` +
    `mode&nbsp; ${controls.mode === 'fly' ? 'FLY' : 'WALK'} &nbsp;×${controls.speedMul.toFixed(1)}<br>` +
    (room && p.y - 1.7 < walkHeight(p.x, p.z, p.y - 1.7) + 4 ? `<span style="color:#36e0ff">${room.name}</span><br>` : '') +
    `speed ${mph.toFixed(0)} mph<br>` +
    `alt&nbsp;&nbsp; ${(p.y - getHeight(p.x, p.z)).toFixed(0)} m<br>` +
    `Vira&nbsp; ${toVira.toFixed(1)} mi<br>` +
    `Saltbrush ${toTown.toFixed(1)} mi<br>` +
    `Halcyon ${(Math.hypot(p.x - HALCYON.x, p.z - HALCYON.z) / MILE).toFixed(1)} mi<br>` +
    `Ironwood ${(Math.hypot(p.x - IRONWOOD.x, p.z - IRONWOOD.z) / MILE).toFixed(1)} mi<br>` +
    `${DEATH_VALLEY.name}, Death Valley<br>` +
    `${clockText()}<br>` +
    `sun ${sunElev.toFixed(1)}° &nbsp;gate ${dc.gate.open || dc.gate.auto ? 'OPEN' : 'closed'}<br>` +
    `Vira staff: ${traffic.counts.onSite} on site &middot; ${traffic.counts.commuting} driving<br>` +
    `&nbsp;&nbsp;${people.counts.working} working outside or in the halls &middot; ${people.counts.walking} walking &middot; ${people.counts.inside} in the ops building`;
  followPanel.innerHTML = traffic.following ? traffic.describe(simMs) : people.describe(simMs);
  followPanel.classList.toggle('hidden', !traffic.following && !people.following);
  drawMinimap();
}

// ---------- loop ----------
document.getElementById('loading').remove();
window.world = {
  scene, renderer, camera, controls, pipe, traffic, people, halls, indoorFill,
  // jump the world clock to a Death Valley local hour today (for testing)
  setHour: (h) => {
    const parts = new Intl.DateTimeFormat('en-US', { timeZone: DEATH_VALLEY.tz, hour: 'numeric', minute: 'numeric', hourCycle: 'h23' }).formatToParts(new Date(simMs));
    const cur = +parts.find((x) => x.type === 'hour').value + +parts.find((x) => x.type === 'minute').value / 60;
    simMs += (h - cur) * 3600000; timeRate = 1; syncSky();
  },
};
world.setTime = (e) => { sunElev = e; updateSun(); };
const clock = new THREE.Clock();
let elapsed = 0, skyT = 0;
const drawSize = new THREE.Vector2();
renderer.setAnimationLoop(() => {
  // a page opened while hidden starts at 0 x 0 and may never get a resize event
  renderer.getSize(drawSize);
  if (drawSize.x !== innerWidth || drawSize.y !== innerHeight) fitToWindow();
  const dt = Math.min(clock.getDelta(), 0.1);
  elapsed += dt;
  const k = controls.keys;
  simMs += dt * 1000 * timeRate;
  if (k.has('BracketRight')) simMs += dt * 3600000 * 1.5; // hold to scrub 1.5 hours per second
  if (k.has('BracketLeft')) simMs -= dt * 3600000 * 1.5;
  skyT += dt;
  if (skyT > (timeRate > 1 || k.has('BracketRight') || k.has('BracketLeft') ? 0 : 1)) { skyT = 0; syncSky(); }

  dc.gate.auto = traffic.update(simMs, dt * timeRate);
  halls.update(camera.position);
  people.update(simMs, camera.position, halls.current);
  if (traffic.following || (people.following && people.chase(camera, dt))) {
    if (traffic.following) traffic.chase(camera, dt);
    // keep the free camera pointed the same way, so leaving follow mode doesn't jump
    const dir = camera.getWorldDirection(new THREE.Vector3());
    controls.yaw = Math.atan2(-dir.x, -dir.z); controls.pitch = Math.asin(dir.y);
    controls.vel.set(0, 0, 0);
  } else controls.update(dt);
  const p = camera.position;
  p.x = THREE.MathUtils.clamp(p.x, BOUNDS.X0 + 12000, BOUNDS.X1 - 12000);
  p.z = THREE.MathUtils.clamp(p.z, BOUNDS.Z0 + 12000, BOUNDS.Z1 - 12000);
  terrain.update(p);
  // cities draw only within range; past that they are lost in the haze anyway
  for (const [obj, x, z, range] of farCull) obj.visible = Math.hypot(p.x - x, p.z - z) < range;
  sky.position.copy(p);
  moonMesh.position.copy(p).addScaledVector(moonDir, 80000);
  moonMesh.lookAt(p);
  stars.position.copy(p);
  clouds.position.x = p.x; clouds.position.z = p.z;
  clouds.material.uniforms.camPos.value.copy(p);
  cloudUniforms.cloudTime.value = elapsed;
  pipe.grade.uniforms.time.value = elapsed % 100;
  camera.updateMatrixWorld();
  pipe.csm.update();
  brush.update(p);
  dc.update(dt, elapsed);
  updateInteriors(p, dt, elapsed);
  updateHud(dt);
  pipe.composer.render(dt);
});

function fitToWindow() {
  if (!innerWidth || !innerHeight) return;
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  pipe.resize(innerWidth, innerHeight);
}
addEventListener('resize', fitToWindow);
