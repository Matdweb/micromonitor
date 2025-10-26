import { Bar } from "react-chartjs-2";
import { Chart, BarElement, CategoryScale, LinearScale, Legend } from "chart.js";
Chart.register(BarElement, CategoryScale, LinearScale, Legend);

export default function CostComparisonChart({ costs }) {
  const data = {
    labels: ["AWS", "Azure", "GCP"],
    datasets: [
      {
        label: "Predicted Cost ($)",
        data: [costs.AWS, costs.Azure, costs.GCP],
        backgroundColor: ["#38bdf8", "#60a5fa", "#818cf8"],
      },
    ],
  };

  return (
    <div className="bg-panel-bg p-4 rounded-lg border border-[#1e2d3d]">
      <h3 className="text-accent mb-2">Cross-Cloud Cost Comparison</h3>
      <Bar data={data} options={{ responsive: true, plugins: { legend: { labels: { color: '#cbd5e1' } } }, scales: { x: { ticks: { color: '#64748b' } }, y: { ticks: { color: '#64748b' } } } }} />
    </div>
  );
}