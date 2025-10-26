import { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import { Chart, LineElement, CategoryScale, LinearScale, PointElement, Legend } from "chart.js";
import { api } from "../../api/api";

Chart.register(LineElement, CategoryScale, LinearScale, PointElement, Legend);

export default function ContainerMetricsChart({ containerId }) {
  const [data, setData] = useState([]);
  
  useEffect(() => {
    if (!containerId) return;
    const interval = setInterval(async () => {
      const res = await api.getContainerStats(containerId)
      setData((prev) => [...prev.slice(-10), { time: new Date().toLocaleTimeString(), ...res }]);
    }, 2000);
    return () => clearInterval(interval);
  }, [containerId]);

  const chartData = {
    labels: data.map((d) => d.time),
    datasets: [
      {
        label: "CPU %",
        data: data.map((d) => d.cpu_percent),
        borderColor: "#38bdf8",
        fill: false,
        tension: 0.3,
      },
      {
        label: "Memory %",
        data: data.map((d) => d.memory_percent),
        borderColor: "#f472b6",
        fill: false,
        tension: 0.3,
      },
    ],
  };

  return (
    <div className="bg-panel-bg p-4 rounded-lg border border-[#1e2d3d] max-h-80">
      <h3 className="text-accent mb-2">Real-Time Metrics</h3>
      <Line data={chartData} options={{ responsive: true, plugins: { legend: { labels: { color: '#cbd5e1' } } }, scales: { x: { ticks: { color: '#64748b' } }, y: { ticks: { color: '#64748b' } } } }} />
    </div>
  );
}