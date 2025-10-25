import HostStats from "./components/HostStats";
import ContainerList from "./components/ContainerList";
import TerminalLogs from "./components/TerminalLogs";

export default function App() {
  return (
    <div className="min-h-screen p-6 bg-terminal-bg text-terminal-text">
      <h1 className="text-3xl mb-6 text-terminal-accent font-bold">⚙️ MicroMonitor Dashboard</h1>
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        <HostStats />
        <ContainerList />
      </div>
      <TerminalLogs />
    </div>
  );
}
