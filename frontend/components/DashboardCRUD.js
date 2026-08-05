import React, { useState, useRef, useEffect } from 'react';
import { Edit2, Trash2, Plus, X, Settings, Eye, EyeOff } from 'lucide-react';
import Button3D from './Button3D';
import Card3D from './Card3D';

export default function DashboardCRUD({
  selectedEntity,
  robots,
  sensors,
  zones,
  onDelete,
  onUpdate,
  onCreate,
  viewMode,
  onViewModeChange,
  lightIntensity,
  onLightIntensityChange,
  autoRotate,
  onAutoRotateChange,
}) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingEntity, setEditingEntity] = useState(null);
  const [formData, setFormData] = useState({});
  const [entityType, setEntityType] = useState('robot');

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleCreateOrUpdate = async () => {
    if (editingEntity) {
      await onUpdate(editingEntity.type, editingEntity.id, formData);
      setEditingEntity(null);
    } else {
      await onCreate(entityType, formData);
      setShowCreateForm(false);
    }
    setFormData({});
  };

  const handleEditEntity = () => {
    if (selectedEntity) {
      setEditingEntity(selectedEntity);
      setFormData(selectedEntity);
    }
  };

  const handleDeleteEntity = async () => {
    if (selectedEntity && window.confirm(`Delete ${selectedEntity.type}: ${selectedEntity.name || selectedEntity.id}?`)) {
      await onDelete(selectedEntity.type, selectedEntity.id);
    }
  };

  return (
    <div className="space-y-4">
      {/* View Controls */}
      <Card3D variant="primary" className="p-4">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-300">View Controls</h3>
            <button
              onClick={() => onAutoRotateChange(!autoRotate)}
              className={`p-2 rounded ${autoRotate ? 'bg-cyan-900/50 text-cyan-300' : 'bg-slate-900/50 text-slate-400'} transition`}
              title={autoRotate ? 'Disable auto-rotate' : 'Enable auto-rotate'}
            >
              {autoRotate ? <Eye size={16} /> : <EyeOff size={16} />}
            </button>
          </div>

          {/* View Mode Tabs */}
          <div className="grid grid-cols-3 gap-2">
            {['realworld', 'wireframe', 'drone'].map((mode) => (
              <button
                key={mode}
                onClick={() => onViewModeChange(mode)}
                className={`px-3 py-2 rounded text-xs font-bold uppercase transition ${
                  viewMode === mode
                    ? 'bg-cyan-600 text-white'
                    : 'bg-slate-900/50 text-slate-300 hover:bg-slate-800'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          {/* Light Intensity Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-300">Sunlight</label>
              <span className="text-xs text-cyan-300">{Math.round(lightIntensity * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={lightIntensity}
              onChange={(e) => onLightIntensityChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded appearance-none cursor-pointer"
            />
          </div>
        </div>
      </Card3D>

      {/* Entity Stats */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        <Card3D variant="success" glowing glowColor="#00FF00" className="p-3">
          <p className="text-xs font-bold text-green-300">{robots.length}</p>
          <p className="text-[10px] text-green-200">ROBOTS</p>
        </Card3D>
        <Card3D variant="warning" glowing glowColor="#FFD700" className="p-3">
          <p className="text-xs font-bold text-yellow-300">{sensors.length}</p>
          <p className="text-[10px] text-yellow-200">SENSORS</p>
        </Card3D>
        <Card3D variant="danger" glowing glowColor="#FF1493" className="p-3">
          <p className="text-xs font-bold text-red-300">{zones.length}</p>
          <p className="text-[10px] text-red-200">ZONES</p>
        </Card3D>
      </div>

      {/* Create New Entity */}
      {!showCreateForm && !editingEntity && (
        <Button3D variant="primary" size="md" onClick={() => setShowCreateForm(true)} icon={Plus} className="w-full">
          Create Entity
        </Button3D>
      )}

      {/* Create Form */}
      {showCreateForm && (
        <Card3D variant="primary" className="p-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-cyan-300">Create New</h3>
              <button onClick={() => setShowCreateForm(false)} className="text-slate-400 hover:text-white">
                <X size={16} />
              </button>
            </div>

            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-white text-sm"
            >
              <option value="robot">Robot</option>
              <option value="sensor">Sensor</option>
              <option value="zone">Zone</option>
            </select>

            <input
              type="text"
              placeholder="Name"
              value={formData.name || ''}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-white text-sm"
            />

            {entityType === 'robot' && (
              <>
                <select
                  value={formData.type || 'humanoid'}
                  onChange={(e) => handleInputChange('type', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-white text-sm"
                >
                  <option value="humanoid">Humanoid</option>
                  <option value="quadruped">Quadruped</option>
                  <option value="drone">Drone</option>
                </select>
                <input
                  type="text"
                  placeholder="Location"
                  value={formData.location || ''}
                  onChange={(e) => handleInputChange('location', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-white text-sm"
                />
              </>
            )}

            {entityType === 'sensor' && (
              <>
                <select
                  value={formData.type || 'temperature'}
                  onChange={(e) => handleInputChange('type', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-white text-sm"
                >
                  <option value="temperature">Temperature</option>
                  <option value="humidity">Humidity</option>
                  <option value="pressure">Pressure</option>
                  <option value="motion">Motion</option>
                  <option value="light">Light</option>
                </select>
              </>
            )}

            <div className="flex gap-2">
              <Button3D variant="success" size="sm" onClick={handleCreateOrUpdate} className="flex-1">
                Create
              </Button3D>
              <Button3D variant="ghost" size="sm" onClick={() => setShowCreateForm(false)} className="flex-1">
                Cancel
              </Button3D>
            </div>
          </div>
        </Card3D>
      )}

      {/* Edit Form */}
      {editingEntity && (
        <Card3D variant="primary" className="p-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-cyan-300">Edit {editingEntity.type}</h3>
              <button onClick={() => setEditingEntity(null)} className="text-slate-400 hover:text-white">
                <X size={16} />
              </button>
            </div>

            <input
              type="text"
              placeholder="Name"
              value={formData.name || ''}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-white text-sm"
            />

            {editingEntity.type === 'robot' && (
              <input
                type="text"
                placeholder="Location"
                value={formData.location || ''}
                onChange={(e) => handleInputChange('location', e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-white text-sm"
              />
            )}

            <div className="flex gap-2">
              <Button3D variant="success" size="sm" onClick={handleCreateOrUpdate} className="flex-1">
                Save
              </Button3D>
              <Button3D variant="ghost" size="sm" onClick={() => setEditingEntity(null)} className="flex-1">
                Cancel
              </Button3D>
            </div>
          </div>
        </Card3D>
      )}

      {/* Selected Entity Details and Actions */}
      {selectedEntity && !showCreateForm && !editingEntity && (
        <Card3D variant="success" glowing glowColor="#00FF00" className="p-4">
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-green-300">Selected: {selectedEntity.name || selectedEntity.type}</h3>

            <div className="grid grid-cols-2 gap-2 text-xs text-slate-300">
              <div>
                <p className="text-[10px] text-slate-400 uppercase">Type</p>
                <p className="text-white font-semibold">{selectedEntity.type}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400 uppercase">ID</p>
                <p className="text-white font-semibold truncate">{selectedEntity.id}</p>
              </div>

              {selectedEntity.status && (
                <div>
                  <p className="text-[10px] text-slate-400 uppercase">Status</p>
                  <p className={`font-semibold ${selectedEntity.status === 'active' ? 'text-green-300' : 'text-yellow-300'}`}>
                    {selectedEntity.status}
                  </p>
                </div>
              )}

              {selectedEntity.battery !== undefined && (
                <div>
                  <p className="text-[10px] text-slate-400 uppercase">Battery</p>
                  <p className="text-white font-semibold">{selectedEntity.battery}%</p>
                </div>
              )}

              {selectedEntity.value && (
                <div>
                  <p className="text-[10px] text-slate-400 uppercase">Value</p>
                  <p className="text-white font-semibold">{selectedEntity.value}</p>
                </div>
              )}

              {selectedEntity.location && (
                <div>
                  <p className="text-[10px] text-slate-400 uppercase">Location</p>
                  <p className="text-white font-semibold">{selectedEntity.location}</p>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-2">
              <Button3D variant="secondary" size="sm" onClick={handleEditEntity} icon={Edit2} className="flex-1">
                Edit
              </Button3D>
              <Button3D variant="danger" size="sm" onClick={handleDeleteEntity} icon={Trash2} className="flex-1">
                Delete
              </Button3D>
            </div>

            {/* Device Screen Preview */}
            {selectedEntity.type === 'robot' && selectedEntity.type !== 'drone' && (
              <div className="mt-3 p-3 bg-black/50 rounded border border-slate-700">
                <p className="text-[10px] text-slate-400 uppercase mb-2">Preview</p>
                <div className="bg-slate-900 rounded aspect-video flex items-center justify-center text-slate-500 text-xs">
                  Live Camera Feed
                </div>
              </div>
            )}
          </div>
        </Card3D>
      )}

      {/* No Entity Selected */}
      {!selectedEntity && !showCreateForm && !editingEntity && (
        <Card3D variant="default" className="p-4 text-center text-slate-400 text-xs">
          <p>Click on objects in the 3D scene to select and manage them</p>
        </Card3D>
      )}
    </div>
  );
}
