<script setup lang="ts">
// Date de debut de la saison des pluies, annee par annee (IMERG vs POWER)
import { CategoryScale, Chart, Legend, LinearScale, LineController, LineElement, PointElement, Tooltip } from 'chart.js'
import type { Climat } from '~/composables/useFieldShiftApi'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend)

const props = defineProps<{ climat: Climat }>()
const { t, locale } = useI18n()
const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

// Jours de l'annee affiches sur l'axe : 15 fevrier, 1er mars, ... 15 mai
const REPERES = [46, 60, 74, 91, 105, 121, 135]
const langue = () => (locale.value === 'en' ? 'en-GB' : 'fr-FR')
function jourEnDate(jour: number, mois: 'long' | 'short' = 'long'): string {
  const d = new Date(2001, 0, 1)
  d.setDate(d.getDate() + Math.round(jour) - 1)
  return d.toLocaleDateString(langue(), { day: 'numeric', month: mois })
}

function dessiner() {
  if (!canvas.value) return
  chart?.destroy()
  const donnees = props.climat.debut_saison
  const jours = donnees.flatMap((d) => [d.jour_imerg, d.jour_power]).filter((j): j is number => j != null)
  if (!jours.length) return
  const min = Math.min(...jours) - 5
  const max = Math.max(...jours) + 5

  chart = new Chart(canvas.value, {
    type: 'line',
    data: {
      labels: donnees.map((d) => String(d.annee)),
      datasets: [
        {
          label: 'GPM IMERG',
          data: donnees.map((d) => d.jour_imerg),
          borderColor: '#2e7d43',
          backgroundColor: '#2e7d43',
          borderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
        },
        {
          label: t('outil.graphiques.powerBiaise'),
          data: donnees.map((d) => d.jour_power),
          borderColor: '#9fb0b8',
          backgroundColor: '#9fb0b8',
          borderWidth: 2,
          borderDash: [5, 4],
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, boxHeight: 6, color: '#4d6359' } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label} : ${ctx.parsed.y != null ? jourEnDate(ctx.parsed.y) : 'n.d.'}`,
          },
        },
      },
      scales: {
        y: {
          reverse: true,
          min,
          max,
          afterBuildTicks: (axis) => {
            axis.ticks = REPERES.filter((v) => v >= min && v <= max).map((value) => ({ value }))
          },
          ticks: { callback: (v) => jourEnDate(Number(v), 'short'), color: '#4d6359' },
          grid: { color: '#e3ebe5' },
          border: { display: false },
        },
        x: { grid: { display: false }, ticks: { color: '#4d6359', maxRotation: 0, autoSkipPadding: 12 } },
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
    <canvas ref="canvas" :aria-label="t('outil.graphiques.debutAria')" role="img" />
  </div>
</template>