"""
Diffusion load balancing : chaque agent negocie uniquement avec ses voisins
directs, sans vision globale ni chef d'orchestre. C'est l'algorithme
"nearest-neighbor diffusion" classique (Cybenko, 1989) -- simple a
implementer et a expliquer, mais deja pleinement representatif du
fonctionnement d'un systeme autonomique decentralise.

Principe par round :
  Pour chaque arete (u, v) du reseau, si u est plus charge que v (en
  utilisation relative, load/capacity), u transfere une fraction ALPHA de
  l'ecart vers v. Tous les transferts d'un round sont calcules a partir de
  l'etat de depart du round (synchrone), puis appliques simultanement --
  ca evite les effets d'ordre de parcours des aretes.
"""
from __future__ import annotations

import networkx as nx

from agent import Agent

ALPHA = 0.5  # fraction de l'ecart transferee a chaque round (taux de diffusion)


def diffusion_round(graph: nx.Graph, agents: dict[int, Agent]) -> float:
    """Execute un round de diffusion. Retourne le volume total de charge
    deplacee (utile pour detecter la convergence : proche de 0 = stable).
    """
    transfers: dict[int, float] = {node: 0.0 for node in agents}
    total_moved = 0.0

    for u, v in graph.edges:
        agent_u, agent_v = agents[u], agents[v]
        if not agent_u.alive or not agent_v.alive:
            continue

        # On equilibre sur l'utilisation relative (load/capacity), pas la
        # charge brute -- deux agents de capacites differentes doivent
        # converger vers le meme taux d'occupation, pas la meme charge.
        diff_util = agent_u.utilization - agent_v.utilization
        if diff_util <= 0:
            continue

        # Convertit l'ecart d'utilisation en volume de charge a transferer,
        # proportionnel aux capacites des deux agents.
        amount = ALPHA * diff_util * (agent_u.capacity * agent_v.capacity) / (
            agent_u.capacity + agent_v.capacity
        )
        amount = min(amount, agent_u.load)  # jamais transferer plus que ce qu'on a
        if amount <= 0:
            continue

        transfers[u] -= amount
        transfers[v] += amount
        total_moved += amount

    for node, delta in transfers.items():
        agents[node].load = max(0.0, agents[node].load + delta)

    return total_moved


def run_diffusion(
    graph: nx.Graph,
    agents: dict[int, Agent],
    max_rounds: int = 200,
    convergence_threshold: float = 0.5,
    on_round=None,
) -> int:
    """Fait tourner la diffusion jusqu'a convergence (le volume deplace par
    round passe sous convergence_threshold) ou max_rounds. Retourne le
    nombre de rounds effectivement executes. `on_round(round_idx, agents)`
    est appele apres chaque round si fourni (pour collecter des metriques).
    """
    for round_idx in range(1, max_rounds + 1):
        moved = diffusion_round(graph, agents)
        if on_round is not None:
            on_round(round_idx, agents)
        if moved < convergence_threshold:
            return round_idx
    return max_rounds
