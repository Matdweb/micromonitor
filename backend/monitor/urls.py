from django.urls import path
from . import views

urlpatterns = [
    path('containers/', views.list_containers, name='list_containers'),
    path('containers/stats/', views.all_containers_stats, name='all_containers_stats'),
    path('containers/<str:cid>/stats/', views.container_stats, name='container_stats'),
    path('run/', views.run_container, name='run_container'),
    path('stop/', views.stop_container, name='stop_container'),
    path('host-stats/', views.host_stats, name='host_stats'),
    path('cost/', views.estimate_cost, name='estimate_cost'),
    path('stress-test/', views.stress_test, name='stress test'),
    path('benchmark_container/', views.benchmark_container, name='benchmark_container'),
    path('predict_cost_from_benchmark/', views.predict_cost_from_benchmark, name='predict_cost_from_benchmark')
]
