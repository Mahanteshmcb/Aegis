import React from 'react';

export default function RobotForm({ formData, setFormData, onSubmit, editingId, onCancel }) {
  return (
    <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-6 mb-8">
      <h2 className="text-lg font-bold text-aegis-primary mb-4">
        {editingId ? 'Edit Robot' : 'Add New Robot'}
      </h2>
      <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Robot Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., RoboAlpha"
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
            required
          />
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Type</label>
          <select
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          >
            <option value="humanoid">Humanoid</option>
            <option value="quadruped">Quadruped</option>
            <option value="drone">Drone</option>
            <option value="wheeled">Wheeled</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Location</label>
          <select
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          >
            <option value="charging-station">Charging Station</option>
            <option value="living-quarters">Living Quarters</option>
            <option value="laboratory">Laboratory</option>
            <option value="greenhouse">Greenhouse</option>
            <option value="storage">Storage</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Status</label>
          <select
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          >
            <option value="idle">Idle</option>
            <option value="active">Active</option>
            <option value="charging">Charging</option>
            <option value="error">Error</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Battery %</label>
          <input
            type="number"
            min="0"
            max="100"
            value={formData.battery}
            onChange={(e) => setFormData({ ...formData, battery: parseInt(e.target.value || '0') })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          />
        </div>

        <div className="col-span-1 md:col-span-2 lg:col-span-5 flex gap-2">
          <button
            type="submit"
            className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-500 transition-all text-sm font-bold"
          >
            {editingId ? 'Update Robot' : 'Create Robot'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 transition-all text-sm font-bold"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
