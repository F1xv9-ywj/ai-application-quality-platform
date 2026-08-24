from locust import HttpUser, between, task


class EvalForgeUser(HttpUser):
    wait_time = between(0.2, 1.0)

    @task(4)
    def chat(self) -> None:
        self.client.post("/api/chat", json={"question": "退款期限是多久？", "top_k": 3})

    @task(1)
    def health(self) -> None:
        self.client.get("/api/health")
