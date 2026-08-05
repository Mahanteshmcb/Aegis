import React, { useState } from 'react';
import { Trash2, TrendingUp, AlertCircle, Plus, Zap } from 'lucide-react';
import useCurrentUser from '../hooks/useCurrentUser';

export default function WasteDashboard() {
  const { user, loading } = useCurrentUser();
  const [containers, setContainers] = useState([
    { id: 1, name: 'General Waste', type: 'general', level: 72, capacity: 100, status: 'operational' },
    { id: 2, name: 'Recycling', type: 'recycling', level: 45, capacity: 150, status: 'operational' },
    { id: 3, name: 'Composting', type: 'composting', level: 88, capacity: 120, status: 'operational' },
  ]);

  const handleAddContainer = () => {
    const newContainer = {
      id: containers.length + 1,
      name: 'New Container',
      type: 'general',
      level: 30,
      capacity: 100,
      status: 'operational'
    };
    setContainers([...containers, newContainer]);
  };

  const handleDeleteContainer = (id) => {
    setContainers(containers.filter(c => c.id !== id));
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">♻️ Waste Management System</h1>
        <p className="text-slate-400">Monitor waste processing, recycling, and disposal operations</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-gradient-to-br from-slate-600/20 to-slate-700/10 border border-slate-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <Trash2 className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Total Waste</p>
          <p className="text-2xl font-bold text-white mt-1">1,240 kg</p>
        </div>
        <div className="bg-gradient-to-br from-green-600/20 to-green-700/10 border border-green-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <Zap className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Recycling</p>
          <p className="text-2xl font-bold text-white mt-1">68%</p>
        </div>
        <div className="bg-gradient-to-br from-yellow-600/20 to-yellow-700/10 border border-yellow-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <TrendingUp className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Composting</p>
          <p className="text-2xl font-bold text-white mt-1">32%</p>
        </div>
        <div className="bg-gradient-to-br from-red-600/20 to-red-700/10 border border-red-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <AlertCircle className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Hazardous</p>
          <p className="text-2xl font-bold text-white mt-1">8%</p>
        </div>
        <div className="bg-gradient-to-br from-cyan-600/20 to-cyan-700/10 border border-cyan-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <Zap className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Efficiency</p>
          <p className="text-2xl font-bold text-white mt-1">89%</p>
        </div>
      </div>

      {/* Waste Containers */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Waste Containers</h2>
          <button 
            onClick={handleAddContainer}
            className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={20} /> Add Container
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {containers.map((container) => (
            <div key={container.id} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">{container.name}</h3>
                  <p className="text-sm text-slate-400 capitalize">{container.type}</p>
                </div>
                <Trash2 className="text-amber-400" size={24} />
              </div>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-slate-300">Fill Level</span>
                    <span className="text-xs font-semibold text-white">{container.level}%</span>
                  </div>
                  <div className="w-full bg-slate-600 rounded-full h-2">
                    <div 
                      className="h-2 rounded-full bg-amber-500"
                      style={{ width: `${container.level}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-400">Status</span>
                    <p className="text-green-400 font-semibold capitalize">{container.status}</p>
                  </div>
                  <div>
                    <span className="text-slate-400">Capacity</span>
                    <p className="text-white font-semibold">{container.capacity} kg</p>
                  </div>
                </div>

                <button
                  onClick={() => handleDeleteContainer(container.id)}
                  className="w-full mt-2 text-xs bg-red-600/20 hover:bg-red-600/40 text-red-300 py-1 rounded transition-colors"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">Recycling Operations</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Current Rate</p>
              <p className="font-semibold text-green-400">68%</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Material Sorted</p>
              <p className="font-semibold text-green-400">840 kg</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">System Health</p>
              <p className="font-semibold text-green-400">96%</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Next Maintenance</p>
              <p className="font-semibold text-blue-400">7 days</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">Composting Process</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Active Batches</p>
              <p className="font-semibold text-blue-400">3</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Compost Ready</p>
              <p className="font-semibold text-green-400">280 kg</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Avg Temperature</p>
              <p className="font-semibold text-blue-400">58°C</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Time to Ready</p>
              <p className="font-semibold text-blue-400">5 weeks</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
