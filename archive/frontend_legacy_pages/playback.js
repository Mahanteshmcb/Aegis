import React, { useEffect, useState } from 'react';
import useCurrentUser from '../../hooks/useCurrentUser';
import { createPlaybackSession, listPlaybackSessions, startPlaybackSession, stopPlaybackSession, exportPlaybackCSV } from '../../utils/api';

export default function AdminPlayback() {
  const { token } = useCurrentUser();
  const [sessions, setSessions] = useState([]);
  const [name, setName] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');

  const load = async () => {
    try {
      const res = await listPlaybackSessions(token);
      setSessions(res.data || []);
    } catch (e) {
      console.error(e);
      alert('Failed to load sessions');
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!name || !startTime || !endTime) return alert('Fill name, start and end');
    try {
      await createPlaybackSession(token, {
        name,
        start_time: new Date(startTime).toISOString(),
        end_time: new Date(endTime).toISOString(),
      });
      setName(''); setStartTime(''); setEndTime('');
      load();
    } catch (e) {
      console.error(e);
      alert('Failed to create session');
    }
  };

  const handleStart = async (id) => {
    try {
      await startPlaybackSession(token, id);
      load();
    } catch (e) { console.error(e); alert('Start failed'); }
  };

  const handleStop = async (id) => {
    try {
      await stopPlaybackSession(token, id);
      load();
    } catch (e) { console.error(e); alert('Stop failed'); }
  };

  const handleExport = async (id, name) => {
    try {
      const blob = await exportPlaybackCSV(token, id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${name || 'playback'}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) { console.error(e); alert('Export failed'); }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Telemetry Playback</h1>
      <div className="mb-4">
        <input className="border p-2 mr-2" placeholder="Name" value={name} onChange={(e)=>setName(e.target.value)} />
        <input type="datetime-local" className="border p-2 mr-2" value={startTime} onChange={(e)=>setStartTime(e.target.value)} />
        <input type="datetime-local" className="border p-2 mr-2" value={endTime} onChange={(e)=>setEndTime(e.target.value)} />
        <button className="bg-blue-600 text-white px-3 py-2 rounded" onClick={handleCreate}>Create</button>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-2">Sessions</h2>
        <table className="w-full table-auto border">
          <thead>
            <tr>
              <th className="border px-2 py-1">Name</th>
              <th className="border px-2 py-1">Range</th>
              <th className="border px-2 py-1">Status</th>
              <th className="border px-2 py-1">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map(s=> (
              <tr key={s.id}>
                <td className="border px-2 py-1">{s.name}</td>
                <td className="border px-2 py-1">{new Date(s.start_time).toLocaleString()} - {new Date(s.end_time).toLocaleString()}</td>
                <td className="border px-2 py-1">{s.status}</td>
                <td className="border px-2 py-1">
                  {s.status !== 'running' ? <button className="bg-green-600 text-white px-2 py-1 mr-2 rounded" onClick={()=>handleStart(s.id)}>Start</button> : <button className="bg-yellow-600 text-white px-2 py-1 mr-2 rounded" onClick={()=>handleStop(s.id)}>Stop</button>}
                  <button className="bg-gray-600 text-white px-2 py-1 mr-2 rounded" onClick={()=>handleExport(s.id, s.name)}>Export CSV</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
