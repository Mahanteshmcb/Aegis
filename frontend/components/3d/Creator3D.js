import React, { useState } from 'react';
import { Plus, X } from 'lucide-react';

/**
 * 3D Creator Panel - appears in empty space
 * Allows creating new robots, sensors, or zones
 */
export default function Creator3D({ onCreateRobot, onCreateSensor, onCreateZone, onClose }) {
  const [showMenu, setShowMenu] = useState(true);
  const [activeForm, setActiveForm] = useState(null);
  const [formData, setFormData] = useState({});

  const handleCreateRobot = () => {
    onCreateRobot({
      name: formData.name || `Robot-${Date.now()}`,
      type: formData.type || 'humanoid',
      status: 'idle',
      battery: 100,
      location: formData.location || 'charging-station',
    });
    setActiveForm(null);
    setFormData({});
  };

  const handleCreateSensor = () => {
    onCreateSensor({
      name: formData.name || `Sensor-${Date.now()}`,
      type: formData.type || 'temperature',
      location: formData.location || 'zone-a',
      zone_id: formData.zone_id || null,
    });
    setActiveForm(null);
    setFormData({});
  };

  const handleCreateZone = () => {
    onCreateZone({
      name: formData.name || `Zone-${Date.now()}`,
      type: formData.type || 'greenhouse',
      location: formData.location || 'building-a',
      description: formData.description || '',
    });
    setActiveForm(null);
    setFormData({});
  };

  return (
    <div className="fixed bottom-6 left-6 z-50 w-72">
      {/* Menu Button */}
      {!activeForm && (
        <div className="bg-gradient-to-br from-emerald-600 to-teal-600 rounded-lg shadow-2xl border border-white/20 overflow-hidden">
          <div className="bg-gradient-to-r from-black/40 to-black/20 p-4 border-b border-white/10">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Create Entity</h3>
            <p className="text-xs text-white/60">Add new robots, sensors, or zones</p>
          </div>

          <div className="p-4 space-y-2 bg-black/60">
            <button
              onClick={() => setActiveForm('robot')}
              className="w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-bold text-sm transition flex items-center justify-between"
            >
              <span>🤖 New Robot</span>
              <Plus size={16} />
            </button>
            <button
              onClick={() => setActiveForm('sensor')}
              className="w-full px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded font-bold text-sm transition flex items-center justify-between"
            >
              <span>📡 New Sensor</span>
              <Plus size={16} />
            </button>
            <button
              onClick={() => setActiveForm('zone')}
              className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded font-bold text-sm transition flex items-center justify-between"
            >
              <span>📍 New Zone</span>
              <Plus size={16} />
            </button>
            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded font-bold text-sm transition"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Robot Form */}
      {activeForm === 'robot' && (
        <div className="bg-gradient-to-br from-cyan-600 to-blue-600 rounded-lg shadow-2xl border border-white/20 overflow-hidden">
          <div className="bg-gradient-to-r from-black/40 to-black/20 p-4 border-b border-white/10 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">🤖 New Robot</h3>
            <button onClick={() => setActiveForm(null)} className="text-white/60 hover:text-white">
              <X size={18} />
            </button>
          </div>
          <div className="p-4 space-y-3 bg-black/60">
            <div>
              <label className="text-xs font-bold text-white/60 uppercase">Name</label>
              <input
                type="text"
                placeholder="e.g., RoboAlpha"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-white/60 uppercase">Type</label>
              <select
                value={formData.type || 'humanoid'}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
              >
                <option value="humanoid">Humanoid</option>
                <option value="quadruped">Quadruped</option>
                <option value="drone">Drone</option>
                <option value="wheeled">Wheeled</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-white/60 uppercase">Location</label>
              <select
                value={formData.location || 'charging-station'}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
              >
                <option value="charging-station">Charging Station</option>
                <option value="greenhouse">Greenhouse</option>
                <option value="laboratory">Laboratory</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2">
              <button
                onClick={handleCreateRobot}
                className="px-3 py-2 bg-green-600 hover:bg-green-500 text-white rounded font-bold text-sm transition"
              >
                Create
              </button>
              <button
                onClick={() => setActiveForm(null)}
                className="px-3 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded font-bold text-sm transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sensor Form */}
      {activeForm === 'sensor' && (
        <div className="bg-gradient-to-br from-green-600 to-emerald-600 rounded-lg shadow-2xl border border-white/20 overflow-hidden">
          <div className="bg-gradient-to-r from-black/40 to-black/20 p-4 border-b border-white/10 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">📡 New Sensor</h3>
            <button onClick={() => setActiveForm(null)} className="text-white/60 hover:text-white">
              <X size={18} />
            </button>
          </div>
          <div className="p-4 space-y-3 bg-black/60">
            <div>
              <label className="text-xs font-bold text-white/60 uppercase">Name</label>
              <input
                type="text"
                placeholder="e.g., TempSensor-01"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-white/60 uppercase">Type</label>
              <select
                value={formData.type || 'temperature'}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
              >
                <option value="temperature">Temperature</option>
                <option value="humidity">Humidity</option>
                <option value="pressure">Pressure</option>
                <option value="motion">Motion</option>
                <option value="light">Light</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-white/60 uppercase">Location</label>
              <input
                type="text"
                placeholder="e.g., Greenhouse A"
                value={formData.location || ''}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
              />
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2">
              <button
                onClick={handleCreateSensor}
                className="px-3 py-2 bg-green-600 hover:bg-green-500 text-white rounded font-bold text-sm transition"
              >
                Create
              </button>
              <button
                onClick={() => setActiveForm(null)}
                className="px-3 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded font-bold text-sm transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Zone Form */}
      {activeForm === 'zone' && (
        <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg shadow-2xl border border-white/20 overflow-hidden">
          <div className="bg-gradient-to-r from-black/40 to-black/20 p-4 border-b border-white/10 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">📍 New Zone</h3>
            <button onClick={() => setActiveForm(null)} className="text-white/60 hover:text-white">
              <X size={18} />
            </button>
          </div>
          <div className="p-4 space-y-3 bg-black/60">
            <div>
              <label className="text-xs font-bold text-white/60 uppercase">Name</label>
              <input
                type="text"
                placeholder="e.g., Greenhouse Alpha"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-white/60 uppercase">Type</label>
              <select
                value={formData.type || 'greenhouse'}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
              >
                <option value="greenhouse">Greenhouse</option>
                <option value="laboratory">Laboratory</option>
                <option value="storage">Storage</option>
                <option value="quarters">Quarters</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-white/60 uppercase">Description</label>
              <textarea
                placeholder="Zone details..."
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none resize-none"
                rows="2"
              />
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2">
              <button
                onClick={handleCreateZone}
                className="px-3 py-2 bg-green-600 hover:bg-green-500 text-white rounded font-bold text-sm transition"
              >
                Create
              </button>
              <button
                onClick={() => setActiveForm(null)}
                className="px-3 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded font-bold text-sm transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
