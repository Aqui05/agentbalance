"""
Scenarios de simulation :

1. `run_static_vs_diffusion` : sous un flux continu de nouvelles taches
   arrivant sur des agents aleatoires (aucune coordination a l'arrivee, comme
   des requetes qui atterrissent sur le noeud le plus proche), on compare
   deux mondes :
     - statique  : les agents ne se coordonnent jamais entre eux
     - diffusion : apres chaque arrivee, un round de negociation locale
   et on mesure l'ecart-type de charge dans le temps.

2. `run_resilience_scenario` : uniquement en mode diffusion, on injecte un
   pic de charge soudain sur un agent puis on simule la panne d'un agent,
   pour verifier que le systeme s'adapte sans intervention centrale et
   mesurer le temps de recuperation.
"""
from __future__ import annotations

import copy
import random

import networkx as nx

from agent import Agent, build_network, init_agents
from diffusion import diffusion_round
from metrics import max_utilization, utilization_stddev


def _inject_arrivals(agents: dict[int, Agent], rng: random.Random, n_arrivals: int) -> None:
    alive_ids = [aid for aid, a in agents.items() if a.alive]
    if not alive_ids:
        return
    for _ in range(n_arrivals):
        target = rng.choice(alive_ids)
        agents[target].load += rng.uniform(5, 15)


def _process_tasks(agents: dict[int, Agent], service_rate: float = 0.15) -> None:
    """Chaque agent traite (retire de sa file) une partie de sa charge,
    plafonnee par sa capacite -- comme un serveur qui repond aux requetes
    a un debit proportionnel a sa puissance. Sans ca, la charge totale du
    systeme ne fait que croitre et aucun etat stationnaire n'est possible,
    ce qui rend une mesure de "retour a la normale" apres panne denuee de sens.
    """
    for a in agents.values():
        if not a.alive:
            continue
        throughput = a.capacity * service_rate
        a.load = max(0.0, a.load - throughput)


def run_static_vs_diffusion(
    n_agents: int = 20,
    rounds: int = 60,
    seed: int = 42,
) -> dict:
    graph = build_network(n_agents, seed=seed)
    base_agents = init_agents(graph, seed=seed)

    static_agents = copy.deepcopy(base_agents)
    diffusion_agents = copy.deepcopy(base_agents)

    rng_static = random.Random(seed + 1)
    rng_diffusion = random.Random(seed + 1)  # meme graine -> memes arrivees, comparaison equitable

    history = {"static": [], "diffusion": []}
    diffusion_utilization_by_round: list[dict[int, float]] = []

    for _ in range(rounds):
        _inject_arrivals(static_agents, rng_static, n_arrivals=n_agents)
        _process_tasks(static_agents)
        history["static"].append(utilization_stddev(static_agents))
        # pas de rebalancement en mode statique : c'est la baseline "sans coordination"

        _inject_arrivals(diffusion_agents, rng_diffusion, n_arrivals=n_agents)
        _process_tasks(diffusion_agents)
        diffusion_round(graph, diffusion_agents)
        history["diffusion"].append(utilization_stddev(diffusion_agents))
        diffusion_utilization_by_round.append({aid: a.utilization for aid, a in diffusion_agents.items()})

    return {
        "graph": graph,
        "static_agents": static_agents,
        "diffusion_agents": diffusion_agents,
        "initial_agents": base_agents,
        "history": history,
        "diffusion_utilization_by_round": diffusion_utilization_by_round,
    }


def run_resilience_scenario(
    n_agents: int = 20,
    rounds: int = 80,
    spike_round: int = 20,
    failure_round: int = 45,
    seed: int = 7,
) -> dict:
    graph = build_network(n_agents, seed=seed)
    agents = init_agents(graph, seed=seed)
    rng = random.Random(seed + 1)

    stddev_history: list[float] = []
    max_util_history: list[float] = []
    utilization_by_round: list[dict[int, float]] = []
    alive_by_round: list[dict[int, bool]] = []
    failed_node: int | None = None

    for round_idx in range(1, rounds + 1):
        _inject_arrivals(agents, rng, n_arrivals=n_agents)
        _process_tasks(agents)

        if round_idx == spike_round:
            # Pic soudain : un agent recoit un gros afflux d'un coup
            # (ex. campagne virale routee sans equilibrage en amont).
            target = rng.choice([a.agent_id for a in agents.values() if a.alive])
            agents[target].load += agents[target].capacity * 3

        if round_idx == failure_round:
            # Panne d'un agent : sa charge est perdue/redistribuee en urgence
            # a ses voisins vivants, puis il sort du reseau (ne participe
            # plus aux rounds suivants).
            candidates = [a.agent_id for a in agents.values() if a.alive]
            failed_node = rng.choice(candidates)
            neighbors = [n for n in graph.neighbors(failed_node) if agents[n].alive]
            if neighbors:
                share = agents[failed_node].load / len(neighbors)
                for n in neighbors:
                    agents[n].load += share
            agents[failed_node].load = 0.0
            agents[failed_node].alive = False

        diffusion_round(graph, agents)
        stddev_history.append(utilization_stddev(agents))
        max_util_history.append(max_utilization(agents))
        utilization_by_round.append({aid: a.utilization for aid, a in agents.items()})
        alive_by_round.append({aid: a.alive for aid, a in agents.items()})

    # Temps de recuperation : nombre de rounds apres la panne pour redescendre
    # sous 1.2x l'ecart-type "de croisiere" observe juste avant le pic (on
    # prend une fenetre proche du pic, pas depuis le round 1, pour eviter de
    # biaiser la reference avec le regime transitoire de demarrage).
    warmup_window = stddev_history[max(0, spike_round - 10) : spike_round - 1]
    baseline_stddev = sum(warmup_window) / max(1, len(warmup_window))

    def _recovery_time(start_round: int, end_round: int) -> int | None:
        for i in range(start_round, end_round):
            if stddev_history[i] <= baseline_stddev * 1.2:
                return (i + 1) - start_round
        return None

    recovery_after_spike = _recovery_time(spike_round, failure_round - 1)
    recovery_after_failure = _recovery_time(failure_round, rounds)

    return {
        "graph": graph,
        "agents": agents,
        "stddev_history": stddev_history,
        "max_util_history": max_util_history,
        "utilization_by_round": utilization_by_round,
        "alive_by_round": alive_by_round,
        "spike_round": spike_round,
        "failure_round": failure_round,
        "failed_node": failed_node,
        "baseline_stddev": baseline_stddev,
        "recovery_rounds_after_spike": recovery_after_spike,
        "recovery_rounds_after_failure": recovery_after_failure,
    }
