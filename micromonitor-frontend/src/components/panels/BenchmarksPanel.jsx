import React, { useEffect, useState } from "react";
import { api } from "../../api/api";

export default function BenchmarksPanel() {
  const [containers, setContainers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [running, setRunning] = useState(false);
  const [loadingBenchmark, setLoadingBenchmark] = useState(false);

  useEffect(() => {
    loadContainers();
  }, []);

  // ✅ fetch containers on mount
  async function loadContainers() {
    try {
      const data = await api.listContainersStats();
      setContainers(data);
    } catch (e) {
      console.error(e);
    }
  }

  // ✅ fetch latest benchmark when selected changes
  useEffect(() => {
    if (!selected) return;
    fetchLastBenchmark(selected);
  }, [selected]);

  async function fetchLastBenchmark(containerId) {
    try {
      setLoadingBenchmark(true);
      const res = await api.getLastBenchmark(containerId);
      setBenchmark(res);
    } catch (e) {
      console.error(e);
      setBenchmark(null);
    } finally {
      setLoadingBenchmark(false);
    }
  }

  // ✅ run a new benchmark manually
  async function runBenchmark() {
    if (!selected) return alert("Select container first");
    setRunning(true);
    try {
      const res = await api.benchmarkContainer({
        container_id: selected,
        duration: 15
      });
      setBenchmark(res); // update display immediately
    } catch (e) {
      console.error(e);
      alert("Benchmark failed: " + e.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="grid grid-cols-2 gap-6">
      <div className="bg-card-bg p-4 rounded">
        <h2 className="text-accent font-semibold mb-2">Benchmarks</h2>
        <label className="text-sm text-text-secondary">Container</label>
        <select
          onChange={(e) => setSelected(e.target.value)}
          className="w-full bg-[#041823] p-2 rounded"
        >
          <option value="">-- choose --</option>
          {containers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name || c.id}
            </option>
          ))}
        </select>

        <button
          onClick={runBenchmark}
          disabled={!selected || running}
          className={`mt-3 w-full p-2 rounded ${
            running
              ? "bg-gray-700 text-text-secondary"
              : "bg-accent text-black hover:bg-accent-light"
          }`}
        >
          {running ? "Running..." : "Run 15s Benchmark"}
        </button>
      </div>

      <div className="bg-card-bg p-4 rounded">
        <h3 className="text-accent font-semibold">Latest Benchmark</h3>

        {loadingBenchmark ? (
          <div className="text-text-secondary mt-3">Loading...</div>
        ) : benchmark ? (
          <div className="mt-2 text-sm space-y-1">
            <div>
              Avg CPU: <strong>{benchmark.avg_cpu_percent}%</strong>
            </div>
            <div>
              Avg Memory: <strong>{benchmark.avg_memory_gb} GB</strong>
            </div>
            <div>
              Disk I/O (MB/s):{" "}
              <strong>{benchmark.avg_disk_io_mb_s}</strong>
            </div>
            <div>
              Net I/O (MB/s): <strong>{benchmark.avg_net_io_mb_s}</strong>
            </div>
            {benchmark.timestamp && (
              <div className="text-xs text-text-secondary">
                Recorded: {new Date(benchmark.timestamp).toLocaleString()}
              </div>
            )}
          </div>
        ) : (
          <div className="text-text-secondary mt-3">
            No benchmark results yet.
          </div>
        )}
      </div>
    </section>
  );
}