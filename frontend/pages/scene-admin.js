import React, { useState } from 'react'

export default function SceneAdmin() {
  const [status, setStatus] = useState('unknown')
  const [tickSeconds, setTickSeconds] = useState(1.0)
  const [simStatus, setSimStatus] = useState(null)
  const [entities, setEntities] = useState([])
  const [selectedEntity, setSelectedEntity] = useState(null)
  const [autoIntervalId, setAutoIntervalId] = useState(null)
  const [commandText, setCommandText] = useState('')
  const [commandParams, setCommandParams] = useState('{}')
  const [jobs, setJobs] = useState([])
  const [jobName, setJobName] = useState('')
  const [jobScheduledAt, setJobScheduledAt] = useState('')
  const [jobDeviceId, setJobDeviceId] = useState(null)
  const [jobCron, setJobCron] = useState('')
  const [jobLogs, setJobLogs] = useState({})

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'

  const call = async (path) => {
    const res = await fetch(`${API_URL}/api/v1/scene/admin/${path}`, { method: 'POST' })
    const j = await res.json()
    setStatus(JSON.stringify(j))
    if (path === 'seed' || path === 'clear') loadEntities()
  }

  const setSpeed = async () => {
    const res = await fetch(`${API_URL}/api/v1/scene/admin/speed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seconds: Number(tickSeconds) }),
    })
    const j = await res.json()
    setStatus(JSON.stringify(j))
  }

  const loadStatus = async () => {
    const res = await fetch(`${API_URL}/api/v1/scene/admin/status`)
    const j = await res.json()
    setSimStatus(j)
  }

  const loadEntities = async () => {
    const res = await fetch(`${API_URL}/api/v1/scene/entities`)
    const list = await res.json()
    setEntities(list)
  }

  const selectEntity = (e) => {
    setSelectedEntity({ ...e })
    setJobDeviceId(e.id)
  }

  const saveEntity = async () => {
    if (!selectedEntity) return
    const res = await fetch(`${API_URL}/api/v1/scene/entities/${selectedEntity.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: selectedEntity.name,
        type: selectedEntity.type,
        x: Number(selectedEntity.x),
        y: Number(selectedEntity.y),
        z: Number(selectedEntity.z),
        rotation: Number(selectedEntity.rotation),
        state: selectedEntity.state || {},
      }),
    })
    const j = await res.json()
    setStatus(JSON.stringify(j))
    loadEntities()
  }

  const sendCommand = async () => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'
    let params = {}
    try {
      params = JSON.parse(commandParams)
    } catch (e) {
      setStatus('Invalid JSON for params')
      return
    }
    const payload = { event: 'robot:command', target_id: selectedEntity?.id, command: commandText, params }
    const res = await fetch(`${API_URL}/api/v1/scene/admin/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const j = await res.json()
    setStatus(JSON.stringify(j))
  }

  const loadJobs = async () => {
    const res = await fetch(`${API_URL}/api/v1/scene/admin/jobs`)
    const list = await res.json()
    setJobs(list)
  }

  const cancelJob = async (id) => {
    const res = await fetch(`${API_URL}/api/v1/scene/admin/job/${id}/cancel`, { method: 'POST' })
    const j = await res.json()
    setStatus(JSON.stringify(j))
    loadJobs()
  }

  const loadJobLogs = async (id) => {
    const res = await fetch(`${API_URL}/api/v1/scene/admin/job/${id}/logs`)
    const list = await res.json()
    setJobLogs((s) => ({ ...s, [id]: list }))
  }

  const [userRole, setUserRole] = useState('admin')

  const createJob = async () => {
    const payload = {
      name: jobName || commandText,
      command: commandText,
      parameters: JSON.parse(commandParams || '{}'),
      scheduled_at: jobScheduledAt || null,
      device_id: jobDeviceId || null,
      cron: jobCron || null,
    }
    const res = await fetch(`${API_URL}/api/v1/scene/admin/job`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-User-Role': userRole }, body: JSON.stringify(payload) })
    const j = await res.json()
    setStatus(JSON.stringify(j))
    loadJobs()
  }

  const toggleAuto = () => {
    if (autoIntervalId) {
      clearInterval(autoIntervalId)
      setAutoIntervalId(null)
      setStatus('Automation stopped')
      return
    }
    // send the current command every tickSeconds
    const id = setInterval(() => {
      sendCommand()
    }, Number(tickSeconds) * 1000)
    setAutoIntervalId(id)
    setStatus('Automation started')
  }

  // load initial state
  React.useEffect(() => {
    loadEntities()
    loadStatus()
  }, [])

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Scene Admin</h1>
      <div className="flex gap-2 mb-4">
        <button className="btn" onClick={() => call('pause')}>Pause Simulation</button>
        <button className="btn" onClick={() => call('resume')}>Resume Simulation</button>
        <button className="btn" onClick={() => call('seed')}>Seed Demo Entities</button>
        <button className="btn btn-danger" onClick={() => call('clear')}>Clear Entities</button>
      </div>
      <div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ marginRight: 8 }}>Tick seconds:</label>
          <input type="number" step="0.1" value={tickSeconds} onChange={(e) => setTickSeconds(e.target.value)} style={{ width: 80, marginRight: 8 }} />
          <button className="btn" onClick={setSpeed}>Set Speed</button>
          <button className="btn" onClick={loadStatus} style={{ marginLeft: 8 }}>Refresh Status</button>
        </div>
        <div style={{ marginBottom: 12 }}>
          <strong>Simulator:</strong> {simStatus ? JSON.stringify(simStatus) : 'unknown'}
        </div>
        <div style={{ marginBottom: 12 }}>
          <h3>Entities</h3>
          <button className="btn" onClick={loadEntities}>Refresh Entities</button>
          <ul>
            {entities.map((e) => (
              <li key={e.id} style={{ marginTop: 6 }}>
                <button className="btn" onClick={() => selectEntity(e)} style={{ marginRight: 8 }}>Select</button>
                <strong>{e.name}</strong> — {e.type} @ {Number(e.x).toFixed(2)},{Number(e.y).toFixed(2)},{Number(e.z).toFixed(2)}
              </li>
            ))}
          </ul>
          {selectedEntity ? (
            <div style={{ marginTop: 8 }}>
              <h4>Edit: {selectedEntity.name}</h4>
              <div style={{ display: 'flex', gap: 8 }}>
                <input value={selectedEntity.name} onChange={(e) => setSelectedEntity({ ...selectedEntity, name: e.target.value })} />
                <input value={selectedEntity.type} onChange={(e) => setSelectedEntity({ ...selectedEntity, type: e.target.value })} />
                <input value={selectedEntity.x} onChange={(e) => setSelectedEntity({ ...selectedEntity, x: e.target.value })} style={{ width: 80 }} />
                <input value={selectedEntity.y} onChange={(e) => setSelectedEntity({ ...selectedEntity, y: e.target.value })} style={{ width: 80 }} />
                <input value={selectedEntity.z} onChange={(e) => setSelectedEntity({ ...selectedEntity, z: e.target.value })} style={{ width: 80 }} />
                <input value={selectedEntity.rotation} onChange={(e) => setSelectedEntity({ ...selectedEntity, rotation: e.target.value })} style={{ width: 80 }} />
                <button className="btn" onClick={saveEntity}>Save</button>
              </div>
            </div>
          ) : null}
        </div>

        <div style={{ marginBottom: 12 }}>
          <h3>Manual Command</h3>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input placeholder="command (e.g. start)" value={commandText} onChange={(e) => setCommandText(e.target.value)} />
            <input placeholder='params as JSON' value={commandParams} onChange={(e) => setCommandParams(e.target.value)} style={{ width: 240 }} />
            <button className="btn" onClick={sendCommand}>Send</button>
            <button className="btn" onClick={toggleAuto}>{autoIntervalId ? 'Stop Auto' : 'Start Auto'}</button>
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <h3>Automation Jobs</h3>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input placeholder="job name" value={jobName} onChange={(e) => setJobName(e.target.value)} />
            <input placeholder="scheduled at (ISO)" value={jobScheduledAt} onChange={(e) => setJobScheduledAt(e.target.value)} style={{ width: 220 }} />
            <select value={jobDeviceId || ''} onChange={(e) => setJobDeviceId(e.target.value ? Number(e.target.value) : null)}>
              <option value="">-- device (optional) --</option>
              {entities.map((en) => (
                <option key={en.id} value={en.id}>{en.name} ({en.type})</option>
              ))}
            </select>
            <input placeholder="cron (optional)" value={jobCron} onChange={(e) => setJobCron(e.target.value)} style={{ width: 160 }} />
            <select value={userRole} onChange={(e) => setUserRole(e.target.value)} style={{ marginLeft: 8 }}>
              <option value="admin">admin</option>
              <option value="operator">operator</option>
              <option value="viewer">viewer</option>
            </select>
            <button className="btn" onClick={createJob}>Create Job</button>
            <button className="btn" onClick={loadJobs}>Refresh Jobs</button>
          </div>
          <ul>
            {jobs.map((j) => (
              <li key={j.id} style={{ marginTop: 6 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <strong>{j.name}</strong>
                  <span style={{ color: '#666' }}>{j.command}</span>
                  <span style={{ color: '#666' }}>{j.scheduled_at || 'now'}</span>
                  <span style={{ color: '#666' }}>{j.status}</span>
                  <button className="btn" onClick={() => cancelJob(j.id)}>Cancel</button>
                  <button className="btn" onClick={() => loadJobLogs(j.id)}>View Logs</button>
                </div>
                {jobLogs[j.id] ? (
                  <pre style={{ background: '#fafafa', padding: 8, marginTop: 6 }}>{JSON.stringify(jobLogs[j.id], null, 2)}</pre>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
        <strong>Last response:</strong>
        <pre className="mt-2 p-2 bg-gray-100 rounded">{status}</pre>
      </div>
    </div>
  )
}
