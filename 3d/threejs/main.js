import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0f14);

const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(22, 16, 22);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

scene.add(new THREE.AmbientLight(0xffffff, 0.5));
const dir = new THREE.DirectionalLight(0xffffff, 0.9);
dir.position.set(10, 20, 15);
scene.add(dir);

function box(w, h, d, color, x, y, z) {
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(w, h, d),
    new THREE.MeshStandardMaterial({ color, metalness: 0.2, roughness: 0.45 })
  );
  mesh.position.set(x, y, z);
  scene.add(mesh);
  return mesh;
}

box(20, 1, 14, 0x666666, 0, 0, 0);      // substrate
// Layer-2 bottom memory rings
box(15.8, 2.0, 1.2, 0x2ca25f, 0, 1.3, -5.1); // HBM ring bottom segment
box(15.8, 2.0, 1.2, 0x2ca25f, 0, 1.3,  5.1); // HBM ring top segment
box(1.2, 2.0, 8.8, 0x2ca25f, -7.3, 1.3, 0);  // HBM left
box(1.2, 2.0, 8.8, 0x2ca25f,  7.3, 1.3, 0);  // HBM right

// Layer-2 outer HBF rectangular ring
box(18.8, 2.3, 1.0, 0xf16913, 0, 1.3, -6.6); // bottom
box(18.8, 2.3, 1.0, 0xf16913, 0, 1.3,  6.6); // top
box(1.0, 2.3, 11.2, 0xf16913, -8.9, 1.3, 0); // left
box(1.0, 2.3, 11.2, 0xf16913,  8.9, 1.3, 0); // right

// Bridge and Layer-1 top compute
box(14.6, 0.2, 9.6, 0x8f6b32, 0, 2.5, 0); // bridge slab
box(14, 1, 9, 0x3c78d8, 0, 3.2, 0);       // Layer-1 compute die (top)

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
