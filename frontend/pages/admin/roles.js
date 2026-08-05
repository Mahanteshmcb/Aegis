import React, { useState, useEffect } from 'react';
import Layout3D from '../../components/Layout3D';
import Button3D from '../../components/Button3D';
import Card3D from '../../components/Card3D';
import { Plus, Trash2, Edit2, X, Check } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const AVAILABLE_PERMISSIONS = [
  { id: 'read_robots', label: 'Read Robots', category: 'Robot Management' },
  { id: 'create_robots', label: 'Create Robots', category: 'Robot Management' },
  { id: 'update_robots', label: 'Update Robots', category: 'Robot Management' },
  { id: 'delete_robots', label: 'Delete Robots', category: 'Robot Management' },
  { id: 'read_sensors', label: 'Read Sensors', category: 'Sensor Management' },
  { id: 'create_sensors', label: 'Create Sensors', category: 'Sensor Management' },
  { id: 'update_sensors', label: 'Update Sensors', category: 'Sensor Management' },
  { id: 'delete_sensors', label: 'Delete Sensors', category: 'Sensor Management' },
  { id: 'read_zones', label: 'Read Zones', category: 'Zone Management' },
  { id: 'create_zones', label: 'Create Zones', category: 'Zone Management' },
  { id: 'update_zones', label: 'Update Zones', category: 'Zone Management' },
  { id: 'delete_zones', label: 'Delete Zones', category: 'Zone Management' },
  { id: 'read_safety', label: 'Read Safety', category: 'Safety' },
  { id: 'manage_safety', label: 'Manage Safety', category: 'Safety' },
  { id: 'read_analytics', label: 'Read Analytics', category: 'Analytics' },
  { id: 'read_audit_logs', label: 'Read Audit Logs', category: 'Audit' },
  { id: 'manage_users', label: 'Manage Users', category: 'User Management' },
  { id: 'manage_roles', label: 'Manage Roles', category: 'User Management' },
];

