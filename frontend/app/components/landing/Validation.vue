<script setup lang="ts">
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { BarController, BarElement, CategoryScale, Chart, Legend, LinearScale, Tooltip } from 'chart.js'

gsap.registerPlugin(ScrollTrigger)
Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const { t, locale } = useI18n()

// Pluie annuelle (mm) : station IRAD Dschang vs satellites.
// Source : data/processed/dschang_station_validation.json (scripts/station_irad.py). 2018 absente des releves.
const ANNEES = [
  { annee: 2014, station: 2053, imerg: 2184, power: 1525 },
  { annee: 2015, station: 1616, imerg: 1765, power: 3081 },
  { annee: 2016, station: 1768, imerg: 2062, power: 3639 },
  { annee: 2017, station: 1508, imerg: 1723, power: 3452 },
  { annee: 2019, station: 2417, imerg: 2076, power: 2501 },
  { annee: 2020, station: 1896, imerg: 2133, power: 2981 },
  { annee: 2021, station: 1607, imerg: 1479, power: 1861 },
  { annee: 2022, station: 2287, imerg: 2071, power: 3135 },
  { annee: 2023, station: 2430, imerg: 1843, power: 1916 },
  { annee: 2024, station: 2196, imerg: 1941, power: 1909 },
]

// Comparaison mois par mois sur 118 mois
const SOURCES = [
  { id: 'imerg', retenu: true },
  { id: 'power', retenu: false },
]
const STATS = ['correlation', 'biais', 'erreur'] as const

const COULEURS = { station: '#164333', imerg: '#43aa5c', power: '#b9c6cc' }

const racine = ref<HTMLElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null
let ctx: gsap.Context | null = null

const nombre = (v: number) => v.toLocaleString(locale.value === 'en' ? 'en-US' : 'fr-FR')

function dessiner(anime: boolean) {
  if (!canvas.value) return
  chart?.destroy()
  chart = new Chart(canvas.value, {
    type: 'bar',
    data: {
      labels: ANNEES.map((a) => String(a.annee)),
      datasets: (['station', 'imerg', 'power'] as const).map((cle) => ({
        label: t(`validation.graphique.${cle}`),
        data: ANNEES.map((a) => a[cle]),
        backgroundColor: COULEURS[cle],
        borderRadius: { topLeft: 3, topRight: 3 },
        borderSkipped: 'bottom' as const,
        categoryPercentage: 0.78,
        barPercentage: 0.92,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: anime ? { duration: 1200, easing: 'easeOutQuart' } : false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, boxHeight: 7, color: '#4d6359', padding: 16 } },
        tooltip: {
          callbacks: { label: (c) => `${c.dataset.label} : ${nombre(c.parsed.y ?? 0)} mm` },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: t('validation.graphique.unite'), color: '#4d6359' },
          ticks: { color: '#4d6359', callback: (v) => nombre(Number(v)) },
          grid: { color: '#e3ebe5' },
          border: { display: false },
        },
        x: { ticks: { color: '#4d6359' }, grid: { display: false } },
      },
    },
  })
}

onMounted(async () => {
  await nextTick()
  if (!racine.value) return
  const reduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  ctx = gsap.context(() => {
    if (reduit) {
      dessiner(false)
      return
    }
    gsap.from('[data-revele]', {
      opacity: 0,
      y: 30,
      duration: 0.8,
      stagger: 0.1,
      ease: 'power3.out',
      scrollTrigger: { trigger: racine.value, start: 'top 75%' },
    })
    // Le graphique se dessine quand il arrive a l'ecran
    ScrollTrigger.create({ trigger: canvas.value, start: 'top 85%', once: true, onEnter: () => dessiner(true) })
  }, racine.value)
})

// Changement de langue : legende et unites traduites
watch(locale, () => chart && dessiner(false))

onBeforeUnmount(() => {
  chart?.destroy()
  ctx?.revert()
})
</script>

