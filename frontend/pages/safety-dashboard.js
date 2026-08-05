import { useEffect, useState } from 'react'
import useCurrentUser from '../hooks/useCurrentUser'
import {
  getPerimeterStatus,
  triggerPerimeterLockdown,
  releasePerimeterLockdown,
  verifyBiometricScan,
  getAccessControlLogs,
  getPatrolStatus,
  startRoboticPatrol,
  stopRoboticPatrol,
  getEvacuationStatus,
  triggerEvacuationProtocol,
  completeEvacuationProtocol,
} from '../utils/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function SafetyDashboard() {
  const { user, loading } = useCurrentUser()
  const [events, setEvents] = useState([])
  const [sensors, setSensors] = useState([])
  const [estop, setEstop] = useState({ active: false, reason: null })
  const [perimeter, setPerimeter] = useState({ active: false, reason: null, initiated_by: null })
  const [accessLogs, setAccessLogs] = useState([])
  const [patrol, setPatrol] = useState({
    active: false,
    route_name: null,
    assigned_robot: null,
    status: 'idle',
    started_at: null,
    completed_at: null,
  })
  const [evacuation, setEvacuation] = useState({
    active: false,
    initiated_by: null,
    incident_type: null,
    affected_zones: [],
    stage: 'standby',
    instructions: null,
    reason: null,
    started_at: null,
    ended_at: null,
  })
  const [evacType, setEvacType] = useState('security breach')
  const [evacZones, setEvacZones] = useState('Zone Alpha, Zone Bravo')
  const [biometricScanId, setBiometricScanId] = useState('BIO-ACCESS-001')
  const [biometricMethod, setBiometricMethod] = useState('fingerprint')
  const [biometricResponse, setBiometricResponse] = useState(null)
  const [loadingData, setLoadingData] = useState(true)
  const [actionInProgress, setActionInProgress] = useState(false)

  useEffect(() => {
    if (!loading && user) {
      fetchData()
      subscribeToEvents()
    }
    return () => {
      if (window.__safetyEventSource) {
        window.__safetyEventSource.close()
        window.__safetyEventSource = null
      }
    }
  }, [loading, user])

  function subscribeToEvents() {
    try {
      const es = new EventSource(`${API_URL}/api/v1/stream/events`)
      window.__safetyEventSource = es
      es.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data)
          if (data && data.type === 'safety_event') {
            setEvents((prev) => [
              {
                id: Date.now(),
                severity: data.severity || 'info',
                message: data.message,
                created_at: new Date().toISOString(),
              },
              ...prev,
            ])
          }
        } catch (err) {
          console.error('SSE parse', err)
        }
      }
    } catch (err) {
      console.error('SSE error', err)
    }
  }

  async function fetchData() {
    setLoadingData(true)
    const token = localStorage.getItem('aegis_token')
    try {
      const [ev, sn, es, perimeterData, accessLogData, patrolData, evacuationData] = await Promise.all([
        fetch(`${API_URL}/api/v1/safety/events`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/sensors`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/safety/estop`, { headers: { Authorization: `Bearer ${token}` } }),
        getPerimeterStatus(token).catch(() => null),
        getAccessControlLogs(token).catch(() => []),
        getPatrolStatus(token).catch(() => null),
        getEvacuationStatus(token).catch(() => null),
      ])

      setEvents(ev && ev.ok ? await ev.json() : [])
      setSensors(sn && sn.ok ? await sn.json() : [])
      if (es && es.ok) {
        setEstop(await es.json())
      }
      setPerimeter(perimeterData || { active: false, reason: null, initiated_by: null })
      setAccessLogs(Array.isArray(accessLogData) ? accessLogData : [])
      setPatrol(patrolData || { active: false, route_name: null, assigned_robot: null, status: 'idle', started_at: null, completed_at: null })
      setEvacuation(evacuationData || { active: false, initiated_by: null, incident_type: null, affected_zones: [], stage: 'standby', instructions: null, reason: null, started_at: null, ended_at: null })
    } catch (err) {
      console.error(err)
      // Set safe defaults on error
      setPerimeter({ active: false, reason: null, initiated_by: null })
      setAccessLogs([])
      setPatrol({ active: false, route_name: null, assigned_robot: null, status: 'idle', started_at: null, completed_at: null })
      setEvacuation({ active: false, initiated_by: null, incident_type: null, affected_zones: [], stage: 'standby', instructions: null, reason: null, started_at: null, ended_at: null })
    } finally {
      setLoadingData(false)
    }
  }

  async function changeEstop(enable) {
    setActionInProgress(true)
    const token = localStorage.getItem('aegis_token')
    try {
      const url = enable ? '/api/v1/safety/estop' : '/api/v1/safety/estop/release'
      const body = enable ? JSON.stringify({ reason: 'Manual emergency stop triggered from dashboard' }) : undefined
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body,
      })
      if (!resp.ok) throw new Error('Failed to update emergency stop')
      await fetchData()
    } catch (err) {
      console.error(err)
      alert('Unable to update emergency stop status')
    } finally {
      setActionInProgress(false)
    }
  }

  async function changePerimeterLockdown(enable) {
    setActionInProgress(true)
    const token = localStorage.getItem('aegis_token')
    try {
      if (enable) {
        await triggerPerimeterLockdown(token, {
          reason: 'Manual perimeter lockdown initiated from dashboard',
        })
      } else {
        await releasePerimeterLockdown(token)
      }
      await fetchData()
    } catch (err) {
      console.error(err)
      alert('Unable to update perimeter lockdown status')
    } finally {
      setActionInProgress(false)
    }
  }

  async function submitBiometricScan() {
    setActionInProgress(true)
    const token = localStorage.getItem('aegis_token')
    try {
      const payload = {
        user_name: user?.email || 'operator@aegis.com',
        scan_id: biometricScanId,
        biometric_type: biometricMethod,
        location: 'Main Gate',
      }
      const result = await verifyBiometricScan(token, payload)
      setBiometricResponse(result)
      await fetchData()
    } catch (err) {
      console.error(err)
      setBiometricResponse({ success: false, status: 'denied', message: err.message })
    } finally {
      setActionInProgress(false)
    }
  }

  async function startPatrol() {
    setActionInProgress(true)
    const token = localStorage.getItem('aegis_token')
    try {
      await startRoboticPatrol(token, {
        route_name: 'Perimeter Sweep Alpha',
        assigned_robot: 'Aegis Rover Patrol Unit',
        zone_sequence: ['Gate House', 'North Wall', 'East Tower', 'South Gate'],
        reason: 'Routine perimeter security sweep',
      })
      await fetchData()
    } catch (err) {
      console.error(err)
      alert('Unable to start robotic patrol')
    } finally {
      setActionInProgress(false)
    }
  }

  async function stopPatrol() {
    setActionInProgress(true)
    const token = localStorage.getItem('aegis_token')
    try {
      await stopRoboticPatrol(token)
      await fetchData()
    } catch (err) {
      console.error(err)
      alert('Unable to stop robotic patrol')
    } finally {
      setActionInProgress(false)
    }
  }

  async function triggerEvacuation() {
    setActionInProgress(true)
    const token = localStorage.getItem('aegis_token')
    try {
      await triggerEvacuationProtocol(token, {
        incident_type: evacType,
        affected_zones: evacZones.split(',').map((value) => value.trim()).filter(Boolean),
        reason: 'Triggered from safety dashboard',
      })
      await fetchData()
    } catch (err) {
      console.error(err)
      alert('Unable to trigger evacuation protocol')
    } finally {
      setActionInProgress(false)
    }
  }

  async function completeEvacuation() {
    setActionInProgress(true)
    const token = localStorage.getItem('aegis_token')
    try {
      await completeEvacuationProtocol(token)
      await fetchData()
    } catch (err) {
      console.error(err)
      alert('Unable to complete evacuation protocol')
    } finally {
      setActionInProgress(false)
    }
  }

  const severityCounts = events.reduce((acc, item) => {
    acc[item.severity || 'info'] = (acc[item.severity || 'info'] || 0) + 1
    return acc
  }, {})

  const sopSteps = [
    '1. Confirm alert source and location.',
    '2. Isolate affected equipment or zone immediately.',
    '3. Notify operations and safety team.',
    '4. Follow decontamination and ventilation procedures.',
    '5. Document event and update incident log.',
  ]

  if (loading || loadingData) return <div className="p-6">Loading safety dashboard...</div>

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Safety Dashboard</h1>
          <p className="text-sm text-slate-500 mt-2">
            Estate security, access control, and emergency response monitoring.
          </p>
        </div>
      </div>

      <section className="grid gap-4 xl:grid-cols-4">
        <div className="p-4 border rounded bg-white shadow-sm">
          <div className="text-sm text-slate-500">Emergency Stop</div>
          <div className="mt-2 text-2xl font-semibold">{estop.active ? 'ACTIVE' : 'CLEAR'}</div>
          <div className="text-sm text-gray-600 mt-2">
            {estop.active ? `Reason: ${estop.reason || 'No reason provided'}` : 'No emergency stop is active.'}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button disabled={actionInProgress || estop.active} onClick={() => changeEstop(true)} className="px-3 py-2 bg-red-600 text-white rounded disabled:opacity-60">
              Activate
            </button>
            <button disabled={actionInProgress || !estop.active} onClick={() => changeEstop(false)} className="px-3 py-2 bg-emerald-600 text-white rounded disabled:opacity-60">
              Release
            </button>
          </div>
        </div>

        <div className="p-4 border rounded bg-white shadow-sm">
          <div className="text-sm text-slate-500">Perimeter Lockdown</div>
          <div className="mt-2 text-2xl font-semibold">{perimeter.active ? 'LOCKED' : 'OPEN'}</div>
          <div className="text-sm text-gray-600 mt-2">
            {perimeter.active ? `Activated by ${perimeter.initiated_by || 'operator'}` : 'Perimeter is operating normally.'}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button disabled={actionInProgress || perimeter.active} onClick={() => changePerimeterLockdown(true)} className="px-3 py-2 bg-amber-600 text-slate-950 rounded disabled:opacity-60">
              Lockdown
            </button>
            <button disabled={actionInProgress || !perimeter.active} onClick={() => changePerimeterLockdown(false)} className="px-3 py-2 bg-slate-800 text-white rounded disabled:opacity-60">
              Release
            </button>
          </div>
        </div>

        <div className="p-4 border rounded bg-white shadow-sm">
          <div className="text-sm text-slate-500">Access Control Events</div>
          <div className="mt-2 text-2xl font-semibold">{accessLogs.length}</div>
          <div className="text-sm text-gray-600 mt-2">Latest biometric and perimeter actions stored securely.</div>
        </div>

        <div className="p-4 border rounded bg-white shadow-sm">
          <div className="text-sm text-slate-500">Recent Alerts</div>
          <div className="mt-2 text-2xl font-semibold">{events.length}</div>
          <div className="text-sm text-gray-600 mt-2">
            Critical: {severityCounts.critical || 0} / Warning: {severityCounts.warning || 0} / Info: {severityCounts.info || 0}
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="p-4 border rounded bg-white shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold mb-2">Robotic Patrol Control</h2>
              <p className="text-sm text-slate-500">Manage perimeter sweep missions and verify patrol coverage.</p>
            </div>
            <span className="text-xs uppercase tracking-[0.18em] text-slate-400">Patrol</span>
          </div>
          <div className="mt-4 space-y-2 text-sm text-slate-700">
            <div><strong>Status:</strong> {patrol.status.toUpperCase()}</div>
            <div><strong>Route:</strong> {patrol.route_name || 'N/A'}</div>
            <div><strong>Robot:</strong> {patrol.assigned_robot || 'Unassigned'}</div>
            <div><strong>Started:</strong> {patrol.started_at ? new Date(patrol.started_at).toLocaleString() : 'Not active'}</div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button disabled={actionInProgress || patrol.active} onClick={startPatrol} className="px-3 py-2 bg-slate-900 text-white rounded disabled:opacity-60">
              Start Patrol
            </button>
            <button disabled={actionInProgress || !patrol.active} onClick={stopPatrol} className="px-3 py-2 bg-amber-600 text-slate-950 rounded disabled:opacity-60">
              Stop Patrol
            </button>
          </div>
        </div>

        <div className="p-4 border rounded bg-white shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold mb-2">Evacuation Protocol</h2>
              <p className="text-sm text-slate-500">Trigger and resolve estate evacuation procedures.</p>
            </div>
            <span className="text-xs uppercase tracking-[0.18em] text-slate-400">Evacuation</span>
          </div>
          <div className="mt-4 space-y-2 text-sm text-slate-700">
            <div><strong>Active:</strong> {evacuation.active ? 'Yes' : 'No'}</div>
            <div><strong>Incident:</strong> {evacuation.incident_type || 'None'}</div>
            <div><strong>Stage:</strong> {evacuation.stage}</div>
            <div><strong>Zones:</strong> {evacuation.affected_zones?.join(', ') || 'None'}</div>
          </div>
          <div className="mt-4">
            <label className="block text-sm text-slate-600 mb-2">Incident Type</label>
            <input
              type="text"
              value={evacType}
              onChange={(event) => setEvacType(event.target.value)}
              className="w-full rounded border border-slate-300 px-3 py-2 mb-3"
            />
            <label className="block text-sm text-slate-600 mb-2">Affected Zones</label>
            <input
              type="text"
              value={evacZones}
              onChange={(event) => setEvacZones(event.target.value)}
              className="w-full rounded border border-slate-300 px-3 py-2 mb-4"
            />
            <div className="flex flex-wrap gap-2">
              <button disabled={actionInProgress || evacuation.active} onClick={triggerEvacuation} className="px-3 py-2 bg-red-600 text-white rounded disabled:opacity-60">
                Trigger Evacuation
              </button>
              <button disabled={actionInProgress || !evacuation.active} onClick={completeEvacuation} className="px-3 py-2 bg-emerald-600 text-white rounded disabled:opacity-60">
                Complete Evacuation
              </button>
            </div>
          </div>
          {evacuation.instructions ? (
            <div className="mt-4 rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800">
              <div className="font-semibold">Instructions</div>
              <div>{evacuation.instructions}</div>
            </div>
          ) : null}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="p-4 border rounded bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Biometric Entry Simulation</h2>
          <label className="block text-sm text-slate-600 mb-2">Scan ID</label>
          <input
            type="text"
            value={biometricScanId}
            onChange={(event) => setBiometricScanId(event.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 mb-3"
          />
          <label className="block text-sm text-slate-600 mb-2">Biometric Type</label>
          <select
            value={biometricMethod}
            onChange={(event) => setBiometricMethod(event.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 mb-4"
          >
            <option value="fingerprint">Fingerprint</option>
            <option value="iris">Iris</option>
            <option value="facial">Facial</option>
          </select>
          <button
            disabled={actionInProgress}
            onClick={submitBiometricScan}
            className="px-4 py-2 bg-slate-900 text-white rounded disabled:opacity-60"
          >
            Submit Biometric Scan
          </button>
          {biometricResponse ? (
            <div className="mt-4 rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800">
              <div className="font-semibold">Result: {biometricResponse.status.toUpperCase()}</div>
              <div>{biometricResponse.message}</div>
            </div>
          ) : null}
        </div>

        <div className="p-4 border rounded bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Standard Operating Procedures</h2>
          <div className="grid gap-2">
            {sopSteps.map((step) => (
              <div key={step} className="p-3 border rounded bg-slate-50">
                {step}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="p-4 border rounded bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Recent Safety Events</h2>
          {events.length === 0 ? (
            <p>No safety events.</p>
          ) : (
            <ul className="space-y-2">
              {events.map((e) => (
                <li key={e.id} className="p-3 border rounded bg-slate-50">
                  <div className="font-semibold">{(e.severity || 'info').toUpperCase()}</div>
                  <div className="text-sm text-slate-700">{e.message}</div>
                  <div className="text-xs text-slate-500 mt-1">{new Date(e.created_at).toLocaleString()}</div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="p-4 border rounded bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Access Control Log</h2>
          {accessLogs.length === 0 ? (
            <p>No access events recorded yet.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {accessLogs.slice(0, 8).map((log) => (
                <li key={log.id} className="rounded border border-slate-200 bg-slate-50 p-3">
                  <div className="font-semibold">{log.method} — {log.status.toUpperCase()}</div>
                  <div className="text-slate-700">{log.message}</div>
                  <div className="text-xs text-slate-500 mt-1">{new Date(log.created_at).toLocaleString()}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Sensor Health</h2>
        {sensors.length === 0 ? (
          <p>No sensors.</p>
        ) : (
          <ul className="space-y-2">
            {sensors.map((s) => (
              <li key={s.id} className="p-3 border rounded bg-white">
                <div className="font-semibold">{s.name || `Sensor ${s.id}`}</div>
                <div className="text-sm text-slate-700">Last reading: {JSON.stringify(s.last_reading) || 'N/A'}</div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
