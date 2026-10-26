import { useCallback, useEffect, useState } from 'react'
import useCurrentUser from '../hooks/useCurrentUser'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function Storage(){
  const { user, token, loading } = useCurrentUser()
  const [facilities, setFacilities] = useState([])
  const [inventory, setInventory] = useState([])
  const [loadingData, setLoadingData] = useState(true)
  const [selectedFacility, setSelectedFacility] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [saving, setSaving] = useState(false)
  const [simulating, setSimulating] = useState(false)
  const [editingItemId, setEditingItemId] = useState(null)
  const [editingItem, setEditingItem] = useState(null)
  const [editingFacilityId, setEditingFacilityId] = useState(null)
  const [editingFacility, setEditingFacility] = useState(null)
  const [search, setSearch] = useState('')
  const [expiryFilter, setExpiryFilter] = useState('all')
  const [updatedAt, setUpdatedAt] = useState(null)

  const [facilityForm, setFacilityForm] = useState({ name: '', location: '', type: '', capacity: '' })
  const [inventoryForm, setInventoryForm] = useState({ facility_id: '', name: '', description: '', quantity: '', unit: '', lot_number: '', expires_at: '' })

  const fetchData = useCallback(async () => {
    if (!token) return
    setLoadingData(true)
    try{
      const [fRes, iRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/storage/facilities`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/storage/inventory`, { headers: { Authorization: `Bearer ${token}` } }),
      ])
      const [facilityData, inventoryData] = await Promise.all([fRes.json().catch(() => []), iRes.json().catch(() => [])])
      if (!fRes.ok || !iRes.ok) throw new Error('Unable to load tenant storage data.')
      const nextFacilities = Array.isArray(facilityData) ? facilityData : []
      setFacilities(nextFacilities)
      setInventory(Array.isArray(inventoryData) ? inventoryData : [])
      setUpdatedAt(new Date())
      if (selectedFacility && !nextFacilities.some((facility) => facility.id === selectedFacility)) setSelectedFacility(null)
      setError('')
    }catch(err){
      setError(err.message || 'Unable to load tenant storage data.')
    }finally{
      setLoadingData(false)
    }
  }, [selectedFacility, token])

  async function advanceSimulation(){
    setSimulating(true)
    setError('')
    try{
      const response = await fetch(`${API_URL}/api/v1/storage/simulation/advance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
        body: JSON.stringify({ step_hours: 24 }),
      })
      const result = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(result.detail || 'Unable to advance storage simulation.')
      const consumed = Object.entries(result.consumed_by_unit || {})
        .map(([unit, amount]) => `${amount} ${unit}`)
        .join(', ')
      setSuccess(`Advanced one demo day. Simulated inventory use: ${consumed || 'none'}. Only demo lots were changed.`)
      await fetchData()
    }catch(err){
      setError(err.message || 'Unable to advance storage simulation.')
    }finally{
      setSimulating(false)
    }
  }

  useEffect(() => {
    if (!loading && user) fetchData()
  }, [loading, user, fetchData])

  async function createFacility(e){
    e.preventDefault()
    setSaving(true)
    setError('')
    try{
      const resp = await fetch(`${API_URL}/api/v1/storage/facilities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: facilityForm.name,
          location: facilityForm.location,
          type: facilityForm.type,
          capacity: facilityForm.capacity ? Number(facilityForm.capacity) : null,
        })
      })
      const result = await resp.json().catch(() => ({}))
      if(!resp.ok) throw new Error(result.detail || 'Failed to create facility')
      setFacilityForm({ name: '', location: '', type: '', capacity: '' })
      setSuccess('Storage facility created.')
      await fetchData()
    }catch(err){
      setError(err.message || 'Failed to create facility.')
    }finally{
      setSaving(false)
    }
  }

  async function createInventory(e){
    e.preventDefault()
    setSaving(true)
    setError('')
    try{
      const resp = await fetch(`${API_URL}/api/v1/storage/inventory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          facility_id: Number(inventoryForm.facility_id),
          name: inventoryForm.name,
          description: inventoryForm.description,
          quantity: Number(inventoryForm.quantity),
          unit: inventoryForm.unit,
          lot_number: inventoryForm.lot_number,
          expires_at: inventoryForm.expires_at ? new Date(inventoryForm.expires_at).toISOString() : null,
        })
      })
      const result = await resp.json().catch(() => ({}))
      if(!resp.ok) throw new Error(result.detail || 'Failed to create inventory item')
      setInventoryForm({ facility_id: '', name: '', description: '', quantity: '', unit: '', lot_number: '', expires_at: '' })
      setSuccess('Inventory item added.')
      await fetchData()
    }catch(err){
      setError(err.message || 'Failed to create inventory item.')
    }finally{
      setSaving(false)
    }
  }

  async function saveInventoryEdit(event){
    event.preventDefault()
    if (!editingItemId || !editingItem) return
    setSaving(true)
    setError('')
    try{
      const resp = await fetch(`${API_URL}/api/v1/storage/inventory/${editingItemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: editingItem.name,
          description: editingItem.description,
          quantity: Number(editingItem.quantity),
          unit: editingItem.unit,
          lot_number: editingItem.lot_number,
          expires_at: editingItem.expires_at ? new Date(editingItem.expires_at).toISOString() : null,
        }),
      })
      const result = await resp.json().catch(() => ({}))
      if (!resp.ok) throw new Error(result.detail || 'Unable to update inventory item.')
      setEditingItemId(null)
      setEditingItem(null)
      setSuccess('Inventory item updated.')
      await fetchData()
    }catch(err){
      setError(err.message || 'Unable to update inventory item.')
    }finally{
      setSaving(false)
    }
  }

  async function deleteInventoryItem(item){
    if (!window.confirm(`Delete inventory item "${item.name}"?`)) return
    setSaving(true)
    setError('')
    try{
      const resp = await fetch(`${API_URL}/api/v1/storage/inventory/${item.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      const result = await resp.json().catch(() => ({}))
      if (!resp.ok) throw new Error(result.detail || 'Unable to delete inventory item.')
      setSuccess('Inventory item deleted.')
      await fetchData()
    }catch(err){
      setError(err.message || 'Unable to delete inventory item.')
    }finally{
      setSaving(false)
    }
  }

  async function saveFacilityEdit(event){
    event.preventDefault()
    if (!editingFacilityId || !editingFacility) return
    setSaving(true)
    setError('')
    try{
      const resp = await fetch(`${API_URL}/api/v1/storage/facilities/${editingFacilityId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: editingFacility.name,
          location: editingFacility.location,
          type: editingFacility.type,
          capacity: editingFacility.capacity === '' ? null : Number(editingFacility.capacity),
        }),
      })
      const result = await resp.json().catch(() => ({}))
      if (!resp.ok) throw new Error(result.detail || 'Unable to update facility.')
      setEditingFacilityId(null)
      setEditingFacility(null)
      setSuccess('Facility updated.')
      await fetchData()
    }catch(err){
      setError(err.message || 'Unable to update facility.')
    }finally{
      setSaving(false)
    }
  }

  async function deleteFacility(facility){
    if (!window.confirm(`Delete facility "${facility.name}"?`)) return
    setSaving(true)
    setError('')
    try{
      const resp = await fetch(`${API_URL}/api/v1/storage/facilities/${facility.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      const result = await resp.json().catch(() => ({}))
      if (!resp.ok) throw new Error(result.detail || 'Unable to delete facility.')
      if (String(selectedFacility) === String(facility.id)) setSelectedFacility(null)
      setSuccess('Facility deleted.')
      await fetchData()
    }catch(err){
      setError(err.message || 'Unable to delete facility.')
    }finally{
      setSaving(false)
    }
  }

  if(loading) return <div className="min-h-screen bg-slate-950 p-6 text-slate-200">Checking session...</div>
  if(!user) return <div className="min-h-screen bg-slate-950 p-6 text-slate-200">Sign in to view tenant storage. <Link href="/login" className="text-cyan-300">Sign in</Link></div>

  const facilityInventory = selectedFacility ? inventory.filter(i => String(i.facility_id) === String(selectedFacility)) : []
  const expiryState = (item) => {
    if (!item.expires_at) return 'no-date'
    const time = new Date(item.expires_at).getTime()
    if (time < Date.now()) return 'expired'
    if (time <= Date.now() + 30 * 86400000) return 'expiring'
    return 'current'
  }
  const expiringSoon = inventory.filter((item) => expiryState(item) === 'expiring').length
  const expiredCount = inventory.filter((item) => expiryState(item) === 'expired').length
  const filteredFacilities = facilities.filter((facility) => `${facility.name} ${facility.location || ''} ${facility.type || ''}`.toLowerCase().includes(search.toLowerCase()))
  const filteredInventory = facilityInventory.filter((item) => {
    const matchesSearch = `${item.name} ${item.description || ''} ${item.lot_number || ''}`.toLowerCase().includes(search.toLowerCase())
    const state = expiryState(item)
    const matchesExpiry = expiryFilter === 'all' || (expiryFilter === 'attention' && ['expired', 'expiring'].includes(state)) || state === expiryFilter
    return matchesSearch && matchesExpiry
  })

  return (
    <div className="min-h-screen bg-slate-950 p-6 text-slate-100 space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-800 pb-4">
        <div><h1 className="text-3xl font-bold text-white">Storage Facility Management</h1><p className="mt-1 text-sm text-slate-400">Tenant facilities, stock records, lots, expiry tracking, and isolated demo inventory simulation.</p></div>
        <div className="flex items-center gap-3"><span className="text-xs text-slate-500">{updatedAt ? `Updated ${updatedAt.toLocaleTimeString()}` : 'No snapshot'}</span><button type="button" onClick={advanceSimulation} disabled={simulating || loadingData || !token} className="rounded bg-cyan-700 px-3 py-2 text-sm text-white disabled:opacity-50">{simulating ? 'Simulating...' : 'Advance 1 demo day'}</button><button type="button" onClick={fetchData} disabled={loadingData} className="rounded border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-cyan-600 disabled:opacity-50">{loadingData ? 'Refreshing...' : 'Refresh'}</button></div>
      </header>
      {error && <div role="alert" className="rounded border border-red-700 bg-red-900/20 p-3 text-sm text-red-200">{error}</div>}
      {success && <div role="status" className="rounded border border-emerald-700 bg-emerald-900/20 p-3 text-sm text-emerald-200">{success}</div>}
      {loadingData && <p className="text-sm text-slate-400">Refreshing storage data...</p>}
      <div className="grid gap-4 sm:grid-cols-4 text-sm">
        <div className="border-b border-slate-800 pb-3"><p className="text-slate-400">Facilities</p><p className="mt-1 text-2xl font-semibold">{facilities.length}</p></div>
        <div className="border-b border-slate-800 pb-3"><p className="text-slate-400">Inventory records</p><p className="mt-1 text-2xl font-semibold">{inventory.length}</p></div>
        <div className="border-b border-slate-800 pb-3"><p className="text-slate-400">Expiring within 30 days</p><p className="mt-1 text-2xl font-semibold">{expiringSoon}</p></div>
        <div className="border-b border-slate-800 pb-3"><p className="text-slate-400">Expired lots</p><p className="mt-1 text-2xl font-semibold">{expiredCount}</p></div>
      </div>

      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_14rem]">
        <label className="text-xs text-slate-400">Search facilities, items, lots
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Name, location, or lot number" className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" />
        </label>
        <label className="text-xs text-slate-400">Expiry status
          <select value={expiryFilter} onChange={(event) => setExpiryFilter(event.target.value)} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white">
            <option value="all">All inventory</option><option value="attention">Expired or expiring</option><option value="expired">Expired</option><option value="expiring">Expiring within 30 days</option><option value="current">More than 30 days</option><option value="no-date">No expiry date</option>
          </select>
        </label>
      </div>

      <section>
        <h2 className="text-xl font-semibold mb-3 text-white">Storage Facilities</h2>
        <details className="mb-4 max-w-lg border-b border-slate-800 pb-3">
        <summary className="cursor-pointer py-2 text-sm font-semibold text-cyan-200">Register a facility</summary>
        <form onSubmit={createFacility} className="mt-3 space-y-3 p-4 border border-slate-700 rounded bg-slate-900/80">
          <div>
            <label className="block text-sm font-medium text-slate-300">Facility Name</label>
            <input value={facilityForm.name} onChange={e => setFacilityForm({ ...facilityForm, name: e.target.value })} required className="w-full p-2 border border-slate-700 rounded bg-slate-950 text-white placeholder-slate-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300">Location</label>
            <input value={facilityForm.location} onChange={e => setFacilityForm({ ...facilityForm, location: e.target.value })} className="w-full p-2 border border-slate-700 rounded bg-slate-950 text-white placeholder-slate-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300">Type (cold/dry/chemical/etc)</label>
            <input value={facilityForm.type} onChange={e => setFacilityForm({ ...facilityForm, type: e.target.value })} className="w-full p-2 border border-slate-700 rounded bg-slate-950 text-white placeholder-slate-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300">Capacity</label>
            <input type="number" value={facilityForm.capacity} onChange={e => setFacilityForm({ ...facilityForm, capacity: e.target.value })} className="w-full p-2 border border-slate-700 rounded bg-slate-950 text-white placeholder-slate-500" />
          </div>
          <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50">{saving ? 'Saving...' : 'Create Facility'}</button>
        </form>
        </details>

        {facilities.length === 0 ? <p className="text-slate-400">No facilities yet.</p> : (
          <ul className="space-y-2">
            {filteredFacilities.map(f => (
              <li key={f.id} className={`border rounded p-4 ${selectedFacility === f.id ? 'bg-blue-950/60 border-blue-500' : 'bg-slate-900/80 border-slate-700'}`}>
                {editingFacilityId === f.id ? <form onSubmit={saveFacilityEdit} className="grid gap-2 sm:grid-cols-2">
                  <input required value={editingFacility.name} onChange={(event) => setEditingFacility({ ...editingFacility, name: event.target.value })} aria-label="Facility name" className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-white" />
                  <input value={editingFacility.location || ''} onChange={(event) => setEditingFacility({ ...editingFacility, location: event.target.value })} aria-label="Facility location" className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-white" />
                  <input value={editingFacility.type || ''} onChange={(event) => setEditingFacility({ ...editingFacility, type: event.target.value })} aria-label="Facility type" className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-white" />
                  <input type="number" value={editingFacility.capacity ?? ''} onChange={(event) => setEditingFacility({ ...editingFacility, capacity: event.target.value })} aria-label="Facility capacity" className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-white" />
                  <div className="flex gap-2 sm:col-span-2"><button disabled={saving} className="rounded bg-cyan-800 px-3 py-1 text-xs text-white">Save</button><button type="button" onClick={() => setEditingFacilityId(null)} className="rounded border border-slate-700 px-3 py-1 text-xs text-slate-200">Cancel</button></div>
                </form> : <div className="flex flex-wrap items-start justify-between gap-3">
                  <button type="button" onClick={() => setSelectedFacility(f.id)} aria-pressed={selectedFacility === f.id} className="min-w-0 flex-1 text-left">
                    <div className="font-semibold text-white">{f.name}</div>
                    <div className="text-sm text-slate-300">{f.location || 'No location'} · Type: {f.type || 'N/A'} · Capacity: {f.capacity ?? 'N/A'}</div>
                    <div className="mt-1 text-xs text-slate-400">{inventory.filter((item) => String(item.facility_id) === String(f.id)).length} records · {inventory.filter((item) => String(item.facility_id) === String(f.id) && ['expired', 'expiring'].includes(expiryState(item))).length} expiry attention</div>
                  </button>
                  <div className="flex gap-2"><button type="button" onClick={() => { setEditingFacilityId(f.id); setEditingFacility({ ...f }); }} className="text-xs text-cyan-200 hover:text-white">Edit</button><button type="button" onClick={() => deleteFacility(f)} disabled={saving || inventory.some((item) => String(item.facility_id) === String(f.id))} title={inventory.some((item) => String(item.facility_id) === String(f.id)) ? 'Remove or move inventory first' : 'Delete facility'} className="text-xs text-red-300 disabled:opacity-40">Delete</button></div>
                </div>}
              </li>
            ))}
          </ul>
        )}
      </section>

      {selectedFacility && (
        <section>
          <h2 className="text-xl font-semibold mb-3 text-white">Inventory for {facilities.find(f => f.id === selectedFacility)?.name}</h2>
          <details className="mb-4 max-w-lg border-b border-slate-800 pb-3">
          <summary className="cursor-pointer py-2 text-sm font-semibold text-cyan-200">Add inventory lot</summary>
          <form onSubmit={createInventory} className="mt-3 space-y-3 p-4 border border-slate-700 rounded bg-slate-900/80">
            <div>
              <label className="block text-sm font-medium text-slate-300">Item Name</label>
              <input value={inventoryForm.name} onChange={e => setInventoryForm({ ...inventoryForm, name: e.target.value })} required className="w-full p-2 border border-slate-700 rounded bg-slate-950 text-white placeholder-slate-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300">Description</label>
              <input value={inventoryForm.description} onChange={e => setInventoryForm({ ...inventoryForm, description: e.target.value })} className="w-full p-2 border border-slate-700 rounded bg-slate-950 text-white placeholder-slate-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300">Quantity</label>
              <input type="number" step="0.01" value={inventoryForm.quantity} onChange={e => setInventoryForm({ ...inventoryForm, quantity: e.target.value })} required className="w-full p-2 border border-slate-700 rounded bg-slate-950 text-white placeholder-slate-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300">Unit</label>
              <input value={inventoryForm.unit} onChange={e => setInventoryForm({ ...inventoryForm, unit: e.target.value })} placeholder="e.g., mL, kg, units" className="w-full p-2 border border-slate-700 rounded bg-slate-950 text-white placeholder-slate-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300">Lot Number</label>
              <input value={inventoryForm.lot_number} onChange={e => setInventoryForm({ ...inventoryForm, lot_number: e.target.value })} className="w-full p-2 border border-slate-700 rounded bg-slate-950 text-white placeholder-slate-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300">Expires At</label>
              <input type="datetime-local" value={inventoryForm.expires_at} onChange={e => setInventoryForm({ ...inventoryForm, expires_at: e.target.value })} className="w-full p-2 border border-slate-700 rounded bg-slate-950 text-white" />
            </div>
            <button type="submit" disabled={saving} className="px-4 py-2 bg-indigo-600 text-white rounded disabled:opacity-50">{saving ? 'Saving...' : 'Add Inventory Item'}</button>
          </form>
          </details>

          {filteredInventory.length === 0 ? <p className="text-slate-400">No inventory items match this facility and filter.</p> : (
            <ul className="space-y-2">
              {filteredInventory.map(item => (
                <li key={item.id} className="p-3 border border-slate-700 rounded bg-slate-900/80">
                  {editingItemId === item.id ? <form onSubmit={saveInventoryEdit} className="grid gap-2 sm:grid-cols-2">
                    <input required value={editingItem.name} onChange={(event) => setEditingItem({ ...editingItem, name: event.target.value })} aria-label="Inventory item name" className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-white" />
                    <input value={editingItem.description || ''} onChange={(event) => setEditingItem({ ...editingItem, description: event.target.value })} aria-label="Inventory item description" className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-white" />
                    <input type="number" step="0.01" required value={editingItem.quantity} onChange={(event) => setEditingItem({ ...editingItem, quantity: event.target.value })} aria-label="Inventory quantity" className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-white" />
                    <input value={editingItem.unit || ''} onChange={(event) => setEditingItem({ ...editingItem, unit: event.target.value })} aria-label="Inventory unit" className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-white" />
                    <input value={editingItem.lot_number || ''} onChange={(event) => setEditingItem({ ...editingItem, lot_number: event.target.value })} aria-label="Lot number" className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-white" />
                    <input type="datetime-local" value={editingItem.expires_at || ''} onChange={(event) => setEditingItem({ ...editingItem, expires_at: event.target.value })} aria-label="Expiry date" className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-white" />
                    <div className="flex gap-2 sm:col-span-2"><button disabled={saving} className="rounded bg-cyan-800 px-3 py-1 text-xs text-white">Save</button><button type="button" onClick={() => setEditingItemId(null)} className="rounded border border-slate-700 px-3 py-1 text-xs text-slate-200">Cancel</button></div>
                  </form> : <>
                    <div className="flex flex-wrap items-start justify-between gap-2"><div className="font-semibold text-white">{item.name}</div><span className={`text-xs uppercase ${expiryState(item) === 'expired' ? 'text-red-300' : expiryState(item) === 'expiring' ? 'text-amber-300' : 'text-slate-500'}`}>{expiryState(item) === 'no-date' ? 'No expiry date' : expiryState(item)}</span></div>
                    <div className="text-sm text-slate-300">{item.description || 'No description'}</div>
                    <div className="text-sm text-slate-400">Qty: {item.quantity} {item.unit || ''} — Lot: {item.lot_number || 'N/A'} — Expires: {item.expires_at ? new Date(item.expires_at).toLocaleDateString() : 'N/A'}</div>
                    <div className="mt-2 flex gap-3"><button type="button" onClick={() => { setEditingItemId(item.id); setEditingItem({ ...item, expires_at: item.expires_at ? new Date(item.expires_at).toISOString().slice(0, 16) : '' }); }} className="text-xs text-cyan-200 hover:text-white">Edit</button><button type="button" onClick={() => deleteInventoryItem(item)} disabled={saving} className="text-xs text-red-300 hover:text-red-100 disabled:opacity-50">Delete</button></div>
                  </>}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  )
}
