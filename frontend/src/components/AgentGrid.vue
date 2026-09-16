<template>
  <div
    class="grid gap-1 w-full"
    :style="{ gridTemplateColumns: `repeat(${grid.cols}, minmax(0, 1fr))` }"
  >
    <div
      v-for="(pos, idStr) in grid.positions"
      :key="idStr"
      class="aspect-square rounded flex items-center justify-center text-[10px] font-semibold text-white transition-colors duration-200"
      :style="{
        gridRow: pos.row + 1,
        gridColumn: pos.col + 1,
        backgroundColor: cellColor(idStr),
        opacity: isAlive(idStr) ? 1 : 0.25,
      }"
      :title="cellTitle(idStr)"
    >
      {{ isAlive(idStr) ? idStr : "×" }}
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  grid: { type: Object, required: true }, // { rows, cols, positions: {id: {row, col}} }
  utilization: { type: Object, default: () => ({}) }, // {id: value}
  alive: { type: Object, default: () => ({}) }, // {id: bool}, optionnel
});

function congestionColor(ratio) {
  const r = Math.max(0, Math.min(1, ratio));
  const stops = [
    [0.0, [26, 152, 80]],
    [0.5, [254, 224, 139]],
    [1.0, [215, 48, 39]],
  ];
  for (let i = 0; i < stops.length - 1; i++) {
    const [p0, c0] = stops[i], [p1, c1] = stops[i + 1];
    if (r >= p0 && r <= p1) {
      const t = (r - p0) / (p1 - p0);
      const c = c0.map((v, idx) => Math.round(v + t * (c1[idx] - v)));
      return `rgb(${c[0]},${c[1]},${c[2]})`;
    }
  }
  return "rgb(215,48,39)";
}

function isAlive(id) {
  if (!(id in props.alive)) return true; // pas de notion de panne dans ce scenario
  return props.alive[id];
}

function cellColor(id) {
  if (!isAlive(id)) return "#9AA0A6";
  return congestionColor(props.utilization[id] ?? 0);
}

function cellTitle(id) {
  const util = props.utilization[id];
  return `Agent ${id} — utilisation ${util !== undefined ? (util * 100).toFixed(0) + "%" : "?"}`;
}
</script>
