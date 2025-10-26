from django.urls import path
from . import views

urlpatterns = [
    path('containers/', views.list_containers, name='list_containers'),
    path('containers/stats/', views.all_containers_stats, name='all_containers_stats'),
    path("container-stats/<str:container_id>/", views.container_stats, name="container-stats"),
    path("container-logs/<str:container_id>/", views.stream_logs, name="stream-logs"),
    path('run/', views.run_container, name='run_container'),
    path('stop/', views.stop_container, name='stop_container'),
    path('host-stats/', views.host_stats, name='host_stats'),
    path('cost/', views.estimate_cost, name='estimate_cost'),
    path('stress-test/', views.stress_test, name='stress test'),
    path('benchmark_container/', views.benchmark_container, name='benchmark_container'),
    path('predict_cost_from_benchmark/', views.predict_cost_from_benchmark, name='predict_cost_from_benchmark'),
    path("generate-report/", views.generate_report, name="generate-report"),
    path("benchmarks/last/<str:container_id>/", views.get_last_benchmark, name="get-last-benchmark"),
]
