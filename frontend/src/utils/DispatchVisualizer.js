// Dispatch Event Visualizer
// Shows visual effects when autonomous events trigger dispatches

export class DispatchVisualizer {
  constructor(scene) {
    this.scene = scene;
    this.dispatchHistory = [];
    this.maxHistory = 10;
    
    // Create a sparkle material for dispatch effects
    const sparkGeo = new THREE.SphereGeometry(1, 12, 12);
    const sparkMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    this.sparkMesh = new THREE.Mesh(sparkGeo, sparkMat);
    this.sparkMesh.visible = false;
    scene.add(this.sparkMesh);
    
    // Trail effect meshes
    this.trailMeshes = [];
  }

  // Add a dispatch event to the visualization
  addDispatch(event) {
    const { zone, ruleId, severity, value, timestamp } = event;
    
    // Add to history
    this.dispatchHistory.unshift({ zone, ruleId, severity, value, timestamp });
    if (this.dispatchHistory.length > this.maxHistory) {
      this.dispatchHistory.pop();
    }
    
    // Create visual effect at zone position
    this.createSparkEffect(zone, severity);
    
    // Update stats display (could connect to DOM)
    this.updateStats();
  }

  createSparkEffect(zoneId, severity) {
    // Determine spark color and intensity by severity
    const severityColors = {
      high: { color: 0xff0000, intensity: 1.5 },
      medium: { color: 0xffa500, intensity: 1.0 },
      low: { color: 0xffff00, intensity: 0.5 },
      normal: { color: 0x00ff00, intensity: 0.3 }
    };
    
    const s = severityColors[severity] || severityColors.normal;
    
    // Position spark at zone center
    const zonePositions = {
      zone_alpha: { x: 0, z: 0 },
      zone_beta: { x: 100, z: 0 }
    };
    
    const pos = zonePositions[zoneId] || { x: 0, z: 0 };
    
    this.sparkMesh.position.set(pos.x, 3, pos.z);
    this.sparkMesh.material.color.setHex(s.color);
    this.sparkMesh.material.opacity = 0.8;
    this.sparkMesh.visible = true;
    
    // Scale based on intensity
    this.sparkMesh.scale.set(s.intensity, s.intensity, s.intensity);
    
    // Animate fade out
    const startTime = performance.now();
    const fadeDuration = 2000; // 2 seconds
    
    const animate = () => {
      const elapsed = performance.now() - startTime;
      const progress = Math.min(elapsed / fadeDuration, 1);
      
      // Fade out
      this.sparkMesh.material.opacity = 0.8 * (1 - progress);
      this.sparkMesh.scale.set(
        s.intensity * (1 - progress),
        s.intensity * (1 - progress),
        s.intensity * (1 - progress)
      );
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        this.sparkMesh.visible = false;
      }
    };
    
    requestAnimationFrame(animate);
  }

  // Update dispatch statistics
  updateStats() {
    const stats = {
      total: this.dispatchHistory.length,
      bySeverity: { high: 0, medium: 0, low: 0, normal: 0 },
      byZone: { zone_alpha: 0, zone_beta: 0 }
    };
    
    this.dispatchHistory.forEach(d => {
      if (stats.bySeverity[d.severity]) stats.bySeverity[d.severity]++;
      if (stats.byZone[d.zone]) stats.byZone[d.zone]++;
    });
    
    return stats;
  }

  // Get dispatch history
  getHistory() {
    return this.dispatchHistory;
  }

  // Clear history
  clear() {
    this.dispatchHistory = [];
    this.trailMeshes = [];
    this.sparkMesh.visible = false;
  }
}