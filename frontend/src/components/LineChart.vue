<template>
  <div class="bg-white rounded-lg shadow p-4">
    <h3 class="text-sm font-semibold text-gray-700 mb-2">{{ title }}</h3>
    <canvas ref="canvasEl" class="w-full" height="160"></canvas>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch, ref } from "vue";
import Chart from "chart.js/auto";

const props = defineProps({
  title: { type: String, required: true },
  datasets: { type: Array, required: true }, // [{label, data, color}]
  yLabel: { type: String, default: "" },
  currentRound: { type: Number, default: null },
  lines: { type: Array, default: () => [] }, // [{round, color, label}]
});

const canvasEl = ref(null);
let chart = null;

function markerPlugin() {
  return {
    id: "roundMarkers",
    beforeDraw(c) {
      const { ctx, chartArea, scales } = c;
      if (!chartArea) return;
      ctx.save();

      for (const line of props.lines) {
        const x = scales.x.getPixelForValue(line.round);
        ctx.strokeStyle = line.color;
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        ctx.moveTo(x, chartArea.top);
        ctx.lineTo(x, chartArea.bottom);
        ctx.stroke();
      }

      if (props.currentRound != null) {
        const x = scales.x.getPixelForValue(props.currentRound);
        ctx.setLineDash([]);
        ctx.strokeStyle = "#2E7DD1";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x, chartArea.top);
        ctx.lineTo(x, chartArea.bottom);
        ctx.stroke();
      }
      ctx.restore();
    },
  };
}

function render() {
  if (chart) chart.destroy();
  const labels = props.datasets[0]?.data.map((_, i) => i + 1) ?? [];
  chart = new Chart(canvasEl.value, {
    type: "line",
    data: {
      labels,
      datasets: props.datasets.map((d) => ({
        label: d.label,
        data: d.data,
        borderColor: d.color,
        backgroundColor: "transparent",
        tension: 0.25,
        pointRadius: 0,
      })),
    },
    options: {
      responsive: true,
      animation: false,
      interaction: { intersect: false, mode: "index" },
      scales: {
        x: { title: { display: true, text: "Round" } },
        y: { title: { display: true, text: props.yLabel } },
      },
      plugins: { legend: { display: props.datasets.length > 1, position: "bottom" } },
    },
    plugins: [markerPlugin()],
  });
}

onMounted(render);
onBeforeUnmount(() => chart?.destroy());
watch(() => props.datasets, render);
watch(() => props.currentRound, () => chart?.update());
</script>
