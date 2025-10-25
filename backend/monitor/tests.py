# backend/monitor/tests.py
from django.test import TestCase
from django.urls import reverse
import docker
from rest_framework import status

class MonitorAPITest(TestCase):
    def test_host_stats(self):
        url = reverse('list_containers').replace('/containers/', '/host-stats/')  # hack: build path
        resp = self.client.get('/api/host-stats/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('cpu_percent', data)
        self.assertIn('memory_percent', data)

    def test_list_containers(self):
        # Attempt to instantiate docker client; if unavailable, just skip
        try:
            client = docker.from_env()
            client.ping()
        except Exception:
            self.skipTest("Docker not available in test environment")

        resp = self.client.get('/api/containers/')
        self.assertIn(resp.status_code, [200, 503])
