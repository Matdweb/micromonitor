from django.contrib import admin
from .models import ContainerBenchmark

@admin.register(ContainerBenchmark)
class ContainerBenchmarkAdmin(admin.ModelAdmin):
    list_display = ("container_id", "name", "avg_cpu_percent", "avg_memory_gb", "timestamp")
    list_filter = ("timestamp",)
