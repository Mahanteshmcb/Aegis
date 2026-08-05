import React, { useState, useEffect } from 'react';
import { Play, Square, RotateCw, Navigation2, Zap, AlertTriangle, Send } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// Real-time Robot Control Panel
export function RobotControl({ robot, token }) {
  const [status, setStatus] = useState(robot.status);
  const [battery, setBattery] = useState(robot.battery);
  const [targetX, setTargetX] = useState(0);
  const [targetY, setTargetY] = useState(0);
  const [targetZ, setTargetZ] = useState(0);
  const [isMoving, setIsMoving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Simulate battery drain
    const interval = setInterval(() => {
      setBattery(prev => Math.max(0, prev - 0.5));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const sendCommand = async (command) => {
    try {
      setError(null);
      const response = await fetch(`${API_URL}/api/v1/robots/${robot.id}/command`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          command: command,
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) throw new Error('Command failed');
      const data = await response.json();
      console.log('Command sent:', data);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 3000);
    }
  };

  const handleStartMovement = async () => {
    setIsMoving(true);
    await sendCommand({
      type: 'move',
      target: { x: targetX, y: targetY, z: targetZ },
    });
    setStatus('moving');
  };

  const handleStop = async () => {
    setIsMoving(false);
    await sendCommand({ type: 'stop' });
    setStatus('idle');
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white">{robot.name}</h3>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${
          status === 'idle' ? 'bg-green-900 text-green-300' :
          status === 'moving' ? 'bg-blue-900 text-blue-300' :
          'bg-red-900 text-red-300'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            status === 'idle' ? 'bg-green-400' :
            status === 'moving' ? 'bg-blue-400' :
            'bg-red-400'
          } animate-pulse`} />
          {status.toUpperCase()}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="flex gap-2 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
          <AlertTriangle size={16} className="flex-shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {/* Battery Status */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-slate-400">Battery</p>
          <p className="text-sm font-semibold text-white">{battery.toFixed(1)}%</p>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all ${
              battery > 50 ? 'bg-green-500' :
              battery > 20 ? 'bg-yellow-500' :
              'bg-red-500'
            }`}
            style={{ width: `${battery}%` }}
          />
        </div>
      </div>

      {/* Movement Controls */}
      <div>
        <p className="text-sm font-semibold text-white mb-3">Movement Controls</p>
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">X (m)</label>
            <input
              type="number"
              value={targetX}
              onChange={(e) => setTargetX(parseFloat(e.target.value))}
              className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
              disabled={isMoving}
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Y (m)</label>
            <input
              type="number"
              value={targetY}
              onChange={(e) => setTargetY(parseFloat(e.target.value))}
              className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
              disabled={isMoving}
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Z (m)</label>
            <input
              type="number"
              value={targetZ}
              onChange={(e) => setTargetZ(parseFloat(e.target.value))}
              className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
              disabled={isMoving}
            />
          </div>
        </div>

        {/* D-Pad Style Controls */}
        <div className="flex justify-center gap-2 mb-4">
          <button
            onClick={() => setTargetX(targetX - 1)}
            className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-slate-300"
            disabled={isMoving}
            title="Move Left"
          >
            ◀
          </button>
          <div className="flex flex-col gap-2">
            <button
              onClick={() => setTargetY(targetY + 1)}
              className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-slate-300"
              disabled={isMoving}
              title="Move Forward"
            >
              ▲
            </button>
            <button
              onClick={() => setTargetY(targetY - 1)}
              className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-slate-300"
              disabled={isMoving}
              title="Move Backward"
            >
              ▼
            </button>
          </div>
          <button
            onClick={() => setTargetX(targetX + 1)}
            className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-slate-300"
            disabled={isMoving}
            title="Move Right"
          >
            ▶
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleStartMovement}
            disabled={isMoving}
            className="flex-1 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-green-900 text-white px-4 py-2 rounded-lg transition-colors font-semibold"
          >
            <Play size={16} />
            Move
          </button>
          <button
            onClick={handleStop}
            disabled={!isMoving}
            className="flex-1 flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 disabled:bg-red-900 text-white px-4 py-2 rounded-lg transition-colors font-semibold"
          >
            <Square size={16} />
            Stop
          </button>
        </div>
      </div>

      {/* Task Information */}
      <div className="pt-4 border-t border-slate-700">
        <p className="text-sm text-slate-400 mb-2">Active Tasks: {robot.active_tasks}</p>
        <div className="space-y-1 text-xs text-slate-400">
          <p>Type: {robot.type}</p>
          <p>Zone: {robot.zone}</p>
          <p>Last Update: Now</p>
        </div>
      </div>
    </div>
  );
}

