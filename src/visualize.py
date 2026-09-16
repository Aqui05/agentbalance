"""Genere les graphiques utilises dans le README / la candidature."""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")  # pas d'affichage interactif, on sauvegarde en fichiers
import matplotlib.pyplot as plt

from agent import Agent


def plot_before_after(initial_agents: dict[int, Agent], final_agents: dict[int, Agent], out_path: str) -> None:
    ids = sorted(initial_agents.keys())
    before = [initial_agents[i].utilization for i in ids]
    after = [final_agents[i].utilization for i in ids]

    x = range(len(ids))
    width = 0.4

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar([i - width / 2 for i in x], before, width, label="Avant (round 0)", color="#D34C4C")
    ax.bar([i + width / 2 for i in x], after, width, label="Après (diffusion)", color="#1B8A5A")
    ax.set_xlabel("Agent")
    ax.set_ylabel("Utilisation (charge / capacité)")
    ax.set_title("Répartition de charge avant / après diffusion")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_convergence(history: dict[str, list[float]], out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(history["static"], label="Statique (sans coordination)", color="#D34C4C")
    ax.plot(history["diffusion"], label="Diffusion (négociation locale)", color="#1B8A5A")
    ax.set_xlabel("Round")
    ax.set_ylabel("Écart-type de l'utilisation entre agents")
    ax.set_title("Convergence : statique vs diffusion, sous flux continu de tâches")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_resilience(
    stddev_history: list[float],
    spike_round: int,
    failure_round: int,
    out_path: str,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(range(1, len(stddev_history) + 1), stddev_history, color="#2E7DD1")
    ax.axvline(spike_round, color="#E0A100", linestyle="--", label="Pic de charge soudain")
    ax.axvline(failure_round, color="#D34C4C", linestyle="--", label="Panne d'un agent")
    ax.set_xlabel("Round")
    ax.set_ylabel("Écart-type de l'utilisation entre agents")
    ax.set_title("Résilience : réaction à un pic de charge puis à une panne")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)
