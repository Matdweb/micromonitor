## 🚀 MicroMonitor

**MicroMonitor** is a **real-time Docker container monitoring and cloud cost estimation platform** built with **Django + React + Docker SDK**.  
It enables developers and DevOps engineers to **benchmark, predict, and compare cloud provider costs** (AWS, Azure, GCP) directly from their local containers — no cloud account required.

---

## 🧠 Concept

MicroMonitor helps simulate how your Docker containers would perform and cost in real cloud environments.  
It tracks **live resource usage (CPU, memory, network, disk)** using Docker’s API and **estimates pricing** using real-world cloud provider models.

Key use cases:
- 🔍 Benchmark containers before deployment.
- 💰 Predict operational costs across different cloud platforms.
- 📊 Compare workload behaviors and pricing models visually.
- 🧪 Stress test containers safely on your own hardware.

---

## ⚙️ Tech Stack

**Backend**
- Django 5.x  
- Django REST Framework  
- Docker SDK for Python  
- psutil  
- SQLite (default, easy to switch to PostgreSQL)

**Frontend**
- React 18 + Vite  
- TailwindCSS  
- Chart.js / react-chartjs-2 for live metrics and cost visualization

**DevOps**
- Docker & Docker Compose

---

## 🧩 Core Features

### 🔹 Container Monitoring
- Real-time metrics fetched directly from Docker (`psutil` + `docker-py`).
- CPU, Memory, Disk, and Network statistics per container.
- Benchmark mode to record average resource usage snapshots.

### 🔹 Cost Prediction
- Pricing model based on AWS, Azure, and GCP hourly rates.
- Predicts cost per container based on:
  - Average CPU & Memory usage
  - Workload intensity (`light`, `medium`, `heavy`)
  - Duration (hours → weeks)

### 🔹 Benchmark Calibration
- Runs short container benchmarks to analyze behavior.
- Predicts longer-term cost projections using those baselines.

### 🔹 Reporting
- Generates shareable reports with real container metrics.
- Includes predicted costs and platform comparisons.
- Ready-to-embed HTML summaries for documentation.

---

## 🧰 Project Structure

~~~ text
micromonitor/
├── backend/
│   ├── manage.py
│   ├── Dockerfile
│   ├── micromonitor/
│   └── api/
│       ├── views.py
│       ├── models.py
│       ├── pricing.json
│       └── utils/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── api/
│   │   ├── styles/
│   │   └── App.jsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
└── README.md
~~~

---

## 🧩 Getting Started

### 1️⃣ Clone the repository

~~~ bash
git clone https://github.com/mat-dweb/micromonitor.git
cd micromonitor
~~~

### 2️⃣ Build and run all containers

~~~ bash
docker compose up --build
~~~

This command:
- Builds both **frontend** and **backend** containers.  
- Starts Django API on **http://localhost:8000**  
- Starts React frontend on **http://localhost:5173**

---

## 🧩 Backend Configuration

Default environment variables:

~~~ bash
PYTHONUNBUFFERED=1
DJANGO_SETTINGS_MODULE=micromonitor.settings
~~~

### API Endpoints (examples)

~~~ bash
GET  /api/containers/stats/          # list running containers and stats
POST /api/benchmark/                 # run 15s benchmark on container
POST /api/predict-cost/              # predict cost for selected provider
GET  /api/pricing/                   # get current pricing data
~~~

---

## 🧩 Frontend Configuration

The frontend automatically connects to backend through Docker’s internal network.

### Example API config (src/api/api.js)

~~~ js
const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
~~~

In docker-compose, this is injected as:

~~~ yaml
environment:
  - VITE_API_URL=http://backend:8000/api
~~~

---

## 🧩 Example Workflows

### 🧪 Run a Benchmark
1. Open the UI → Select a container → click **“Run 15s Benchmark”**
2. Wait for results → CPU, Memory, Disk, Net usage displayed.
3. Data is stored and ready for cost predictions.

### 💰 Predict Cloud Cost
1. Select provider (AWS/Azure/GCP)
2. Choose duration (e.g., 168 hours = 1 week)
3. Select intensity (`light`, `medium`, `heavy`)
4. Receive instant estimated total cost.

### 🧮 Compare Providers
- A cost comparison chart shows how different clouds would price your workload.
- Values scale exponentially over time — realistic cloud growth model.

---

## 📈 Example Prediction Output

~~~ json
{
  "provider": "AWS",
  "workload_intensity": "medium",
  "duration_hours": 168,
  "scaled_cpu_percent": 6.36,
  "scaled_memory_gb": 0.189,
  "cpu_cost": 26.71,
  "memory_cost": 0.16,
  "total_cost": 26.88,
  "currency": "USD",
  "from_benchmark_timestamp": "2025-10-25T07:44:57.014839+00:00"
}
~~~

---

## 🐳 Docker Setup

**Backend Dockerfile**

~~~ dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
~~~

**Frontend Dockerfile**

~~~ dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
~~~

**docker-compose.yml**

~~~ yaml
version: "3.9"
services:
  backend:
    build: ./backend
    container_name: micromonitor-backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - micromonitor-net

  frontend:
    build: ./frontend
    container_name: micromonitor-frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://backend:8000/api
    depends_on:
      - backend
    networks:
      - micromonitor-net

networks:
  micromonitor-net:
    driver: bridge
~~~

---

## Demo 📷

https://github.com/user-attachments/assets/5227bd70-da1b-44ca-a1b4-79975920ff60

🧩 Project by [Matias Vargas](https://mat-dweb.lovable.app/)  
*"MicroMonitor: Benchmark smarter. Predict faster. Deploy cheaper.”*
