
from locust import HttpUser, task, between


class UsuarioLaboratorio(HttpUser):
    # Pausa entre solicitudes para evitar ráfagas.
    wait_time = between(3, 5)

    @task
    def consultar_inicio(self):
        with self.client.get(
            "/",
            timeout=5,
            catch_response=True,
            name="GET /"
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"HTTP inesperado: {response.status_code}"
                )
