"""Metriques utilisees pour comparer les scenarios (statique vs diffusion,
avant/apres panne).
"""
from __future__ import annotations

import statistics

from agent import Agent


def utilization_stddev(agents: dict[int, Agent]) -> float:
    """Ecart-type de l'utilisation (load/capacity) entre agents vivants.
    C'est LA metrique de repartition de charge : proche de 0 = charge bien
    equilibree entre tous les agents, peu importe leurs capacites respectives.
    """
    utils = [a.utilization for a in agents.values() if a.alive]
    if len(utils) < 2:
        return 0.0
    return statistics.pstdev(utils)


def total_load(agents: dict[int, Agent]) -> float:
    return sum(a.load for a in agents.values() if a.alive)


def max_utilization(agents: dict[int, Agent]) -> float:
    utils = [a.utilization for a in agents.values() if a.alive]
    return max(utils) if utils else 0.0
