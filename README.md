# AgentBalance — Répartition de charge décentralisée par négociation locale

Simulation d'un ensemble d'agents (noeuds de calcul) qui répartissent une
charge de travail entre eux **sans chef d'orchestre central** : chaque
agent négocie uniquement avec ses voisins directs, et le système converge
vers un équilibre global à partir de décisions purement locales.

## Architecture

```
src/                → coeur de la simulation (partagé par tout le reste)
  agent.py            Agent (charge, capacité) + construction du réseau (grille torique)
  diffusion.py        algorithme de diffusion (négociation locale par round)
  simulator.py        scénarios : flux continu de tâches, perturbations (pic, panne)
  metrics.py          écart-type d'utilisation, utilisation max, charge totale
  visualize.py         génération des graphiques (matplotlib)
  main.py              exécute les 3 scénarios, sauvegarde les graphiques dans results/
backend/            → API FastAPI (conteneurisée), expose src/ en HTTP
  app/main.py
  Dockerfile
frontend/           → interface Vue 3 + Tailwind + Chart.js
  src/
    App.vue
    api.js
    components/       AgentGrid (heatmap), LineChart, ControlPanel
  Dockerfile
  nginx.conf
tests/              → tests automatisés (pytest) — simulation + API
docker-compose.yml  → orchestre backend + frontend
```

**Topologie** : grille 2D torique (~20 noeuds, 4 voisins chacun) — le cas
d'école classique pour étudier la diffusion, ni trop connectée (ce qui
masquerait les effets de propagation), ni trop clairsemée.

**Modélisation réaliste** : les agents ne font pas qu'accumuler de la
charge — ils la **traitent** à un débit proportionnel à leur capacité
(comme un serveur qui répond aux requêtes), ce qui crée un vrai régime
stationnaire plutôt qu'une croissance illimitée, et rend les mesures de
récupération après incident significatives.

## Résultats

### 1. Convergence pure depuis un état déséquilibré

À partir d'un état initial très déséquilibré (certains agents à 230%
d'utilisation, d'autres à 0%), la diffusion seule (sans nouvelle arrivée)
fait passer l'écart-type d'utilisation de **0,898 à 0,308 en 29 rounds**.

![Avant / après diffusion](results/before_after.png)

*(la convergence n'est pas totale : sur une topologie locale, l'information
met du temps à traverser tout le réseau — un résultat attendu et
révélateur de la nature du compromis décentralisé/global)*

### 2. Statique vs diffusion, sous flux continu de tâches

En simulant l'arrivée continue de nouvelles tâches sur des agents
aléatoires (comme des requêtes non coordonnées à l'entrée du système),
sur 60 rounds :

| | Écart-type moyen | Écart-type final |
|---|---|---|
| **Statique** (sans coordination) | 0,697 | 0,442 |
| **Diffusion** (négociation locale) | 0,200 | 0,052 |

**Réduction moyenne de l'écart-type grâce à la diffusion : 71,3 %.**

![Convergence statique vs diffusion](results/convergence.png)

### 3. Résilience face à un pic de charge et à une panne d'agent

Scénario : régime stationnaire, puis un **pic soudain** (round 20, un
agent reçoit 3x sa capacité d'un coup) suivi d'une **panne d'agent**
(round 45, un noeud est retiré du réseau, sa charge redistribuée en
urgence à ses voisins) :

- Écart-type de référence (régime stationnaire) : **0,184**
- Pic au moment du choc de charge : **0,294**
- Récupération sous le seuil de référence : **1 round** après le pic,
  **1 round** après la panne

![Résilience](results/resilience.png)

Le système absorbe la panne d'un agent presque sans à-coup visible — la
charge du noeud tombé est réabsorbée par ses voisins directs en un round,
sans intervention centrale.

## Lancer avec Docker (interface web complète)

```bash
docker compose up --build
```

- Frontend (interface complète, avec grille d'agents animée + graphiques
  + contrôles pour relancer la simulation avec d'autres paramètres) :
  http://localhost:8080
- Backend (API brute) : http://localhost:8000/api/health,
  http://localhost:8000/api/scenario/resilience

C'est la façon recommandée d'explorer le projet : contrairement au script
`main.py` (qui s'exécute une fois et s'arrête), le backend reste actif et
répond à la demande — tu peux changer le nombre d'agents, le round du pic
ou de la panne, et relancer directement depuis l'interface.

### Développer sans Docker

```bash
# Terminal 1 : backend
pip install -r backend/requirements.txt
PYTHONPATH=src uvicorn main:app --app-dir backend/app --reload --port 8000

# Terminal 2 : frontend (proxy /api vers localhost:8000, voir vite.config.js)
cd frontend
npm install
npm run dev
```

## Lancer le script (rapport statique, sans interface)

```bash
pip install -r requirements.txt
cd src
python3 main.py        # exécute les 3 scénarios, régénère results/*.png
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

