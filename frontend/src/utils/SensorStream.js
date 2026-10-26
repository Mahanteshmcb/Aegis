// Sensor Data Stream using WebSocket
// Connects to backend EventEngine for real-time sensor evaluations

export class SensorStream {
  constructor(apiBase = 'http://localhost:8001') {
    this.apiBase = apiBase;
    this.socket = null;
    this.subscribers = [];
    this.zoneReadings = {};
    this.connected = false;
    this.sessionToken = null;
  }

  async login(credentials) {
    const response = await fetch(`${this.apiBase}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    
    if (response.ok) {
      const data = await response.json();
      this.sessionToken = data.access_token || data.session_token;
      this.connect();
      return true;
    }
    return false;
  }

  connect() {
    if (!this.sessionToken) return;
    if (this.socket) this.socket.close();
    
    this.socket = new WebSocket(
      `${this.apiBase}/api/v1/estate-config/ws/telemetry?session=${this.sessionToken}`
    );

    this.socket.onopen = () => {
      this.connected = true;
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };

    this.socket.onclose = () => {
      this.connected = false;
      // Attempt reconnect after delay
      setTimeout(() => this.connect(), 3000);
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(data) {
    const { type, zone, sensorType, value, timestamp, ruleId, severity } = data;
    
    // Initialize zone readings if needed
    if (!this.zoneReadings[zone]) {
      this.zoneReadings[zone] = {};
    }

    this.zoneReadings[zone][sensorType] = {
      value,
      timestamp: timestamp || new Date().toISOString(),
      sensorType,
      zone,
      ruleId,
      severity
    };

    // Notify all subscribers
    this.subscribers.forEach(cb => cb({
      type: 'sensor_update',
      data: this.zoneReadings[zone][sensorType]
    }));
    
    // Also update rover telemetry if present
    if (roverId && position) {
      this.subscribers.forEach(cb => cb({
        type: 'rover_update',
        roverId,
        position,
        batteryLevel
      }));
    }
  }

  subscribe(callback) {
    this.subscribers.push(callback);
    // Return unsubscribe function
    return () => {
      this.subscribers = this.subscribers.filter(cb => cb !== callback);
    };
  }

  // Fetch initial estate config and start monitoring
  async startMonitoring() {
    // Fetch estate config
    const cfgResponse = await fetch(`${this.apiBase}/api/v1/estate-config/status`);
    if (cfgResponse.ok) {
      const cfg = await cfgResponse.json();
      this.zoneReadings = cfg || {};
    }

    // Subscribe to ongoing updates
    return this.subscribe((update) => {
      this.onSensorUpdate(update);
    });
  }

  onSensorUpdate(update) {
    // Default handler - can be overridden
    console.log('Sensor update:', update);
  }

  // Evaluate a manual sensor reading
  async evaluateReading(sensorType, value, zone) {
    const response = await fetch(`${this.apiBase}/api/v1/ai/evaluate-reading`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.sessionToken ? { 'Authorization': `Bearer ${this.sessionToken}` } : {})
      },
      body: JSON.stringify({ sensorType, value, zone })
    });

    if (response.ok) {
      return await response.json();
    }
    return null;
  }

  getZoneReadings(zoneId) {
    return this.zoneReadings[zoneId] || {};
  }

  getAllReadings() {
    return this.zoneReadings;
  }
}