<template>
  <section id="validation" ref="racine" class="fond-sombre relative overflow-hidden bg-foret text-white py-20 md:py-28">
    <span aria-hidden="true" class="billons-deco absolute inset-0 opacity-[0.05]" />

    <div class="relative mx-auto max-w-7xl px-4 md:px-6">
      <!-- En-tete -->
      <div class="grid gap-8 lg:grid-cols-[1fr_20rem] lg:items-end">
        <div class="max-w-3xl">
          <p data-revele class="sur-titre text-soleil">{{ t('validation.surTitre') }}</p>
          <h2 data-revele class="titre-large mt-4 text-3xl sm:text-4xl xl:text-5xl leading-tight">
            {{ t('validation.titre') }}
          </h2>
          <p data-revele class="mt-5 text-lg text-white/80 leading-relaxed">{{ t('validation.intro') }}</p>
        </div>
        <!-- Photo prise a la station -->
        <figure data-revele class="overflow-hidden rounded-2xl border border-white/15 bg-white/5">
          <img
            src="/images/hero/hero-3.jpg"
            :alt="t('validation.photoAlt')"
            class="h-40 w-full object-cover"
            loading="lazy"
            width="680"
            height="510"
          />
          <figcaption class="px-4 py-3 text-xs text-white/70">{{ t('validation.photoLegende') }}</figcaption>
        </figure>
      </div>

      <!-- IMERG retenu / POWER ecarte -->
      <div class="mt-12 grid gap-4 md:grid-cols-2">
        <article
          v-for="s in SOURCES"
          :key="s.id"
          data-revele
          class="rounded-2xl p-6 md:p-7 border"
          :class="s.retenu ? 'bg-white text-foret border-white' : 'bg-white/5 border-white/15'"
        >
          <div class="flex items-center justify-between gap-3">
            <h3 class="text-lg font-bold">{{ t(`validation.sources.${s.id}.nom`) }}</h3>
            <span
              class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold"
              :class="s.retenu ? 'bg-feuille text-foret' : 'bg-white/10 text-white/80'"
            >
              <i class="pi text-[0.65rem]" :class="s.retenu ? 'pi-check' : 'pi-times'" aria-hidden="true" />
              {{ t(`validation.sources.${s.id}.statut`) }}
            </span>
          </div>
          <dl class="mt-6 grid grid-cols-3 gap-3">
            <!-- dt avant dd (ordre HTML valide), affiche sous le chiffre -->
            <div v-for="st in STATS" :key="st" class="flex flex-col-reverse justify-end">
              <dt class="mt-2 text-xs leading-snug" :class="s.retenu ? 'text-encre-2' : 'text-white/65'">
                {{ t(`validation.stats.${st}`) }}
              </dt>
              <dd class="titre-large text-2xl sm:text-3xl md:text-4xl tabular-nums leading-none whitespace-nowrap">
                {{ t(`validation.sources.${s.id}.${st}`) }}
              </dd>
            </div>
          </dl>
          <p class="mt-5 text-sm leading-relaxed" :class="s.retenu ? 'text-encre-2' : 'text-white/70'">
            {{ t(`validation.sources.${s.id}.verdict`) }}
          </p>
        </article>
      </div>

      <!-- Graphique annuel -->
      <figure data-revele class="mt-4 rounded-2xl bg-white text-foret p-5 md:p-7">
        <figcaption class="flex flex-col md:flex-row md:items-end md:justify-between gap-1 mb-4">
          <span class="font-bold text-lg">{{ t('validation.graphique.titre') }}</span>
          <span class="text-sm text-encre-2">{{ t('validation.graphique.moyennes') }}</span>
        </figcaption>
        <div class="h-72 md:h-80">
          <canvas ref="canvas" role="img" :aria-label="t('validation.graphique.aria')" />
        </div>
        <!-- Les memes donnees en tableau, pour les lecteurs d'ecran -->
        <table class="sr-only">
          <caption>{{ t('validation.graphique.titre') }}</caption>
          <thead>
            <tr>
              <th scope="col">{{ t('validation.graphique.annee') }}</th>
              <th scope="col">{{ t('validation.graphique.station') }}</th>
              <th scope="col">{{ t('validation.graphique.imerg') }}</th>
              <th scope="col">{{ t('validation.graphique.power') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in ANNEES" :key="a.annee">
              <th scope="row">{{ a.annee }}</th>
              <td>{{ a.station }} mm</td>
              <td>{{ a.imerg }} mm</td>
              <td>{{ a.power }} mm</td>
            </tr>
          </tbody>
        </table>
        <p class="mt-4 text-xs text-encre-2">{{ t('validation.graphique.note') }}</p>
      </figure>

      <!-- Saison par saison -->
      <p data-revele class="mt-8 max-w-3xl text-white/85 leading-relaxed">
        <i class="pi pi-info-circle text-soleil mr-1.5" aria-hidden="true" />
        {{ t('validation.saisons') }}
      </p>
    </div>
  </section>
</template>

<style scoped>
.billons-deco {
  background: repeating-linear-gradient(115deg, transparent 0 46px, #ffffff 46px 47px);
}
</style>