<template>
  <div class="bg-white rounded-lg shadow p-4 space-y-4">
    <div>
      <label class="text-xs text-gray-500 block mb-1">Scénario</label>
      <div class="flex flex-col gap-1">
        <button
          v-for="tab in tabs" :key="tab.id"
          class="py-1.5 rounded border text-sm text-left px-2"
          :class="scenario === tab.id ? 'bg-primary text-white border-primary' : 'border-primary text-primary'"
          @click="$emit('update:scenario', tab.id)"
        >{{ tab.label }}</button>
      </div>
    </div>

    <div v-if="maxRound > 0">
      <label class="text-xs text-gray-500 block mb-1">
        Round : <span class="font-semibold">{{ round }}</span> / {{ maxRound }}
      </label>
      <input
        type="range" min="1" :max="maxRound" :value="round"
        class="w-full accent-primary"
        @input="$emit('update:round', Number($event.target.value))"
      />
      <button class="w-full mt-2 py-1.5 rounded bg-secondary text-white text-sm" @click="$emit('toggle-play')">
        {{ playing ? "⏸ Pause" : "▶ Lecture automatique" }}
      </button>
    </div>

    <div class="border-t pt-3 space-y-2">
      <p class="text-xs font-semibold text-gray-600">Paramètres</p>

      <label class="text-xs text-gray-500 block">
        Nombre d'agents : {{ params.nAgents }}
        <input type="range" min="8" max="60" step="1" :value="params.nAgents" class="w-full accent-secondary"
          @input="update('nAgents', Number($event.target.value))" />
      </label>

      <label v-if="scenario === 'resilience'" class="text-xs text-gray-500 block">
        Round du pic de charge
        <input type="number" min="1" :value="params.spikeRound" class="w-full border rounded px-2 py-1 text-sm"
          @change="update('spikeRound', Number($event.target.value))" />
      </label>

      <label v-if="scenario === 'resilience'" class="text-xs text-gray-500 block">
        Round de la panne
        <input type="number" min="1" :value="params.failureRound" class="w-full border rounded px-2 py-1 text-sm"
          @change="update('failureRound', Number($event.target.value))" />
      </label>

      <button class="w-full py-1.5 rounded border border-secondary text-secondary text-sm" @click="$emit('rerun')" :disabled="loading">
        {{ loading ? "Simulation en cours…" : "🔄 Relancer la simulation" }}
      </button>
    </div>

    <div class="border-t pt-3 text-xs text-gray-600 space-y-1">
      <slot name="stats" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  scenario: String,
  round: Number,
  maxRound: Number,
  playing: Boolean,
  params: Object,
  loading: Boolean,
});

const emit = defineEmits(["update:scenario", "update:round", "toggle-play", "rerun", "update:params"]);

const tabs = [
  { id: "convergence", label: "Convergence pure" },
  { id: "static-vs-diffusion", label: "Statique vs Diffusion" },
  { id: "resilience", label: "Résilience (pic + panne)" },
];

function update(key, value) {
  emit("update:params", { key, value });
}
</script>
