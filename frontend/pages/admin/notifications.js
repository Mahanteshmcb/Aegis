import React, { useEffect, useState } from 'react';
import useCurrentUser from '../../hooks/useCurrentUser';
import { createNotificationRule, listNotificationRules, deleteNotificationRule } from '../../utils/api';

export default function AdminNotifications(){
  const { token } = useCurrentUser();
  const [rules, setRules] = useState([]);
  const [name, setName] = useState('');
  const [condition, setCondition] = useState('');

  const load = async ()=>{
    try{
      const res = await listNotificationRules(token);
      setRules(res.data || []);
    }catch(e){console.error(e); alert('Failed to load rules')}
  }

  useEffect(()=>{load()},[])

  const handleCreate = async ()=>{
    try{
      await createNotificationRule(token, {name, condition});
      setName(''); setCondition('');
      load();
    }catch(e){console.error(e); alert('Create failed')}
  }

  const handleDelete = async (id)=>{
    if(!confirm('Delete rule?')) return;
    try{await deleteNotificationRule(token, id); load();}catch(e){console.error(e); alert('Delete failed')}
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Notification Rules</h1>
      <div className="mb-4">
        <input className="border p-2 mr-2" placeholder="Name" value={name} onChange={(e)=>setName(e.target.value)} />
        <input className="border p-2 mr-2" placeholder="Condition" value={condition} onChange={(e)=>setCondition(e.target.value)} />
        <button className="bg-blue-600 text-white px-3 py-2 rounded" onClick={handleCreate}>Create</button>
      </div>
      <ul>
        {rules.map(r=> (
          <li key={r.id} className="mb-2">
            <strong>{r.name}</strong>: {r.condition} <button className="ml-3 text-red-600" onClick={()=>handleDelete(r.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
