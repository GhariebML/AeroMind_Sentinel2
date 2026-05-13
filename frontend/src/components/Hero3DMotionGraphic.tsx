import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function Hero3DMotionGraphic() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    // ── 1. Scene Setup ──
    const scene = new THREE.Scene();

    // Camera setup
    const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 4, 12);

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // ── 2. Lighting ──
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);

    const cyanLight = new THREE.PointLight(0x22d3ee, 8, 20);
    cyanLight.position.set(4, 5, 4);
    scene.add(cyanLight);

    const emeraldLight = new THREE.PointLight(0x10b981, 6, 20);
    emeraldLight.position.set(-4, -3, 2);
    scene.add(emeraldLight);

    // ── 3. Procedural Abstract Surveillance Core ──
    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Central Emissive Crystal Core
    const crystalGeo = new THREE.OctahedronGeometry(1.2, 0);
    const crystalMat = new THREE.MeshPhysicalMaterial({
      color: 0x0891b2,
      emissive: 0x06b6d4,
      emissiveIntensity: 0.8,
      roughness: 0.1,
      metalness: 0.9,
      transmission: 0.6,
      transparent: true,
      opacity: 0.9,
      wireframe: false,
    });
    const crystalMesh = new THREE.Mesh(crystalGeo, crystalMat);
    coreGroup.add(crystalMesh);

    // Inner glowing particle/wireframe overlay for the crystal
    const innerWireGeo = new THREE.OctahedronGeometry(1.25, 1);
    const innerWireMat = new THREE.MeshBasicMaterial({
      color: 0x34d399,
      wireframe: true,
      transparent: true,
      opacity: 0.3,
    });
    const innerWireMesh = new THREE.Mesh(innerWireGeo, innerWireMat);
    coreGroup.add(innerWireMesh);

    // Rotor/Gimbal Ring 1 (Inner Cyan)
    const ring1Geo = new THREE.TorusGeometry(2.2, 0.08, 16, 64);
    const ring1Mat = new THREE.MeshStandardMaterial({
      color: 0x22d3ee,
      emissive: 0x0891b2,
      emissiveIntensity: 0.5,
      metalness: 0.8,
      roughness: 0.2,
    });
    const ring1Mesh = new THREE.Mesh(ring1Geo, ring1Mat);
    ring1Mesh.rotation.x = Math.PI / 4;
    coreGroup.add(ring1Mesh);

    // Rotor/Gimbal Ring 2 (Outer Emerald)
    const ring2Geo = new THREE.TorusGeometry(3.0, 0.05, 16, 64);
    const ring2Mat = new THREE.MeshStandardMaterial({
      color: 0x10b981,
      emissive: 0x059669,
      emissiveIntensity: 0.6,
      metalness: 0.9,
      roughness: 0.1,
    });
    const ring2Mesh = new THREE.Mesh(ring2Geo, ring2Mat);
    ring2Mesh.rotation.y = Math.PI / 3;
    coreGroup.add(ring2Mesh);

    // Orbiting Satellites / Data Packets
    const satGroup = new THREE.Group();
    coreGroup.add(satGroup);

    const satGeo = new THREE.SphereGeometry(0.12, 16, 16);
    const satMat1 = new THREE.MeshBasicMaterial({ color: 0x67e8f9 });
    const satMat2 = new THREE.MeshBasicMaterial({ color: 0xa7f3d0 });

    const sat1 = new THREE.Mesh(satGeo, satMat1);
    sat1.position.set(3.8, 0, 0);
    satGroup.add(sat1);

    const sat2 = new THREE.Mesh(satGeo, satMat2);
    sat2.position.set(-3.8, 0, 0);
    satGroup.add(sat2);

    // ── 4. Ground Scanning Field Below ──
    const scanGroup = new THREE.Group();
    scanGroup.position.y = -3.5;
    scene.add(scanGroup);

    // Virtual target circular plane
    const floorGridGeo = new THREE.RingGeometry(0.5, 5, 32);
    const floorGridMat = new THREE.MeshBasicMaterial({
      color: 0x0e7490,
      wireframe: true,
      transparent: true,
      opacity: 0.15,
      side: THREE.DoubleSide,
    });
    const floorGridMesh = new THREE.Mesh(floorGridGeo, floorGridMat);
    floorGridMesh.rotation.x = Math.PI / 2;
    scanGroup.add(floorGridMesh);

    // Expanding Scanning Laser Rings
    const scanRingCount = 3;
    const scanRings: THREE.Mesh[] = [];
    const scanRingGeo = new THREE.TorusGeometry(1, 0.03, 8, 48);
    const scanRingMat = new THREE.MeshBasicMaterial({
      color: 0x34d399,
      transparent: true,
      opacity: 0.8,
    });

    for (let i = 0; i < scanRingCount; i += 1) {
      const sMesh = new THREE.Mesh(scanRingGeo, scanRingMat.clone());
      sMesh.rotation.x = Math.PI / 2;
      // Staggered scales
      const initialScale = 1 + i * 1.5;
      sMesh.scale.set(initialScale, initialScale, 1);
      scanGroup.add(sMesh);
      scanRings.push(sMesh);
    }

    // ── 5. Autonomous Animation Loop ──
    const clock = new THREE.Clock();
    let animationFrameId = 0;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Core group floating & tilting autonomously
      coreGroup.position.y = Math.sin(elapsed * 1.2) * 0.3;
      coreGroup.rotation.y = elapsed * 0.4;

      // Inner crystal spinning in reverse
      crystalMesh.rotation.y = -elapsed * 0.8;
      crystalMesh.rotation.x = elapsed * 0.3;
      innerWireMesh.rotation.y = -elapsed * 0.8;
      innerWireMesh.rotation.x = elapsed * 0.3;

      // Outer rings distinct continuous loops
      ring1Mesh.rotation.z = elapsed * 0.6;
      ring2Mesh.rotation.z = -elapsed * 0.4;

      // Satellites orbiting faster
      satGroup.rotation.z = elapsed * 1.5;
      satGroup.rotation.y = elapsed * 0.8;

      // Update scanning rings
      scanRings.forEach((ringMesh) => {
        const mat = ringMesh.material as THREE.MeshBasicMaterial;
        // Expand ring scale smoothly
        ringMesh.scale.x += 0.025;
        ringMesh.scale.y += 0.025;
        
        // Reset scale loop and fade out at boundary
        if (ringMesh.scale.x > 5.0) {
          ringMesh.scale.set(0.2, 0.2, 1);
          mat.opacity = 0.8;
        } else {
          // Fade opacity based on scale expansion
          mat.opacity = Math.max(0, 0.8 * (1 - ringMesh.scale.x / 5.0));
        }
      });

      // Smooth render
      renderer.render(scene, camera);
    };

    animate();

    // ── 6. Resize Observer Handling ──
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width && height) {
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
          renderer.setSize(width, height);
        }
      }
    });

    resizeObserver.observe(container);

    // ── 7. Comprehensive Lifecycle Cleanup ──
    return () => {
      cancelAnimationFrame(animationFrameId);
      resizeObserver.disconnect();
      if (container && renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }

      // Dispose resources
      crystalGeo.dispose();
      crystalMat.dispose();
      innerWireGeo.dispose();
      innerWireMat.dispose();
      ring1Geo.dispose();
      ring1Mat.dispose();
      ring2Geo.dispose();
      ring2Mat.dispose();
      satGeo.dispose();
      satMat1.dispose();
      satMat2.dispose();
      floorGridGeo.dispose();
      floorGridMat.dispose();
      scanRingGeo.dispose();
      scanRingMat.dispose();
      scanRings.forEach((r) => {
        (r.material as THREE.Material).dispose();
      });
      renderer.dispose();
    };
  }, []);

  return (
    <div className="relative w-full h-full min-h-[380px] flex items-center justify-center">
      {/* Target Canvas Container */}
      <div ref={containerRef} className="absolute inset-0 w-full h-full z-10" />

      {/* Decorative Cyber Grid Background details inside the container */}
      <div className="absolute inset-0 z-0 pointer-events-none rounded-[2rem] overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl" />
      </div>
    </div>
  );
}
