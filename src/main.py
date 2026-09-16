"""
Execute les deux scenarios et produit :
  - les graphiques dans results/
  - un resume chiffre affiche dans le terminal (et reutilisable tel quel
    dans le README / la lettre de motivation).
"""
from __future__ import annotations

import os
import statistics

from diffusion import run_diffusion
from metrics import utilization_stddev
from simulator import run_resilience_scenario, run_static_vs_diffusion
from visualize import ensure_dir, plot_before_after, plot_convergence, plot_resilience

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def main() -> None:
    ensure_dir(RESULTS_DIR)

    print("=== Scenario 1 : convergence pure depuis un etat desequilibre ===")
    from agent import build_network, init_agents
    import copy

    graph2 = build_network(20, seed=42)
    agents2 = init_agents(graph2, seed=42)
    agents2_initial = copy.deepcopy(agents2)
    initial_stddev = utilization_stddev(agents2)
    rounds_to_converge = run_diffusion(graph2, agents2, max_rounds=200, convergence_threshold=0.5)
    final_stddev = utilization_stddev(agents2)
    print(f"Ecart-type initial : {initial_stddev:.3f}")
    print(f"Ecart-type final   : {final_stddev:.3f}  (apres {rounds_to_converge} rounds)")

    plot_before_after(agents2_initial, agents2, f"{RESULTS_DIR}/before_after.png")

    print("\n=== Scenario 2 : statique vs diffusion (flux continu de taches) ===")
    result = run_static_vs_diffusion(n_agents=20, rounds=60, seed=42)
    history = result["history"]

    plot_convergence(history, f"{RESULTS_DIR}/convergence.png")

    static_final = history["static"][-1]
    diffusion_final = history["diffusion"][-1]
    static_avg = statistics.mean(history["static"])
    diffusion_avg = statistics.mean(history["diffusion"])

    print(f"Ecart-type moyen (statique)   : {static_avg:.3f}")
    print(f"Ecart-type moyen (diffusion)  : {diffusion_avg:.3f}")
    print(f"Ecart-type final (statique)   : {static_final:.3f}")
    print(f"Ecart-type final (diffusion)  : {diffusion_final:.3f}")
    reduction_pct = (1 - diffusion_avg / static_avg) * 100 if static_avg else 0
    print(f"Reduction moyenne de l'ecart-type grace a la diffusion : {reduction_pct:.1f}%")

    print("\n=== Scenario 3 : resilience (pic de charge + panne d'un agent) ===")
    res = run_resilience_scenario(n_agents=20, rounds=80, spike_round=20, failure_round=45, seed=7)
    plot_resilience(
        res["stddev_history"], res["spike_round"], res["failure_round"],
        f"{RESULTS_DIR}/resilience.png",
    )
    print(f"Agent en panne              : node-{res['failed_node']}")
    print(f"Ecart-type de reference     : {res['baseline_stddev']:.3f}")
    print(f"Ecart-type au pic (round {res['spike_round']})  : {res['stddev_history'][res['spike_round']-1]:.3f}")
    print(f"Ecart-type a la panne (round {res['failure_round']}) : {res['stddev_history'][res['failure_round']-1]:.3f}")
    if res["recovery_rounds_after_spike"] is not None:
        print(f"Temps de recuperation apres le pic  : {res['recovery_rounds_after_spike']} rounds")
    else:
        print("Le systeme n'a pas retrouve son niveau de reference avant la panne suivante.")
    if res["recovery_rounds_after_failure"] is not None:
        print(f"Temps de recuperation apres la panne : {res['recovery_rounds_after_failure']} rounds")
    else:
        print("Le systeme n'a pas retrouve son niveau de reference dans la fenetre simulee.")

    print(f"\nGraphiques sauvegardes dans {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
