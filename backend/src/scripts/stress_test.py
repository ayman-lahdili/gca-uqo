from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(5, 15)

    @task
    def get_uqo_courses(self):
        self.client.get("/v1/uqo/cours?departement=DII")
