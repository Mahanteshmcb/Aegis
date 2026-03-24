import Sidebar from './Sidebar';
import Header from './Header';

export default function Main({ children }) {
  return (
    <div className="flex h-screen bg-[#0b1120] font-sans text-aegis-text">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-x-hidden overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}