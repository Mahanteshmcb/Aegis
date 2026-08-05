import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Search, Trash2, Edit2 } from 'lucide-react';
import useCurrentUser from '../hooks/useCurrentUser';
import useEstateState from '../hooks/useEstateState';
import RobotForm from '../components/forms/RobotForm';
import Layout3D from '../components/Layout3D';
import Button3D from '../components/Button3D';
import Card3D from '../components/Card3D';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function RobotsManagement() {
  const { user, loading } = useCurrentUser();
  const estateState = useEstateState();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'humanoid',
    location: 'charging-station',
    status: 'idle',
    battery: 100,
  });
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!loading && user) {
      fetchRobots();
    }
  }, [user, loading]);

  const fetchRobots = async () => {
    try {
      estateState.setLoading(true);
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/robots`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const robots = res.ok ? await res.json() : [];
      
      const robotsWithPositions = (Array.isArray(robots) ? robots : []).map((r, i) => ({
        ...r,
        position: [-5 + (i % 3) * 5, 1, 5 - Math.floor(i / 3) * 5],
        status: r.status || 'idle',
      }));

      estateState.setRobots(robotsWithPositions);
      estateState.setLoading(false);
    } catch (err) {
      console.error('Error fetching robots:', err);
      estateState.setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('aegis_token');
      const method = editingId ? 'PUT' : 'POST';
      const endpoint = editingId ? `/api/v1/robots/${editingId}` : '/api/v1/robots';

      const res = await fetch(`${API_URL}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        const robot = await res.json();
        if (editingId) {
          estateState.updateRobot(editingId, robot);
        } else {
          estateState.addRobot(robot);
        }
        setFormData({ name: '', type: 'humanoid', location: 'charging-station', status: 'idle', battery: 100 });
        setEditingId(null);
        setShowForm(false);
      }
    } catch (err) {
      console.error('Error saving robot:', err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this robot?')) return;

    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/robots/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        estateState.deleteRobot(id);
      }
    } catch (err) {
      console.error('Error deleting robot:', err);
    }
  };

  const handleEdit = (robot) => {
    setFormData({
      name: robot.name || '',
      type: robot.type || 'humanoid',
      location: robot.location || 'charging-station',
      status: robot.status || 'idle',
      battery: robot.battery || 100,
    });
    setEditingId(robot.id);
    setShowForm(true);
  };

  const filteredRobots = estateState.robots.filter((r) =>
    r.name?.toLowerCase().includes(search.toLowerCase()) ||
    r.type?.toLowerCase().includes(search.toLowerCase())
  );

  const typeIcons = {
    humanoid: '🤖',
    quadruped: '🐕',
    drone: '🚁',
    wheeled: '🤖',
  };

  const statusColors = {
    active: 'from-green-600 to-emerald-600',
    charging: 'from-yellow-600 to-amber-600',
    idle: 'from-slate-600 to-slate-700',
    error: 'from-red-600 to-orange-600',
  };

  if (loading) {
    return (
      <Layout3D title="ROBOT MANAGEMENT" icon="🤖" subtitle="Loading fleet data...">
        <div className="flex items-center justify-center h-96">
          <div className="text-aegis-muted animate-pulse text-lg">Scanning robot network...</div>
        </div>
      </Layout3D>
    );
  }

  return (
    <Layout3D
      title="ROBOT MANAGEMENT"
      icon="🤖"
      subtitle="Manage, monitor, and control your autonomous robot fleet"
    >
      <div className="space-y-8">
        {/* Controls Bar */}
        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-3 text-aegis-muted" size={20} />
            <input
              type="text"
              placeholder="Search robots by name or type..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-black/50 border border-cyan-500/30 hover:border-cyan-500/60 rounded-lg text-white placeholder-aegis-muted text-sm focus:border-cyan-400 focus:outline-none transition-all"
            />
          </div>
          <Button3D
            variant="primary"
            size="md"
            icon={showForm ? undefined : Plus}
            onClick={() => {
              setShowForm(!showForm);
              setEditingId(null);
              setFormData({ name: '', type: 'humanoid', location: 'charging-station', status: 'idle', battery: 100 });
            }}
          >
            {showForm ? '✕ CANCEL' : '+ ADD ROBOT'}
          </Button3D>
        </div>

        {/* Add/Edit Form */}
        {showForm && (
          <Card3D variant="primary" glowing glowColor="#00f2ff">
            <RobotForm
              formData={formData}
              setFormData={setFormData}
              editingId={editingId}
              onSubmit={handleSubmit}
              onCancel={() => {
                setShowForm(false);
                setEditingId(null);
                setFormData({ name: '', type: 'humanoid', location: 'charging-station', status: 'idle', battery: 100 });
              }}
            />
          </Card3D>
        )}

        {/* Stats Bar */}
        <div className="grid grid-cols-3 gap-4">
          <Card3D variant="primary">
            <div className="text-center">
              <p className="text-3xl font-bold text-cyan-300">{estateState.robots.length}</p>
              <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Total Robots</p>
            </div>
          </Card3D>
          <Card3D variant="success">
            <div className="text-center">
              <p className="text-3xl font-bold text-green-300">
                {estateState.robots.filter((r) => r.status === 'active').length}
              </p>
              <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Active</p>
            </div>
          </Card3D>
          <Card3D variant="warning">
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-300">
                {Math.round(
                  estateState.robots.reduce((sum, r) => sum + (r.battery || 100), 0) / Math.max(estateState.robots.length, 1)
                )}
                %
              </p>
              <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Avg Battery</p>
            </div>
          </Card3D>
        </div>

        {/* Robots Grid */}
        <div>
          {filteredRobots.length === 0 ? (
            <Card3D variant="default" className="text-center py-12">
              <p className="text-aegis-muted text-lg">No robots found</p>
              <p className="text-xs text-aegis-muted mt-2">Create a new robot to get started</p>
            </Card3D>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredRobots.map((robot) => (
                <Card3D
                  key={robot.id}
                  variant={
                    robot.status === 'active'
                      ? 'success'
                      : robot.status === 'charging'
                      ? 'warning'
                      : robot.status === 'error'
                      ? 'danger'
                      : 'default'
                  }
                  glowing
                  glowColor={
                    robot.status === 'active'
                      ? '#00FF00'
                      : robot.status === 'charging'
                      ? '#FFD700'
                      : robot.status === 'error'
                      ? '#FF0000'
                      : '#666666'
                  }
                >
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-2xl">{typeIcons[robot.type] || '🤖'}</p>
                        <h3 className="text-lg font-bold text-white mt-2">
                          {robot.name || `Robot ${robot.id}`}
                        </h3>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-bold text-white bg-gradient-to-r ${statusColors[robot.status] || statusColors.idle}`}
                      >
                        {(robot.status || 'idle').toUpperCase()}
                      </span>
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-aegis-muted">Type:</span>
                        <span className="text-white capitalize">{robot.type || 'humanoid'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-aegis-muted">Location:</span>
                        <span className="text-white capitalize">{robot.location || 'unknown'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-aegis-muted">Battery:</span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all ${
                                robot.battery >= 75
                                  ? 'bg-green-500'
                                  : robot.battery >= 50
                                  ? 'bg-yellow-500'
                                  : robot.battery >= 25
                                  ? 'bg-orange-500'
                                  : 'bg-red-500'
                              }`}
                              style={{ width: `${robot.battery || 100}%` }}
                            />
                          </div>
                          <span className="text-white font-mono">{robot.battery || 100}%</span>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-4">
                      <Button3D
                        variant="secondary"
                        size="sm"
                        icon={Edit2}
                        onClick={() => handleEdit(robot)}
                      >
                        EDIT
                      </Button3D>
                      <Button3D
                        variant="danger"
                        size="sm"
                        icon={Trash2}
                        onClick={() => handleDelete(robot.id)}
                      >
                        DELETE
                      </Button3D>
                    </div>
                  </div>
                </Card3D>
              ))}
            </div>
          )}
        </div>

        {/* Back Button */}
        <div className="flex gap-4 pt-8">
          <Link href="/dashboard">
            <Button3D variant="ghost">← BACK TO DASHBOARD</Button3D>
          </Link>
          <Link href="/dashboard-3d">
            <Button3D variant="primary">🌐 VIEW IN 3D</Button3D>
          </Link>
        </div>
      </div>
    </Layout3D>
  );
}
