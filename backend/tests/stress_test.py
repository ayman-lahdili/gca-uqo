from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(5, 15)

    @task
    def get_uqo_courses(self):
        self.client.get("/v1/uqo/cours?departement=DII")

    @task
    def get_uqo_programmes(self):
        for cycle in range(1, 4):
            self.client.get(f"/v1/uqo/programmes?departement=INFOR&cycle={cycle}")
