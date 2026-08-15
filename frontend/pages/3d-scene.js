import React, { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import socketClient from '../utils/socketClient'

const ThreeScene = dynamic(() => import('../components/ThreeScene'), { ssr: false, loading: () => <div>Loading 3D scene...</div> })

export default function ScenePage() {
  const [entities, setEntities] = useState([])
  const [zones, setZones] = useState([])
  const [isPlacing, setIsPlacing] = useState(false)
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'
  const [currentPlacementPos, setCurrentPlacementPos] = useState(null)

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'
    const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null
    socketClient.initializeSocket(token, API_URL)

    const handle = (payload) => {
      setEntities((prev) => {
        if (payload.deleted) return prev.filter((e) => e.id !== payload.id)
        const idx = prev.findIndex((e) => e.id === payload.id)
        if (idx === -1) return [...prev, payload]
        const copy = [...prev]
        copy[idx] = { ...copy[idx], ...payload }
        return copy
      })
    }

    socketClient.subscribeToSceneEntities(handle)

    // fetch initial entities from backend API
    Promise.all([
      fetch(`${API_URL}/api/v1/scene/entities`).then((r) => {
        if (!r.ok) throw new Error(`status ${r.status}`)
        return r.json()
      }),
      fetch(`${API_URL}/api/v1/spatial/zones`).then((r) => {
        if (!r.ok) return []
        return r.json()
      }).catch(() => []),
    ])
      .then(([entitiesList, zonesList]) => {
        setEntities(entitiesList)
        setZones(zonesList || [])
      })
      .catch((err) => {
        console.error('Failed to fetch initial scene data', err)
      })

    return () => {
      socketClient.unsubscribeFromSceneEntities()
      socketClient.disconnectSocket()
    }
  }, [])

  const createEntity = async (payload) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null
    const resp = await fetch(`${API_URL}/api/v1/scene/entities`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    })
    if (!resp.ok) throw new Error(`status ${resp.status}`)
    const created = await resp.json()
    // update local list (server broadcasts too)
    setEntities((prev) => {
      const idx = prev.findIndex((e) => e.id === created.id)
      if (idx === -1) return [...prev, created]
      const copy = [...prev]
      copy[idx] = { ...copy[idx], ...created }
      return copy
    })
    return created
  }

  return (
    <div style={{ padding: 16 }}>
      <h1>3D Scene (Day 73)</h1>
      <div style={{ marginBottom: 8 }}>
        <button onClick={() => setIsPlacing((s) => !s)} className={`px-2 py-1 rounded ${isPlacing ? 'bg-red-500 text-white' : 'bg-slate-200'}`}>
          {isPlacing ? 'Cancel Placement' : 'Place New Entity'}
        </button>
      </div>
      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ flex: 1 }}>
          <h2>Entities</h2>
          <ul>
            {entities.map((e) => (
              <li key={e.id}>
                <strong>{e.name}</strong> — {e.type} @ {e.x},{e.y},{e.z}
              </li>
            ))}
          </ul>
          {isPlacing && (
            <div style={{ marginTop: 12 }}>
              <PlacementPanel
                placementPos={currentPlacementPos}
                onCreate={async ({ name, type, model, rotation }) => {
                  if (!currentPlacementPos) return alert('Pick a placement point by clicking the ground')
                  const payload = { name, type, x: currentPlacementPos.x, y: currentPlacementPos.z || 0, z: currentPlacementPos.y, rotation: rotation || 0, state: {}, model }
                  try {
                    await createEntity(payload)
                    setIsPlacing(false)
                  } catch (err) {
                    console.error('Failed to create entity', err)
                    alert('Failed to create entity')
                  }
                }}
              />
            </div>
          )}
        </div>
        <div style={{ width: 640, height: 480, border: '1px solid #ddd' }}>
          <h2 style={{ margin: 8 }}>3D View</h2>
          <ThreeScene entities={entities} zones={zones} onCreateEntity={createEntity} isPlacing={isPlacing} onPlacementChanged={(p) => setCurrentPlacementPos(p)} />
        </div>
      </div>
    </div>
  )
}

function PlacementPanel({ placementPos, onCreate }) {
  const [name, setName] = useState('New Device')
  const [type, setType] = useState('device')
  const [model, setModel] = useState('BoxTextured.glb')
  const [rotation, setRotation] = useState(0)

  const models = ['BoxTextured.glb', 'CesiumMilkTruck.glb', 'DamagedHelmet.glb', 'Fox.glb', 'ToyCar.glb']

  return (
    <div className="bg-white/95 p-3 rounded shadow-sm text-sm">
      <div className="font-bold">Place New Entity</div>
      <div className="mt-2 text-xs">Click on the ground in the 3D view to pick a placement point, then press Create.</div>
      <div className="mt-2">
        <label className="text-xs">Name</label>
        <input className="w-full" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div className="mt-2">
        <label className="text-xs">Type</label>
        <input className="w-full" value={type} onChange={(e) => setType(e.target.value)} />
      </div>
      <div className="mt-2">
        <label className="text-xs">Model</label>
        <select className="w-full" value={model} onChange={(e) => setModel(e.target.value)}>
          {models.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>
      <div className="mt-2 text-xs">Position: {placementPos ? `${placementPos.x.toFixed(2)}, ${placementPos.y.toFixed(2)}, ${placementPos.z.toFixed(2)}` : '—'}</div>
      <div className="mt-2">
        <label className="text-xs">Rotation (deg)</label>
        <input type="range" min="0" max="360" value={rotation} onChange={(e) => setRotation(Number(e.target.value))} />
        <div className="text-xs">{rotation.toFixed(0)}°</div>
      </div>
      <div className="mt-3 flex gap-2">
        <button
          onClick={() => onCreate({ name, type, model, rotation })}
          className="px-2 py-1 bg-aegis-primary text-white rounded"
        >
          Create
        </button>
      </div>
    </div>
  )
}
