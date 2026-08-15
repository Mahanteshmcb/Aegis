import React, { useRef, useEffect, useState, Suspense } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Html, Environment, ContactShadows, Sky, GizmoHelper, GizmoViewport, useCursor, useGLTF } from '@react-three/drei'

function EntityMesh({ entity, selected, onSelect, onHover }) {
  const ref = useRef()

  // Smoothly move to the entity position each frame with easing
  useFrame(() => {
    if (!ref.current) return
    const targetX = entity.x ?? 0
    const targetY = entity.z ?? 0
    const targetZ = entity.y ?? 0
    const ease = 0.14
    ref.current.position.x += (targetX - ref.current.position.x) * ease
    ref.current.position.y += (targetY - ref.current.position.y) * ease
    ref.current.position.z += (targetZ - ref.current.position.z) * ease
    // smoothly interpolate to stored entity.rotation (degrees) instead of auto-spinning
    const targetRotY = (entity.rotation ?? 0) * (Math.PI / 180)
    ref.current.rotation.y += (targetRotY - ref.current.rotation.y) * 0.12
  })

  const color = entity.type === 'robot' ? '#ff6b6b' : entity.type === 'pump' ? '#4dabf7' : '#90ee90'

  // Map logical entity types to model files in public/models
  const modelMap = {
    robot: { url: '/models/Fox.glb', scale: 0.25 },
    vehicle: { url: '/models/ToyCar.glb', scale: 0.5 },
    truck: { url: '/models/CesiumMilkTruck.glb', scale: 0.5 },
    device: { url: '/models/DamagedHelmet.glb', scale: 0.5 },
    box: { url: '/models/BoxTextured.glb', scale: 0.8 },
  }

  const modelEntry = entity.model ? { url: `/models/${entity.model}`, scale: 0.6 } : (modelMap[entity.type] || { url: null, scale: 0.6 })

  useCursor(true, 'pointer')

  return (
      <group
      ref={ref}
      position={[entity.x ?? 0, entity.z ?? 0, entity.y ?? 0]}
      onClick={() => onSelect(entity.id)}
      onPointerOver={(e) => {
        e.stopPropagation()
        if (onHover) onHover(entity.id, true)
      }}
      onPointerOut={(e) => {
        e.stopPropagation()
        if (onHover) onHover(entity.id, false)
      }}
    >
      {modelEntry.url ? (
        <Suspense fallback={<mesh>
          <boxGeometry args={[1, 0.6, 1]} />
          <meshStandardMaterial color={selected ? '#ffd43b' : color} roughness={0.4} metalness={0.1} />
        </mesh>}>
          <Model url={modelEntry.url} selected={selected} scale={modelEntry.scale} />
        </Suspense>
      ) : (
        <mesh castShadow receiveShadow>
          <boxGeometry args={[1, 0.6, 1]} />
          <meshStandardMaterial color={selected ? '#ffd43b' : color} roughness={0.4} metalness={0.1} />
        </mesh>
      )}

      <Html center distanceFactor={6} style={{ pointerEvents: 'none' }}>
        <div style={{ background: 'rgba(255,255,255,0.9)', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>
          <strong style={{ display: 'block' }}>{entity.name}</strong>
          <span style={{ fontSize: 11 }}>{entity.type}</span>
        </div>
      </Html>
    </group>
  )
}

function Model({ url, selected, scale = 0.6 }) {
  // load gltf and return primitive
  const { scene } = useGLTF(url)
  const s = selected ? Math.max(scale, 0.6) : scale
  return <primitive object={scene} scale={s} dispose={null} />
}

function SceneContent({ entities, selectedId, onSelect, onGroundClick, placingPreview, onPointerMove, onEntityHover }) {
  return (
    <>
      <ambientLight intensity={0.8} />
      <directionalLight position={[10, 20, 10]} intensity={1.0} castShadow shadow-mapSize-width={1024} shadow-mapSize-height={1024} />
      <Sky sunPosition={[100, 20, 10]} />
      <Environment preset="city" />

      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.5, 0]}
        receiveShadow
        onPointerDown={(e) => {
          e.stopPropagation()
          if (onGroundClick && e.point) {
            onGroundClick({ x: e.point.x, y: e.point.y, z: e.point.z })
          }
        }}
        onPointerMove={(e) => {
          e.stopPropagation()
          if (onPointerMove && e.point) {
            onPointerMove({ x: e.point.x, y: e.point.y, z: e.point.z })
          }
        }}
      >
        <planeGeometry args={[200, 200]} />
        <meshStandardMaterial color="#bfc7c2" roughness={0.9} metalness={0.0} />
      </mesh>
      {placingPreview && (
        <mesh position={[placingPreview.x, placingPreview.y, placingPreview.z]}>
          <cylinderGeometry args={[0.3, 0.3, 0.05, 16]} />
          <meshStandardMaterial color="#ffd43b" emissive="#ffd43b" emissiveIntensity={0.6} />
        </mesh>
      )}
      <ContactShadows position={[0, -0.51, 0]} opacity={0.6} scale={40} blur={2} far={2} />
      <gridHelper args={[100, 100, '#2b2b2b', '#1a1a1a']} />
      {entities.map((e) => (
        <EntityMesh key={e.id} entity={e} selected={selectedId === e.id} onSelect={onSelect} onHover={onEntityHover} />
      ))}
    </>
  )
}

