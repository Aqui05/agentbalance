import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agent import build_network, init_agents
from diffusion import diffusion_round, run_diffusion
from metrics import utilization_stddev


def test_diffusion_round_reduces_or_maintains_stddev():
    graph = build_network(12, seed=1)
    agents = init_agents(graph, seed=1)
    before = utilization_stddev(agents)

    diffusion_round(graph, agents)
    after = utilization_stddev(agents)

    assert after <= before


def test_diffusion_converges_within_bounded_rounds():
    graph = build_network(16, seed=2)
    agents = init_agents(graph, seed=2)

    rounds = run_diffusion(graph, agents, max_rounds=200, convergence_threshold=0.5)

    assert rounds < 200  # doit converger avant la limite, pas juste s'arreter au max


def test_diffusion_never_creates_negative_load():
    graph = build_network(10, seed=3)
    agents = init_agents(graph, seed=3)

    run_diffusion(graph, agents, max_rounds=50)

    assert all(a.load >= 0 for a in agents.values())


def test_total_load_is_conserved_by_diffusion():
    # La diffusion redistribue, elle ne cree ni ne detruit de charge.
    graph = build_network(10, seed=4)
    agents = init_agents(graph, seed=4)
    total_before = sum(a.load for a in agents.values())

    for _ in range(20):
        diffusion_round(graph, agents)

    total_after = sum(a.load for a in agents.values())
    assert abs(total_after - total_before) < 1e-6


if __name__ == "__main__":
    test_diffusion_round_reduces_or_maintains_stddev()
    test_diffusion_converges_within_bounded_rounds()
    test_diffusion_never_creates_negative_load()
    test_total_load_is_conserved_by_diffusion()
    print("Tous les tests passent.")
