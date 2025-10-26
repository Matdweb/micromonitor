const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} failed: ${res.status} ${text}`);
  }

  return res.json();
}

export const api = {
  listContainers: () => request("/containers/"),
  listContainersStats: () => request("/containers/stats/"),
  benchmarkContainer: (body) =>
    request("/benchmark_container/", { method: "POST", body: JSON.stringify(body) }),
  predictFromBenchmark: (body) =>
    request("/predict_cost_from_benchmark/", { method: "POST", body: JSON.stringify(body) }),
  runStressTest: (body) =>
    request("/stress-test/", { method: "POST", body: JSON.stringify(body) }),
  estimateCost: (body) =>
    request("/estimate-cost/", { method: "POST", body: JSON.stringify(body) }),
  generateReportData: (body) =>
    request("/generate-report/", { method: "POST", body: JSON.stringify(body) }),
  getContainerStats: (containerId) => 
    request(`/container-stats/${containerId}/`),
  getContainerLogs: async (containerId) => {
    const path=`/container-logs/${containerId}/`
    const res = await fetch(`${API_BASE}${path}`);

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API ${path} failed: ${res.status} ${text}`);
    }

    const stream = res.body.pipeThrough(new TextDecoderStream());
    for await (const value of stream) {
      return value
    }
  },
  getLastBenchmark: async (containerId) =>
    request(`/benchmarks/last/${containerId}/`, { method: "GET" }),
};
