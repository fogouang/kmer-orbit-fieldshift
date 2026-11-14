<script setup lang="ts">
import * as L from "leaflet";

const props = defineProps<{
  latitude: number;
  longitude: number;
  nom: string;
}>();
const { t } = useI18n();

const el = ref<HTMLDivElement | null>(null);
let carte: L.Map | null = null;
let point: L.CircleMarker | null = null;

function placer() {
  if (!carte) return;
  const pos: L.LatLngExpression = [props.latitude, props.longitude];
  carte.setView(pos, 13);
  point?.remove();
  point = L.circleMarker(pos, {
    radius: 9,
    color: "#ffffff",
    weight: 3,
    fillColor: "#2e7d43",
    fillOpacity: 1,
  })
    .addTo(carte)
    .bindTooltip(props.nom, { direction: "top", offset: [0, -8] });
}

onMounted(async () => {
  // composant .client : le gabarit n'est rendu qu'apres le montage
  await nextTick();
  if (!el.value) return;
  carte = L.map(el.value, { scrollWheelZoom: false, attributionControl: true });
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap",
  }).addTo(carte);
  placer();
});

watch(() => [props.latitude, props.longitude], placer);
onBeforeUnmount(() => carte?.remove());
</script>

<template>
  <div
    ref="el"
    class="h-44 w-full rounded-lg border border-trait z-0"
    role="img"
    :aria-label="t('outil.panneau.carte', { nom })"
  />
</template>