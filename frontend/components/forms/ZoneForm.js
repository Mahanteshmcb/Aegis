import React from 'react';

export default function ZoneForm({ formData, setFormData, onSubmit, editingId, onCancel }) {
  return (
    <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-6 mb-8">
      <h2 className="text-lg font-bold text-aegis-primary mb-4">
        {editingId ? 'Edit Zone' : 'Add New Zone'}
      </h2>
      <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Zone Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Greenhouse Alpha"
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
            required
          />
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Location</label>
          <input
            type="text"
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            placeholder="e.g., Building A, Floor 2"
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          />
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Type</label>
          <select
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          >
            <option value="greenhouse">Greenhouse</option>
            <option value="laboratory">Laboratory</option>
            <option value="storage">Storage</option>
            <option value="quarters">Quarters</option>
            <option value="common">Common Area</option>
          </select>
        </div>

        <div className="col-span-1 md:col-span-2 lg:col-span-3">
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Zone description..."
            rows="3"
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none resize-none"
          />
        </div>

        <div className="col-span-1 md:col-span-2 lg:col-span-3 flex gap-2">
          <button
            type="submit"
            className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-500 transition-all text-sm font-bold"
          >
            {editingId ? 'Update Zone' : 'Create Zone'}
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
