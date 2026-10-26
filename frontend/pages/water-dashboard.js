import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, Droplet, Plus, RefreshCw, TrendingUp } from 'lucide-react';
import useCurrentUser from '../hooks/useCurrentUser';
import {
  createWaterCollectionSystem,
  getIrrigationSystems,
  getWaterCollectionSystems,
  getWaterPurificationUnits,
  getWaterQualityReadings,
  getWaterRecyclingLoops,
  advanceWaterSimulation,
} from '../utils/api';

export default function WaterDashboard() {
  const { loading: authLoading, token } = useCurrentUser();
  const [collections, setCollections] = useState([]);
  const [purificationUnits, setPurificationUnits] = useState([]);
  const [irrigationSystems, setIrrigationSystems] = useState([]);
  const [recyclingLoops, setRecyclingLoops] = useState([]);
  const [qualityReadings, setQualityReadings] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState({ system_name: '', collection_type: 'rainfall', capacity_liters: '', location: '' });

  const fetchWaterData = useCallback(async () => {
    if (!token) return;
    setLoadingData(true);
    try {
      const [collectionData, purificationData, irrigationData, recyclingData, qualityData] = await Promise.all([
        getWaterCollectionSystems(token),
        getWaterPurificationUnits(token),
        getIrrigationSystems(token),
        getWaterRecyclingLoops(token),
        Promise.all(['collection', 'purified', 'irrigation_input', 'irrigation_output']
          .map((location) => getWaterQualityReadings(token, location).catch(() => []))),
      ]);
      setCollections(Array.isArray(collectionData) ? collectionData : []);
      setPurificationUnits(Array.isArray(purificationData) ? purificationData : []);
      setIrrigationSystems(Array.isArray(irrigationData) ? irrigationData : []);
      setRecyclingLoops(Array.isArray(recyclingData) ? recyclingData : []);
      setQualityReadings(qualityData.flat().sort((left, right) => new Date(right.created_at) - new Date(left.created_at)));
      setError('');
    } catch (fetchError) {
      setError(fetchError.message || 'Unable to load water operations.');
    } finally {
      setLoadingData(false);
    }
  }, [token]);

  useEffect(() => {
    if (!authLoading && token) fetchWaterData();
  }, [authLoading, token, fetchWaterData]);

  const metrics = useMemo(() => {
    const storedVolume = collections.reduce((sum, system) => sum + Number(system.current_volume_liters || 0), 0);
    const totalCapacity = collections.reduce((sum, system) => sum + Number(system.capacity_liters || 0), 0);
    const dailyRecycled = recyclingLoops.reduce((sum, loop) => sum + Number(loop.daily_recycled_liters || 0), 0);
    const activeLoops = recyclingLoops.filter((loop) => loop.active).length;
    const quality = qualityReadings[0]?.overall_quality_status || 'No readings';
    return { storedVolume, totalCapacity, dailyRecycled, activeLoops, quality };
  }, [collections, qualityReadings, recyclingLoops]);

  const handleCreateSystem = async (event) => {
    event.preventDefault();
    const capacity = Number(formData.capacity_liters);
    if (!formData.system_name.trim() || !Number.isFinite(capacity) || capacity <= 0) {
      setError('Enter a system name and a capacity greater than zero.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await createWaterCollectionSystem(token, {
        ...formData,
        system_name: formData.system_name.trim(),
        capacity_liters: capacity,
        location: formData.location.trim() || null,
      });
      setFormData({ system_name: '', collection_type: 'rainfall', capacity_liters: '', location: '' });
      setShowForm(false);
      setSuccess('Collection system registered.');
      await fetchWaterData();
    } catch (createError) {
      setError(createError.message || 'Unable to register collection system.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAdvanceSimulation = async () => {
    setSimulating(true);
    setError('');
    try {
      const result = await advanceWaterSimulation(token);
      setSuccess(`Advanced one demo day. Rainfall ${result.rainfall_added_liters} L; recycled ${result.recycled_liters} L; irrigation used ${result.irrigation_used_liters} L. Synthetic quality readings are not generated.`);
      await fetchWaterData();
    } catch (simulationError) {
      setError(simulationError.message || 'Unable to advance water simulation.');
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
        <h1 className="text-4xl font-bold text-white mb-2">Water Management</h1>
        <p className="text-slate-400">Monitor and simulate water collection, purification, recycling, and irrigation. Demo values are generic, not measured.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleAdvanceSimulation} disabled={loadingData || simulating || !token} className="rounded bg-cyan-700 px-3 py-2 text-sm text-white disabled:opacity-50">
            {simulating ? 'Simulating...' : 'Advance 1 demo day'}
          </button>
          <button onClick={fetchWaterData} disabled={loadingData} className="inline-flex items-center gap-2 rounded border border-cyan-600/50 px-3 py-2 text-sm text-cyan-200 disabled:opacity-50">
            <RefreshCw size={16} /> {loadingData ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && <div role="alert" className="rounded border border-red-700 bg-red-900/20 p-3 text-sm text-red-200">{error}</div>}
      {success && <div role="status" className="rounded border border-emerald-700 bg-emerald-900/20 p-3 text-sm text-emerald-200">{success}</div>}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="br-linear-to-br from-blue-600/20 to-blue-700/10 border border-blue-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <Droplet className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Stored Volume</p>
          <p className="text-2xl font-bold text-white mt-1">{loadingData ? '—' : `${metrics.storedVolume.toLocaleString()} L`}</p>
          <p className="mt-1 text-xs text-slate-500">of {metrics.totalCapacity.toLocaleString()} L capacity</p>
        </div>
        <div className="br-linear-to-br from-green-600/20 to-green-700/10 border border-green-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <TrendingUp className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Daily Recycled</p>
          <p className="text-2xl font-bold text-white mt-1">{loadingData ? '—' : `${metrics.dailyRecycled.toLocaleString()} L`}</p>
        </div>
        <div className="br-linear-to-br from-cyan-600/20 to-cyan-700/10 border border-cyan-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <Droplet className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Active Recycling Loops</p>
          <p className="text-2xl font-bold text-white mt-1">{loadingData ? '—' : `${metrics.activeLoops}/${recyclingLoops.length}`}</p>
        </div>
        <div className="br-linear-to-br from-emerald-600/20 to-emerald-700/10 border border-emerald-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <AlertCircle className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Quality</p>
          <p className="text-2xl font-bold text-white mt-1 capitalize">{loadingData ? '—' : metrics.quality}</p>
        </div>
      </div>

      {/* Water Collection Systems */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Water Collection Systems</h2>
          <button
            onClick={() => setShowForm((visible) => !visible)}
            className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={20} /> {showForm ? 'Cancel' : 'Add System'}
          </button>
        </div>

        {showForm && <form onSubmit={handleCreateSystem} className="mb-6 grid gap-3 rounded border border-slate-700 bg-slate-900/70 p-4 md:grid-cols-4">
          <input required maxLength={200} aria-label="System name" value={formData.system_name} onChange={(event) => setFormData({ ...formData, system_name: event.target.value })} placeholder="System name" className="rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white" />
          <select aria-label="Collection type" value={formData.collection_type} onChange={(event) => setFormData({ ...formData, collection_type: event.target.value })} className="rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white">
            <option value="rainfall">Rainfall</option><option value="condensation">Condensation</option><option value="greywater">Greywater</option>
          </select>
          <input required type="number" min="1" step="any" aria-label="Capacity in liters" value={formData.capacity_liters} onChange={(event) => setFormData({ ...formData, capacity_liters: event.target.value })} placeholder="Capacity (L)" className="rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white" />
          <div className="flex gap-2"><input aria-label="Location" value={formData.location} onChange={(event) => setFormData({ ...formData, location: event.target.value })} placeholder="Location" className="min-w-0 flex-1 rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white" /><button type="submit" disabled={submitting} className="rounded bg-cyan-700 px-4 py-2 text-white disabled:opacity-50">{submitting ? 'Saving...' : 'Save'}</button></div>
        </form>}

        {loadingData ? <p className="py-8 text-center text-slate-400">Loading water systems...</p> : collections.length === 0 ? <p className="py-8 text-center text-slate-400">No collection systems registered.</p> : <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {collections.map((collection) => (
            <div key={collection.id} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">{collection.system_name}</h3>
                  <p className="text-sm text-slate-400 capitalize">{collection.collection_type}</p>
                </div>
                <Droplet className="text-blue-400" size={24} />
              </div>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-slate-300">Fill Level</span>
                    <span className="text-xs font-semibold text-white">{collection.capacity_liters > 0 ? Math.round((collection.current_volume_liters / collection.capacity_liters) * 100) : 0}%</span>
                  </div>
                  <div className="w-full bg-slate-600 rounded-full h-2">
                    <div 
                      className="h-2 rounded-full bg-blue-500"
                      style={{ width: `${collection.capacity_liters > 0 ? Math.min(100, (collection.current_volume_liters / collection.capacity_liters) * 100) : 0}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-400">Current</span>
                    <p className="text-white font-semibold">{Number(collection.current_volume_liters || 0).toLocaleString()} L</p>
                  </div>
                  <div>
                    <span className="text-slate-400">Capacity</span>
                    <p className="text-white font-semibold">{Number(collection.capacity_liters || 0).toLocaleString()} L</p>
                  </div>
                  <div className="col-span-2">
                    <span className="text-slate-400">Location</span>
                    <p className="text-white font-semibold text-sm">{collection.location || 'Not specified'}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>}
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">Recycling System</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Recycling Rate</p>
              <p className="font-semibold text-green-400">{metrics.activeLoops}/{recyclingLoops.length} active</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Filtered Volume</p>
              <p className="font-semibold text-green-400">{metrics.dailyRecycled.toLocaleString()} L/day</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">System Health</p>
              <p className="font-semibold text-green-400">{purificationUnits.filter((unit) => unit.status === 'ready' || unit.status === 'active').length}/{purificationUnits.length || '—'}</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Next Maintenance</p>
              <p className="font-semibold text-blue-400">{purificationUnits.filter((unit) => unit.status === 'maintenance').length} requiring maintenance</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">Irrigation Usage</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Daily Usage</p>
              <p className="font-semibold text-blue-400">{irrigationSystems.reduce((sum, system) => sum + Number(system.water_per_cycle_liters || 0), 0).toLocaleString()} L/cycle</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Plant Health Score</p>
              <p className="font-semibold text-green-400">{irrigationSystems.filter((system) => system.status === 'watering').length}/{irrigationSystems.length || '—'} watering</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Soil Moisture</p>
              <p className="font-semibold text-blue-400">{irrigationSystems.filter((system) => system.optimization_enabled).length}/{irrigationSystems.length || '—'} optimized</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Last Watering</p>
              <p className="font-semibold text-blue-400">{irrigationSystems.filter((system) => system.last_watering).length} with watering history</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
