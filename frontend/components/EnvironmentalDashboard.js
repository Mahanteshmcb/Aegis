import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Card from './Card';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

/**
 * Living Quarters Environmental Control Dashboard
 * Temperature, humidity, air quality, HVAC status, comfort management
 */
export default function EnvironmentalDashboard({ zoneId }) {
  const [currentEnv, setCurrentEnv] = useState(null);
  const [airQuality, setAirQuality] = useState(null);
  const [setpoint, setSetpoint] = useState(22);
  const [selectedScene, setSelectedScene] = useState('home');
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!zoneId) return;

    const fetchData = async () => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;
      if (!token) {
        setError('Authentication token missing');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);

        const envResponse = await fetch(`${API_URL}/api/v1/environmental/zones/${zoneId}/current`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (!envResponse.ok) throw new Error('Failed to load current environmental state');
        const envData = await envResponse.json();
        setCurrentEnv(envData);
        setSetpoint(envData.setpoint || 22);

        const aqResponse = await fetch(`${API_URL}/api/v1/environmental/zones/${zoneId}/air-quality/current`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (!aqResponse.ok) throw new Error('Failed to load air quality');
        const aqData = await aqResponse.json();
        setAirQuality(aqData);

        const trendResponse = await fetch(`${API_URL}/api/v1/environmental/zones/${zoneId}/air-quality/24h`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (!trendResponse.ok) throw new Error('Failed to load air quality history');
        const trendResult = await trendResponse.json();
        setTrendData(trendResult.data || []);

        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to fetch environmental data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [zoneId]);

  const getAuthHeaders = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;
    return {
      Authorization: token ? `Bearer ${token}` : undefined,
      'Content-Type': 'application/json',
    };
  };

  const handleSetpointChange = async (newSetpoint) => {
    if (!zoneId) return;
    setSetpoint(newSetpoint);
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;
      if (!token) return;

      const response = await fetch(`${API_URL}/api/v1/environmental/zones/${zoneId}/setpoint`, {
        method: 'PATCH',
        headers: {
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ setpoint: newSetpoint }),
      });

      if (!response.ok) {
        throw new Error('Failed to update setpoint');
      }
    } catch (err) {
      console.error('Failed to update setpoint:', err);
      setSetpoint(currentEnv?.setpoint || 22);
    }
  };

  const handleSceneChange = async (scene) => {
    if (!zoneId) return;
    setSelectedScene(scene);
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;
      if (!token) return;

      const response = await fetch(`${API_URL}/api/v1/environmental/zones/${zoneId}/scene/${scene}`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error('Failed to activate scene');
      }
    } catch (err) {
      console.error('Failed to activate scene:', err);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading environmental data...</div>;
  if (error) return <div className="p-8 text-center text-red-600">{error}</div>;
  if (!currentEnv || !airQuality) return <div className="p-8 text-center">No data available</div>;

  // Determine status colors
  const getTempStatus = () => {
    const diff = currentEnv.temperature - setpoint;
    if (Math.abs(diff) < 0.5) return 'text-green-600';
    if (Math.abs(diff) < 1) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCO2Status = () => {
    if (airQuality.co2.ppm < 800) return 'text-green-600';
    if (airQuality.co2.ppm < 1200) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getHumidityStatus = () => {
    if (airQuality.humidity.percent >= 40 && airQuality.humidity.percent <= 60) return 'text-green-600';
    return 'text-orange-600';
  };

  return (
    <div className="space-y-6 p-6 bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-4xl font-bold text-gray-800">Climate Control</h1>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-600">Last updated: {new Date(currentEnv.timestamp).toLocaleTimeString()}</div>
          <Link href="/schedules" className="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700">Schedules</Link>
        </div>
      </div>

      {/* Main Temperature Control Panel */}
      <Card className="bg-white shadow-lg border-l-4 border-blue-500">
        <div className="grid grid-cols-2 gap-8">
          {/* Current Temperature */}
          <div className="flex flex-col items-center justify-center">
            <p className="text-gray-600 text-sm mb-2">Current Temperature</p>
            <p className={`text-6xl font-bold ${getTempStatus()}`}>
              {currentEnv.temperature.toFixed(1)}°C
            </p>
            <p className="text-gray-600 text-sm mt-2">
              {currentEnv.temperature < setpoint ? '↑ Heating' : currentEnv.temperature > setpoint ? '↓ Cooling' : '✓ At target'}
            </p>
          </div>

          {/* Temperature Control */}
          <div className="flex flex-col justify-center">
            <p className="text-gray-600 text-sm mb-4">Target Temperature</p>
            <div className="flex items-center justify-center mb-4">
              <button
                onClick={() => handleSetpointChange(Math.max(16, setpoint - 1))}
                className="px-4 py-2 bg-blue-500 text-white rounded-l hover:bg-blue-600"
              >
                −
              </button>
              <input
                type="number"
                value={setpoint}
                onChange={(e) => handleSetpointChange(parseFloat(e.target.value))}
                className="w-24 text-center text-2xl font-bold border-2 border-blue-500 py-2"
                min="16"
                max="28"
                step="0.5"
              />
              <button
                onClick={() => handleSetpointChange(Math.min(28, setpoint + 1))}
                className="px-4 py-2 bg-blue-500 text-white rounded-r hover:bg-blue-600"
              >
                +
              </button>
            </div>
            <input
              type="range"
              min="16"
              max="28"
              step="0.5"
              value={setpoint}
              onChange={(e) => handleSetpointChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-gray-600 mt-2 text-center">16°C — 28°C</p>
          </div>
        </div>

        {/* HVAC System Status */}
        <div className="mt-6 pt-6 border-t-2 border-gray-200 grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-gray-600 text-sm">Compressor</p>
            <p className="text-xl font-bold text-blue-600">{currentEnv.compressor_speed_hz.toFixed(0)} Hz</p>
            <p className="text-xs text-gray-600">{currentEnv.hvac_mode === 'heat' ? '🔥 Heating' : currentEnv.hvac_mode === 'cool' ? '❄️ Cooling' : '✓ Idle'}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-600 text-sm">Fan Speed</p>
            <p className="text-xl font-bold text-indigo-600">{currentEnv.fan_speed_percent.toFixed(0)}%</p>
          </div>
          <div className="text-center">
            <p className="text-gray-600 text-sm">Mode</p>
            <p className="text-xl font-bold text-purple-600">{currentEnv.hvac_mode.toUpperCase()}</p>
          </div>
        </div>
      </Card>

      {/* Comfort Scenes */}
      <Card className="bg-white shadow-lg">
        <h2 className="text-xl font-bold mb-4">Quick Scenes</h2>
        <div className="grid grid-cols-4 gap-4">
          {[
            { name: 'home', label: '🏠 Home', setpoint: 22 },
            { name: 'away', label: '🚗 Away', setpoint: 26 },
            { name: 'sleep', label: '😴 Sleep', setpoint: 19 },
            { name: 'party', label: '🎉 Party', setpoint: 21 }
          ].map(scene => (
            <button
              key={scene.name}
              onClick={() => handleSceneChange(scene.name)}
              className={`p-4 rounded-lg font-semibold transition ${
                selectedScene === scene.name
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
              }`}
            >
              {scene.label}
              <p className="text-xs mt-1">{scene.setpoint}°C</p>
            </button>
          ))}
        </div>
      </Card>

      {/* Air Quality Dashboard */}
      <div className="grid grid-cols-2 gap-6">
        {/* CO₂ Status */}
        <Card className="bg-white shadow-lg">
          <div className="text-center">
            <p className="text-gray-600 text-sm mb-2">Carbon Dioxide (CO₂)</p>
            <p className={`text-4xl font-bold ${getCO2Status()} mb-2`}>
              {airQuality.co2.ppm.toFixed(0)} ppm
            </p>
            <p className="text-xs text-gray-600 mb-3">
              {airQuality.co2.status === 'excellent' && '✓ Excellent air quality'}
              {airQuality.co2.status === 'good' && '✓ Good air quality'}
              {airQuality.co2.status === 'fair' && '⚠️ Fair - ventilate'}
              {airQuality.co2.status === 'poor' && '🚨 Poor - immediate ventilation'}
            </p>
            <div className="w-full bg-gray-300 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition ${
                  airQuality.co2.status === 'excellent' ? 'bg-green-500' :
                  airQuality.co2.status === 'good' ? 'bg-yellow-500' :
                  'bg-red-500'
                }`}
                style={{ width: `${Math.min(100, (airQuality.co2.ppm / 2000) * 100)}%` }}
              />
            </div>
          </div>
        </Card>

        {/* Humidity Status */}
        <Card className="bg-white shadow-lg">
          <div className="text-center">
            <p className="text-gray-600 text-sm mb-2">Relative Humidity</p>
            <p className={`text-4xl font-bold ${getHumidityStatus()} mb-2`}>
              {airQuality.humidity.percent.toFixed(0)}%
            </p>
            <p className="text-xs text-gray-600 mb-3">
              {airQuality.humidity.status === 'optimal' && '✓ Optimal (comfort)'}
              {airQuality.humidity.status === 'high' && '⚠️ High (mold risk)'}
              {airQuality.humidity.status === 'low' && '⚠️ Low (respiratory)'}
            </p>
            <div className="w-full bg-gray-300 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition ${
                  airQuality.humidity.percent >= 40 && airQuality.humidity.percent <= 60 ? 'bg-green-500' :
                  'bg-orange-500'
                }`}
                style={{ width: `${airQuality.humidity.percent}%` }}
              />
            </div>
          </div>
        </Card>

        {/* PM2.5 Status */}
        <Card className="bg-white shadow-lg">
          <div className="text-center">
            <p className="text-gray-600 text-sm mb-2">Fine Particulate (PM2.5)</p>
            <p className="text-3xl font-bold text-blue-600 mb-2">
              {airQuality.pm25 ? airQuality.pm25.value.toFixed(0) : 'N/A'} µg/m³
            </p>
            <p className="text-xs text-green-600">✓ Air purifier: Off</p>
          </div>
        </Card>

        {/* VOC Status */}
        <Card className="bg-white shadow-lg">
          <div className="text-center">
            <p className="text-gray-600 text-sm mb-2">Volatile Organics (VOC)</p>
            <p className="text-3xl font-bold text-green-600 mb-2">
              {airQuality.voc ? airQuality.voc.ppb.toFixed(0) : 'N/A'} ppb
            </p>
            <p className="text-xs text-green-600">✓ Safe level</p>
          </div>
        </Card>
      </div>

      {/* 24-Hour Trend Chart */}
      {trendData.length > 0 && (
        <Card className="bg-white shadow-lg">
          <h2 className="text-xl font-bold mb-4">24-Hour Air Quality Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(time) => new Date(time).toLocaleTimeString([], { hour: '2-digit' })}
              />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip
                formatter={(value) => value.toFixed(0)}
                labelFormatter={(label) => new Date(label).toLocaleString()}
              />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="co2_ppm"
                stroke="#ef4444"
                name="CO₂ (ppm)"
                isAnimationActive={false}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="humidity"
                stroke="#3b82f6"
                name="Humidity (%)"
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* System Information */}
      <Card className="bg-white shadow-lg text-sm text-gray-600">
        <h3 className="font-bold mb-2">System Information</h3>
        <ul className="space-y-1">
          <li>✓ HVAC System: 6-8 kW variable capacity heat pump</li>
          <li>✓ Multi-zone control: 4-6 independent zones</li>
          <li>✓ Air quality sensors: CO₂, VOC, PM2.5, humidity</li>
          <li>✓ Fresh air ventilation: 500-1200 CFM</li>
          <li>✓ Circadian rhythm: Sleep optimization enabled</li>
        </ul>
      </Card>
    </div>
  );
}
