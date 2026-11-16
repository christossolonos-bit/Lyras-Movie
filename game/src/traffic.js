import * as THREE from 'three';
import { vehicleGeometry } from './props.js';
import { blob } from './textures.js';
import { mergeParts, part, globalUniforms } from './util.js';
import { buildStaff, stateAt, nextShift, crewName, CITY_NAMES } from './commute.js';
import { localClock } from './sun.js';

// Vira's staff cars: each one belongs to a person with a job, a shift and a house, and
// moves from the world clock: parked in the driveway, on the road at shift change, parked
// in the lot while they work. Any car can be followed with the camera.
const GATE = new THREE.Vector3(31, 0, -650);

export function buildTraffic(roster) {
  const staff = buildStaff(roster);
  const group = new THREE.Group();
  const kinds = {};
  for (const e of staff) (kinds[e.kind] ||= []).push(e);

  const paint = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.32, metalness: 0.55 });
  const glassMat = new THREE.MeshStandardMaterial({ color: '#1b2329', roughness: 0.06, metalness: 0.9 });
  const trimMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.6, metalness: 0.2 });
  const lampMat = new THREE.MeshBasicMaterial({ vertexColors: true, toneMapped: false });
  const shadowGeo = new THREE.PlaneGeometry(2.6, 5.6); shadowGeo.rotateX(-Math.PI / 2);
  const shadowMat = new THREE.MeshBasicMaterial({ map: blob(), transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4 });
  const meshes = [];
  for (const [kind, list] of Object.entries(kinds)) {
    const geo = vehicleGeometry(kind);
    // head and tail lamps, shown only while driving after dark
    const front = Math.max(...Array.from({ length: geo.body.attributes.position.count }, (_, i) => geo.body.attributes.position.getZ(i)));
    const back = Math.min(...Array.from({ length: geo.body.attributes.position.count }, (_, i) => geo.body.attributes.position.getZ(i)));
    const lamps = mergeParts([-0.6, 0.6].flatMap((x) => [
      part(new THREE.BoxGeometry(0.42, 0.14, 0.05), '#fff6e0', x, 0.78, front + 0.03),
      part(new THREE.BoxGeometry(0.36, 0.14, 0.05), '#ff2010', x, 0.86, back - 0.03),
    ]));
    const mk = (g, m, cast) => {
      const im = new THREE.InstancedMesh(g, m, list.length);
      im.frustumCulled = false; im.castShadow = cast; im.receiveShadow = true;
      im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      group.add(im);
      return im;
    };
    const body = mk(geo.body, paint, true), glass = mk(geo.glass, glassMat, true), trim = mk(geo.trim, trimMat, true);
    const lamp = mk(lamps, lampMat, false), shadow = mk(shadowGeo, shadowMat, false);
    shadow.renderOrder = 2;
    list.forEach((e, i) => { body.setColorAt(i, new THREE.Color(e.color)); e.slot = i; e.parts = [body, glass, trim, lamp, shadow]; });
    meshes.push(body, glass, trim, lamp, shadow);
  }

  const pose = { x: 0, y: 0, z: 0, hx: 0, hz: 1, speed: 0 };
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0), one = new THREE.Vector3(1, 1, 1), zero = new THREE.Matrix4().makeScale(0, 0, 0), v = new THREE.Vector3();
  for (const e of staff) {
    e.parkHome = e.routeHome.at(e.routeHome.duration, { ...pose });
    e.parkWork = e.route.at(e.route.duration, { ...pose });
    e.heading = Math.atan2(e.parkHome.hx, e.parkHome.hz);
    e.pos = new THREE.Vector3();
  }

  let following = null;
  const counts = { onSite: 0, commuting: 0, home: 0 };

  function update(t, dt) {
    const night = globalUniforms.night.value > 0.25;
    counts.onSite = counts.commuting = counts.home = 0;
    let nearGate = false;
    for (const e of staff) {
      const st = stateAt(e, t);
      e.state = st;
      let p;
      if (st.mode === 'toWork') p = e.route.at(st.tau, pose);
      else if (st.mode === 'toHome') p = e.routeHome.at(st.tau, pose);
      else p = st.mode === 'work' ? e.parkWork : e.parkHome;
      const moving = st.mode === 'toWork' || st.mode === 'toHome';
      counts[moving ? 'commuting' : st.mode === 'work' ? 'onSite' : 'home']++;
      const target = Math.atan2(p.hx, p.hz);
      if (moving && dt < 0.5) {
        let dh = target - e.heading;
        dh = Math.atan2(Math.sin(dh), Math.cos(dh));
        e.heading += dh * (1 - Math.exp(-dt * 6));
      } else e.heading = target;
      e.pos.set(p.x, p.y, p.z);
      e.speed = moving ? p.speed : 0;
      if (moving && e.pos.distanceToSquared(GATE) < 60 * 60) nearGate = true;
      q.setFromAxisAngle(up, e.heading);
      m4.compose(e.pos, q, one);
      const [body, glass, trim, lamp, shadow] = e.parts;
      body.setMatrixAt(e.slot, m4); glass.setMatrixAt(e.slot, m4); trim.setMatrixAt(e.slot, m4); shadow.setMatrixAt(e.slot, m4);
      lamp.setMatrixAt(e.slot, moving && night ? m4 : zero);
    }
    for (const m of meshes) m.instanceMatrix.needsUpdate = true;
    return nearGate;
  }

  // ---------- follow camera ----------
  const order = () => staff.filter((e) => e.state && (e.state.mode === 'toWork' || e.state.mode === 'toHome'));
  function followNext() {
    const moving = order();
    const pool = moving.length ? moving : staff;
    const i = following ? pool.indexOf(following) : -1;
    following = pool[(i + 1) % pool.length];
    return following;
  }
  function followNearest(p) {
    let best = null, bd = Infinity;
    for (const e of staff) { const d = e.pos.distanceToSquared(p); if (d < bd) { bd = d; best = e; } }
    following = best;
    return following;
  }
  const camPos = new THREE.Vector3(), camLook = new THREE.Vector3();
  function chase(camera, dt) {
    if (!following) return false;
    const e = following, fx = Math.sin(e.heading), fz = Math.cos(e.heading);
    const back = e.speed > 15 ? 13 : 9, high = e.speed > 15 ? 4.2 : 3.4;
    v.set(e.pos.x - fx * back, e.pos.y + high, e.pos.z - fz * back);
    const k = dt > 0.5 ? 1 : 1 - Math.exp(-dt * 5);
    if (camPos.distanceTo(v) > 400) camPos.copy(v); else camPos.lerp(v, k);
    camLook.set(e.pos.x + fx * 6, e.pos.y + 1.2, e.pos.z + fz * 6);
    camera.position.copy(camPos);
    camera.lookAt(camLook);
    return true;
  }
  function describe(t) {
    if (!following) return '';
    const e = following, st = e.state || stateAt(e, t);
    const mins = (ms) => `${Math.max(1, Math.round(ms / 60000))} min`;
    const doing = {
      toWork: `Driving to Vira &middot; arrives in ${mins(st.eta)}`,
      toHome: `Driving home to ${CITY_NAMES[e.city]} &middot; ${mins(st.eta)} to go`,
      work: `At work &middot; shift ends ${localClock(new Date(st.shift?.end || t))}`,
      home: (() => { const n = nextShift(e, t); return n ? `At home &middot; next shift ${localClock(new Date(n.start))}` : 'At home'; })(),
    }[st.mode];
    const crew = crewName(e);
    return `<b>FOLLOWING</b><br>${e.name}${e.age ? `, ${e.age}` : ''}<br>${e.title || e.role}${crew ? ` &middot; ${crew}` : ''}<br>` +
      `Lives in ${CITY_NAMES[e.city]}<br>${doing}<br>${e.speed > 0 ? Math.round(e.speed * 2.237) + ' mph' : 'parked'}`;
  }

  return {
    group, staff, counts, update, followNext, followNearest, chase, describe,
    get following() { return following; },
    unfollow() { following = null; },
  };
}
