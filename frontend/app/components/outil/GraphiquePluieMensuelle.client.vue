<script setup lang="ts">
// Pluie moyenne par mois : premiere decennie vs deuxieme decennie (IMERG)
import { BarController, BarElement, CategoryScale, Chart, Legend, LinearScale, Tooltip } from 'chart.js'
import type { Climat } from '~/composables/useFieldShiftApi'

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const props = defineProps<{ climat: Climat }>()
const { t, locale } = useI18n()
const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

function dessiner() {
  if (!canvas.value) return
  chart?.destroy()
  const m = props.climat.pluie_mensuelle
  const espace = locale.value === 'en' ? '' : ' '
  chart = new Chart(canvas.value, {
    type: 'bar',
    data: {
      labels: m.map((x) => t(`mois.${x.mois}`)),
      datasets: [
        {
          label: props.climat.periode_a,
          data: m.map((x) => x.periode_a_mm),
          backgroundColor: '#b9c6cc',
          borderRadius: { topLeft: 4, topRight: 4 },
          borderSkipped: 'bottom',
        },
        {
          label: props.climat.periode_b,
          data: m.map((x) => x.periode_b_mm),
          backgroundColor: '#2e7d43',
          borderRadius: { topLeft: 4, topRight: 4 },
          borderSkipped: 'bottom',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, boxHeight: 6, color: '#4d6359' } },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label} : ${Math.round(ctx.parsed.y ?? 0)} mm`,
            footer: (items) => {
              const e = m[items[0]?.dataIndex ?? 0]?.ecart_pct
              return e == null ? '' : `${t('outil.graphiques.ecart')} : ${e > 0 ? '+' : ''}${Math.round(e)}${espace}%`
            },
          },
        },
      },
      scales: {
        y: {
          title: { display: true, text: t('outil.graphiques.mmMois'), color: '#4d6359' },
          grid: { color: '#e3ebe5' },
          border: { display: false },
          ticks: { color: '#4d6359' },
        },
        x: { grid: { display: false }, ticks: { color: '#4d6359', maxRotation: 0 } },
      },
    },
  })
}

onMounted(async () => {
  // composant .client : le gabarit n'est rendu qu'apres le montage
  await nextTick()
  dessiner()
})
watch([() => props.climat, locale], dessiner)
onBeforeUnmount(() => chart?.destroy())
</script>

<template>
  <div class="h-72">
    <canvas ref="canvas" :aria-label="t('outil.graphiques.moisAria')" role="img" />
  </div>
</template>