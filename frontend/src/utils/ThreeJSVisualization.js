// Three.js Zone Visualization for Aegis Dashboard
import * as THREE from 'three';

export class ZoneVisualizer {
  constructor(containerRef) {
    this.container = containerRef;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(
      75,
      this.container.clientWidth / (this.container.clientHeight || 1),
      0.1,
      1000
    );
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.zones = [];
    this.sensors = [];
    this.rover = null;
    this.ws = null;
    this.animateId = null;
    
    if (this.container) {
      this.container.style.width = '100%';
      this.container.style.height = '400px';
      this.container.style.background = '#1a1a2e';
    }
  }
  
  // WebSocket management
  connectWS(endpoint = '/api/v1/estate-config/ws/telemetry') {
    this.ws = new WebSocket(endpoint);
    this.ws.onopen = () => console.log('WebSocket connected');
    this.ws.onmessage = (event) => this.handleTelemetry(event.data);
    this.ws.onerror = (error) => console.error('WebSocket error:', error);
    this.ws.onclose = () => console.log('WebSocket disconnected');
  }
  
  disconnectWS() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  handleTelemetry(data) {
    if (!data) return;
    // Handle different data types
    if (data.type === 'sensor_reading') {
      this.updateSensor(data.sensor_id, data.value, data.status);
    } else if (data.type === 'rover_update') {
      this.updateRoverPosition(data.id, data.position);
      if (data.battery_level !== undefined) this.updateRoverBattery(data.id, data.battery_level);
    } else if (data.type === 'zone_update') {
      this.loadConfig(data.config);
    }
  }
  
  // ... rest of the class stays the same

  init() {
    this.setupRenderer();
    this.setupCamera();
    this.createLights();
    this.createAxes();
    this.animate();
  }

  setupRenderer() {
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    if (this.container) {
      this.container.innerHTML = '';
      this.container.appendChild(this.renderer.domElement);
    }
    window.addEventListener('resize', () => {
      this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    });
  }

  setupCamera() {
    this.camera.position.z = 50;
    this.camera.position.y = 20;
    this.camera.lookAt(0, 0, 0);
  }

  createLights() {
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(50, 50, 50);
    this.scene.add(dirLight);
    this.scene.add(new THREE.HemisphereLight(0x87ceeb, 0xffe5b4, 0.5));
  }

  createAxes() {
    this.scene.add(new THREE.AxesHelper(20));
  }

  loadConfig(config) {
    if (this.zones.length > 0) {
      this.zones.forEach(z => this.scene.remove(z.mesh));
      this.zones = [];
      this.sensors = [];
    }

    if (!config?.zones) return;

    config.zones.forEach((zone, i) => {
      const w = zone.coordinates.width || 100;
      const d = zone.coordinates.depth || 100;
      const geometry = new THREE.BoxGeometry(w, 1, d);
      const color = zone.zone_id === 'zone_alpha' ? 0x00ff00 : 0x0000ff;
      const material = new THREE.MeshStandardMaterial({
        color, opacity: 0.3, transparent: true, side: THREE.DoubleSide
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(
        zone.coordinates.x || (i * 100),
        0.5,
        zone.coordinates.y || 0
      );
      this.scene.add(mesh);
      this.zones.push({
        mesh, zoneId: zone.zone_id, name: zone.name || `Zone ${zone.zone_id}`,
        sensors: zone.sensors || []
      });
    });

    // Create rover at origin
    this.createRover({ id: 'rover_1' });

    // Create sensors
    config.zones.forEach(z => this.createZoneSensors(z));
  }

  createRover(cfg) {
    if (this.rover?.mesh) this.scene.remove(this.rover.mesh);
    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(8, 8, 8),
      new THREE.MeshStandardMaterial({ color: 0xff0000 })
    );
    mesh.position.set(cfg.position?.x || 0, 5, cfg.position?.y || 0);
    this.scene.add(mesh);
    this.rover = { mesh, id: cfg.id, isMoving: false, path: [], cwp: 0 };
  }

  moveRover(dt = 0.1) {
    if (!this.rover || !this.rover.isMoving || this.rover.cwp >= this.rover.path.length) return;
    const wp = this.rover.path[this.rover.cwp];
    const cur = this.rover.mesh.position;
    const dir = new THREE.Vector3().subVectors(wp, cur).normalize();
    cur.x += dir.x * this.rover.speed * dt;
    cur.z += dir.z * this.rover.speed * dt;
    const wp2 = this.rover.path[this.rover.cwp];
    if (cur.distanceTo(wp2) < 1.0) {
      this.rover.cwp++;
      if (this.rover.cwp >= this.rover.path.length) this.rover.isMoving = false;
    }
  }

  animate() {
    this.moveRover();
    this.renderer.render(this.scene, this.camera);
    this.animateId = requestAnimationFrame(() => this.animate());
  }

  updateSensor(sensorId, value, status) {
    const s = this.sensors.find(s => s.sensorId === sensorId);
    if (s) {
      s.value = value;
      s.status = status;
      const colors = { normal: 0x00ff00, critical: 0xff0000, warning: 0xffa500 };
      s.mesh.material.color.setHex(colors[status] || 0x00ff00);
    }
  }
}