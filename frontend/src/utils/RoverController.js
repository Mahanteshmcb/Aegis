// Rover Navigation Controller
// Handles rover movement between zones based on tasks

export class RoverController {
  constructor(scene, visualizer) {
    this.scene = scene;
    this.visualizer = visualizer;
    
    // Rover mesh
    this.mesh = new THREE.Mesh(
      new THREE.BoxGeometry(8, 8, 8),
      new THREE.MeshStandardMaterial({ color: 0xff0000 })
    );
    this.mesh.position.set(0, 5, 0);
    scene.add(this.mesh);
    
    // Movement state
    this.targetPos = new THREE.Vector3(0, 5, 0);
    this.currentPos = new THREE.Vector3(0, 5, 0);
    this.isMoving = false;
    this.speed = 3; // units per second
    this.path = [];
    this.waypointIndex = 0;
    this.task = null;
  }

  // Set target zone by zone ID
  setTargetZone(zoneId, zoneConfigs) {
    const zone = zoneConfigs?.find(z => z.zone_id === zoneId);
    if (!zone) {
      console.error(`Zone ${zoneId} not found in configs`);
      return;
    }
    
    const x = zone.coordinates?.x || 0;
    const z = zone.coordinates?.y || 0;
    
    this.targetPos.set(x, 5, z);
    this.isMoving = true;
    this.waypointIndex = 0;
    this.path = [this.mesh.position.clone(), this.targetPos.clone()];
    this.task = null;
    
    console.log(`Rover navigating to zone: ${zoneId} at (${x}, ${z})`);
  }

  // Set target from task object
  receiveTask(task) {
    this.task = task;
    const zoneId = task?.zone || 'zone_alpha';
    // Get zone configs from visualizer or external source
    // For now, use simple coordinate mapping
    const zoneMap = {
      zone_alpha: { x: 0, z: 0 },
      zone_beta: { x: 100, z: 0 }
    };
    
    const coords = zoneMap[zoneId] || { x: 0, z: 0 };
    this.setTargetZone(zoneId, [{ zone_id: zoneId, coordinates: { x: coords.x, y: coords.z } }]);
  }

  // Update rover position each frame
  update(deltaTime) {
    if (!this.isMoving) return;
    
    // Move towards target
    const dir = new THREE.Vector3()
      .subVectors(this.targetPos, this.mesh.position)
      .normalize();
    
    this.mesh.position.x += dir.x * this.speed * deltaTime;
    this.mesh.position.z += dir.z * this.speed * deltaTime;
    
    // Check distance to target
    const distance = this.mesh.position.distanceTo(this.targetPos);
    
    if (distance < 2.0) {
      this.mesh.position.copy(this.targetPos);
      this.isMoving = false;
      console.log(`Rover arrived at zone targeting (${this.targetPos.x}, ${this.targetPos.z})`);
      
      if (this.task) {
        this.task.status = 'completed';
        this.task.completedAt = new Date().toISOString();
        console.log(`Task "${this.task.title}" completed`);
      }
    }
  }

  // Get current rover status
  getStatus() {
    return {
      position: {
        x: this.mesh.position.x.toFixed(2),
        y: this.mesh.position.y,
        z: this.mesh.position.z.toFixed(2)
      },
      isMoving: this.isMoving,
      targetZone: this.targetPos,
      currentTask: this.task?.title || 'none'
    };
  }

  // Stop rover movement
  stop() {
    this.isMoving = false;
    this.path = [];
    this.waypointIndex = 0;
  }
}