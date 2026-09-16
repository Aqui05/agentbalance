"""
Modelisation des agents et du reseau de voisinage.

Topologie : grille 2D torique (chaque agent a exactement 4 voisins, les
bords "s'enroulent"). C'est le cas d'ecole classique pour etudier la
diffusion load balancing en litterature systemes distribues -- ni trop
connecte (ce qui masquerait les effets de propagation), ni trop clairsemé.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

import networkx as nx


@dataclass
class Agent:
    """Un agent = un noeud de calcul (serveur simule)."""

    agent_id: int
    capacity: float          # charge que l'agent peut absorber confortablement
    load: float               # charge actuelle (nombre de "taches" en unites de calcul)
    alive: bool = True

    @property
    def utilization(self) -> float:
        if self.capacity <= 0:
            return float("inf")
        return self.load / self.capacity


def grid_shape(n_agents: int) -> tuple[int, int]:
    """Dimensions (rows, cols) de la grille toroidale pour n_agents --
    reutilise par build_network() et par le backend (pour positionner
    chaque agent sur une grille visuelle cote frontend)."""
    rows = int(round(n_agents ** 0.5))
    rows = max(1, rows)
    cols = max(1, -(-n_agents // rows))  # ceil division
    return rows, cols


def build_network(n_agents: int, seed: int | None = None) -> nx.Graph:
    """Construit une grille 2D torique d'environ n_agents noeuds.

    On cherche les dimensions (rows, cols) les plus carrees possible pour
    que rows*cols == n_agents (ou tres proche).
    """
    rows, cols = grid_shape(n_agents)

    graph = nx.grid_2d_graph(rows, cols, periodic=True)
    graph = nx.convert_node_labels_to_integers(graph)

    # Si rows*cols > n_agents (arrondi), on retire les noeuds en trop.
    while graph.number_of_nodes() > n_agents:
        graph.remove_node(max(graph.nodes))

    return graph


def init_agents(graph: nx.Graph, seed: int | None = None) -> dict[int, Agent]:
    """Cree les agents avec des charges initiales volontairement desequilibrees
    (certains noeuds sur-charges, d'autres presque vides) pour rendre le
    rebalancement visible et mesurable.
    """
    rng = random.Random(seed)
    agents: dict[int, Agent] = {}

    for node in graph.nodes:
        capacity = rng.uniform(80, 120)
        # Desequilibre volontaire : ~30% des noeuds demarrent tres charges
        if rng.random() < 0.3:
            load = capacity * rng.uniform(1.5, 2.5)
        else:
            load = capacity * rng.uniform(0.0, 0.6)
        agents[node] = Agent(agent_id=node, capacity=capacity, load=load)

    return agents
