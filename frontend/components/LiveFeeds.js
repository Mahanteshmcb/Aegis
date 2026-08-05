import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, Volume2, VolumeX, Maximize, Camera, Mic } from 'lucide-react';

// Live Feed Component for Cameras, Microphones, and Sensors
export function LiveFeed({ device, token }) {
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showTimeline, setShowTimeline] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const handlePlayback = (timestamp) => {
    // Simulate historical playback
    console.log(`Playing footage from: ${new Date(timestamp).toLocaleString()}`);
  };

  return (
    <div className="flex flex-col h-full bg-black rounded-lg overflow-hidden border border-slate-700">
      {/* Video/Feed Display */}
      <div className="flex-1 bg-gradient-to-br from-slate-900 to-black flex items-center justify-center relative">
        {device.type === 'camera' ? (
          <div className="w-full h-full flex flex-col items-center justify-center">
            <Camera size={64} className="text-slate-600 mb-4" />
            <p className="text-slate-400">📹 Live Camera Feed</p>
            <p className="text-xs text-slate-500 mt-2">Device: {device.name}</p>
            <div className="mt-4 text-xs text-slate-400">
              <p>Resolution: 1920x1080 @ 30fps</p>
              <p>Status: {device.status === 'active' ? '🟢 Streaming' : '🔴 Offline'}</p>
            </div>
          </div>
        ) : device.type === 'microphone' ? (
          <div className="w-full h-full flex flex-col items-center justify-center">
            <Mic size={64} className="text-slate-600 mb-4" />
            <p className="text-slate-400">🎤 Live Audio Feed</p>
            <p className="text-xs text-slate-500 mt-2">Device: {device.name}</p>
            <div className="mt-4 flex gap-2">
              {[...Array(20)].map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-gradient-to-t from-cyan-500 to-blue-500 rounded-full"
                  style={{
                    height: `${Math.random() * 30 + 10}px`,
                    animation: `pulse ${0.3 + Math.random() * 0.2}s infinite`,
                  }}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center">
            <p className="text-slate-400">📊 Sensor Data Stream</p>
            <p className="text-xs text-slate-500 mt-2">{device.name}</p>
            <div className="mt-4 text-sm text-slate-400">
              <p>Current Value: {device.value} {device.unit}</p>
              <p>Avg: {device.average} {device.unit}</p>
              <p>Status: {device.status}</p>
            </div>
          </div>
        )}

        {/* Recording Indicator */}
        {isPlaying && (
          <div className="absolute top-3 right-3 flex items-center gap-2 bg-red-900/80 px-3 py-1 rounded-full">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-xs text-red-200">LIVE</span>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="bg-slate-800/50 border-t border-slate-700 p-3 space-y-3">
        {/* Timeline */}
        {showTimeline && (
          <div className="space-y-2">
            <p className="text-xs text-slate-400">Historical Timeline (Past 24h)</p>
            <div className="h-8 bg-slate-900 rounded border border-slate-700 flex items-center px-2 cursor-pointer">
              {[...Array(24)].map((_, i) => (
                <div
                  key={i}
                  className="flex-1 h-6 mx-0.5 bg-slate-700/50 hover:bg-slate-600 rounded text-xs flex items-center justify-center cursor-pointer transition-colors"
                  onClick={() => handlePlayback(Date.now() - (24 - i) * 3600 * 1000)}
                  title={`${i}h ago`}
                >
                  {i === 0 && '24'}
                  {i === 23 && 'Now'}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Primary Controls */}
        <div className="flex gap-2 justify-between items-center">
          <div className="flex gap-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-slate-300 hover:text-white"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause size={16} /> : <Play size={16} />}
            </button>
            <button
              onClick={() => setShowTimeline(!showTimeline)}
              className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-slate-300 hover:text-white"
              title="Timeline"
            >
              <RotateCcw size={16} />
            </button>
          </div>

          <div className="text-xs text-slate-400 font-mono">
            {formatTime(recordingTime)}
          </div>

          <div className="flex gap-2">
            {device.type === 'microphone' && (
              <button
                onClick={() => setIsMuted(!isMuted)}
                className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-slate-300 hover:text-white"
                title={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
              </button>
            )}
            <button
              className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-slate-300 hover:text-white"
              title="Fullscreen"
            >
              <Maximize size={16} />
            </button>
          </div>
        </div>

        {/* Device Info */}
        <div className="grid grid-cols-3 gap-2 text-xs text-slate-400 bg-slate-900/30 p-2 rounded">
          <div>
            <p className="text-slate-500">Location</p>
            <p className="text-slate-300">{device.location}</p>
          </div>
          <div>
            <p className="text-slate-500">Status</p>
            <p className="text-green-400">{device.status}</p>
          </div>
          <div>
            <p className="text-slate-500">Last Update</p>
            <p className="text-slate-300">Now</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Multi-Feed Display Component
export function LiveFeedsGrid({ devices, token }) {
  const [selectedDeviceId, setSelectedDeviceId] = useState(devices[0]?.id);

  if (!devices || devices.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-900 rounded-lg border border-slate-700">
        <p className="text-slate-400">No active devices</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 w-full h-full auto-rows-fr">
      {/* Main Feed */}
      <div className="lg:col-span-2">
        {devices
          .filter(d => d.id === selectedDeviceId)
          .map(device => (
            <LiveFeed key={device.id} device={device} token={token} />
          ))}
      </div>

      {/* Device List */}
      <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden flex flex-col">
        <div className="p-3 border-b border-slate-700 bg-slate-900/50">
          <p className="text-sm font-semibold text-white">Active Devices</p>
        </div>
        <div className="flex-1 overflow-y-auto space-y-1 p-2">
          {devices.map(device => (
            <button
              key={device.id}
              onClick={() => setSelectedDeviceId(device.id)}
              className={`w-full p-2 rounded text-left transition-all ${
                selectedDeviceId === device.id
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <p className="text-sm font-medium">{device.name}</p>
              <p className="text-xs opacity-70">{device.type}</p>
              <p className={`text-xs mt-1 ${device.status === 'active' ? 'text-green-400' : 'text-red-400'}`}>
                ● {device.status}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
