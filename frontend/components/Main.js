export default function Main({ children }) {
  return (
    <main className="flex-1 overflow-x-hidden overflow-y-auto p-6">
      {children}
    </main>
  );
}