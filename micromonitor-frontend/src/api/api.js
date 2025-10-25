const API_BASE = "http://127.0.0.1:8000/api";

export async function fetchHostStats() {
  const res = await fetch(`${API_BASE}/host-stats/`);
  return await res.json();
}

export async function fetchContainers() {
  const res = await fetch(`${API_BASE}/containers/stats/`);
  return await res.json();
}

export async function estimateCost(containerId) {
  const res = await fetch(`${API_BASE}/cost/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider: "AWS", container_id: containerId }),
  });
  return await res.json();
}

export async function runStressTest(params) {
  const res = await fetch(`${API_BASE}/stress-test/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  return await res.json();
}
