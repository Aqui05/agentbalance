"""
API du backend AgentBalance.

Expose les 3 scenarios (deja utilises par main.py pour generer des images
statiques) en JSON, consommes par le frontend Vue. Le coeur de la
simulation (agent.py, diffusion.py, simulator.py, metrics.py) n'est pas
duplique : importe directement depuis src/ (voir backend/Dockerfile).
"""
from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from agent import build_network, grid_shape, init_agents
from diffusion import run_diffusion
from metrics import utilization_stddev
from simulator import run_resilience_scenario, run_static_vs_diffusion

app = FastAPI(title="AgentBalance API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _positions(n_agents: int) -> dict[int, dict]:
    rows, cols = grid_shape(n_agents)
    return {i: {"row": i // cols, "col": i % cols} for i in range(n_agents)}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/scenario/convergence")
def scenario_convergence(
    n_agents: int = Query(20, ge=4, le=200),
    seed: int = 42,
    max_rounds: int = Query(200, ge=10, le=1000),
):
    graph = build_network(n_agents, seed=seed)
    agents = init_agents(graph, seed=seed)
    initial_utilization = {aid: a.utilization for aid, a in agents.items()}
    initial_stddev = utilization_stddev(agents)

    stddev_by_round: list[float] = []
    utilization_by_round: list[dict[int, float]] = []

    def on_round(_round_idx, current_agents):
        stddev_by_round.append(utilization_stddev(current_agents))
        utilization_by_round.append({aid: a.utilization for aid, a in current_agents.items()})

    rounds_to_converge = run_diffusion(graph, agents, max_rounds=max_rounds, on_round=on_round)
    final_utilization = {aid: a.utilization for aid, a in agents.items()}

    rows, cols = grid_shape(n_agents)
    return {
        "grid": {"rows": rows, "cols": cols, "positions": _positions(n_agents)},
        "initial_utilization": initial_utilization,
        "final_utilization": final_utilization,
        "initial_stddev": initial_stddev,
        "final_stddev": utilization_stddev(agents),
        "rounds_to_converge": rounds_to_converge,
        "stddev_by_round": stddev_by_round,
        "utilization_by_round": utilization_by_round,
    }


@app.get("/api/scenario/static-vs-diffusion")
def scenario_static_vs_diffusion(
    n_agents: int = Query(20, ge=4, le=200),
    rounds: int = Query(60, ge=5, le=500),
    seed: int = 42,
):
    result = run_static_vs_diffusion(n_agents=n_agents, rounds=rounds, seed=seed)
    rows, cols = grid_shape(n_agents)
    return {
        "grid": {"rows": rows, "cols": cols, "positions": _positions(n_agents)},
        "history": result["history"],
        "diffusion_utilization_by_round": result["diffusion_utilization_by_round"],
    }


@app.get("/api/scenario/resilience")
def scenario_resilience(
    n_agents: int = Query(20, ge=4, le=200),
    rounds: int = Query(80, ge=10, le=500),
    spike_round: int = Query(20, ge=1),
    failure_round: int = Query(45, ge=1),
    seed: int = 7,
):
    result = run_resilience_scenario(
        n_agents=n_agents, rounds=rounds, spike_round=spike_round,
        failure_round=failure_round, seed=seed,
    )
    rows, cols = grid_shape(n_agents)
    return {
        "grid": {"rows": rows, "cols": cols, "positions": _positions(n_agents)},
        "stddev_history": result["stddev_history"],
        "max_util_history": result["max_util_history"],
        "utilization_by_round": result["utilization_by_round"],
        "alive_by_round": result["alive_by_round"],
        "spike_round": result["spike_round"],
        "failure_round": result["failure_round"],
        "failed_node": result["failed_node"],
        "baseline_stddev": result["baseline_stddev"],
        "recovery_rounds_after_spike": result["recovery_rounds_after_spike"],
        "recovery_rounds_after_failure": result["recovery_rounds_after_failure"],
    }