// Zone Control Panel
export function ZoneControl({ zone, token }) {
  const [securityLevel, setSecurityLevel] = useState(zone.security_level);
  const [isArmed, setIsArmed] = useState(zone.is_armed);
  const [accessLevel, setAccessLevel] = useState('restricted');
  const [error, setError] = useState(null);

  const updateZoneSecurity = async (level) => {
    try {
      setError(null);
      const response = await fetch(`${API_URL}/api/v1/zones/${zone.id}/security`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ security_level: level }),
      });

      if (!response.ok) throw new Error('Update failed');
      setSecurityLevel(level);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 3000);
    }
  };

  const toggleArming = async () => {
    try {
      setError(null);
      const response = await fetch(`${API_URL}/api/v1/zones/${zone.id}/arm`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ armed: !isArmed }),
      });

      if (!response.ok) throw new Error('Arming failed');
      setIsArmed(!isArmed);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 3000);
    }
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white">{zone.name}</h3>
        <button
          onClick={toggleArming}
          className={`px-4 py-2 rounded-lg font-semibold transition-all ${
            isArmed
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-green-600 hover:bg-green-700 text-white'
          }`}
        >
          {isArmed ? '🛡️ ARMED' : '🔓 DISARMED'}
        </button>
      </div>

      {error && (
        <div className="flex gap-2 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
          <AlertTriangle size={16} className="flex-shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {/* Security Level Controls */}
      <div>
        <p className="text-sm font-semibold text-white mb-3">Security Level</p>
        <div className="grid grid-cols-4 gap-2">
          {['low', 'medium', 'high', 'critical'].map((level) => (
            <button
              key={level}
              onClick={() => updateZoneSecurity(level)}
              className={`p-3 rounded-lg text-xs font-semibold transition-all capitalize ${
                securityLevel === level
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* Access Control */}
      <div>
        <p className="text-sm font-semibold text-white mb-3">Access Level</p>
        <select
          value={accessLevel}
          onChange={(e) => setAccessLevel(e.target.value)}
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
        >
          <option value="public">Public</option>
          <option value="restricted">Restricted</option>
          <option value="authorized_only">Authorized Only</option>
          <option value="locked">Locked</option>
        </select>
      </div>

      {/* Zone Statistics */}
      <div className="pt-4 border-t border-slate-700 grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-slate-400 mb-1">Status</p>
          <p className="text-sm font-semibold text-green-400">{zone.status}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400 mb-1">Sensors</p>
          <p className="text-sm font-semibold text-white">{zone.sensor_count}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400 mb-1">Alerts</p>
          <p className="text-sm font-semibold text-yellow-400">{zone.active_alerts || 0}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400 mb-1">Last Activity</p>
          <p className="text-sm font-semibold text-slate-300">2m ago</p>
        </div>
      </div>
    </div>
  );
}

// System Commands Panel
export function SystemCommands({ token }) {
  const [commandHistory, setCommandHistory] = useState([]);
  const [commandInput, setCommandInput] = useState('');

  const executeCommand = async () => {
    if (!commandInput.trim()) return;

    try {
      const response = await fetch(`${API_URL}/api/v1/system/execute-command`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: commandInput }),
      });

      if (!response.ok) throw new Error('Command failed');
      
      const newCommand = {
        id: Date.now(),
        input: commandInput,
        output: 'Command executed',
        timestamp: new Date().toLocaleTimeString(),
      };
      
      setCommandHistory([newCommand, ...commandHistory.slice(0, 9)]);
      setCommandInput('');
    } catch (err) {
      const newCommand = {
        id: Date.now(),
        input: commandInput,
        output: `Error: ${err.message}`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setCommandHistory([newCommand, ...commandHistory.slice(0, 9)]);
    }
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 space-y-4">
      <h3 className="text-lg font-bold text-white">System Commands</h3>

      {/* Command Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={commandInput}
          onChange={(e) => setCommandInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && executeCommand()}
          placeholder="Enter system command..."
          className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm placeholder-slate-500"
        />
        <button
          onClick={executeCommand}
          className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <Send size={16} />
        </button>
      </div>

      {/* Command History */}
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {commandHistory.map((cmd) => (
          <div key={cmd.id} className="bg-slate-900/50 border border-slate-700 rounded p-2 text-xs space-y-1">
            <div className="flex items-center justify-between">
              <p className="text-slate-400">{cmd.timestamp}</p>
              <p className="text-cyan-400">$ {cmd.input}</p>
            </div>
            <p className="text-slate-400 ml-2">→ {cmd.output}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
