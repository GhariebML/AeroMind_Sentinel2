import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.150.1/build/three.module.js';

export function initThreeJS() {
    const container = document.getElementById('hero-3d-canvas');
    if (!container) return;

    // Setup scene, camera, renderer
    const scene = new THREE.Scene();
    
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 5, 20);
    
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // ─── Cyber-Physical Grid ───
    const gridSize = 60;
    const gridDivisions = 30;
    const gridHelper = new THREE.GridHelper(gridSize, gridDivisions, 0x00e5ff, 0x00e5ff);
    gridHelper.material.opacity = 0.2;
    gridHelper.material.transparent = true;
    gridHelper.position.y = -2;
    scene.add(gridHelper);

    // ─── Glowing Particles (Data Points) ───
    const particleCount = 200;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const velocities = [];

    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 40;
        positions[i * 3 + 1] = Math.random() * 10 - 2;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 40;
        
        velocities.push({
            y: Math.random() * 0.02 + 0.01
        });
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
        color: 0x00e5ff,
        size: 0.15,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // ─── Center "Drone" abstract representation ───
    const coreGeo = new THREE.OctahedronGeometry(0.8, 0);
    const coreMat = new THREE.MeshBasicMaterial({ 
        color: 0x00d68f, 
        wireframe: true,
        transparent: true,
        opacity: 0.8
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    coreMesh.position.y = 2;
    scene.add(coreMesh);

    // Outer ring
    const ringGeo = new THREE.TorusGeometry(1.5, 0.05, 16, 100);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff, transparent: true, opacity: 0.5 });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.position.y = 2;
    ringMesh.rotation.x = Math.PI / 2;
    scene.add(ringMesh);

    // ─── Animation Loop ───
    const clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);
        const elapsedTime = clock.getElapsedTime();

        // Rotate center object
        coreMesh.rotation.y += 0.01;
        coreMesh.rotation.x += 0.005;
        
        ringMesh.rotation.z -= 0.005;
        
        // Bobbing motion
        coreMesh.position.y = 2 + Math.sin(elapsedTime * 2) * 0.2;
        ringMesh.position.y = 2 + Math.sin(elapsedTime * 2) * 0.2;

        // Move particles
        const posAttribute = geometry.getAttribute('position');
        for (let i = 0; i < particleCount; i++) {
            let y = posAttribute.getY(i);
            y += velocities[i].y;
            
            if (y > 10) {
                y = -2;
            }
            posAttribute.setY(i, y);
        }
        posAttribute.needsUpdate = true;

        // Subtle camera movement
        camera.position.x = Math.sin(elapsedTime * 0.2) * 5;
        camera.lookAt(0, 2, 0);

        renderer.render(scene, camera);
    }

    animate();

    // ─── Handle Resize ───
    window.addEventListener('resize', () => {
        if (!container) return;
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
}
