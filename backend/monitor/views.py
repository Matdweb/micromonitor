from django.shortcuts import render
import os
import json
import docker
import psutil
import threading
import time
import math
import random
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import ContainerBenchmark 
from django.http import StreamingHttpResponse
from docker import from_env

PRICING_FILE = os.path.join(os.path.dirname(__file__), "pricing.json")

DEFAULT_PRICING = {
  "AWS": {"cpu_hour": 0.025, "gb_memory_hour": 0.005},
  "Azure": {"cpu_hour": 0.022, "gb_memory_hour": 0.006},
  "GCP": {"cpu_hour": 0.021, "gb_memory_hour": 0.004}
}

def load_pricing():
    if os.path.exists(PRICING_FILE):
        return json.load(open(PRICING_FILE))
    return DEFAULT_PRICING

def calculate_exponential_cost(cpu_percent, mem_gb, duration_seconds, pricing):
    """
    Exponentially increases cost over time.
    The longer the resource is used, the more expensive each second becomes.
    """
    base_cpu_rate = pricing.get("cpu_hour", 0.045) / 3600  # per second
    base_mem_rate = pricing.get("gb_memory_hour", 0.005) / 3600

    total_cost = 0.0
    for t in range(duration_seconds):
        time_factor = math.exp(t / duration_seconds)  # grows exponentially
        cpu_cost = base_cpu_rate * (cpu_percent / 100.0) * time_factor
        mem_cost = base_mem_rate * mem_gb * time_factor
        total_cost += (cpu_cost + mem_cost)
    return round(total_cost, 8)


def get_docker_client():
    try:
        client = docker.from_env()
        return client
    except Exception as e:
        return None

