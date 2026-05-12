import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function AnimatedBackground() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return undefined;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x020617, 0.012);

    const camera = new THREE.PerspectiveCamera(68, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 18, 58);
    camera.lookAt(0, -8, -20);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.6));
    renderer.setSize(window.innerWidth, window.innerHeight);
    mount.appendChild(renderer.domElement);

    const grid = new THREE.GridHelper(260, 72, 0x22d3ee, 0x1d4ed8);
    grid.position.y = -12;
    const gridMaterial = grid.material as THREE.Material;
    gridMaterial.transparent = true;
    gridMaterial.opacity = 0.25;
    scene.add(grid);

    const roadGeometry = new THREE.PlaneGeometry(34, 220, 1, 1);
    const roadMaterial = new THREE.MeshBasicMaterial({ color: 0x07111f, transparent: true, opacity: 0.48, side: THREE.DoubleSide });
    const road = new THREE.Mesh(roadGeometry, roadMaterial);
    road.rotation.x = Math.PI / 2;
    road.position.y = -11.6;
    road.position.z = -34;
    scene.add(road);

    const particleCount = 180;
    const positions = new Float32Array(particleCount * 3);
    const speeds = new Float32Array(particleCount);
    for (let i = 0; i < particleCount; i += 1) {
      positions[i * 3] = (Math.random() - 0.5) * 130;
      positions[i * 3 + 1] = -8 + Math.random() * 30;
      positions[i * 3 + 2] = -160 + Math.random() * 220;
      speeds[i] = 0.25 + Math.random() * 0.85;
    }
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMaterial = new THREE.PointsMaterial({ size: 0.65, color: 0x22d3ee, transparent: true, opacity: 0.72, blending: THREE.AdditiveBlending });
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    const clock = new THREE.Clock();
    let animationId = 0;

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();
      grid.position.z = (elapsed * 12) % 8;
      road.position.z = -34 + Math.sin(elapsed * 0.5) * 2;
      camera.position.x = Math.sin(elapsed * 0.18) * 4;
      const pos = particleGeometry.attributes.position.array as Float32Array;
      for (let i = 0; i < particleCount; i += 1) {
        const z = i * 3 + 2;
        pos[z] += speeds[i];
        if (pos[z] > 70) pos[z] = -160;
      }
      particleGeometry.attributes.position.needsUpdate = true;
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
      mount.removeChild(renderer.domElement);
      grid.geometry.dispose();
      gridMaterial.dispose();
      roadGeometry.dispose();
      roadMaterial.dispose();
      particleGeometry.dispose();
      particleMaterial.dispose();
      renderer.dispose();
    };
  }, []);

  return <div ref={mountRef} className="pointer-events-none fixed inset-0 z-0 opacity-80" aria-hidden="true" />;
}
