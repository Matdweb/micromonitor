import React, { useEffect, useState } from "react";
import ContainerLogs from "./ContainerLogs";
import ContainerMetricsChart from "./ContainerMetricsChart";
import { api } from "../../api/api";

export default function ContainersPanel() {
  const [containers, setContainers] = useState([]);

  async function load() {
    try {
      const data = await api.listContainersStats();
      setContainers(data);
    } catch (e) {
      console.error(e);
    }
  }

  useEffect(()=>{ load(); const i=setInterval(load, 8000); return ()=>clearInterval(i); }, []);

  return (
    <section>
      <h2 className="text-accent font-semibold mb-3">Containers</h2>
      <div className="grid grid-cols-1 gap-4">
        {containers.map(c => (
          <div key={c.id} className="bg-card-bg p-4 rounded">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-sm text-text-secondary">{c.id}</div>
                <div className="font-medium text-text-primary">{c.name || c.id}</div>
                <div className="text-xs text-text-secondary">{c.status}</div>
              </div>
              <div className="text-right">
                <div className="text-sm">CPU</div>
                <div className="text-xl font-semibold">{c.cpu_percent}%</div>
              </div>
            </div>
            <div className="mt-3 text-sm text-text-secondary">
              <div>Memory: {c.memory_usage_mb} MB ({c.memory_percent}%)</div>
              <div>RX/TX: {c.rx_mb}/{c.tx_mb} MB</div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <ContainerLogs selected={c.id} />
              <ContainerMetricsChart containerId={c.id} />
            </div>
          </div>
        ))}
      </div>

    </section>
  );
}
