import React from 'react';

export default function UserForm({ formData, setFormData, onSubmit, editingId, onCancel }) {
  return (
    <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-6 mb-8">
      <h2 className="text-lg font-bold text-aegis-primary mb-4">
        {editingId ? 'Edit User' : 'Add New User'}
      </h2>
      <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Email</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="user@example.com"
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
            required
          />
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Role</label>
          <select
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          >
            <option value="viewer">Viewer</option>
            <option value="operator">Operator</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Status</label>
          <select
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>

        <div className="col-span-1 md:col-span-2 lg:col-span-3 flex gap-2">
          <button
            type="submit"
            className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-500 transition-all text-sm font-bold"
          >
            {editingId ? 'Update User' : 'Create User'}
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