// FollowCamera removed: replaced by CameraController which handles follow/center behavior

function CameraController({ follow, selected, centerRef, entities }) {
  const { camera, gl } = useThree()
  const controls = useThree().controls

  useFrame(() => {
    // Handle follow mode
    if (follow && selected) {
      const target = entities.find((e) => e.id === selected)
      if (target) {
        const tx = target.x ?? 0
        const ty = (target.z ?? 0) + 2
        const tz = target.y ?? 0
        camera.position.x += (tx - camera.position.x) * 0.08
        camera.position.y += (ty - camera.position.y) * 0.08
        camera.position.z += (tz + 6 - camera.position.z) * 0.08
        camera.lookAt(tx, ty, tz)
        if (controls) {
          controls.target.set(tx, ty, tz)
        }
      }
    }

    // Handle one-off center request
    if (centerRef && centerRef.current) {
      const id = centerRef.current
      const target = entities.find((e) => e.id === id)
      if (target) {
        const tx = target.x ?? 0
        const ty = (target.z ?? 0) + 2
        const tz = target.y ?? 0
        // desired camera position offset behind and above
        const desired = { x: tx + 0, y: ty + 4, z: tz + 8 }
        // lerp camera toward desired
        camera.position.x += (desired.x - camera.position.x) * 0.18
        camera.position.y += (desired.y - camera.position.y) * 0.18
        camera.position.z += (desired.z - camera.position.z) * 0.18
        if (controls) {
          controls.target.x += (tx - controls.target.x) * 0.18
          controls.target.y += (ty - controls.target.y) * 0.18
          controls.target.z += (tz - controls.target.z) * 0.18
          controls.update()
        }
        // stop when close enough
        const dx = camera.position.x - desired.x
        const dy = camera.position.y - desired.y
        const dz = camera.position.z - desired.z
        if (Math.sqrt(dx * dx + dy * dy + dz * dz) < 0.2) {
          centerRef.current = null
        }
      } else {
        centerRef.current = null
      }
    }
  })

  return null
}

function ZoneBox({ zone, highlighted = false }) {
  // Compute box size and center from spatial zone bounds (db coords in meters)
  const sizeX = Math.abs(zone.max_x - zone.min_x)
  const sizeY = Math.abs(zone.max_z - zone.min_z)
  const sizeZ = Math.abs(zone.max_y - zone.min_y)
  const centerX = (zone.min_x + zone.max_x) / 2
  const centerY = (zone.min_z + zone.max_z) / 2
  const centerZ = (zone.min_y + zone.max_y) / 2

  return (
    <group position={[centerX, centerY, centerZ]}>
      <mesh>
        <boxGeometry args={[Math.max(sizeX, 0.1), Math.max(sizeY, 0.1), Math.max(sizeZ, 0.1)]} />
        <meshStandardMaterial color={'#1f77b4'} transparent opacity={highlighted ? 0.22 : 0.12} roughness={0.9} />
      </mesh>
      <mesh>
        <boxGeometry args={[Math.max(sizeX, 0.1), Math.max(sizeY, 0.1), Math.max(sizeZ, 0.1)]} />
        <meshBasicMaterial color={highlighted ? '#ff7f0e' : '#1f77b4'} wireframe opacity={highlighted ? 0.9 : 0.6} />
      </mesh>
      <Html position={[0, sizeY / 2 + 0.2, 0]} distanceFactor={6} style={{ pointerEvents: 'none' }}>
        <div style={{ background: 'rgba(255,255,255,0.85)', padding: '4px 8px', borderRadius: 4, fontSize: 12 }}>
          <strong>{zone.name}</strong>
          <div style={{ fontSize: 11 }}>{zone.zone_type || zone.description || zone.location}</div>
        </div>
      </Html>
    </group>
  )
}


