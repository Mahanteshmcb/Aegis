import { useCallback, useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/router'
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
  const router = useRouter()
  const { user, loading, token } = useCurrentUser()
  const [events, setEvents] = useState([])
  const [sensors, setSensors] = useState([])
  const [zones, setZones] = useState([])
  const [robots, setRobots] = useState([])
  const [estop, setEstop] = useState({ active: null, reason: null })
  const [perimeter, setPerimeter] = useState({ active: null, reason: null, initiated_by: null })
  const [accessLogs, setAccessLogs] = useState([])
  const [patrol, setPatrol] = useState({
    active: null,
    route_name: null,
    assigned_robot: null,
    status: 'unknown',
    started_at: null,
    completed_at: null,
  })
  const [evacuation, setEvacuation] = useState({
    active: null,
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
  const [evacZones, setEvacZones] = useState([])
  const [selectedRobotId, setSelectedRobotId] = useState('')
  const [biometricScanId, setBiometricScanId] = useState('BIO-ACCESS-001')
  const [biometricMethod, setBiometricMethod] = useState('fingerprint')
  const [biometricResponse, setBiometricResponse] = useState(null)
  const [loadingData, setLoadingData] = useState(true)
  const [actionInProgress, setActionInProgress] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const hasLoadedRef = useRef(false)

  const fetchData = useCallback(async () => {
    if (!token) return
    if (!hasLoadedRef.current) setLoadingData(true)
    try {
      const headers = { Authorization: `Bearer ${token}` }
      const [ev, sn, es, perimeterData, accessLogData, patrolData, evacuationData, zoneResponse, deviceResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/safety/events`, { headers }),
        fetch(`${API_URL}/api/v1/sensors`, { headers }),
        fetch(`${API_URL}/api/v1/safety/estop`, { headers }),
        getPerimeterStatus(token).catch(() => null),
        getAccessControlLogs(token).catch(() => []),
        getPatrolStatus(token).catch(() => null),
        getEvacuationStatus(token).catch(() => null),
        fetch(`${API_URL}/api/v1/zones`, { headers }).catch(() => null),
        fetch(`${API_URL}/api/v1/digital-twin/devices`, { headers }).catch(() => null),
      ])

      if (!ev.ok || !sn.ok || !es.ok) throw new Error('Unable to load safety status. Check the API connection and permissions.')
      const [eventData, sensorData, estopData] = await Promise.all([ev.json(), sn.json(), es.json()])
      setEvents(Array.isArray(eventData) ? eventData : [])
      setSensors(Array.isArray(sensorData) ? sensorData : [])
      setEstop(estopData)
      const zoneData = zoneResponse?.ok ? await zoneResponse.json().catch(() => []) : []
      setZones(Array.isArray(zoneData) ? zoneData : [])
      setEvacZones((selected) => selected.length ? selected : (Array.isArray(zoneData) ? zoneData.slice(0, 2).map((zone) => zone.name) : []))
      const deviceData = deviceResponse?.ok ? await deviceResponse.json().catch(() => []) : []
      const robotData = Array.isArray(deviceData) ? deviceData.filter((device) => device.kind === 'robot') : []
      setRobots(robotData)
      setSelectedRobotId((currentId) => robotData.some((robot) => String(robot.id) === String(currentId)) ? currentId : robotData[0]?.id?.toString() || '')
      if (perimeterData) setPerimeter(perimeterData)
      setAccessLogs(Array.isArray(accessLogData) ? accessLogData : [])
      if (patrolData) setPatrol(patrolData)
      if (evacuationData) setEvacuation(evacuationData)
      setError('')
    } catch (err) {
      setError(err.message || 'Unable to load safety status.')
    } finally {
      hasLoadedRef.current = true
      setLoadingData(false)
    }
  }, [token])

  useEffect(() => {
    if (!loading && user) fetchData()
    else if (!loading && !user) router.push('/login')
  }, [loading, user, fetchData, router])

  useEffect(() => {
    if (loading || !user) return undefined
    const interval = window.setInterval(fetchData, 20000)
    return () => window.clearInterval(interval)
  }, [loading, user, fetchData])

  async function changeEstop(enable) {
    setActionInProgress(true)
    setError('')
    try {
      const url = enable ? '/api/v1/safety/estop' : '/api/v1/safety/estop/release'
      const body = enable ? JSON.stringify({ reason: 'Manual emergency stop triggered from dashboard' }) : undefined
      const resp = await fetch(`${API_URL}${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body,
      })
      if (!resp.ok) throw new Error((await resp.json().catch(() => ({}))).detail || 'Failed to update emergency stop')
      setSuccess(enable ? 'Emergency stop activated.' : 'Emergency stop released.')
      await fetchData()
    } catch (err) {
      setError(err.message || 'Unable to update emergency stop status')
    } finally {
      setActionInProgress(false)
    }
  }

  async function changePerimeterLockdown(enable) {
    setActionInProgress(true)
    setError('')
    try {
      if (enable) {
        await triggerPerimeterLockdown(token, {
          reason: 'Manual perimeter lockdown initiated from dashboard',
        })
      } else {
        await releasePerimeterLockdown(token)
      }
      setSuccess(enable ? 'Perimeter lockdown activated.' : 'Perimeter lockdown released.')
      await fetchData()
    } catch (err) {
      setError(err.message || 'Unable to update perimeter lockdown status')
    } finally {
      setActionInProgress(false)
    }
  }

  async function submitBiometricScan() {
    setActionInProgress(true)
    setError('')
    try {
      const payload = {
        user_name: user?.email || 'operator@aegis.com',
        scan_id: biometricScanId,
        biometric_type: biometricMethod,
        location: 'Main Gate',
      }
      const result = await verifyBiometricScan(token, payload)
      setBiometricResponse(result)
      setSuccess(result.message || 'Biometric result recorded.')
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
    setError('')
    try {
      const selectedRobot = robots.find((robot) => String(robot.id) === String(selectedRobotId))
      if (!selectedRobot) throw new Error('Register a robot before starting a patrol.')
      await startRoboticPatrol(token, {
        route_name: 'Perimeter Patrol',
        assigned_robot: selectedRobot.device_id || selectedRobot.name,
        zone_sequence: zones.map((zone) => zone.name),
        reason: 'Routine perimeter security sweep',
      })
      setSuccess(`Patrol started with ${selectedRobot.name}.`)
      await fetchData()
    } catch (err) {
      setError(err.message || 'Unable to start robotic patrol')
    } finally {
      setActionInProgress(false)
    }
  }

  async function stopPatrol() {
    setActionInProgress(true)
    setError('')
    try {
      await stopRoboticPatrol(token)
      setSuccess('Robotic patrol stopped.')
      await fetchData()
    } catch (err) {
      setError(err.message || 'Unable to stop robotic patrol')
    } finally {
      setActionInProgress(false)
    }
  }

  async function triggerEvacuation() {
    setActionInProgress(true)
    setError('')
    try {
      if (!evacZones.length) throw new Error('Select at least one affected zone.')
      await triggerEvacuationProtocol(token, {
        incident_type: evacType,
        affected_zones: evacZones,
        reason: 'Triggered from safety dashboard',
      })
      setSuccess('Evacuation protocol triggered.')
      await fetchData()
    } catch (err) {
      setError(err.message || 'Unable to trigger evacuation protocol')
    } finally {
      setActionInProgress(false)
    }
  }

  async function completeEvacuation() {
    setActionInProgress(true)
    setError('')
    try {
      await completeEvacuationProtocol(token)
      setSuccess('Evacuation protocol completed.')
      await fetchData()
    } catch (err) {
      setError(err.message || 'Unable to complete evacuation protocol')
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

  if (loading || loadingData) return <div className="min-h-screen bg-slate-950 p-6 text-slate-200">Loading safety dashboard...</div>

  return (
    <div className="min-h-screen bg-slate-950 p-6 text-slate-100 space-y-6">
      {error && <div role="alert" className="rounded border border-red-700 bg-red-950/50 p-3 text-sm text-red-200">{error}</div>}
      {success && <div role="status" className="rounded border border-emerald-700 bg-emerald-950/50 p-3 text-sm text-emerald-200">{success}</div>}
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Safety Dashboard</h1>
          <p className="text-sm text-slate-400 mt-2">
            Estate security, access control, and emergency response monitoring.
          </p>
        </div>
      </div>

      <section className="grid gap-4 xl:grid-cols-4">
        <div className="p-4 border border-slate-700 rounded bg-slate-900/80 shadow-sm shadow-slate-950/50">
          <div className="text-sm text-slate-400">Emergency Stop</div>
          <div className="mt-2 text-2xl font-semibold text-white">{estop.active === true ? 'ACTIVE' : estop.active === false ? 'CLEAR' : 'UNKNOWN'}</div>
          <div className="text-sm text-slate-300 mt-2">
            {estop.active === true ? `Reason: ${estop.reason || 'No reason provided'}` : estop.active === false ? 'No emergency stop is active.' : 'Emergency-stop status unavailable.'}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button disabled={actionInProgress || estop.active !== false} onClick={() => changeEstop(true)} className="px-3 py-2 bg-red-600 text-white rounded disabled:opacity-60">
              Activate
            </button>
            <button disabled={actionInProgress || estop.active !== true} onClick={() => changeEstop(false)} className="px-3 py-2 bg-emerald-600 text-white rounded disabled:opacity-60">
              Release
            </button>
          </div>
        </div>

        <div className="p-4 border border-slate-700 rounded bg-slate-900/80 shadow-sm shadow-slate-950/50">
          <div className="text-sm text-slate-400">Perimeter Lockdown</div>
          <div className="mt-2 text-2xl font-semibold text-white">{perimeter.active === true ? 'LOCKED' : perimeter.active === false ? 'OPEN' : 'UNKNOWN'}</div>
          <div className="text-sm text-slate-300 mt-2">
            {perimeter.active === true ? `Activated by ${perimeter.initiated_by || 'operator'}` : perimeter.active === false ? 'Perimeter is operating normally.' : 'Perimeter status unavailable.'}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button disabled={actionInProgress || perimeter.active !== false} onClick={() => changePerimeterLockdown(true)} className="px-3 py-2 bg-amber-500 text-slate-950 rounded disabled:opacity-60">
              Lockdown
            </button>
            <button disabled={actionInProgress || perimeter.active !== true} onClick={() => changePerimeterLockdown(false)} className="px-3 py-2 bg-slate-700 text-white rounded disabled:opacity-60">
              Release
            </button>
          </div>
        </div>

        <div className="p-4 border border-slate-700 rounded bg-slate-900/80 shadow-sm shadow-slate-950/50">
          <div className="text-sm text-slate-400">Access Control Events</div>
          <div className="mt-2 text-2xl font-semibold text-white">{accessLogs.length}</div>
          <div className="text-sm text-slate-300 mt-2">Latest biometric and perimeter actions stored securely.</div>
        </div>

        <div className="p-4 border border-slate-700 rounded bg-slate-900/80 shadow-sm shadow-slate-950/50">
          <div className="text-sm text-slate-400">Recent Alerts</div>
          <div className="mt-2 text-2xl font-semibold text-white">{events.length}</div>
          <div className="text-sm text-slate-300 mt-2">
            Critical: {severityCounts.critical || 0} / Warning: {severityCounts.warning || 0} / Info: {severityCounts.info || 0}
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="p-4 border border-slate-700 rounded bg-slate-900/80 shadow-sm shadow-slate-950/50">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold mb-2 text-white">Robotic Patrol Control</h2>
              <p className="text-sm text-slate-400">Manage perimeter sweep missions and verify patrol coverage.</p>
            </div>
            <span className="text-xs uppercase tracking-[0.18em] text-slate-500">Patrol</span>
          </div>
          <div className="mt-4 space-y-2 text-sm text-slate-300">
            <div><strong className="text-slate-100">Status:</strong> {(patrol.status || 'unknown').toUpperCase()}</div>
            <div><strong className="text-slate-100">Route:</strong> {patrol.route_name || 'N/A'}</div>
            <div><strong className="text-slate-100">Robot:</strong> {patrol.assigned_robot || 'Unassigned'}</div>
            <div><strong className="text-slate-100">Started:</strong> {patrol.started_at ? new Date(patrol.started_at).toLocaleString() : 'Not active'}</div>
          </div>
          <label className="mt-4 block text-sm text-slate-400" htmlFor="patrol-robot">Assigned robot</label>
          <select id="patrol-robot" value={selectedRobotId} onChange={(event) => setSelectedRobotId(event.target.value)} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-white">
            <option value="">Select registered robot</option>
            {robots.map((robot) => <option key={robot.id} value={robot.id}>{robot.name} ({robot.status})</option>)}
          </select>
          <div className="mt-4 flex flex-wrap gap-2">
            <button disabled={actionInProgress || patrol.active !== false || !selectedRobotId || !zones.length} onClick={startPatrol} className="px-3 py-2 bg-slate-700 text-white rounded disabled:opacity-60">
              Start Patrol
            </button>
            <button disabled={actionInProgress || patrol.active !== true} onClick={stopPatrol} className="px-3 py-2 bg-amber-500 text-slate-950 rounded disabled:opacity-60">
              Stop Patrol
            </button>
          </div>
        </div>

        <div className="p-4 border border-slate-700 rounded bg-slate-900/80 shadow-sm shadow-slate-950/50">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold mb-2 text-white">Evacuation Protocol</h2>
              <p className="text-sm text-slate-400">Trigger and resolve estate evacuation procedures.</p>
            </div>
            <span className="text-xs uppercase tracking-[0.18em] text-slate-500">Evacuation</span>
          </div>
          <div className="mt-4 space-y-2 text-sm text-slate-300">
            <div><strong className="text-slate-100">Active:</strong> {evacuation.active === true ? 'Yes' : evacuation.active === false ? 'No' : 'Unknown'}</div>
            <div><strong className="text-slate-100">Incident:</strong> {evacuation.incident_type || 'None'}</div>
            <div><strong className="text-slate-100">Stage:</strong> {evacuation.stage}</div>
            <div><strong className="text-slate-100">Zones:</strong> {evacuation.affected_zones?.join(', ') || 'None'}</div>
          </div>
          <div className="mt-4">
            <label className="block text-sm text-slate-400 mb-2">Incident Type</label>
            <input
              type="text"
              value={evacType}
              onChange={(event) => setEvacType(event.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 mb-3 text-white placeholder-slate-500"
            />
            <label className="block text-sm text-slate-400 mb-2">Affected Zones</label>
            <select multiple value={evacZones} onChange={(event) => setEvacZones(Array.from(event.target.selectedOptions, (option) => option.value))} aria-label="Affected zones" className="w-full min-h-28 rounded border border-slate-700 bg-slate-950 px-3 py-2 mb-4 text-white">
              {zones.map((zone) => <option key={zone.id} value={zone.name}>{zone.name}</option>)}
            </select>
            <div className="flex flex-wrap gap-2">
              <button disabled={actionInProgress || evacuation.active !== false} onClick={triggerEvacuation} className="px-3 py-2 bg-red-600 text-white rounded disabled:opacity-60">
                Trigger Evacuation
              </button>
              <button disabled={actionInProgress || evacuation.active !== true} onClick={completeEvacuation} className="px-3 py-2 bg-emerald-600 text-white rounded disabled:opacity-60">
                Complete Evacuation
              </button>
            </div>
          </div>
          {evacuation.instructions ? (
            <div className="mt-4 rounded border border-slate-700 bg-slate-950/60 p-3 text-sm text-slate-200">
              <div className="font-semibold text-white">Instructions</div>
              <div>{evacuation.instructions}</div>
            </div>
          ) : null}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="p-4 border border-slate-700 rounded bg-slate-900/80 shadow-sm shadow-slate-950/50">
          <h2 className="text-lg font-semibold mb-3 text-white">Biometric Entry Simulation</h2>
          <label className="block text-sm text-slate-400 mb-2">Scan ID</label>
          <input
            type="text"
            value={biometricScanId}
            onChange={(event) => setBiometricScanId(event.target.value)}
            className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 mb-3 text-white"
          />
          <label className="block text-sm text-slate-400 mb-2">Biometric Type</label>
          <select
            value={biometricMethod}
            onChange={(event) => setBiometricMethod(event.target.value)}
            className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 mb-4 text-white"
          >
            <option value="fingerprint">Fingerprint</option>
            <option value="iris">Iris</option>
            <option value="facial">Facial</option>
          </select>
          <button
            disabled={actionInProgress}
            onClick={submitBiometricScan}
            className="px-4 py-2 bg-slate-700 text-white rounded disabled:opacity-60"
          >
            Submit Biometric Scan
          </button>
          {biometricResponse ? (
            <div className="mt-4 rounded border border-slate-700 bg-slate-950/60 p-3 text-sm text-slate-200">
              <div className="font-semibold text-white">Result: {biometricResponse.status.toUpperCase()}</div>
              <div>{biometricResponse.message}</div>
            </div>
          ) : null}
        </div>

        <div className="p-4 border border-slate-700 rounded bg-slate-900/80 shadow-sm shadow-slate-950/50">
          <h2 className="text-lg font-semibold mb-3 text-white">Standard Operating Procedures</h2>
          <div className="grid gap-2">
            {sopSteps.map((step) => (
              <div key={step} className="p-3 border border-slate-700 rounded bg-slate-950/60 text-slate-200">
                {step}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="p-4 border border-slate-700 rounded bg-slate-900/80 shadow-sm shadow-slate-950/50">
          <h2 className="text-lg font-semibold mb-3 text-white">Recent Safety Events</h2>
          {events.length === 0 ? (
            <p className="text-slate-400">No safety events.</p>
          ) : (
            <ul className="space-y-2">
              {events.map((e) => (
                <li key={e.id} className="p-3 border border-slate-700 rounded bg-slate-950/60">
                  <div className="font-semibold text-white">{(e.severity || 'info').toUpperCase()}</div>
                  <div className="text-sm text-slate-300">{e.message}</div>
                  <div className="text-xs text-slate-500 mt-1">{new Date(e.created_at).toLocaleString()}</div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="p-4 border border-slate-700 rounded bg-slate-900/80 shadow-sm shadow-slate-950/50">
          <h2 className="text-lg font-semibold mb-3 text-white">Access Control Log</h2>
          {accessLogs.length === 0 ? (
            <p className="text-slate-400">No access events recorded yet.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {accessLogs.slice(0, 8).map((log) => (
                <li key={log.id} className="rounded border border-slate-700 bg-slate-950/60 p-3">
                  <div className="font-semibold text-white">{log.method} — {log.status.toUpperCase()}</div>
                  <div className="text-slate-300">{log.message}</div>
                  <div className="text-xs text-slate-500 mt-1">{new Date(log.created_at).toLocaleString()}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-white">Sensor Health</h2>
        {sensors.length === 0 ? (
          <p className="text-slate-400">No sensors.</p>
        ) : (
          <ul className="space-y-2">
            {sensors.map((s) => (
              <li key={s.id} className="p-3 border border-slate-700 rounded bg-slate-900/80 text-slate-200">
                <div className="font-semibold text-white">{s.name || `Sensor ${s.id}`}</div>
                <div className="text-sm text-slate-300">Last reading: {JSON.stringify(s.last_reading) || 'N/A'}</div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
