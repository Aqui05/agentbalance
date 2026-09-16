import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "app"))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_convergence_endpoint():
    res = client.get("/api/scenario/convergence?n_agents=12&max_rounds=100")
    assert res.status_code == 200
    data = res.json()
    assert data["grid"]["rows"] * data["grid"]["cols"] >= 12
    assert len(data["utilization_by_round"]) == data["rounds_to_converge"]
    assert data["final_stddev"] <= data["initial_stddev"]


def test_static_vs_diffusion_endpoint():
    res = client.get("/api/scenario/static-vs-diffusion?n_agents=12&rounds=20")
    assert res.status_code == 200
    data = res.json()
    assert len(data["history"]["static"]) == 20
    assert len(data["diffusion_utilization_by_round"]) == 20


def test_resilience_endpoint():
    res = client.get("/api/scenario/resilience?n_agents=12&rounds=20&spike_round=5&failure_round=12")
    assert res.status_code == 200
    data = res.json()
    assert len(data["stddev_history"]) == 20
    assert data["failed_node"] is not None
    # l'agent en panne doit apparaitre "alive: false" a partir du round de la panne
    last_alive = data["alive_by_round"][-1]
    assert last_alive[str(data["failed_node"])] is False


def test_invalid_params_rejected():
    res = client.get("/api/scenario/resilience?n_agents=2")
    assert res.status_code == 422


if __name__ == "__main__":
    test_health()
    test_convergence_endpoint()
    test_static_vs_diffusion_endpoint()
    test_resilience_endpoint()
    test_invalid_params_rejected()
    print("Tous les tests passent.")