// Helper: check if point (x,y,z) is inside a spatial zone bounding box
function pointInZone(zone, x, y, z) {
  if (!zone) return false
  return x >= zone.min_x && x <= zone.max_x && y >= zone.min_z && y <= zone.max_z && z >= zone.min_y && z <= zone.max_y
}


export default function ThreeScene({ entities = [], zones = [], onCreateEntity = null, isPlacing = false, onPlacementChanged = null }) {
  const [selected, setSelected] = useState(null)
  const [follow, setFollow] = useState(false)
  const centerRef = useRef(null)
  const [placementPos, setPlacementPos] = useState(null)
  const [placingPreview, setPlacingPreview] = useState(null)
  const [placementRotation, setPlacementRotation] = useState(0)
  const [hoveredEntity, setHoveredEntity] = useState(null)
  const [highlightedZoneId, setHighlightedZoneId] = useState(null)
  // Note: Camera control happens inside Canvas via CameraController (useThree must run in Canvas)

  useEffect(() => {
    // preload common models found in public/models for snappy first render
    const models = ['/models/BoxTextured.glb', '/models/CesiumMilkTruck.glb', '/models/DamagedHelmet.glb', '/models/Fox.glb', '/models/ToyCar.glb']
    models.forEach((m) => {
      try {
        useGLTF.preload(m)
      } catch (e) {
        // ignore preload failures in dev
      }
    })
  }, [])

  useEffect(() => {
    // when placement mode is turned off clear preview
    if (!isPlacing) {
      setPlacementPos(null)
      setPlacingPreview(null)
    }
  }, [isPlacing])

  // notify parent page about current placement preview/position
  useEffect(() => {
    if (onPlacementChanged) {
      try {
        onPlacementChanged(placingPreview)
      } catch (e) {
        // ignore
      }
    }
  }, [placingPreview, onPlacementChanged])

  // handle entity hover -> highlight containing zone
  const handleEntityHover = (id, hovering) => {
    if (hovering) {
      setHoveredEntity(id)
      const ent = entities.find((e) => e.id === id)
      if (ent) {
        const z = zones.find((zz) => pointInZone(zz, ent.x, ent.y, ent.z))
        setHighlightedZoneId(z ? z.id : null)
      } else {
        setHighlightedZoneId(null)
      }
    } else {
      setHoveredEntity(null)
      setHighlightedZoneId(null)
    }
  }

  // Note: using internal animation loop to smoothly center camera when requested
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: 360, touchAction: 'none' }}>
      <Canvas shadows style={{ width: '100%', height: '100%' }} camera={{ position: [0, 10, 15], fov: 50 }}>
        <OrbitControls makeDefault enableDamping dampingFactor={0.08} />
        <GizmoHelper alignment="bottom-right" margin={[80, 80]}>
          <GizmoViewport />
        </GizmoHelper>
        <SceneContent
          entities={entities}
          selectedId={selected}
          onSelect={setSelected}
          onGroundClick={(p) => {
            // p is { x, y, z }
            if (onCreateEntity && isPlacing) {
              const snap = 0.5
              const sx = Math.round(p.x / snap) * snap
              const sy = Math.round(p.y / snap) * snap
              const sz = Math.round(p.z / snap) * snap
              setPlacementPos({ x: sx, y: sy, z: sz })
              setPlacingPreview({ x: sx, y: sy, z: sz })
            }
          }}
          onPointerMove={(p) => {
            if (onCreateEntity && isPlacing && p) {
              const snap = 0.5
              const sx = Math.round(p.x / snap) * snap
              const sy = Math.round(p.y / snap) * snap
              const sz = Math.round(p.z / snap) * snap
              setPlacingPreview({ x: sx, y: sy, z: sz })
            }
          }}
          placingPreview={placingPreview}
          onEntityHover={handleEntityHover}
        />
        {zones && zones.map((z) => (
          <ZoneBox key={z.id} zone={z} highlighted={z.id === highlightedZoneId} />
        ))}
        {/* highlight hovered entity's zone */}
        <CameraController follow={follow} selected={selected} centerRef={centerRef} entities={entities} />
      </Canvas>

      {/* overlay UI: read-only details + controls */}
      <div style={{ position: 'absolute', right: 12, top: 12, width: 340, maxWidth: '40%', pointerEvents: 'auto' }}>
        {selected && (
          <div className="bg-white/90 p-3 rounded shadow-sm text-sm text-slate-900">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-bold">{entities.find((e) => e.id === selected)?.name || 'Entity'}</div>
                <div className="text-xs text-slate-600">Type: {entities.find((e) => e.id === selected)?.type}</div>
              </div>
              <div className="ml-2">
                <button
                  onClick={() => {
                    // center camera on entity
                    centerRef.current = selected
                  }}
                  className="px-2 py-1 bg-aegis-primary text-white rounded text-xs mr-2"
                >
                  Center
                </button>
                <button
                  onClick={() => setFollow((f) => !f)}
                  className={`px-2 py-1 rounded text-xs ${follow ? 'bg-red-500 text-white' : 'bg-slate-200 text-slate-800'}`}
                >
                  {follow ? 'Unfollow' : 'Follow'}
                </button>
              </div>
            </div>
            <div className="mt-2 text-xs text-slate-700">
              <div>Position: {(() => {
                const e = entities.find((x) => x.id === selected)
                return e ? `${e.x}, ${e.y}, ${e.z}` : ''
              })()}</div>
              <div className="mt-1">Zone: {(() => {
                const e = entities.find((x) => x.id === selected)
                if (!e) return '—'
                const z = zones.find((zz) => pointInZone(zz, e.x, e.y, e.z))
                return z ? z.name : 'Unassigned'
              })()}</div>
              <div className="mt-2">Status: {(() => {
                const e = entities.find((x) => x.id === selected)
                return e && e.state ? JSON.stringify(e.state) : 'read-only'
              })()}</div>
            </div>
          </div>
        )}
      </div>

      {/* Placement panel removed from viewport — render placement controls in the page UI instead */}

    </div>
  )
}


