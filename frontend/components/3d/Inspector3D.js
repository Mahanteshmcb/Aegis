import React, { useState } from 'react';
import { X, Plus, Edit2, Trash2, Copy, Eye } from 'lucide-react';

/**
 * 3D Inspector Panel - appears when selecting entities in the 3D scene
 * Allows viewing/editing/deleting selected robots, sensors, or zones
 */
export default function Inspector3D({ selectedEntity, onClose, onUpdate, onDelete, onDuplicate }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState(selectedEntity);

  const handleSave = () => {
    onUpdate(editData);
    setIsEditing(false);
  };

  if (!selectedEntity) return null;

  const isRobot = selectedEntity.type === 'robot';
  const isSensor = selectedEntity.type === 'sensor';
  const isZone = selectedEntity.type === 'zone';

  const typeColor = isRobot ? 'from-cyan-600 to-blue-600' : isSensor ? 'from-green-600 to-emerald-600' : 'from-purple-600 to-pink-600';
  const typeIcon = isRobot ? '🤖' : isSensor ? '📡' : '📍';

  return (
    <div className="fixed bottom-6 right-6 z-50 w-96 max-h-[70vh] overflow-y-auto">
      <div className={`bg-gradient-to-br ${typeColor} rounded-lg shadow-2xl border border-white/20 overflow-hidden`}>
        {/* Header */}
        <div className="bg-gradient-to-r from-black/40 to-black/20 p-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{typeIcon}</span>
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                {selectedEntity.type} INSPECTOR
              </h3>
              <p className="text-xs text-white/60">{selectedEntity.name || `${selectedEntity.type} #${selectedEntity.id}`}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/60 hover:text-white transition">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 bg-black/60">
          {!isEditing ? (
            <>
              {/* View Mode */}
              <div className="space-y-3 text-white text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-white/60">ID:</span>
                  <span className="font-mono font-bold">{selectedEntity.id}</span>
                </div>

                {isRobot && (
                  <>
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Type:</span>
                      <span className="capitalize">{selectedEntity.type || 'humanoid'}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Status:</span>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        selectedEntity.status === 'active' ? 'bg-green-900/50 text-green-300' :
                        selectedEntity.status === 'charging' ? 'bg-yellow-900/50 text-yellow-300' :
                        'bg-red-900/50 text-red-300'
                      }`}>
                        {selectedEntity.status || 'idle'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Battery:</span>
                      <span>{selectedEntity.battery || 100}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Location:</span>
                      <span className="text-xs">{selectedEntity.location || 'unknown'}</span>
                    </div>
                  </>
                )}

                {isSensor && (
                  <>
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Sensor Type:</span>
                      <span className="capitalize">{selectedEntity.type || 'temperature'}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Zone ID:</span>
                      <span>{selectedEntity.zone_id || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Location:</span>
                      <span className="text-xs">{selectedEntity.location || 'unknown'}</span>
                    </div>
                    {selectedEntity.last_reading && (
                      <div className="mt-2 p-2 bg-black/40 rounded border border-white/10">
                        <p className="text-xs text-white/60 mb-1">Latest Reading:</p>
                        <p className="text-xs font-mono text-green-400">
                          {JSON.stringify(selectedEntity.last_reading).substring(0, 60)}...
                        </p>
                      </div>
                    )}
                  </>
                )}

                {isZone && (
                  <>
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Zone Type:</span>
                      <span className="capitalize">{selectedEntity.type || 'greenhouse'}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Location:</span>
                      <span className="text-xs">{selectedEntity.location || 'unknown'}</span>
                    </div>
                    {selectedEntity.description && (
                      <div className="mt-2 p-2 bg-black/40 rounded border border-white/10">
                        <p className="text-xs text-white/60 mb-1">Description:</p>
                        <p className="text-xs text-white">{selectedEntity.description}</p>
                      </div>
                    )}
                  </>
                )}

                <div className="pt-2 border-t border-white/10 text-xs text-white/50">
                  Created: {new Date().toLocaleDateString()}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-3 gap-2 pt-4">
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold text-xs transition"
                >
                  <Edit2 size={14} /> Edit
                </button>
                <button
                  onClick={onDuplicate}
                  className="flex items-center justify-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded font-bold text-xs transition"
                >
                  <Copy size={14} /> Clone
                </button>
                <button
                  onClick={onDelete}
                  className="flex items-center justify-center gap-2 px-3 py-2 bg-red-600 hover:bg-red-500 text-white rounded font-bold text-xs transition"
                >
                  <Trash2 size={14} /> Delete
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Edit Mode */}
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-bold text-white/60 uppercase">Name</label>
                  <input
                    type="text"
                    value={editData.name || ''}
                    onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                    className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
                  />
                </div>

                {isRobot && (
                  <>
                    <div>
                      <label className="text-xs font-bold text-white/60 uppercase">Status</label>
                      <select
                        value={editData.status || 'idle'}
                        onChange={(e) => setEditData({ ...editData, status: e.target.value })}
                        className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
                      >
                        <option value="idle">Idle</option>
                        <option value="active">Active</option>
                        <option value="charging">Charging</option>
                        <option value="error">Error</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-white/60 uppercase">Battery (%)</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={editData.battery || 100}
                        onChange={(e) => setEditData({ ...editData, battery: parseInt(e.target.value) })}
                        className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
                      />
                    </div>
                  </>
                )}

                {isSensor && (
                  <div>
                    <label className="text-xs font-bold text-white/60 uppercase">Location</label>
                    <input
                      type="text"
                      value={editData.location || ''}
                      onChange={(e) => setEditData({ ...editData, location: e.target.value })}
                      className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none"
                    />
                  </div>
                )}

                {isZone && (
                  <div>
                    <label className="text-xs font-bold text-white/60 uppercase">Description</label>
                    <textarea
                      value={editData.description || ''}
                      onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                      className="w-full mt-1 px-3 py-2 bg-black/40 border border-white/20 rounded text-white text-sm focus:border-white/40 focus:outline-none resize-none"
                      rows="3"
                    />
                  </div>
                )}
              </div>

              {/* Save/Cancel Buttons */}
              <div className="grid grid-cols-2 gap-2 pt-4">
                <button
                  onClick={handleSave}
                  className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded font-bold text-sm transition"
                >
                  Save
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded font-bold text-sm transition"
                >
                  Cancel
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
