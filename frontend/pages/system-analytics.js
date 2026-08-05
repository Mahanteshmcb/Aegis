import React, { useState } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const analyticsData = [
  { time: '00:00', cpu: 20, memory: 30, network: 25 },
  { time: '04:00', cpu: 25, memory: 35, network: 30 },
  { time: '08:00', cpu: 35, memory: 45, network: 40 },
  { time: '12:00', cpu: 45, memory: 50, network: 55 },
  { time: '16:00', cpu: 52, memory: 55, network: 60 },
  { time: '20:00', cpu: 42, memory: 48, network: 50 },
];

export default function SystemAnalytics() {
  const { user, loading } = useCurrentUser();

  if (loading) {
    return <div className="text-aegis-muted animate-pulse">Loading...</div>;
  }

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">
          📈 SYSTEM ANALYTICS
        </h1>
        <p className="text-aegis-muted">Real-time system performance metrics</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/50 rounded-lg p-4">
          <p className="text-aegis-muted text-xs font-semibold uppercase tracking-wider">Avg CPU Usage</p>
          <p className="text-3xl font-bold text-blue-400 mt-2">37%</p>
        </div>
        <div className="bg-gradient-to-br from-green-900/30 to-green-800/10 border border-green-700/50 rounded-lg p-4">
          <p className="text-aegis-muted text-xs font-semibold uppercase tracking-wider">Avg Memory</p>
          <p className="text-3xl font-bold text-green-400 mt-2">44%</p>
        </div>
        <div className="bg-gradient-to-br from-cyan-900/30 to-cyan-800/10 border border-cyan-700/50 rounded-lg p-4">
          <p className="text-aegis-muted text-xs font-semibold uppercase tracking-wider">Network I/O</p>
          <p className="text-3xl font-bold text-cyan-400 mt-2">42 Mbps</p>
        </div>
        <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/10 border border-purple-700/50 rounded-lg p-4">
          <p className="text-aegis-muted text-xs font-semibold uppercase tracking-wider">Uptime</p>
          <p className="text-3xl font-bold text-purple-400 mt-2">45d 12h</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-6">
          <h2 className="text-lg font-bold text-aegis-primary mb-4">System Performance Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={analyticsData}>
              <defs>
                <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00f2ff" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#00f2ff" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,242,255,0.1)" />
              <XAxis dataKey="time" stroke="#666" />
              <YAxis stroke="#666" />
              <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: '1px solid #00f2ff' }} />
              <Area type="monotone" dataKey="cpu" stroke="#00f2ff" fillOpacity={1} fill="url(#colorCpu)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-6">
          <h2 className="text-lg font-bold text-aegis-primary mb-4">Resource Utilization</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,242,255,0.1)" />
              <XAxis dataKey="time" stroke="#666" />
              <YAxis stroke="#666" />
              <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: '1px solid #00f2ff' }} />
              <Legend />
              <Bar dataKey="memory" fill="#34C759" />
              <Bar dataKey="network" fill="#FF9500" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mt-8">
        <Link href="/dashboard" className="text-aegis-primary hover:text-aegis-primary/80 transition-colors">
          ← Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