function PlacementPanel({ isPlacing, placementPos, placementRotation = 0, onChangeRotation = () => {}, onCreate }) {
  const [name, setName] = useState('New Device')
  const [type, setType] = useState('device')
  const [model, setModel] = useState('BoxTextured.glb')

  const models = ['BoxTextured.glb', 'CesiumMilkTruck.glb', 'DamagedHelmet.glb', 'Fox.glb', 'ToyCar.glb']

  return (
    <div className="bg-white/95 p-3 rounded shadow-sm text-sm">
      <div className="font-bold">Place New Entity</div>
      <div className="mt-2 text-xs">Click on the ground to pick a placement point, then press Create.</div>
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
        <input type="range" min="0" max="360" value={placementRotation} onChange={(e) => onChangeRotation(Number(e.target.value))} />
        <div className="text-xs">{placementRotation.toFixed(0)}°</div>
      </div>
      <div className="mt-3 flex gap-2">
        <button
            onClick={() => {
            if (!placementPos) return alert('Pick a placement point by clicking the ground')
            const payload = { name, type, x: placementPos.x, y: placementPos.z || 0, z: placementPos.y, rotation: placementRotation, state: {}, model }
            onCreate(payload)
          }}
          className="px-2 py-1 bg-aegis-primary text-white rounded"
        >
          Create
        </button>
      </div>
    </div>
  )
}