@api_view(['GET'])
def list_containers(request):
    client = get_docker_client()
    if client is None:
        return Response({"error": "Docker client not available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    containers = []
    for c in client.containers.list(all=True):
        containers.append({
            "id": c.short_id,
            "name": c.name,
            "image": c.image.tags[0] if c.image.tags else str(c.image),
            "status": c.status,
            "created": c.attrs.get('Created'),
        })
    return Response(containers)

@api_view(['POST'])
def run_container(request):
    """
    Run a lightweight container.
    JSON body example:
    {
      "image": "nginx:latest",
      "name": "test-nginx",
      "detach": true,
      "ports": {"80/tcp": 8080},
      "command": null
    }
    """
    data = request.data
    image = data.get('image', 'nginx:latest')
    name = data.get('name')
    detach = data.get('detach', True)
    ports = data.get('ports')  # dict or None
    command = data.get('command')  # optional

    client = get_docker_client()
    if client is None:
        return Response({"error": "Docker client not available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        container = client.containers.run(image, name=name, detach=detach, ports=ports, command=command)
        return Response({
            "id": container.short_id,
            "name": container.name,
            "status": container.status
        }, status=status.HTTP_201_CREATED)
    except docker.errors.ImageNotFound:
        return Response({"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND)
    except docker.errors.APIError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def stop_container(request):
    """
    Stop a container by id or name:
    { "id": "container_id" }
    """
    data = request.data
    cid = data.get('id') or data.get('name')
    if not cid:
        return Response({"error": "id or name required"}, status=status.HTTP_400_BAD_REQUEST)
    client = get_docker_client()
    if client is None:
        return Response({"error": "Docker client not available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        container = client.containers.get(cid)
        container.stop(timeout=10)
        return Response({"id": container.short_id, "status": "stopped"})
    except docker.errors.NotFound:
        return Response({"error": "Container not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def host_stats(request):
    """
    Return simple host metrics via psutil.
    Polling recommended every few seconds by frontend.
    """
    cpu_pct = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()
    stats = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "cpu_percent": cpu_pct,
        "memory_total_gb": round(mem.total / (1024**3), 3),
        "memory_used_gb": round((mem.total - mem.available) / (1024**3), 3),
        "memory_percent": mem.percent,
        "disk_total_gb": round(disk.total / (1024**3), 3),
        "disk_used_gb": round(disk.used / (1024**3), 3),
        "disk_percent": disk.percent,
        "net_bytes_sent": net.bytes_sent,
        "net_bytes_recv": net.bytes_recv,
    }
    return Response(stats)

@api_view(['POST'])
def estimate_cost(request):
    """
    Lightweight cost estimation.
    Request examples:

    1) Provide explicit metrics:
    {
      "provider": "AWS",
      "avg_cpu_percent": 65,
      "avg_memory_gb": 2.5,
      "duration_hours": 1
    }

    2) Use a running container's live stats:
    {
      "provider": "AWS",
      "container_id": "mm-nginx-test",
      "duration_hours": 1   # optional, default 1
    }
    """
    data = request.data or {}
    provider = data.get('provider', 'AWS')

    # Try to get numeric inputs (may be overwritten if container_id is provided)
    try:
        avg_cpu_percent = float(data.get('avg_cpu_percent')) if data.get('avg_cpu_percent') is not None else None
    except (TypeError, ValueError):
        avg_cpu_percent = None

    try:
        avg_memory_gb = float(data.get('avg_memory_gb')) if data.get('avg_memory_gb') is not None else None
    except (TypeError, ValueError):
        avg_memory_gb = None

    try:
        duration_hours = float(data.get('duration_hours')) if data.get('duration_hours') is not None else 1.0
    except (TypeError, ValueError):
        duration_hours = 1.0

    cid = data.get('container_id')

    # If a container id is supplied, try to compute live metrics from Docker stats
    if cid:
        client = get_docker_client()
        if client is None:
            return Response({"error": "Docker client not available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            container = client.containers.get(cid)
        except docker.errors.NotFound:
            return Response({"error": "Container not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error fetching container: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            stats = container.stats(stream=False)
            # Memory in GB
            mem_usage_bytes = stats.get('memory_stats', {}).get('usage', 0)
            mem_limit_bytes = stats.get('memory_stats', {}).get('limit', 0) or 1
            mem_usage_gb = mem_usage_bytes / (1024 ** 3)

            # CPU percent calculation (use Docker formula)
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            total_usage = cpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            prev_total_usage = precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            system_cpu = cpu_stats.get('system_cpu_usage', 0)
            prev_system_cpu = precpu_stats.get('system_cpu_usage', 0)
            percpu = cpu_stats.get('cpu_usage', {}).get('percpu_usage') or []
            cpu_count = len(percpu) if isinstance(percpu, list) and len(percpu) > 0 else 1

            cpu_delta = total_usage - prev_total_usage
            system_delta = system_cpu - prev_system_cpu

            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0

            # Fallback assignments
            avg_cpu_percent = round(cpu_percent, 4)
            avg_memory_gb = round(mem_usage_gb, 6)

            # If duration not specified, default to 1 hour
            duration_hours = duration_hours or 1.0

        except Exception as e:
            return Response({"error": f"Failed to read container stats: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Validate metrics exist (either provided or computed)
    if avg_cpu_percent is None or avg_memory_gb is None:
        return Response({
            "error": "Missing metrics. Provide avg_cpu_percent and avg_memory_gb, or supply container_id."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Load pricing
    pricing = load_pricing().get(provider)
    if pricing is None:
        # fallback to default
        pricing = DEFAULT_PRICING.get(provider, DEFAULT_PRICING['AWS'])

    # Compute costs
    # Interpret avg_cpu_percent as fraction of 1 vCPU (100% = 1 vCPU)
    # Compute costs using exponential model
    
    # cpu_cost = pricing.get('cpu_hour', 0.0) * (avg_cpu_percent / 100.0) * duration_hours
    # mem_cost = pricing.get('gb_memory_hour', 0.0) * avg_memory_gb * duration_hours
    # total_cost = cpu_cost + mem_cost
    
    total_cost = calculate_exponential_cost(avg_cpu_percent, avg_memory_gb, int(duration_hours * 3600), pricing)
    cpu_cost = total_cost * 0.6
    mem_cost = total_cost * 0.4

    response = {
        "provider": provider,
        "container_id": cid,
        "duration_hours": duration_hours,
        "avg_cpu_percent": round(avg_cpu_percent, 6),
        "avg_memory_gb": round(avg_memory_gb, 6),
        "pricing_used": pricing,
        "cpu_cost": round(cpu_cost, 6),
        "memory_cost": round(mem_cost, 6),
        "total_cost": round(total_cost, 6),
    }

    return Response(response, status=status.HTTP_200_OK)

@api_view(['GET'])
def container_stats(request, container_id):
    client = from_env()
    container = client.containers.get(container_id)
    stats = container.stats(stream=False)

    cpu_total = stats["cpu_stats"]["cpu_usage"]["total_usage"]
    system_total = stats["cpu_stats"]["system_cpu_usage"]
    cpu_percent = (cpu_total / system_total) * 100 if system_total > 0 else 0

    mem_usage = stats["memory_stats"]["usage"] / (1024 ** 3)
    mem_limit = stats["memory_stats"].get("limit", 1) / (1024 ** 3)
    mem_percent = (mem_usage / mem_limit) * 100 if mem_limit > 0 else 0

    net_rx = stats["networks"]["eth0"]["rx_bytes"] / (1024 ** 2)
    net_tx = stats["networks"]["eth0"]["tx_bytes"] / (1024 ** 2)

    return Response({
        "cpu_percent": round(cpu_percent, 2),
        "memory_used_gb": round(mem_usage, 3),
        "memory_percent": round(mem_percent, 2),
        "network_rx_mb": round(net_rx, 3),
        "network_tx_mb": round(net_tx, 3),
    })


@api_view(['GET'])
def all_containers_stats(request):
    """
    Return live, detailed resource stats for all running containers.
    Includes CPU, memory, and network usage.
    Example: GET /api/containers/stats/
    """
    client = get_docker_client()
    if client is None:
        return Response({"error": "Docker client not available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    containers_data = []

    try:
        for container in client.containers.list():
            try:
                stats = container.stats(stream=False)

                # CPU usage
                cpu_stats = stats.get('cpu_stats', {})
                precpu_stats = stats.get('precpu_stats', {})
                cpu_count = len(cpu_stats.get('cpu_usage', {}).get('percpu_usage', [])) or 1

                cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                            precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
                system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)

                cpu_percent = 0.0
                if system_delta > 0 and cpu_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0

                # Memory usage
                mem_stats = stats.get('memory_stats', {})
                mem_usage = mem_stats.get('usage', 0)
                mem_limit = mem_stats.get('limit', 1)
                mem_percent = (mem_usage / mem_limit) * 100.0

                # Network usage
                networks = stats.get('networks', {})
                rx_bytes = tx_bytes = 0
                for iface, data in networks.items():
                    rx_bytes += data.get('rx_bytes', 0)
                    tx_bytes += data.get('tx_bytes', 0)

                containers_data.append({
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_usage_mb": round(mem_usage / (1024 ** 2), 2),
                    "memory_limit_mb": round(mem_limit / (1024 ** 2), 2),
                    "memory_percent": round(mem_percent, 2),
                    "rx_mb": round(rx_bytes / (1024 ** 2), 2),
                    "tx_mb": round(tx_bytes / (1024 ** 2), 2),
                })

            except Exception as e:
                containers_data.append({
                    "id": container.short_id,
                    "name": container.name,
                    "status": "error",
                    "error": str(e)
                })

        return Response(containers_data)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def stream_logs(request, container_id):
    """
    Streams live logs for a specific container.
    Usage: GET /container-logs/<container_id>/
    """
    client = from_env()
    container = client.containers.get(container_id)

    def log_stream():
        for line in container.logs(stream=True, tail=50, follow=True):
            yield line.decode('utf-8') + '\n'
            time.sleep(0.1)  # prevent CPU overuse

    response = StreamingHttpResponse(log_stream(), content_type='text/plain')
    response['Cache-Control'] = 'no-cache'
    return response
    
@api_view(['POST'])
def stress_test(request):
    """
    Runs a short CPU/memory stress test on the host machine.
    WARNING: This will use actual CPU and RAM resources.
    Example:
    {
      "cpu_target": 70,
      "memory_gb": 0.5,
      "duration_seconds": 30,
      "provider": "AWS"
    }
    """
    data = request.data
    provider = data.get('provider', 'AWS')
    cpu_target = int(data.get('cpu_target', 50))
    memory_gb = float(data.get('memory_gb', 0.5))
    duration = int(data.get('duration_seconds', 30))

    pricing = load_pricing().get(provider, DEFAULT_PRICING.get(provider, DEFAULT_PRICING['AWS']))

    results = []
    cpu_values = []
    mem_values = []

    start_time = time.time()
    end_time = start_time + duration

    def cpu_load(stop_event):
        """Busy-wait loop to generate CPU load."""
        while not stop_event.is_set():
            _ = math.sqrt(random.random())  # light floating-point operation

    stop_event = threading.Event()
    threads = []
    num_threads = max(1, int((cpu_target / 100.0) * psutil.cpu_count(logical=True)))
    for _ in range(num_threads):
        t = threading.Thread(target=cpu_load, args=(stop_event,))
        t.start()
        threads.append(t)

    try:
        allocated = bytearray(int(memory_gb * 1024**3)) if memory_gb > 0 else None

        while time.time() < end_time:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().used / (1024**3)
            timestamp = round(time.time() - start_time, 2)
            results.append({"time": timestamp, "cpu": cpu, "mem": mem})
            cpu_values.append(cpu)
            mem_values.append(mem)

        stop_event.set()
        for t in threads:
            t.join()

    except Exception as e:
        stop_event.set()
        return Response({"error": f"Stress test failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
    avg_mem = sum(mem_values) / len(mem_values) if mem_values else 0
    cost = calculate_exponential_cost(avg_cpu, memory_gb, duration, pricing)

    response = {
        "provider": provider,
        "cpu_target": cpu_target,
        "memory_target": memory_gb,
        "duration_seconds": duration,
        "measured_avg_cpu": round(avg_cpu, 2),
        "measured_avg_mem": round(avg_mem, 2),
        "estimated_cost": cost,
        "details": results,
        "message": "Stress test completed successfully."
    }
    return Response(response, status=status.HTTP_200_OK)

@api_view(['POST'])
def benchmark_container(request):
    """
    Run a short benchmark calibration on a given container.
    Measures avg CPU%, memory GB, disk I/O, and network I/O over a duration (seconds).
    """
    data = request.data
    container_id = data.get('container_id')
    duration = int(data.get('duration', 15))

    if not container_id:
        return Response({"error": "container_id is required"}, status=400)

    client = get_docker_client()
    try:
        container = client.containers.get(container_id)
    except docker.errors.NotFound:
        return Response({"error": f"Container {container_id} not found"}, status=404)

    # collect stats over time
    samples = []
    start_time = time.time()

    while time.time() - start_time < duration:
        stats = container.stats(stream=False)
        cpu_percent = 0.0
        mem_usage = 0.0
        disk_io = 0.0
        net_io = 0.0

        # --- CPU ---
        try:
            cpu_total = stats["cpu_stats"]["cpu_usage"]["total_usage"]
            precpu_total = stats["precpu_stats"]["cpu_usage"]["total_usage"]
            cpu_delta = cpu_total - precpu_total

            system_total = stats["cpu_stats"].get("system_cpu_usage")
            precpu_system = stats["precpu_stats"].get("system_cpu_usage")
            system_delta = (system_total or 0) - (precpu_system or 0)

            # Determine number of CPUs if available
            cpu_count = len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [])) or psutil.cpu_count()

            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
        except Exception as e:
            print(f"CPU calculation error: {e}")
            
        # --- Memory ---
        try:
            mem_usage = stats["memory_stats"]["usage"] / (1024 ** 3)  # GB
        except Exception:
            pass

        # --- Disk I/O (Host-based using psutil) ---
        try:
            disk_io = psutil.disk_io_counters().read_bytes / (1024 ** 2)  # MB
        except Exception as e:
            print(f'Error on disk reading: {e}')

        # --- Network I/O ---
        try:
            net_io = psutil.net_io_counters().bytes_sent / (1024 ** 2)  # MB
        except Exception:
            pass

        samples.append({
            "cpu_percent": cpu_percent,
            "memory_gb": mem_usage,
            "disk_io_mb": disk_io,
            "net_io_mb": net_io
        })
        time.sleep(1)

    # compute averages
    if not samples:
        return Response({"error": "No samples collected"}, status=500)
    
    avg_cpu = sum(s["cpu_percent"] for s in samples) / len(samples)
    avg_mem = sum(s["memory_gb"] for s in samples) / len(samples)
    avg_disk = (samples[-1]["disk_io_mb"] - samples[0]["disk_io_mb"]) / duration
    avg_net = (samples[-1]["net_io_mb"] - samples[0]["net_io_mb"]) / duration

    response_data = {
        "container_id": container_id,
        "duration": duration,
        "avg_cpu_percent": round(avg_cpu,6),
        "avg_memory_gb": round(avg_mem, 4),
        "avg_disk_io_mb_s": round(avg_disk, 6),
        "avg_net_io_mb_s": round(avg_net, 6),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    ContainerBenchmark.objects.create(
        container_id=container_id,
        name=container.name,
        avg_cpu_percent=response_data["avg_cpu_percent"],
        avg_memory_gb=response_data["avg_memory_gb"],
        avg_disk_io_mb_s=response_data["avg_disk_io_mb_s"],
        avg_net_io_mb_s=response_data["avg_net_io_mb_s"],
        duration_seconds=duration
    )

    return Response(response_data)

@api_view(['POST'])
def predict_cost_from_benchmark(request):
    """
    Predicts cloud cost based on the latest benchmark data for a given container.
    Allows scaling by workload intensity and duration.
    Example:
    {
      "container_id": "abc123",
      "provider": "AWS",
      "duration_hours": 168,
      "workload_intensity": "medium"
    }
    """
    data = request.data
    container_id = data.get("container_id")
    provider = data.get("provider", "AWS")
    duration_hours = float(data.get("duration_hours", 1))
    intensity = data.get("workload_intensity", "light").lower()

    if not container_id:
        return Response({"error": "container_id is required"}, status=400)

    try:
        benchmark = (
            ContainerBenchmark.objects
            .filter(container_id=container_id)
            .order_by("-timestamp")
            .first()
        )
        if not benchmark:
            return Response({"error": "No benchmark data found for container"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
    WORKLOAD_MULTIPLIERS = {
        "light": 1.0,
        "medium": 1.5,
        "heavy": 2.5
    }
    # Load pricing
    pricing = DEFAULT_PRICING.get(provider, DEFAULT_PRICING["AWS"])
    multiplier = WORKLOAD_MULTIPLIERS.get(intensity, 1.0)

    # Apply scaling
    scaled_cpu = benchmark.avg_cpu_percent * multiplier
    scaled_mem = benchmark.avg_memory_gb * multiplier
    
    # Estimate costs
    cpu_cost = pricing["cpu_hour"] * scaled_cpu * duration_hours
    mem_cost = pricing["gb_memory_hour"] * scaled_mem * duration_hours
    total_cost = cpu_cost + mem_cost

    response = {
        "provider": provider,
        "workload_intensity": intensity,
        "duration_hours": duration_hours,
        "scaled_cpu_percent": round(scaled_cpu, 2),
        "scaled_memory_gb": round(scaled_mem, 3),
        "cpu_cost": round(cpu_cost, 4),
        "memory_cost": round(mem_cost, 4),
        "total_cost": round(total_cost, 4),
        "currency": "USD",
        "from_benchmark_timestamp": benchmark.timestamp.isoformat(),
    }

    return Response(response)

@api_view(['GET'])
def get_last_benchmark(request, container_id):
    bench = ContainerBenchmark.objects.filter(container_id=container_id).order_by("timestamp").first()
    if not bench:
        return Response({"detail": "No benchmark found"}, status=404)
    return Response({
        "avg_cpu_percent": bench.avg_cpu_percent,
        "avg_memory_gb": bench.avg_memory_gb,
        "avg_disk_io_mb_s": bench.avg_disk_io_mb_s,
        "avg_net_io_mb_s": bench.avg_net_io_mb_s,
        "timestamp": bench.timestamp
    })

@api_view(['POST'])
def generate_report(request):
    """
    Returns container metrics and predicted cost.
    Example input:
    {
      "container_id": "abc123",
      "provider": "AWS",
      "duration_hours": 168
      "intesity": "medium"
    }
    """
    
    data = request.data
    container_id = data.get("container_id")
    provider = data.get("provider", "AWS")
    duration_hours = float(data.get("duration_hours", 1))
    intensity = data.get("workload_intensity", "light").lower()

    if not container_id:
        return Response({"error": "container_id is required"}, status=400)

    try:
        benchmark = (
            ContainerBenchmark.objects
            .filter(container_id=container_id)
            .order_by("-timestamp")
            .first()
        )
        if not benchmark:
            return Response({"error": "No benchmark data found for container"}, status=500)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
    WORKLOAD_MULTIPLIERS = {
        "light": 1.0,
        "medium": 1.5,
        "heavy": 2.5
    }
    
    # Load pricing
    pricing = DEFAULT_PRICING.get(provider, DEFAULT_PRICING["AWS"])
    multiplier = WORKLOAD_MULTIPLIERS.get(intensity, 1.0)

    # Apply scaling
    scaled_cpu = benchmark.avg_cpu_percent * multiplier
    scaled_mem = benchmark.avg_memory_gb * multiplier
    
    avg_disk = getattr(benchmark, "avg_disk_io_mb_s", 0.6)
    avg_net = getattr(benchmark, "avg_net_io_mb_s", 0.4)
    
    pricing = DEFAULT_PRICING.get(provider, DEFAULT_PRICING["AWS"])
        
    # Estimate costs
    cpu_cost = pricing["cpu_hour"] * scaled_cpu * duration_hours
    mem_cost = pricing["gb_memory_hour"] * scaled_mem * duration_hours
    
    container_name = getattr(benchmark, "container_name", f"Container-{container_id}" if container_id else "Unknown")
    total = cpu_cost + mem_cost

    response = {
        "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        "container_id": container_id,
        "container_name": container_name,
        "provider": provider,
        "duration_hours": duration_hours,
        "avg_cpu_percent": round(scaled_cpu, 2),
        "avg_memory_gb": round(scaled_mem, 3),
        "avg_disk_io_mb_s": round(avg_disk, 3),
        "avg_net_io_mb_s": round(avg_net, 3),
        "predicted_cost": round(total, 6),
        "pricing_used": pricing,
    }

    return Response(response)