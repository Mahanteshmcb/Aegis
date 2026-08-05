import React, { useState, useEffect } from 'react';

export const RealTimeMetrics = ({ data = {} }) => {
  const [animatedValues, setAnimatedValues] = useState({});

  useEffect(() => {
    setAnimatedValues(data);
  }, [data]);

  const metrics = [
    {
      key: 'systemHealth',
      label: 'System Health',
      value: data.systemHealth || 98,
      unit: '%',
      color: '#34C759',
      icon: '⚙️',
    },
    {
      key: 'cpuUsage',
      label: 'CPU Usage',
      value: data.cpuUsage || 42,
      unit: '%',
      color: '#FF9500',
      icon: '⚡',
    },
    {
      key: 'memoryUsage',
      label: 'Memory',
      value: data.memoryUsage || 58,
      unit: '%',
      color: '#5AC8FA',
      icon: '💾',
    },
    {
      key: 'networkLatency',
      label: 'Network',
      value: data.networkLatency || 12,
      unit: 'ms',
      color: '#FF3B30',
      icon: '📡',
    },
    {
      key: 'activeRobots',
      label: 'Active Robots',
      value: data.activeRobots || 3,
      unit: '',
      color: '#00f2ff',
      icon: '🤖',
    },
    {
      key: 'sensorsOnline',
      label: 'Sensors Online',
      value: data.sensorsOnline || 5,
      unit: '',
      color: '#00ffaa',
      icon: '📊',
    },
  ];

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="grid grid-cols-2 gap-3 flex-1">
        {metrics.map((metric, idx) => (
          <div
            key={idx}
            className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-4 hover:border-aegis-primary/60 transition-all duration-300"
          >
            {/* Metric Icon and Label */}
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl">{metric.icon}</span>
              <span className="text-[10px] text-aegis-muted uppercase tracking-wider font-mono">
                {metric.label}
              </span>
            </div>

            {/* Value */}
            <div className="mb-3">
              <div className="flex items-baseline gap-1">
                <span
                  className="text-2xl font-bold font-mono"
                  style={{ color: metric.color }}
                >
                  {Math.round(animatedValues[metric.key] ?? metric.value)}
                </span>
                <span className="text-xs text-aegis-muted">{metric.unit}</span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-black/50 border border-aegis-primary/20 rounded h-1.5 overflow-hidden">
              <div
                className="h-full transition-all duration-500 rounded"
                style={{
                  width: `${Math.round(animatedValues[metric.key] ?? metric.value)}%`,
                  backgroundColor: metric.color,
                  boxShadow: `0 0 10px ${metric.color}`,
                }}
              />
            </div>

            {/* Status Indicator */}
            <div className="mt-2 text-[10px] text-aegis-muted">
              {(animatedValues[metric.key] ?? metric.value) > 80 ? (
                <span className="text-yellow-400">⚠️ High</span>
              ) : (
                <span className="text-green-400">✓ Normal</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* System Status Panel */}
      <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-4 mt-auto">
        <h4 className="text-xs font-bold text-aegis-primary uppercase tracking-widest mb-3">
          🟢 System Status
        </h4>
        <div className="space-y-2 text-[11px] font-mono">
          <div className="flex justify-between">
            <span className="text-aegis-muted">Uptime:</span>
            <span className="text-aegis-primary">45d 12h 34m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-aegis-muted">Last Update:</span>
            <span className="text-aegis-primary">Now</span>
          </div>
          <div className="flex justify-between">
            <span className="text-aegis-muted">All Systems:</span>
            <span className="text-green-400">✓ NOMINAL</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealTimeMetrics;