export default function RoleManagement() {
  const [roles, setRoles] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [newRoleName, setNewRoleName] = useState('');
  const [newRoleDescription, setNewRoleDescription] = useState('');
  const [selectedPermissions, setSelectedPermissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRoles();
  }, []);

  const fetchRoles = async () => {
    try {
      const token = localStorage.getItem('aegis_token');
      const response = await fetch(`${API_URL}/api/v1/roles`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setRoles(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error fetching roles:', error);
      // Initialize with default roles
      setRoles([
        { id: 'admin', name: 'Admin', description: 'Full system access', permissions: ['manage_users', 'manage_roles', ...AVAILABLE_PERMISSIONS.map(p => p.id)] },
        { id: 'operator', name: 'Operator', description: 'Can operate robots and manage sensors', permissions: ['read_robots', 'create_robots', 'update_robots', 'read_sensors', 'update_sensors', 'read_zones'] },
        { id: 'auditor', name: 'Auditor', description: 'Can view and audit system', permissions: ['read_audit_logs', 'read_analytics', 'read_robots', 'read_sensors', 'read_zones', 'read_safety'] },
        { id: 'viewer', name: 'Viewer', description: 'Read-only access', permissions: ['read_robots', 'read_sensors', 'read_zones', 'read_analytics'] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRole = async () => {
    if (!newRoleName.trim()) return;

    const newRole = {
      name: newRoleName,
      description: newRoleDescription,
      permissions: selectedPermissions,
      created_at: new Date().toISOString(),
    };

    try {
      const token = localStorage.getItem('aegis_token');
      await fetch(`${API_URL}/api/v1/roles`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(newRole),
      });

      setRoles([...roles, { id: `role_${Date.now()}`, ...newRole }]);
      setNewRoleName('');
      setNewRoleDescription('');
      setSelectedPermissions([]);
      setShowCreateForm(false);
    } catch (error) {
      console.error('Error creating role:', error);
      // Add locally on error
      setRoles([...roles, { id: `role_${Date.now()}`, ...newRole }]);
      setNewRoleName('');
      setNewRoleDescription('');
      setSelectedPermissions([]);
      setShowCreateForm(false);
    }
  };

  const handleDeleteRole = async (roleId) => {
    if (window.confirm('Delete this role? Users with this role will lose their permissions.')) {
      try {
        const token = localStorage.getItem('aegis_token');
        await fetch(`${API_URL}/api/v1/roles/${roleId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        });
        setRoles(roles.filter(r => r.id !== roleId));
      } catch (error) {
        console.error('Error deleting role:', error);
        // Delete locally on error
        setRoles(roles.filter(r => r.id !== roleId));
      }
    }
  };

  const handlePermissionToggle = (permissionId) => {
    if (selectedPermissions.includes(permissionId)) {
      setSelectedPermissions(selectedPermissions.filter(p => p !== permissionId));
    } else {
      setSelectedPermissions([...selectedPermissions, permissionId]);
    }
  };

  const permissionsByCategory = AVAILABLE_PERMISSIONS.reduce((acc, perm) => {
    if (!acc[perm.category]) acc[perm.category] = [];
    acc[perm.category].push(perm);
    return acc;
  }, {});

  return (
    <Layout3D title="Role Management" icon="👥" subtitle="Create and configure user roles and permissions">
      <div className="space-y-6">
        {/* Roles List */}
        <div className="grid gap-4 lg:grid-cols-2">
          {roles.map((role) => (
            <Card3D key={role.id} variant="primary" glowing glowColor="#00f2ff" className="p-4">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-cyan-300">{role.name}</h3>
                    <p className="text-xs text-slate-400 mt-1">{role.description}</p>
                  </div>
                  {role.id !== 'admin' && role.id !== 'operator' && role.id !== 'auditor' && role.id !== 'viewer' && (
                    <button
                      onClick={() => handleDeleteRole(role.id)}
                      className="p-1 hover:bg-red-900/30 rounded text-red-400"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>

                <div className="space-y-2">
                  <p className="text-xs font-semibold text-slate-300">Permissions ({role.permissions?.length || 0})</p>
                  <div className="flex flex-wrap gap-1">
                    {role.permissions?.slice(0, 5).map((perm) => (
                      <span key={perm} className="text-[10px] bg-cyan-900/30 text-cyan-200 px-2 py-1 rounded border border-cyan-700/30">
                        {perm}
                      </span>
                    ))}
                    {role.permissions && role.permissions.length > 5 && (
                      <span className="text-[10px] bg-slate-900/30 text-slate-300 px-2 py-1 rounded">
                        +{role.permissions.length - 5} more
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </Card3D>
          ))}
        </div>

        {/* Create Role Form */}
        {!showCreateForm && (
          <Button3D
            variant="success"
            size="lg"
            onClick={() => setShowCreateForm(true)}
            icon={Plus}
            className="w-full"
          >
            Create New Role
          </Button3D>
        )}

        {showCreateForm && (
          <Card3D variant="success" className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-green-300">Create New Role</h3>
                <button
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewRoleName('');
                    setNewRoleDescription('');
                    setSelectedPermissions([]);
                  }}
                  className="text-slate-400 hover:text-white"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Role Details */}
              <div className="space-y-3 pb-4 border-b border-slate-700">
                <input
                  type="text"
                  placeholder="Role Name (e.g., Technician, Manager)"
                  value={newRoleName}
                  onChange={(e) => setNewRoleName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-white text-sm focus:border-green-500 outline-none transition"
                />
                <textarea
                  placeholder="Role Description"
                  value={newRoleDescription}
                  onChange={(e) => setNewRoleDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-white text-sm h-16 focus:border-green-500 outline-none transition"
                />
              </div>

              {/* Permission Matrix */}
              <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                <p className="text-xs font-semibold text-slate-300">Select Permissions</p>
                {Object.entries(permissionsByCategory).map(([category, permissions]) => (
                  <div key={category} className="space-y-2">
                    <p className="text-xs font-bold text-cyan-300 uppercase tracking-wider">{category}</p>
                    <div className="grid grid-cols-2 gap-2">
                      {permissions.map((perm) => (
                        <label
                          key={perm.id}
                          className="flex items-center gap-2 p-2 rounded hover:bg-slate-900/50 cursor-pointer transition"
                        >
                          <input
                            type="checkbox"
                            checked={selectedPermissions.includes(perm.id)}
                            onChange={() => handlePermissionToggle(perm.id)}
                            className="w-4 h-4 rounded bg-slate-900 border-slate-700 accent-green-500 cursor-pointer"
                          />
                          <span className="text-xs text-slate-300">{perm.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-4 border-t border-slate-700">
                <Button3D
                  variant="success"
                  size="sm"
                  onClick={handleCreateRole}
                  disabled={!newRoleName.trim()}
                  className="flex-1"
                  icon={Check}
                >
                  Create Role
                </Button3D>
                <Button3D
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewRoleName('');
                    setNewRoleDescription('');
                    setSelectedPermissions([]);
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button3D>
              </div>
            </div>
          </Card3D>
        )}

        {/* Info Section */}
        <Card3D variant="default" className="p-4 bg-slate-900/40">
          <p className="text-xs text-slate-300 leading-relaxed">
            <strong>💡 Tip:</strong> Create custom roles by selecting permissions from available categories. Each role can have a combination of permissions for fine-grained access control. Users assigned to a role will inherit all permissions from that role.
          </p>
        </Card3D>
      </div>
    </Layout3D>
  );
}
