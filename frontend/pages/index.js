import Main from '../components/Main';
import Card from '../components/Card';
import Button from '../components/Button';

export default function Home() {
  return (
    <Main>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold">System Overview</h2>
        <Button variant="primary">Generate AI Audit</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Active Zones">
          <p className="text-3xl font-bold text-aegis-text">3</p>
          <p className="text-sm mt-2">Lab, Farm, Mobility</p>
        </Card>
        <Card title="Vryndara Status">
          <p className="text-3xl font-bold text-aegis-success">Online</p>
          <p className="text-sm mt-2">8 Agents active</p>
        </Card>
        <Card title="Blockchain Ledger">
          <p className="text-3xl font-bold text-aegis-text">1,402</p>
          <p className="text-sm mt-2">Hashes anchored</p>
        </Card>
      </div>
    </Main>
  );
}