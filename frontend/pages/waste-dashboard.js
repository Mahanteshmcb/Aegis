import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, Plus, RefreshCw, Trash2, TrendingUp, Zap } from 'lucide-react';
import useCurrentUser from '../hooks/useCurrentUser';
import {
  createWasteContainer,
  getCompostingProcesses,
  getHazardousWasteStorage,
  getRecyclingProcesses,
  getWasteContainers,
  getWasteMetrics,
  getWasteProcessingLogs,
  getWasteSortingLogs,
  recordWasteSorting,
  advanceWasteSimulation,
} from '../utils/api';

export default function WasteDashboard() {
  const { loading: authLoading, token } = useCurrentUser();
  const [containers, setContainers] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [sortingLogs, setSortingLogs] = useState([]);
  const [compostingProcesses, setCompostingProcesses] = useState([]);
  const [recyclingProcesses, setRecyclingProcesses] = useState([]);
  const [hazardousStorage, setHazardousStorage] = useState([]);
  const [processingLogs, setProcessingLogs] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [showContainerForm, setShowContainerForm] = useState(false);
  const [showSortingForm, setShowSortingForm] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [containerForm, setContainerForm] = useState({ container_name: '', waste_type: 'organic', capacity_kg: '', location: '' });
  const [sortingForm, setSortingForm] = useState({ waste_type: 'organic', weight_kg: '', source_location: '', sorting_method: 'manual' });

  const fetchWasteData = useCallback(async () => {
    if (!token) return;
    setLoadingData(true);
    try {
      const [containerData, metricData, sortingData, compostingData, recyclingData, hazardousData, processingData] = await Promise.all([
        getWasteContainers(token),
        getWasteMetrics(token),
        getWasteSortingLogs(token),
        getCompostingProcesses(token),
        getRecyclingProcesses(token),
        getHazardousWasteStorage(token),
        getWasteProcessingLogs(token),
      ]);
      setContainers(Array.isArray(containerData) ? containerData : []);
      setMetrics(metricData);
      setSortingLogs(Array.isArray(sortingData) ? sortingData : []);
      setCompostingProcesses(Array.isArray(compostingData) ? compostingData : []);
      setRecyclingProcesses(Array.isArray(recyclingData) ? recyclingData : []);
      setHazardousStorage(Array.isArray(hazardousData) ? hazardousData : []);
      setProcessingLogs(Array.isArray(processingData) ? processingData : []);
      setError('');
    } catch (fetchError) {
      setError(fetchError.message || 'Unable to load waste operations.');
    } finally {
      setLoadingData(false);
    }
  }, [token]);

  useEffect(() => {
    if (!authLoading && token) fetchWasteData();
  }, [authLoading, token, fetchWasteData]);

  const totalLoad = useMemo(() => containers.reduce((sum, container) => sum + Number(container.current_load_kg || 0), 0), [containers]);
  const fullContainers = useMemo(() => containers.filter((container) => Number(container.capacity_kg) > 0 && Number(container.current_load_kg) / Number(container.capacity_kg) >= 0.8).length, [containers]);

  const submitContainer = async (event) => {
    event.preventDefault();
    const capacity = Number(containerForm.capacity_kg);
    if (!containerForm.container_name.trim() || !Number.isFinite(capacity) || capacity <= 0) {
      setError('Enter a container name and capacity greater than zero.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await createWasteContainer(token, { ...containerForm, container_name: containerForm.container_name.trim(), capacity_kg: capacity, location: containerForm.location.trim() || null });
      setContainerForm({ container_name: '', waste_type: 'organic', capacity_kg: '', location: '' });
      setShowContainerForm(false);
      setSuccess('Waste container registered.');
      await fetchWasteData();
    } catch (submitError) {
      setError(submitError.message || 'Unable to register container.');
    } finally {
      setSubmitting(false);
    }
  };

  const submitSorting = async (event) => {
    event.preventDefault();
    const weight = Number(sortingForm.weight_kg);
    if (!Number.isFinite(weight) || weight <= 0) {
      setError('Enter a sorting weight greater than zero.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await recordWasteSorting(token, { ...sortingForm, weight_kg: weight, source_location: sortingForm.source_location.trim() || null });
      setSortingForm({ waste_type: 'organic', weight_kg: '', source_location: '', sorting_method: 'manual' });
      setShowSortingForm(false);
      setSuccess('Sorting event recorded.');
      await fetchWasteData();
    } catch (submitError) {
      setError(submitError.message || 'Unable to record sorting event.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAdvanceSimulation = async () => {
    setSimulating(true);
    setError('');
    try {
      const result = await advanceWasteSimulation(token);
      setSuccess(`Advanced one demo day. Generated ${result.generated_waste_kg} kg; recovered ${result.recycled_output_kg} kg. Values use generic demo assumptions.`);
      await fetchWasteData();
    } catch (simulationError) {
      setError(simulationError.message || 'Unable to advance waste simulation.');
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
        <h1 className="text-4xl font-bold text-white mb-2">Waste Operations</h1>
        <p className="text-slate-400">Monitor and simulate collection, composting, and recycling. Demo values are generic, not measured.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleAdvanceSimulation} disabled={loadingData || simulating || !token} className="rounded bg-cyan-700 px-3 py-2 text-sm text-white disabled:opacity-50">
            {simulating ? 'Simulating...' : 'Advance 1 demo day'}
          </button>
          <button onClick={fetchWasteData} disabled={loadingData} className="inline-flex items-center gap-2 rounded border border-cyan-600/50 px-3 py-2 text-sm text-cyan-200 disabled:opacity-50">
            <RefreshCw size={16} /> {loadingData ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && <div role="alert" className="rounded border border-red-700 bg-red-900/20 p-3 text-sm text-red-200">{error}</div>}
      {success && <div role="status" className="rounded border border-emerald-700 bg-emerald-900/20 p-3 text-sm text-emerald-200">{success}</div>}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="br-linear-to-br from-slate-600/20 to-slate-700/10 border border-slate-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <Trash2 className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Total Waste</p>
          <p className="text-2xl font-bold text-white mt-1">{loadingData ? '—' : `${Number(metrics?.total_waste_collected_kg || 0).toLocaleString()} kg`}</p>
        </div>
        <div className="br-linear-to-br from-green-600/20 to-green-700/10 border border-green-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <Zap className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Recycling</p>
          <p className="text-2xl font-bold text-white mt-1">{loadingData ? '—' : `${Number(metrics?.recycling_rate_percent || 0).toFixed(1)}%`}</p>
        </div>
        <div className="br-linear-to-br from-yellow-600/20 to-yellow-700/10 border border-yellow-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <TrendingUp className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Composting</p>
          <p className="text-2xl font-bold text-white mt-1">{loadingData ? '—' : `${Number(metrics?.organic_waste_kg || 0).toLocaleString()} kg`}</p>
        </div>
        <div className="br-linear-to-br from-red-600/20 to-red-700/10 border border-red-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <AlertCircle className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Hazardous</p>
          <p className="text-2xl font-bold text-white mt-1">{loadingData ? '—' : `${Number(metrics?.hazardous_waste_kg || 0).toLocaleString()} kg`}</p>
        </div>
        <div className="br-linear-to-br from-cyan-600/20 to-cyan-700/10 border border-cyan-600/50 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <Zap className="text-slate-300" size={20} />
          </div>
          <p className="text-slate-400 text-sm font-semibold">Efficiency</p>
          <p className="text-2xl font-bold text-white mt-1">{loadingData ? '—' : `${Number(metrics?.waste_diversion_rate_percent || 0).toFixed(1)}%`}</p>
        </div>
      </div>

      {/* Waste Containers */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Waste Containers</h2>
          <div className="flex gap-2">
          <button onClick={() => setShowSortingForm((visible) => !visible)} className="flex items-center gap-2 border border-slate-600 text-slate-200 px-4 py-2 rounded-lg transition-colors">
            <TrendingUp size={18} /> {showSortingForm ? 'Cancel' : 'Record Sorting'}
          </button>
          <button
            onClick={() => setShowContainerForm((visible) => !visible)}
            className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={20} /> {showContainerForm ? 'Cancel' : 'Add Container'}
          </button>
          </div>
        </div>

        {showContainerForm && <form onSubmit={submitContainer} className="mb-4 grid gap-3 rounded border border-slate-700 bg-slate-900/70 p-4 md:grid-cols-4">
          <input required maxLength={200} aria-label="Container name" value={containerForm.container_name} onChange={(event) => setContainerForm({ ...containerForm, container_name: event.target.value })} placeholder="Container name" className="rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white" />
          <select aria-label="Waste type" value={containerForm.waste_type} onChange={(event) => setContainerForm({ ...containerForm, waste_type: event.target.value })} className="rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white"><option value="organic">Organic</option><option value="recyclable">Recyclable</option><option value="hazardous">Hazardous</option><option value="inert">Inert</option></select>
          <input required type="number" min="1" step="any" aria-label="Container capacity in kilograms" value={containerForm.capacity_kg} onChange={(event) => setContainerForm({ ...containerForm, capacity_kg: event.target.value })} placeholder="Capacity (kg)" className="rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white" />
          <div className="flex gap-2"><input aria-label="Container location" value={containerForm.location} onChange={(event) => setContainerForm({ ...containerForm, location: event.target.value })} placeholder="Location" className="min-w-0 flex-1 rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white" /><button disabled={submitting} type="submit" className="rounded bg-cyan-700 px-4 py-2 text-white disabled:opacity-50">{submitting ? 'Saving...' : 'Save'}</button></div>
        </form>}

        {showSortingForm && <form onSubmit={submitSorting} className="mb-4 grid gap-3 rounded border border-slate-700 bg-slate-900/70 p-4 md:grid-cols-4">
          <select aria-label="Sorted waste type" value={sortingForm.waste_type} onChange={(event) => setSortingForm({ ...sortingForm, waste_type: event.target.value })} className="rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white"><option value="organic">Organic</option><option value="recyclable">Recyclable</option><option value="hazardous">Hazardous</option><option value="inert">Inert</option></select>
          <input required type="number" min="0.01" step="any" aria-label="Sorted weight in kilograms" value={sortingForm.weight_kg} onChange={(event) => setSortingForm({ ...sortingForm, weight_kg: event.target.value })} placeholder="Weight (kg)" className="rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white" />
          <input aria-label="Sorting source location" value={sortingForm.source_location} onChange={(event) => setSortingForm({ ...sortingForm, source_location: event.target.value })} placeholder="Source location" className="rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white" />
          <div className="flex gap-2"><select aria-label="Sorting method" value={sortingForm.sorting_method} onChange={(event) => setSortingForm({ ...sortingForm, sorting_method: event.target.value })} className="min-w-0 flex-1 rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white"><option value="manual">Manual</option><option value="automated">Automated</option><option value="hybrid">Hybrid</option></select><button disabled={submitting} type="submit" className="rounded bg-cyan-700 px-4 py-2 text-white disabled:opacity-50">{submitting ? 'Saving...' : 'Record'}</button></div>
        </form>}

        {loadingData ? <p className="py-8 text-center text-slate-400">Loading waste operations...</p> : containers.length === 0 ? <p className="py-8 text-center text-slate-400">No waste containers registered.</p> : <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {containers.map((container) => (
            <div key={container.id} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">{container.container_name}</h3>
                  <p className="text-sm text-slate-400 capitalize">{container.waste_type}</p>
                </div>
                <Trash2 className="text-amber-400" size={24} />
              </div>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-slate-300">Fill Level</span>
                    <span className="text-xs font-semibold text-white">{container.capacity_kg > 0 ? Math.round((container.current_load_kg / container.capacity_kg) * 100) : 0}%</span>
                  </div>
                  <div className="w-full bg-slate-600 rounded-full h-2">
                    <div 
                      className="h-2 rounded-full bg-amber-500"
                      style={{ width: `${container.capacity_kg > 0 ? Math.min(100, (container.current_load_kg / container.capacity_kg) * 100) : 0}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-400">Status</span>
                    <p className={`${container.active ? 'text-green-400' : 'text-slate-400'} font-semibold`}>{container.active ? 'Active' : 'Inactive'}</p>
                  </div>
                  <div>
                    <span className="text-slate-400">Capacity</span>
                    <p className="text-white font-semibold">{Number(container.current_load_kg || 0).toLocaleString()} / {Number(container.capacity_kg || 0).toLocaleString()} kg</p>
                  </div>
                  <div><span className="text-slate-400">Location</span><p className="text-white font-semibold">{container.location || 'Not specified'}</p></div>
                  <div><span className="text-slate-400">Last emptied</span><p className="text-white font-semibold">{container.last_emptied ? new Date(container.last_emptied).toLocaleDateString() : 'Not recorded'}</p></div>
                </div>
              </div>
            </div>
          ))}
        </div>}
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">Recycling Operations</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Current Rate</p>
              <p className="font-semibold text-green-400">{Number(metrics?.recycling_rate_percent || 0).toFixed(1)}%</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Material Sorted</p>
              <p className="font-semibold text-green-400">{Number(metrics?.recyclable_waste_kg || 0).toLocaleString()} kg</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">System Health</p>
              <p className="font-semibold text-green-400">{fullContainers} containers at or above 80% capacity</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Next Maintenance</p>
              <p className="font-semibold text-blue-400">{containers.filter((container) => container.active).length}/{containers.length || '—'} active containers</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">Composting Process</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Active Batches</p>
              <p className="font-semibold text-blue-400">{compostingProcesses.length}</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Compost Ready</p>
              <p className="font-semibold text-green-400">{compostingProcesses.reduce((sum, process) => sum + Number(process.compost_output_kg || 0), 0).toLocaleString()} kg</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Avg Temperature</p>
              <p className="font-semibold text-blue-400">{compostingProcesses.length ? `${(compostingProcesses.reduce((sum, process) => sum + Number(process.temperature_celsius || 0), 0) / compostingProcesses.filter((process) => process.temperature_celsius != null).length || 0).toFixed(1)}°C` : '—'}</p>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
              <p className="text-slate-300 text-sm">Time to Ready</p>
              <p className="font-semibold text-blue-400">{recyclingProcesses.length} recycling processes</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-lg border border-slate-700 bg-slate-800/50 p-6">
          <h2 className="mb-4 text-xl font-bold text-white">Composting batches</h2>
          {compostingProcesses.length === 0 ? <p className="text-sm text-slate-400">No compost batches registered.</p> : <div className="space-y-3">{compostingProcesses.map((process) => <article key={process.id} className="rounded border border-slate-700 bg-slate-900/60 p-3">
            <div className="flex justify-between gap-3"><h3 className="font-semibold text-white">{process.process_name}</h3><span className="text-xs capitalize text-cyan-300">{process.status} · {process.stage || 'stage unavailable'}</span></div>
            <p className="mt-2 text-xs text-slate-400">Input {process.organic_input_kg} kg · remaining {process.current_weight_kg} kg · output {process.compost_output_kg} kg · {process.temperature_celsius ?? '—'}°C · moisture {process.moisture_percent ?? '—'}%</p>
          </article>)}</div>}
        </section>
        <section className="rounded-lg border border-slate-700 bg-slate-800/50 p-6">
          <h2 className="mb-4 text-xl font-bold text-white">Recycling batches</h2>
          {recyclingProcesses.length === 0 ? <p className="text-sm text-slate-400">No recycling batches registered.</p> : <div className="space-y-3">{recyclingProcesses.map((process) => <article key={process.id} className="rounded border border-slate-700 bg-slate-900/60 p-3">
            <div className="flex justify-between gap-3"><h3 className="font-semibold text-white">{process.process_name}</h3><span className="text-xs capitalize text-green-300">{process.status}</span></div>
            <p className="mt-2 text-xs text-slate-400">{process.material_type} · input {process.input_weight_kg} kg · output {process.output_weight_kg} kg · recovery {Number(process.recovery_rate_percent || 0).toFixed(1)}%</p>
          </article>)}</div>}
        </section>
      </div>

      <section className="rounded-lg border border-slate-700 bg-slate-800/50 p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2"><h2 className="text-xl font-bold text-white">Hazardous waste register</h2><span className="text-sm text-slate-400">{hazardousStorage.length} actual records</span></div>
        {hazardousStorage.length === 0 ? <p className="text-sm text-slate-400">No hazardous materials are registered. Demo mode does not invent chemical inventory or safety readings.</p> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b border-slate-700 text-slate-400"><th className="p-2">Material</th><th className="p-2">Classification</th><th className="p-2">Quantity</th><th className="p-2">Condition</th><th className="p-2">Location</th></tr></thead><tbody>{hazardousStorage.map((item) => <tr key={item.id} className="border-b border-slate-800 text-slate-200"><td className="p-2">{item.chemical_name}</td><td className="p-2">{item.hazard_classification || item.chemical_type}</td><td className="p-2">{item.quantity_liters} L</td><td className="p-2">{item.container_condition} · {item.is_sealed ? 'sealed' : 'unsealed'}</td><td className="p-2">{item.storage_location}</td></tr>)}</tbody></table></div>}
      </section>

      <section className="rounded-lg border border-slate-700 bg-slate-800/50 p-6">
        <h2 className="mb-4 text-xl font-bold text-white">Processing history</h2>
        {processingLogs.length === 0 ? <p className="text-sm text-slate-400">No processing events recorded yet. Advance the demo simulation to generate transparent simulation-only process logs.</p> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b border-slate-700 text-slate-400"><th className="p-2">Operation</th><th className="p-2">Waste</th><th className="p-2">Input</th><th className="p-2">Output</th><th className="p-2">Completed</th></tr></thead><tbody>{processingLogs.slice(0, 10).map((log) => <tr key={log.id} className="border-b border-slate-800 text-slate-200"><td className="p-2 capitalize">{log.operation_type}</td><td className="p-2 capitalize">{log.waste_category}</td><td className="p-2">{log.input_weight_kg} kg</td><td className="p-2">{log.output_weight_kg ?? '—'} kg</td><td className="p-2">{new Date(log.completed_at).toLocaleString()}</td></tr>)}</tbody></table></div>}
      </section>

      <section className="rounded-lg border border-slate-700 bg-slate-800/50 p-6">
        <h2 className="mb-4 text-xl font-bold text-white">Recent Sorting Activity</h2>
        {sortingLogs.length === 0 ? <p className="text-sm text-slate-400">No sorting events recorded.</p> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b border-slate-700 text-slate-400"><th className="p-2">Waste</th><th className="p-2">Weight</th><th className="p-2">Method</th><th className="p-2">Quality</th><th className="p-2">Time</th></tr></thead><tbody>{sortingLogs.slice(0, 8).map((log) => <tr key={log.id} className="border-b border-slate-800 text-slate-200"><td className="p-2 capitalize">{log.waste_type}</td><td className="p-2">{log.weight_kg} kg</td><td className="p-2 capitalize">{log.sorting_method}</td><td className="p-2">{log.contamination_detected ? 'Contamination detected' : `${log.quality_score ?? '—'}%`}</td><td className="p-2">{new Date(log.processed_at).toLocaleString()}</td></tr>)}</tbody></table></div>}
      </section>
    </div>
  );
}
