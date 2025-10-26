import React, { useState, useEffect } from "react";
import { api } from "../../api/api";
import CostProjectionChart from "../charts/CostProjectionChart";
import CostComparisonChart from "../charts/CostComparisonChart";

// TODO: link this to an API 

const PRICING = {
  AWS: {"cpu_hour": 0.025, "gb_memory_hour": 0.005},
  Azure: {"cpu_hour": 0.022, "gb_memory_hour": 0.006},
  GCP: {"cpu_hour": 0.021, "gb_memory_hour": 0.004}
}

export default function PredictionsPanel() {
  const [containers, setContainers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [intensity, setIntensity] = useState("medium");
  const [hours, setHours] = useState(168);
  const [provider, setProvider] = useState("AWS");
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  function calculateCrossProviderCosts(prediction) {
    if(!prediction) return {}

    const { scaled_cpu_percent, scaled_memory_gb, duration_hours } = prediction;
    const providers = Object.keys(PRICING);
    const costs = {};

    providers.forEach((provider) => {
      const p = PRICING[provider];
      const cpu_cost = p.cpu_hour * (scaled_cpu_percent) * duration_hours;
      const mem_cost = p.gb_memory_hour * scaled_memory_gb * duration_hours;
      costs[provider] = parseFloat((cpu_cost + mem_cost).toFixed(4));
    });

    return costs;
  }

  const costs = calculateCrossProviderCosts(prediction);

  async function loadContainers() {
    try {
      const data = await api.listContainersStats();
      setContainers(data);
      if (data.length && !selected) setSelected(data[0].id);
    } catch (e) {
      console.error("load containers", e);
    }
  }

  useEffect(() => {
    loadContainers();
    const interval = setInterval(loadContainers, 8000);
    return () => clearInterval(interval);
  }, []);

  async function runPrediction() {
    setLoading(true);
    try {
      const res = await api.predictFromBenchmark({
        container_id: selected,
        provider,
        duration_hours: Number(hours),
        workload_intensity: intensity,
      });
      setPrediction(res);
    } catch (e) {
      console.error(e);
      alert("Please run a benchmark on the container before predicting pricing")
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="grid grid-cols-3 gap-6">
      <div className="col-span-1 bg-card-bg rounded p-4 space-y-4">
        <h2 className="text-accent font-semibold">Predict Cost</h2>

        <label className="text-sm text-text-secondary">Container</label>
        <select value={selected || ""} onChange={(e)=>setSelected(e.target.value)} className="w-full bg-[#041823] p-2 rounded">
          {containers.map(c => <option key={c.id} value={c.id}>{c.name || c.id}</option>)}
        </select>

        <label className="text-sm text-text-secondary">Provider</label>
        <select value={provider} onChange={(e)=>setProvider(e.target.value)} className="w-full bg-[#041823] p-2 rounded">
          <option>AWS</option>
          <option>Azure</option>
          <option>GCP</option>
        </select>

        <label className="text-sm text-text-secondary">Workload</label>
        <select value={intensity} onChange={(e)=>setIntensity(e.target.value)} className="w-full bg-[#041823] p-2 rounded">
          <option value="light">Light</option>
          <option value="medium">Medium</option>
          <option value="heavy">Heavy</option>
        </select>

        <label className="text-sm text-text-secondary">Duration (hours)</label>
        <input type="number" value={hours} onChange={(e)=>setHours(e.target.value)} className="w-full bg-[#041823] p-2 rounded"/>

        <button onClick={runPrediction} disabled={!selected || loading} className="mt-3 w-full bg-accent text-black p-2 rounded">
          {loading ? "Predicting..." : "Run Prediction"}
        </button>

        {prediction && (
          <div className="mt-4 text-sm text-text-secondary">
            <div>Cost: <strong className="text-accent">${prediction.total_cost}</strong></div>
            <div>CPU: {prediction.scaled_cpu_percent}%</div>
            <div>Mem: {prediction.scaled_memory_gb} GB</div>
            <div className="text-xs text-text-secondary mt-2">Benchmark at: {prediction.from_benchmark_timestamp}</div>
          </div>
        )}
      </div>

      <div className="col-span-2 bg-card-bg rounded p-4">
        <CostComparisonChart costs={costs} />

      <button
          onClick={async ()=>{
            try {
              const res = await api.generateReportData({
                container_id: selected,
                provider,
                duration_hours: Number(hours)
              });

              const html = `
                <div style="font-family: monospace; background: #0f172a; color: #e6eef8; padding: 1rem; border-radius: 12px; max-width: 480px;">
                  <h2 style="color:#38bdf8; margin:0;">Container Report</h2>
                  <p style="font-size:0.9rem; color:#94a3b8;">Generated on ${res.timestamp}</p>
                  <hr style="border-color:#123148;">
                  <p><b>Container:</b> ${res.container_name}</p>
                  <p><b>Cloud:</b> ${res.provider}</p>
                  <p><b>Duration:</b> ${res.duration_hours}h</p>
                  <ul style="list-style:none; padding:0;">
                    <li>Avg CPU Usage: ${res.avg_cpu_percent}%</li>
                    <li>Avg Memory Usage: ${res.avg_memory_gb} GB</li>
                    <li>Avg Disk I/O: ${res.avg_disk_io_mb_s} MB/s</li>
                    <li>Avg Net I/O: ${res.avg_net_io_mb_s} MB/s</li>
                  </ul>
                  <hr style="border-color:#123148;">
                  <h3 style="color:#38bdf8;">Predicted Cost</h3>
                  <p style="margin:0;">CPU: $${(res.pricing_used.cpu_hour * res.duration_hours * (res.avg_cpu_percent/100)).toFixed(4)}</p>
                  <p style="margin:0;">Memory: $${(res.pricing_used.gb_memory_hour * res.duration_hours * res.avg_memory_gb).toFixed(4)}</p>
                  <p style="font-weight:bold;">Total: $${res.predicted_cost}</p>
                  <hr style="border-color:#123148;">
                  <p style="font-size:0.8rem; color:#94a3b8; text-align:center;">
                    Built with <b>MicroMonitor</b> · <a href="https://mat-dweb.lovable.app/" style="color:#38bdf8;">mat-dweb</a>
                  </p>
                </div>
              `;

              const blob = new Blob([html], { type: "text/html" });
              const url = URL.createObjectURL(blob);
              const link = document.createElement("a");
              link.href = url;
              link.download = `${res.container_name}_report.html`;
              link.click();
            } catch(e) {
              alert("Error generating report: " + e.message);
            }
          }}
          className="mt-3 w-full bg-[#05202a] border border-[#123148] hover:bg-accent hover:text-black p-2 rounded text-sm transition-colors"
        >
          Generate Report
      </button>
      </div>
      <div className="col-span-3 bg-card-bg rounded p-4">
      <h3 className="text-accent font-semibold mb-2">Projected Cost Over Time</h3>
        <div className="h-80">
          <CostProjectionChart prediction={prediction} hours={hours} />
        </div>
        </div>

    </section>
  );
}
