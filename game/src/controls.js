import * as THREE from 'three';

// Fly / walk camera. Click to capture the mouse, WASD to move.
// getHeight(x, z, feetY) gives the walkable floor; feetY lets stacked interior floors resolve.
export class Controls {
  constructor(camera, dom, getHeight) {
    this.camera = camera; this.dom = dom; this.getHeight = getHeight;
    this.yaw = 0; this.pitch = 0;
    this.keys = new Set();
    this.mode = 'fly';
    this.speedMul = 1;
    this.vel = new THREE.Vector3();
    this.onKey = () => {};
    camera.rotation.order = 'YXZ';

    dom.addEventListener('click', () => dom.requestPointerLock());
    document.addEventListener('mousemove', (e) => {
      if (document.pointerLockElement !== dom) return;
      this.yaw -= e.movementX * 0.0022;
      this.pitch = THREE.MathUtils.clamp(this.pitch - e.movementY * 0.0022, -1.55, 1.55);
    });
    addEventListener('keydown', (e) => {
      if (e.repeat) return;
      this.keys.add(e.code);
      if (e.code === 'KeyF') this.mode = this.mode === 'fly' ? 'walk' : 'fly';
      this.onKey(e.code);
    });
    addEventListener('keyup', (e) => this.keys.delete(e.code));
    addEventListener('blur', () => this.keys.clear());
    addEventListener('wheel', (e) => { this.speedMul = THREE.MathUtils.clamp(this.speedMul * (e.deltaY < 0 ? 1.2 : 1 / 1.2), 0.1, 30); });
  }

  place(pos, target) {
    this.camera.position.copy(pos);
    const d = target.clone().sub(pos).normalize();
    this.yaw = Math.atan2(-d.x, -d.z);
    this.pitch = Math.asin(d.y);
    this.vel.set(0, 0, 0);
  }

  update(dt) {
    const k = this.keys, cam = this.camera;
    const walk = this.mode === 'walk';
    const cp = Math.cos(this.pitch);
    const fwd = walk ? new THREE.Vector3(-Math.sin(this.yaw), 0, -Math.cos(this.yaw))
      : new THREE.Vector3(-Math.sin(this.yaw) * cp, Math.sin(this.pitch), -Math.cos(this.yaw) * cp);
    const right = new THREE.Vector3(Math.cos(this.yaw), 0, -Math.sin(this.yaw));
    const want = new THREE.Vector3();
    if (k.has('KeyW') || k.has('ArrowUp')) want.add(fwd);
    if (k.has('KeyS') || k.has('ArrowDown')) want.sub(fwd);
    if (k.has('KeyD') || k.has('ArrowRight')) want.add(right);
    if (k.has('KeyA') || k.has('ArrowLeft')) want.sub(right);
    if (!walk && k.has('Space')) want.y += 1;
    if (!walk && (k.has('KeyC') || k.has('ControlLeft'))) want.y -= 1;
    if (want.lengthSq() > 0) want.normalize();
    const boost = k.has('ShiftLeft') || k.has('ShiftRight');
    const speed = (walk ? (boost ? 14 : 5) : (boost ? 450 : 60)) * this.speedMul;
    this.vel.lerp(want.multiplyScalar(speed), 1 - Math.exp(-dt * 6));
    cam.position.addScaledVector(this.vel, dt);

    const ground = this.getHeight(cam.position.x, cam.position.z, cam.position.y - 1.7);
    if (walk) cam.position.y = ground + 1.7;
    else cam.position.y = Math.max(cam.position.y, ground + 1.5);

    cam.rotation.y = this.yaw;
    cam.rotation.x = this.pitch;
  }
}
