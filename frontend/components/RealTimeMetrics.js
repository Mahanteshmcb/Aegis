import React, { useEffect, useState } from 'react';

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

export const RealTimeMetrics = ({ data = {} }) => {
  const metrics = [
    {
      key: 'systemHealth',
      label: 'System Health',
      value: Number(data.systemHealth ?? 98),
      unit: '%',
      color: '#34C759',
      icon: '⚙️',
      warningThreshold: 80,
    },
    {
      key: 'cpuUsage',
      label: 'CPU Usage',
      value: Number(data.cpuUsage ?? 42),
      unit: '%',
      color: '#FF9500',
      icon: '⚡',
      warningThreshold: 75,
    },
    {
      key: 'memoryUsage',
      label: 'Memory',
      value: Number(data.memoryUsage ?? 58),
      unit: '%',
      color: '#5AC8FA',
      icon: '💾',
      warningThreshold: 78,
    },
    {
      key: 'networkLatency',
      label: 'Network',
      value: Number(data.networkLatency ?? 12),
      unit: 'ms',
      color: '#FF3B30',
      icon: '📡',
      warningThreshold: 40,
    },
    {
      key: 'activeRobots',
      label: 'Active Robots',
      value: Number(data.activeRobots ?? 3),
      unit: '',
      color: '#00f2ff',
      icon: '🤖',
      warningThreshold: 2,
    },
    {
      key: 'sensorsOnline',
      label: 'Sensors Online',
      value: Number(data.sensorsOnline ?? 5),
      unit: '',
      color: '#00ffaa',
      icon: '📊',
      warningThreshold: 4,
    },
  ];

  const getState = (metric) => {
    const value = metric.value;
    if (metric.key === 'networkLatency') {
      return value > metric.warningThreshold ? 'Elevated' : 'Stable';
    }
    if (metric.key === 'activeRobots' || metric.key === 'sensorsOnline') {
      return value >= metric.warningThreshold ? 'Healthy' : 'Low';
    }
    return value >= metric.warningThreshold ? 'Normal' : 'Watch';
  };

  const [displayValues, setDisplayValues] = useState(() => Object.fromEntries(metrics.map((metric) => [metric.key, metric.value])));

  useEffect(() => {
    const timers = [];

    metrics.forEach((metric) => {
      const start = Number(displayValues[metric.key] ?? metric.value);
      const end = Number(metric.value);
      const diff = end - start;
      if (Math.abs(diff) < 0.0001) return;

      const steps = 14;
      let step = 0;
      const timer = setInterval(() => {
        step += 1;
        const eased = start + (diff * step) / steps;
        setDisplayValues((prev) => ({
          ...prev,
          [metric.key]: step >= steps ? end : eased,
        }));

        if (step >= steps) {
          clearInterval(timer);
        }
      }, 24);

      timers.push(timer);
    });

    return () => timers.forEach((timer) => clearInterval(timer));
  }, [data]);

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="grid grid-cols-2 gap-3 flex-1">
        {metrics.map((metric, idx) => {
          const currentValue = Number(displayValues[metric.key] ?? metric.value);
          const displayValue = clamp(currentValue, 0, 100);
          const barWidth = metric.key === 'activeRobots' || metric.key === 'sensorsOnline' ? `${Math.min((currentValue / 12) * 100, 100)}%` : `${displayValue}%`;
          const state = getState({ ...metric, value: currentValue });
          const isWatch = state !== 'Normal' && state !== 'Healthy' && state !== 'Stable';

          return (
            <div
              key={idx}
              className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-4 hover:border-aegis-primary/60 transition-all duration-300 shadow-[0_0_25px_rgba(34,211,238,0.08)]"
              style={{ boxShadow: isWatch ? `0 0 18px ${metric.color}66` : undefined, transform: 'translateZ(0)' }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl">{metric.icon}</span>
                <span className="text-[10px] text-aegis-muted uppercase tracking-wider font-mono">
                  {metric.label}
                </span>
              </div>

              <div className="mb-3">
                <div className="flex items-baseline gap-1">
                  <span
                    className="text-2xl font-bold font-mono transition-all duration-500"
                    style={{ color: metric.color }}
                  >
                    {Math.round(currentValue)}
                  </span>
                  <span className="text-xs text-aegis-muted">{metric.unit}</span>
                </div>
              </div>

              <div className="w-full bg-black/50 border border-aegis-primary/20 rounded h-1.5 overflow-hidden">
                <div
                  className="h-full rounded transition-all duration-700 ease-out"
                  style={{
                    width: barWidth,
                    background: `linear-gradient(90deg, ${metric.color}, rgba(255,255,255,0.8))`,
                    boxShadow: `0 0 10px ${metric.color}`,
                  }}
                />
              </div>

              <div className="mt-2 text-[10px] flex items-center justify-between">
                <span className={isWatch ? 'text-yellow-400' : 'text-green-400'}>
                  {isWatch ? `⚠️ ${state}` : `✓ ${state}`}
                </span>
                <span className="text-aegis-muted">{metric.unit === '%' ? 'Live' : 'Online'}</span>
              </div>
            </div>
          );
        })}
      </div>

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
