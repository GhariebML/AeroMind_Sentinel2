import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function AnimatedBackground() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // Setup scene
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x050b14, 0.0015);

    // Setup camera
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.y = 15;
    camera.position.z = 50;

    // Setup renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    mountRef.current.appendChild(renderer.domElement);

    // Create 3D Grid Floor
    const gridHelper = new THREE.GridHelper(200, 50, 0x00f0ff, 0x0088ff);
    gridHelper.position.y = -10;
    
    // Add glowing effect material to grid
    const material = gridHelper.material as THREE.Material;
    material.opacity = 0.3;
    material.transparent = true;
    scene.add(gridHelper);

    // Create moving particles (representing data flow / cars)
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 200;
    const posArray = new Float32Array(particlesCount * 3);
    const speeds = new Float32Array(particlesCount);

    for(let i = 0; i < particlesCount * 3; i+=3) {
      // X: spread across width
      posArray[i] = (Math.random() - 0.5) * 100;
      // Y: slightly above grid
      posArray[i+1] = -9 + Math.random() * 2;
      // Z: depth spread
      posArray[i+2] = (Math.random() - 0.5) * 200;
      
      // Speed
      speeds[i/3] = 0.5 + Math.random() * 2;
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

    // Cyan and emerald colors
    const particleMaterial = new THREE.PointsMaterial({
      size: 0.8,
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending
    });

    const particlesMesh = new THREE.Points(particlesGeometry, particleMaterial);
    scene.add(particlesMesh);

    // Animation Loop
    let animationId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Move grid towards camera
      gridHelper.position.z = (elapsedTime * 15) % 4;

      // Move particles towards camera
      const positions = particlesMesh.geometry.attributes.position.array as Float32Array;
      for(let i = 0; i < particlesCount; i++) {
        const idx = i * 3 + 2;
        positions[idx] += speeds[i];
        
        // Reset if too close
        if (positions[idx] > 50) {
          positions[idx] = -150;
        }
      }
      particlesMesh.geometry.attributes.position.needsUpdate = true;

      // Slight camera sway
      camera.position.x = Math.sin(elapsedTime * 0.2) * 5;

      renderer.render(scene, camera);
    };

    animate();

    // Handle Resize
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
      if (mountRef.current) {
        mountRef.current.removeChild(renderer.domElement);
      }
      geometry.dispose();
      material.dispose();
      particleMaterial.dispose();
      particlesGeometry.dispose();
    };
  }, []);

  return (
    <div 
      ref={mountRef} 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
        pointerEvents: 'none'
      }}
    />
  );
}
