import React from 'react';

export default function TaskForm({ formData, setFormData, onSubmit, editingId, onCancel, robots = [], users = [] }) {
  return (
    <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-6 mb-8">
      <h2 className="text-lg font-bold text-aegis-primary mb-4">
        {editingId ? 'Edit Task' : 'Create New Task'}
      </h2>
      <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Task Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Daily Inspection"
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
            required
          />
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Robot</label>
          <select
            value={formData.robot_id || ''}
            onChange={(e) => setFormData({ ...formData, robot_id: parseInt(e.target.value || '0') })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          >
            <option value="">Unassigned</option>
            {robots.map((robot) => (
              <option key={robot.id} value={robot.id}>
                {robot.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Assigned To</label>
          <select
            value={formData.assigned_to || ''}
            onChange={(e) => setFormData({ ...formData, assigned_to: parseInt(e.target.value || '0') })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          >
            <option value="">Unassigned</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.email}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Priority</label>
          <select
            value={formData.priority || 'medium'}
            onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Status</label>
          <select
            value={formData.status || 'pending'}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          >
            <option value="pending">Pending</option>
            <option value="in-progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Due Date</label>
          <input
            type="datetime-local"
            value={formData.due_date || ''}
            onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
          />
        </div>

        <div className="col-span-1 md:col-span-2 lg:col-span-3">
          <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Description</label>
          <textarea
            value={formData.description || ''}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Task description..."
            rows="3"
            className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none resize-none"
          />
        </div>

        <div className="col-span-1 md:col-span-2 lg:col-span-3 flex gap-2">
          <button
            type="submit"
            className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-500 transition-all text-sm font-bold"
          >
            {editingId ? 'Update Task' : 'Create Task'}
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
