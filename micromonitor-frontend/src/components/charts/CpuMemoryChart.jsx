import React from "react";
import { Line } from "react-chartjs-2";

export default function CpuMemoryChart({ series }) {
  const labels = series?.map(s=>s.time) || [];
  const cpu = series?.map(s=>s.cpu) || [];
  const mem = series?.map(s=>s.mem) || [];

  const data = {
    labels,
    datasets: [
      { label: "CPU %", data: cpu, borderColor: "#38bdf8", tension: 0.3 },
      { label: "Memory GB", data: mem, borderColor: "#3fb950", tension: 0.3, yAxisID: 'y1' }
    ]
  };

  const options = {
    responsive: true, maintainAspectRatio: false,
    scales: {
      x: { ticks: { color: "#9fb8c9" } },
      y: { ticks: { color: "#9fb8c9" } },
      y1: { position: "right", ticks: { color: "#9fb8c9" } }
    }
  };

  return <Line data={data} options={options} />;
}
