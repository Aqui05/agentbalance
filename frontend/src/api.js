const BASE = "/api";

async function getJSON(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status} on ${path}`);
  return res.json();
}

export function fetchConvergence({ nAgents = 20, seed = 42, maxRounds = 200 } = {}) {
  const params = new URLSearchParams({ n_agents: nAgents, seed, max_rounds: maxRounds });
  return getJSON(`/scenario/convergence?${params}`);
}

export function fetchStaticVsDiffusion({ nAgents = 20, rounds = 60, seed = 42 } = {}) {
  const params = new URLSearchParams({ n_agents: nAgents, rounds, seed });
  return getJSON(`/scenario/static-vs-diffusion?${params}`);
}

export function fetchResilience({
  nAgents = 20, rounds = 80, spikeRound = 20, failureRound = 45, seed = 7,
} = {}) {
  const params = new URLSearchParams({
    n_agents: nAgents, rounds, spike_round: spikeRound, failure_round: failureRound, seed,
  });
  return getJSON(`/scenario/resilience?${params}`);
}
