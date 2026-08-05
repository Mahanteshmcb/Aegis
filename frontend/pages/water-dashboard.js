import React, { useState } from 'react';
import { Droplet, TrendingUp, AlertCircle, Plus } from 'lucide-react';
import useCurrentUser from '../hooks/useCurrentUser';

export default function WaterDashboard() {
  const { user, loading } = useCurrentUser();
  const [collections, setCollections] = useState([
    { id: 1, name: 'Rainfall Catchment', type: 'rainfall', capacity: 5000, current: 3200, location: 'Roof Zone A' },
    { id: 2, name: 'Greywater Tank', type: 'greywater', capacity: 2000, current: 1500, location: 'East Wing' },
  ]);

  const handleAddSystem = () => {
    const newCollection = {
      id: collections.length + 1,
      name: 'New Collection System',
      type: 'rainfall',
      capacity: 1000,
      current: 500,
      location: 'New Location',
    };
    setCollections([...collections, newCollection]);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">💧 Water Management System</h1>
        <p className="text-slate-400">Monitor water collection, recycling, and irrigation operations</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-600/20 to-blue-700/10 border border-blue-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <Droplet className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Total Collected</p>
          <p className="text-2xl font-bold text-white mt-1">4,700 L</p>
        </div>
        <div className="bg-gradient-to-br from-green-600/20 to-green-700/10 border border-green-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <TrendingUp className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Recycling Rate</p>
          <p className="text-2xl font-bold text-white mt-1">85%</p>
        </div>
        <div className="bg-gradient-to-br from-cyan-600/20 to-cyan-700/10 border border-cyan-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <Droplet className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Recycled Volume</p>
          <p className="text-2xl font-bold text-white mt-1">2,500 L</p>
        </div>
        <div className="bg-gradient-to-br from-emerald-600/20 to-emerald-700/10 border border-emerald-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <AlertCircle className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Quality</p>
          <p className="text-2xl font-bold text-white mt-1">Excellent</p>
        </div>
      </div>

      {/* Water Collection Systems */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Water Collection Systems</h2>
          <button 
            onClick={handleAddSystem}
            className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={20} /> Add System
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {collections.map((collection) => (
            <div key={collection.id} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">{collection.name}</h3>
                  <p className="text-sm text-slate-400 capitalize">{collection.type}</p>
                </div>
                <Droplet className="text-blue-400" size={24} />
              </div>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-slate-300">Fill Level</span>
                    <span className="text-xs font-semibold text-white">{Math.round((collection.current / collection.capacity) * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-600 rounded-full h-2">
                    <div 
                      className="h-2 rounded-full bg-blue-500"
                      style={{ width: `${(collection.current / collection.capacity) * 100}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-400">Current</span>
                    <p className="text-white font-semibold">{collection.current} L</p>
                  </div>
                  <div>
                    <span className="text-slate-400">Capacity</span>
                    <p className="text-white font-semibold">{collection.capacity} L</p>
                  </div>
                  <div className="col-span-2">
                    <span className="text-slate-400">Location</span>
                    <p className="text-white font-semibold text-sm">{collection.location}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">Recycling System</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Recycling Rate</p>
              <p className="font-semibold text-green-400">85%</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Filtered Volume</p>
              <p className="font-semibold text-green-400">2,500 L</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">System Health</p>
              <p className="font-semibold text-green-400">98%</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Next Maintenance</p>
              <p className="font-semibold text-blue-400">3 days</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">Irrigation Usage</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Daily Usage</p>
              <p className="font-semibold text-blue-400">1,200 L</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Plant Health Score</p>
              <p className="font-semibold text-green-400">94%</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Soil Moisture</p>
              <p className="font-semibold text-blue-400">65%</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Last Watering</p>
              <p className="font-semibold text-blue-400">2 hours ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
