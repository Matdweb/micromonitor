from django.db import models

class ContainerBenchmark(models.Model):
    container_id = models.CharField(max_length=128)
    name = models.CharField(max_length=128, blank=True)
    avg_cpu_percent = models.FloatField()
    avg_memory_gb = models.FloatField()
    avg_disk_io_mb_s = models.FloatField()
    avg_net_io_mb_s = models.FloatField()
    duration_seconds = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or self.container_id} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"