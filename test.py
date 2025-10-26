import docker
import psutil

client = docker.from_env()

# Run a lightweight container
container = client.containers.run("nginx", detach=True, name="nginx-test")

# Get live resource stats
stats = container.stats(stream=False)
print('CPU Total usage: ',stats['cpu_stats']['cpu_usage']['total_usage'])
print('Memory usage: ',stats['memory_stats']['usage'])

# Stop and remove container
container.stop()
container.remove()

cpu = psutil.cpu_percent(interval=1)
memory = psutil.virtual_memory().percent
disk = psutil.disk_usage('/').percent
print(cpu, memory, disk)