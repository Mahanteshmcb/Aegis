import { useEffect, useState } from 'react'
import useCurrentUser from '../hooks/useCurrentUser'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function Storage(){
  const { user, loading } = useCurrentUser()
  const [facilities, setFacilities] = useState([])
  const [inventory, setInventory] = useState([])
  const [loadingData, setLoadingData] = useState(true)
  const [selectedFacility, setSelectedFacility] = useState(null)

  const [facilityForm, setFacilityForm] = useState({ name: '', location: '', type: '', capacity: '' })
  const [inventoryForm, setInventoryForm] = useState({ facility_id: '', name: '', description: '', quantity: '', unit: '', lot_number: '', expires_at: '' })

  useEffect(()=>{
    if(!loading && user) {
      fetchData()
      // SSE subscription
      let es
      try{
        es = new EventSource(`${API_URL}/api/v1/stream/events`)
        es.onmessage = (ev) => {
          try{
            const data = JSON.parse(ev.data)
            if(data.type === 'inventory_update' || data.type === 'facility_update'){
              fetchData()
            }
          }catch(err){ console.error('SSE parse', err) }
        }
      }catch(err){ console.error('SSE error', err) }
      return ()=>{ if(es) es.close() }
    }
  }, [loading, user])

  async function fetchData(){
    setLoadingData(true)
    const token = localStorage.getItem('aegis_token')
    try{
      const [fRes, iRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/storage/facilities`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/storage/inventory`, { headers: { Authorization: `Bearer ${token}` } }),
      ])
      setFacilities(fRes.ok ? await fRes.json() : [])
      setInventory(iRes.ok ? await iRes.json() : [])
    }catch(err){
      console.error(err)
    }finally{
      setLoadingData(false)
    }
  }

  async function createFacility(e){
    e.preventDefault()
    const token = localStorage.getItem('aegis_token')
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
      if(!resp.ok) throw new Error('Failed to create facility')
      setFacilityForm({ name: '', location: '', type: '', capacity: '' })
      fetchData()
    }catch(err){
      console.error(err)
      alert('Failed to create facility')
    }
  }

  async function createInventory(e){
    e.preventDefault()
    const token = localStorage.getItem('aegis_token')
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
      if(!resp.ok) throw new Error('Failed to create inventory item')
      setInventoryForm({ facility_id: '', name: '', description: '', quantity: '', unit: '', lot_number: '', expires_at: '' })
      fetchData()
    }catch(err){
      console.error(err)
      alert('Failed to create inventory item')
    }
  }

  if(loading || loadingData) return <div className="p-6">Loading storage management...</div>

  const facilityInventory = selectedFacility ? inventory.filter(i => i.facility_id === selectedFacility) : []

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Storage Facility Management</h1>

      <section>
        <h2 className="text-xl font-semibold mb-3">Storage Facilities</h2>
        <form onSubmit={createFacility} className="space-y-3 max-w-lg mb-4 p-4 border rounded bg-gray-50">
          <div>
            <label className="block text-sm font-medium">Facility Name</label>
            <input value={facilityForm.name} onChange={e => setFacilityForm({ ...facilityForm, name: e.target.value })} required className="w-full p-2 border rounded" />
          </div>
          <div>
            <label className="block text-sm font-medium">Location</label>
            <input value={facilityForm.location} onChange={e => setFacilityForm({ ...facilityForm, location: e.target.value })} className="w-full p-2 border rounded" />
          </div>
          <div>
            <label className="block text-sm font-medium">Type (cold/dry/chemical/etc)</label>
            <input value={facilityForm.type} onChange={e => setFacilityForm({ ...facilityForm, type: e.target.value })} className="w-full p-2 border rounded" />
          </div>
          <div>
            <label className="block text-sm font-medium">Capacity</label>
            <input type="number" value={facilityForm.capacity} onChange={e => setFacilityForm({ ...facilityForm, capacity: e.target.value })} className="w-full p-2 border rounded" />
          </div>
          <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">Create Facility</button>
        </form>

        {facilities.length === 0 ? <p>No facilities yet.</p> : (
          <ul className="space-y-2">
            {facilities.map(f => (
              <li key={f.id} onClick={() => setSelectedFacility(f.id)} className={`p-4 border rounded cursor-pointer transition ${selectedFacility === f.id ? 'bg-blue-100 border-blue-500' : 'bg-white hover:bg-gray-50'}`}>
                <div className="font-semibold">{f.name}</div>
                <div className="text-sm text-gray-600">{f.location || 'No location'} — Type: {f.type || 'N/A'} — Capacity: {f.capacity || 'N/A'}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {selectedFacility && (
        <section>
          <h2 className="text-xl font-semibold mb-3">Inventory for {facilities.find(f => f.id === selectedFacility)?.name}</h2>
          <form onSubmit={createInventory} className="space-y-3 max-w-lg mb-4 p-4 border rounded bg-gray-50">
            <div>
              <label className="block text-sm font-medium">Item Name</label>
              <input value={inventoryForm.name} onChange={e => setInventoryForm({ ...inventoryForm, name: e.target.value })} required className="w-full p-2 border rounded" />
            </div>
            <div>
              <label className="block text-sm font-medium">Description</label>
              <input value={inventoryForm.description} onChange={e => setInventoryForm({ ...inventoryForm, description: e.target.value })} className="w-full p-2 border rounded" />
            </div>
            <div>
              <label className="block text-sm font-medium">Quantity</label>
              <input type="number" step="0.01" value={inventoryForm.quantity} onChange={e => setInventoryForm({ ...inventoryForm, quantity: e.target.value })} required className="w-full p-2 border rounded" />
            </div>
            <div>
              <label className="block text-sm font-medium">Unit</label>
              <input value={inventoryForm.unit} onChange={e => setInventoryForm({ ...inventoryForm, unit: e.target.value })} placeholder="e.g., mL, kg, units" className="w-full p-2 border rounded" />
            </div>
            <div>
              <label className="block text-sm font-medium">Lot Number</label>
              <input value={inventoryForm.lot_number} onChange={e => setInventoryForm({ ...inventoryForm, lot_number: e.target.value })} className="w-full p-2 border rounded" />
            </div>
            <div>
              <label className="block text-sm font-medium">Expires At</label>
              <input type="datetime-local" value={inventoryForm.expires_at} onChange={e => setInventoryForm({ ...inventoryForm, expires_at: e.target.value })} className="w-full p-2 border rounded" />
            </div>
            <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded">Add Inventory Item</button>
          </form>

          {facilityInventory.length === 0 ? <p>No inventory items in this facility.</p> : (
            <ul className="space-y-2">
              {facilityInventory.map(item => (
                <li key={item.id} className="p-3 border rounded">
                  <div className="font-semibold">{item.name}</div>
                  <div className="text-sm text-gray-600">{item.description || 'No description'}</div>
                  <div className="text-sm text-gray-700">Qty: {item.quantity} {item.unit || ''} — Lot: {item.lot_number || 'N/A'} — Expires: {item.expires_at ? new Date(item.expires_at).toLocaleDateString() : 'N/A'}</div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  )
}
