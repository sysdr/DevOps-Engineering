from locust import HttpUser, task, between

class IngressUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def test_homepage(self):
        self.client.get("/")
    
    @task(2)
    def test_health(self):
        self.client.get("/health")
    
    @task(1)
    def test_ssl_info(self):
        self.client.get("/api/ssl-info")
    
    @task(1)
    def test_services(self):
        self.client.get("/api/services")
    
    @task(2)
    def test_load_endpoint(self):
        self.client.get("/api/load-test")
    
    def on_start(self):
        """Called when a user starts"""
        pass
