import React, { useEffect, useRef, useState } from 'react';
import { ZoneVisualizer } from '../utils/ThreeJSVisualization';
import { SensorStream } from '../utils/SensorStream';
import { RoverController } from '../utils/RoverController';
import { DispatchVisualizer } from '../utils/DispatchVisualizer';

const Dashboard = () => {
  const r = useRef(null);
  const [t, setT] = useState(null);
  const [l, setL] = useState(false);
  const [z, setZ] = useState({});
  const [a, setA] = useState([]);
  const [d, setD] = useState([]);
  const [e, setE] = useState('');
  useEffect(() => {
    if (!r.current) return;
    const v = new ZoneVisualizer(r.current);
    v.init();
    return () => cancelAnimationFrame(v.animateId);
  }, []);
  const login = async () => {
    setE('');
    try {
      const res = await fetch('http://localhost:8001/api/v1/auth/login', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'admin@aegis.com', password: 'admin1234' })
      });
      if (res.ok) {
        const D = await res.json(); setT(D.access_token || D.session_token); setL(true); init();
      } else { const D = await res.json(); setE(D.detail || 'Failed'); }
    } catch (ex) { setE('Server down'); }
  };
  const init = async () => {
    try {
      const C = await fetch('http://localhost:8001/api/v1/estate-config/status', {
        headers: { Authorization: `Bearer ${t}` }
      }).then(r => r.json());
      v.loadConfig(C); r.setTargetZone('zone_alpha', C?.zones || []);
      const T = await fetch('http://localhost:8001/api/v1/tasks', {
        headers: { Authorization: `Bearer ${t}` }
      }).then(r => r.json()); setA(T || []);
      const H = await fetch('http://localhost:8001/api/v1/ai/dispatch-history', {
        headers: { Authorization: `Bearer ${t}` }
      }).then(r => r.json()); setD(H || []); disp.clear(); (H || []).forEach(d => disp.addDispatch(d)); setSt(disp.updateStats());
    } catch (ex) { console.error(ex); }
  };
  const h = (u) => {
    const { zone, sensorType, value, severity } = u.data || u;
    setZ(p => ({ ...p, [zone]: { ...p[zone], [sensorType]: { value, status: severity || 'normal' } } }));
    if (sensorType === 'motion' && value) { r.receiveTask({ title: 'Motion Alert', zone }); }
  };
  const c = async (tg) => {
    if (!t) return;
    const rq = await fetch('http://localhost:8001/api/v1/tasks', {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${t}` },
      body: JSON.stringify(tg)
    });
    if (rq.ok) { const nt = await rq.json(); setA(p => [nt, ...p]); r.receiveTask(nt); }
  };
  useEffect(() => {
    const ss = new SensorStream('http://localhost:8001');
// Connect rover WebSocket for real-time telemetry after login ss.subscribe(h); ss.startMonitoring();
    return () => { ss.subscribers = []; };
  }, []);
  return (
    <div style={{ padding: '10px', fontFamily: 'sans-serif' }}>
      {!l && (
        <div style={{ maxWidth: '300px', margin: '0 auto' }}>
          <h3>Aegis Login</h3>
          <input style={{ width: '100%', padding: '8px', margin: '4px 0' }} type='email' placeholder='Email' required />
          <input style={{ width: '100%', padding: '8px', margin: '4px 0' }} type='password' placeholder='Password' required />
          <button onClick={login} style={{ width: '100%', padding: '10px', marginTop: '8px' }}>Login</button>
          {e && <p style={{ color: 'red', marginTop: '8px' }}>{e}</p>}
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '10px', marginTop: '10px' }}>
        <div><h3>3D View</h3><div ref={r} style={{ width: '100%', height: '250px', background: '#1a1a2e' }} /><p style={{ textAlign: 'center', color: '#666', marginTop: '4px' }}>Login to enable</p></div>
        <div><h3>Sensors</h3>{Object.keys(z).length ? (
  <div>
    {Object.entries(z).map(([z, s]) => (
      <div key={z} style={{ padding: '6px', background: '#2a2a3e', marginBottom: '4px' }}>
        <strong>Zone {z}</strong>{Object.entries(s).map(([st, dd]) => (
          <span key={st}> {st}: {dd.value} ({dd.status})</span>
        ))}
      </div>
    ))}
  </div>
) : (
  <p>Loading...</p>
)}
</div>
        <div><h3>Tasks ({a.length})</h3>{a.length ? (
  <div>
    {a.map((t, i) => (
      <div key={i} style={{ padding: '4px', background: '#2a2a3e', marginBottom: '2px' }}>
        <strong>{t.title}</strong> in {t.zone} - {t.status || 'pending'}
      </div>
    ))}
  </div>
) : (
  <p>No tasks</p>
)}
<h4>Dispatches</h4>{d.length ? (
  <div>
    {d.slice(0, 3).map((d, i) => (
      <div key={i} style={{ padding: '4px', background: '#2a2a3e', marginBottom: '2px' }}>
        <strong>{d.ruleId}</strong> in {d.zone} ({d.severity})
      </div>
    ))}
  </div>
) : (
  <p>No dispatches</p>
)}
</div>
      </div>
      <div style={{ marginTop: '10px' }}>
        <h4>Dispatch Task</h4><select onChange={(e) => tf.zone = e.target.value} style={{ width: '100%', padding: '6px', marginBottom: '4px' }}><option value=''>Zone</option><option value='zone_alpha'>Alpha</option><option value='zone_beta'>Beta</option></select><input placeholder='Title' onChange={(e) => tf.title = e.target.value} style={{ width: '100%', padding: '6px', marginBottom: '6px' }} /><button onClick={() => c({ title: tf.title || 'New', zone: tf.zone })} style={{ width: '100%', padding: '6px', background: '#28a745', color: 'white', border: 'none' }}>Dispatch</button><div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>admin@aegis.com / admin1234</div>
      </div>
    </div>
  );
};
const tf = { zone: '', title: '' };
export default Dashboard;