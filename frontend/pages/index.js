import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/router';
import Main from '../components/Main';
import Card from '../components/Card';
import Button from '../components/Button';
import ActivityLog from '../components/ActivityLog';
import ProtectedRoute from '../components/ProtectedRoute';
import TacticalMap from '../components/TacticalMap';
import { getTenantInfo, getZones, getSensors, getAuditLogs } from '../utils/api'; 

export default function Home() {
  const router = useRouter();
  const [tenantName, setTenantName] = useState('Initializing...');
  const [zones, setZones] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [aiReport, setAiReport] = useState(null);

  const refreshSystemState = useCallback(async () => {
    const token = localStorage.getItem('aegis_token');
    if (!token) {
      setIsLoading(false); 
      return false;
    }

    try {
      const results = await Promise.allSettled([
        getTenantInfo(token),
        getZones(token),
        getSensors(token),
        getAuditLogs(token)
      ]);

      const sessionExpired = results.some(r => 
        r.status === 'rejected' && (r.reason.message?.includes('401') || r.reason.status === 401)
      );

      if (sessionExpired) {
        console.warn("Session Expired (401). Forcing logout.");
        localStorage.removeItem('aegis_token');
        router.push('/login');
        return false; 
      }

      if (results[0].status === 'fulfilled') setTenantName(results[0].value.name);
      if (results[1].status === 'fulfilled') setZones(results[1].value || []);
      if (results[2].status === 'fulfilled') setSensors(results[2].value || []);
      if (results[3].status === 'fulfilled') setLogs(results[3].value?.slice(-10).reverse() || []);
      
      setError(null);
      return true;
    } catch (err) {
      console.error("Dashboard Sync Error:", err);
      return false;
    } finally {
      setIsLoading(false); 
    }
  }, [router]);

  useEffect(() => {
    let isSubscribed = true;
    let heartbeat;

    const startSync = async () => {
      if (!isSubscribed) return;
      const success = await refreshSystemState();
      
      if (success && isSubscribed) {
        heartbeat = setInterval(async () => {
           const stillValid = await refreshSystemState();
           if (!stillValid) {
              clearInterval(heartbeat);
           }
        }, 5000);
      }
    };

    startSync();

    return () => {
      isSubscribed = false;
      if (heartbeat) clearInterval(heartbeat);
    };
  }, [refreshSystemState]);

  const runVryndaraAnalysis = async () => {
    setIsAnalyzing(true);
    const token = localStorage.getItem('aegis_token');
    try {
      const response = await fetch('http://localhost:8080/api/v1/research/analysis/logs', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json' 
        }
      });
      const data = await response.json();
      setAiReport(data);
    } catch (err) {
      setError("AI Core unreachable");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getLatestTelemetry = () => {
    // 1. Ensure we have data
    if (!Array.isArray(sensors) || sensors.length === 0) {
      return { value: '---', unit: '' };
    }

    // 2. Sort by sensor_id descending to get the newest node first
    const sorted = [...sensors].sort((a, b) => {
      const idA = a.id || a.sensor_id || 0;
      const idB = b.id || b.sensor_id || 0;
      return idB - idA;
    });

    // 3. Iterate through to find the first sensor that actually has a value
    for (const sensor of sorted) {
      // THE FIX: Look directly at sensor.value, not sensor.last_reading!
      if (sensor.value !== null && sensor.value !== undefined) {
        const val = sensor.value;
        return {
          value: typeof val === 'number' ? val.toFixed(2) : parseFloat(val).toFixed(2),
          unit: sensor.unit || '°C'
        };
      }
    }

    // 4. If all sensors have null values, show waiting
    return { value: '---', unit: 'WAITING DATA' };
  };

  const telemetry = getLatestTelemetry();
  const hasValidValue = !['---'].includes(telemetry.value);
  const isAnomaly = hasValidValue && parseFloat(telemetry.value) > 23.5;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0b1120] flex items-center justify-center">
        <div className="text-aegis-primary font-mono text-sm animate-pulse tracking-widest uppercase">
          Initializing Holographic Stream...
        </div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <Main>
        {aiReport && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-aegis-primary p-6 rounded-lg max-w-md w-full shadow-[0_0_25px_rgba(0,242,255,0.2)]">
              <h3 className="text-aegis-primary font-mono uppercase tracking-tighter mb-4 text-xl underline decoration-aegis-primary/30">Vryndara Intel Report</h3>
              <p className="text-white mb-4 italic text-sm">"{aiReport.message}"</p>
              <ul className="space-y-2 mb-6">
                {aiReport.findings.map((f, i) => (
                  <li key={i} className="text-[11px] text-slate-400 border-l border-aegis-primary pl-2 uppercase font-mono">{f}</li>
                ))}
              </ul>
              <Button variant="secondary" onClick={() => setAiReport(null)}>Dismiss Access</Button>
            </div>
          </div>
        )}

        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-semibold text-white">System Overview</h2>
            <p className="text-aegis-primary font-mono text-xs tracking-[0.3em] uppercase mt-1">Sector: {tenantName}</p>
          </div>
          <Button variant="primary" onClick={runVryndaraAnalysis} disabled={isAnalyzing}>
            {isAnalyzing ? "Processing..." : "Generate AI Audit"}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card title="Active Zones">
            <p className="text-4xl font-bold text-white">{zones.length}</p>
            <div className="text-sm mt-3 text-slate-400 font-mono">
              {zones.length > 0 ? (
                <ul className="space-y-1">
                  {zones.map(z => (
                    <li key={z.id} className="flex justify-between border-b border-white/5 pb-1">
                      <span className="truncate w-32">{z.name}</span>
                      <span className="text-aegis-success text-[9px] border border-aegis-success/30 px-1 rounded">OPERATIONAL</span>
                    </li>
                  ))}
                </ul>
              ) : "No active zones detected"}
            </div>
          </Card>
          
          <Card title="Live Telemetry">
            <p className={`text-4xl font-bold transition-colors duration-500 ${
              isAnomaly ? 'text-red-500 animate-pulse' : 'text-aegis-success'
            }`}>
              {telemetry.value}{telemetry.unit}
            </p>
            <p className="text-sm mt-3 text-slate-400 font-mono">{sensors.length} Nodes Connected</p>
          </Card>
          
          <Card title="Blockchain Ledger">
            <p className="text-4xl font-bold text-white">{logs.length + 1402}</p>
            <p className="text-sm mt-3 text-slate-400 font-mono uppercase text-[10px] tracking-widest">Integrity Hashes</p>
          </Card>
        </div>

        <TacticalMap anomaly={isAnomaly} />
        <ActivityLog logs={logs} />
      </Main>
    </ProtectedRoute>
  );
}