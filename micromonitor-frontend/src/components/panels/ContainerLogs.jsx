import { useEffect, useState } from "react";
import { api } from "../../api/api";

export default function ContainerLogs({ selected }) {
  const [logs, setLogs] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [lastHash, setLastHash] = useState(null);

  useEffect(() => {
    if (!selected) return;
    setLogs("");
    setIsLoading(true);

    let isCancelled = false;

    const fetchLogs = async () => {
      try {
        const text = await api.getContainerLogs(selected);
        if (!isCancelled && text) {
          const hash = text.slice(-300);
          if (hash !== lastHash) {
            setLogs((prev) => (prev + text).slice(-6000));
            setLastHash(hash);
          }
        }
      } catch (err) {
        if (!isCancelled) console.error("Error fetching logs:", err);
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);

    return () => {
      isCancelled = true;
      clearInterval(interval);
    };
  }, [selected]);
  

  useEffect(()=>{
    console.log(logs)
  },[logs])

  return (
    <div className="bg-panel-bg p-4 rounded-lg text-sm font-mono text-text-secondary overflow-y-auto h-full max-h-80 border border-[#1e2d3d]">
      <h3 className="text-accent mb-2">Live Logs</h3>
      {isLoading && logs === "" && <p>Fetching logs...</p>}
      <pre>{logs || "No logs available"}</pre>
    </div>
  );
}