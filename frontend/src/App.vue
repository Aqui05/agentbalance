<template>
  <div class="h-full flex flex-col bg-gray-100">
    <header class="bg-primary text-white px-4 py-3 shadow">
      <h1 class="text-lg font-semibold">🖧 AgentBalance — Répartition de charge décentralisée</h1>
      <p class="text-xs opacity-90">Agents qui négocient localement, sans chef d'orchestre central</p>
    </header>

    <div v-if="error" class="m-4 p-3 bg-red-100 text-red-700 rounded text-sm">
      Impossible de contacter le backend ({{ error }}). Vérifiez qu'il tourne
      bien sur <code>/api</code> (voir README, section Docker).
    </div>

    <div v-else-if="!data" class="flex-1 flex items-center justify-center text-gray-500">
      Chargement de la simulation…
    </div>

    <div v-else class="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 p-4 min-h-0 overflow-y-auto">
      <div class="lg:col-span-1">
        <ControlPanel
          :scenario="scenario"
          :round="round"
          :max-round="maxRound"
          :playing="playing"
          :params="params"
          :loading="loading"
          @update:scenario="changeScenario"
          @update:round="round = $event"
          @toggle-play="togglePlay"
          @rerun="loadData"
          @update:params="onParamChange"
        >
          <template #stats>
            <p v-if="scenario === 'convergence'">
              Écart-type initial : <b>{{ data.initial_stddev.toFixed(3) }}</b><br />
              Écart-type final : <b>{{ data.final_stddev.toFixed(3) }}</b><br />
              Convergence en <b>{{ data.rounds_to_converge }}</b> rounds
            </p>
            <p v-else-if="scenario === 'static-vs-diffusion'">
              Écart-type moyen statique : <b>{{ avg(data.history.static).toFixed(3) }}</b><br />
              Écart-type moyen diffusion : <b>{{ avg(data.history.diffusion).toFixed(3) }}</b><br />
              Réduction : <b>{{ reductionPct.toFixed(1) }}%</b>
            </p>
            <p v-else-if="scenario === 'resilience'">
              Agent en panne : <b>node-{{ data.failed_node }}</b><br />
              Écart-type de référence : <b>{{ data.baseline_stddev.toFixed(3) }}</b><br />
              Récupération après le pic : <b>{{ data.recovery_rounds_after_spike ?? "—" }} rounds</b><br />
              Récupération après la panne : <b>{{ data.recovery_rounds_after_failure ?? "—" }} rounds</b>
            </p>
          </template>
        </ControlPanel>
      </div>

      <div class="lg:col-span-1">
        <div class="bg-white rounded-lg shadow p-4 h-full">
          <h3 class="text-sm font-semibold text-gray-700 mb-2">Grille des agents (utilisation)</h3>
          <AgentGrid :grid="data.grid" :utilization="currentUtilization" :alive="currentAlive" />
          <div class="flex gap-3 mt-3 text-[11px] text-gray-500">
            <span><span class="inline-block w-3 h-3 rounded" style="background:#1a9850"></span> fluide</span>
            <span><span class="inline-block w-3 h-3 rounded" style="background:#fee08b"></span> chargé</span>
            <span><span class="inline-block w-3 h-3 rounded" style="background:#d73027"></span> saturé</span>
            <span><span class="inline-block w-3 h-3 rounded bg-gray-400 opacity-25"></span> hors ligne</span>
          </div>
        </div>
      </div>

      <div class="lg:col-span-2 space-y-4">
        <LineChart
          v-for="chart in charts" :key="chart.title"
          :title="chart.title" :datasets="chart.datasets" :y-label="chart.yLabel"
          :current-round="round" :lines="chart.lines || []"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref } from "vue";
import ControlPanel from "./components/ControlPanel.vue";
import AgentGrid from "./components/AgentGrid.vue";
import LineChart from "./components/LineChart.vue";
import { fetchConvergence, fetchStaticVsDiffusion, fetchResilience } from "./api.js";

const scenario = ref("resilience");
const round = ref(1);
const playing = ref(false);
const loading = ref(false);
const error = ref(null);
const data = ref(null);
let playTimer = null;

const params = reactive({
  nAgents: 20,
  spikeRound: 20,
  failureRound: 45,
});

const maxRound = computed(() => {
  if (!data.value) return 0;
  if (scenario.value === "convergence") return data.value.utilization_by_round.length;
  if (scenario.value === "static-vs-diffusion") return data.value.history.static.length;
  if (scenario.value === "resilience") return data.value.stddev_history.length;
  return 0;
});

const currentUtilization = computed(() => {
  if (!data.value) return {};
  const idx = round.value - 1;
  if (scenario.value === "convergence") return data.value.utilization_by_round[idx] ?? {};
  if (scenario.value === "static-vs-diffusion") return data.value.diffusion_utilization_by_round[idx] ?? {};
  if (scenario.value === "resilience") return data.value.utilization_by_round[idx] ?? {};
  return {};
});

const currentAlive = computed(() => {
  if (!data.value || scenario.value !== "resilience") return {};
  return data.value.alive_by_round[round.value - 1] ?? {};
});

const reductionPct = computed(() => {
  if (!data.value || scenario.value !== "static-vs-diffusion") return 0;
  const s = avg(data.value.history.static), d = avg(data.value.history.diffusion);
  return s ? (1 - d / s) * 100 : 0;
});

const charts = computed(() => {
  if (!data.value) return [];
  if (scenario.value === "convergence") {
    return [{
      title: "Écart-type d'utilisation (convergence pure)",
      yLabel: "Écart-type",
      datasets: [{ label: "Écart-type", data: data.value.stddev_by_round, color: "#1B8A5A" }],
    }];
  }
  if (scenario.value === "static-vs-diffusion") {
    return [{
      title: "Statique vs diffusion, sous flux continu",
      yLabel: "Écart-type",
      datasets: [
        { label: "Statique", data: data.value.history.static, color: "#D34C4C" },
        { label: "Diffusion", data: data.value.history.diffusion, color: "#1B8A5A" },
      ],
    }];
  }
  if (scenario.value === "resilience") {
    return [{
      title: "Résilience : pic de charge puis panne d'un agent",
      yLabel: "Écart-type",
      datasets: [{ label: "Écart-type", data: data.value.stddev_history, color: "#2E7DD1" }],
      lines: [
        { round: data.value.spike_round, color: "#E0A100", label: "Pic" },
        { round: data.value.failure_round, color: "#D34C4C", label: "Panne" },
      ],
    }];
  }
  return [];
});

function avg(arr) {
  return arr.reduce((s, v) => s + v, 0) / (arr.length || 1);
}

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    if (scenario.value === "convergence") {
      data.value = await fetchConvergence({ nAgents: params.nAgents });
    } else if (scenario.value === "static-vs-diffusion") {
      data.value = await fetchStaticVsDiffusion({ nAgents: params.nAgents });
    } else {
      data.value = await fetchResilience({
        nAgents: params.nAgents, spikeRound: params.spikeRound, failureRound: params.failureRound,
      });
    }
    round.value = 1;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function changeScenario(newScenario) {
  scenario.value = newScenario;
  loadData();
}

function onParamChange({ key, value }) {
  params[key] = value;
}

function togglePlay() {
  playing.value = !playing.value;
  if (playing.value) {
    playTimer = setInterval(() => {
      round.value = round.value >= maxRound.value ? 1 : round.value + 1;
    }, 900);
  } else {
    clearInterval(playTimer);
  }
}

onBeforeUnmount(() => clearInterval(playTimer));

loadData();
</script>
