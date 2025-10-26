import { Line } from "react-chartjs-2";

export default function CostProjectionChart({ prediction, hours = 168 }) {
  if (!prediction) {
    return <div className="flex items-center justify-center h-full text-text-secondary">Run a prediction to see a chart</div>;
  }

  const total = Number(prediction.total_cost || 0) || 0;
  const points = Math.min(24, Math.ceil(hours / Math.max(1, hours / 24))); // up to 24 points
  const labels = Array.from({ length: points }, (_, i) => `${Math.round((i+1) * (hours/points))}h`);
  const dataPoints = labels.map((_, i) => ((i+1)/points) * total);

  const data = {
    labels,
    datasets: [
      {
        label: "Accumulated Cost (USD)",
        data: dataPoints,
        borderColor: "#38bdf8",
        backgroundColor: "rgba(56,189,248,0.15)",
        fill: true,
        tension: 0.3,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: { ticks: { color: "#9fb8c9" } },
      y: { ticks: { color: "#9fb8c9" } }
    },
    plugins: { legend: { labels: { color: "#cfeffb" } } }
  };

  return <Line data={data} options={options}/>;
}
