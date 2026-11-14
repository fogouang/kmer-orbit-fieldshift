<script setup lang="ts">
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { COULEURS_CULTURES } from '~/utils/cultures'

gsap.registerPlugin(ScrollTrigger)

const { t } = useI18n()
const localePath = useLocalePath()

// Les 3 entrees du moteur
const ENTREES = [
  { id: 'climat', icone: 'pi-cloud', sources: ['NASA GPM IMERG', 'NASA POWER'] },
  { id: 'sol', icone: 'pi-map-marker', sources: ['ISRIC SoilGrids'] },
  { id: 'priorites', icone: 'pi-sliders-h', sources: [] as string[] },
]

// Ce que fait le moteur : 4 points traduits (commentCaMarche.moteur.points.0 a .3)
const POINTS_MOTEUR = computed(() => [0, 1, 2, 3].map((i) => t(`commentCaMarche.moteur.points.${i}`)))

// Les 3 meilleures rotations reellement proposees pour la parcelle de l'IRAD Dschang
// (une culture sur 2 campagnes = manioc)
const OPTIONS = [
  { note: 89, blocs: [['mais', 1], ['haricot', 1], ['pomme_de_terre', 1], ['arachide', 1]] },
  { note: 86, blocs: [['arachide', 1], ['mais', 1], ['manioc', 2]] },
  { note: 82, blocs: [['mais', 1], ['haricot', 1], ['manioc', 2]] },
] as const

const racine = ref<HTMLElement | null>(null)
let ctx: gsap.Context | null = null

onMounted(async () => {
  await nextTick()
  if (!racine.value) return
  ctx = gsap.context(() => {
    const mm = gsap.matchMedia()
    mm.add('(prefers-reduced-motion: no-preference)', () => {
      gsap.from('[data-revele]', {
        opacity: 0,
        y: 30,
        duration: 0.8,
        stagger: 0.1,
        ease: 'power3.out',
        scrollTrigger: { trigger: racine.value, start: 'top 75%' },
      })
      // Les 3 flux convergent vers le moteur
      gsap.fromTo(
        '[data-flux]',
        { clipPath: 'inset(0 0 100% 0)' },
        {
          clipPath: 'inset(0 0 0% 0)',
          duration: 1.1,
          ease: 'power2.inOut',
          scrollTrigger: { trigger: '[data-flux]', start: 'top 85%' },
        },
      )
      // Les bandes de rotation se remplissent
      gsap.from('[data-bande] > li', {
        scaleX: 0,
        transformOrigin: 'left',
        duration: 0.5,
        stagger: 0.06,
        ease: 'power2.out',
        scrollTrigger: { trigger: '[data-resultat]', start: 'top 80%' },
      })
    })
  }, racine.value)
})

onBeforeUnmount(() => ctx?.revert())
</script>

<template>
  <section id="comment-ca-marche" ref="racine" class="bg-white py-20 md:py-28 scroll-mt-4">
    <div class="mx-auto max-w-7xl px-4 md:px-6">
      <!-- En-tete -->
      <div class="max-w-3xl">
        <p data-revele class="sur-titre text-primary">{{ t('commentCaMarche.surTitre') }}</p>
        <h2 data-revele class="titre-large mt-4 text-3xl sm:text-4xl xl:text-5xl leading-tight text-foret">
          {{ t('commentCaMarche.titre') }}
        </h2>
        <p data-revele class="mt-5 text-lg text-encre-2 leading-relaxed">{{ t('commentCaMarche.intro') }}</p>
      </div>

      <!-- 1. Les 3 entrees -->
      <ol class="mt-12 grid gap-4 md:grid-cols-3">
        <li
          v-for="(e, i) in ENTREES"
          :key="e.id"
          data-revele
          class="rounded-2xl border border-trait bg-brume p-6"
        >
          <div class="flex items-center justify-between">
            <span class="grid size-11 place-items-center rounded-full bg-white text-primary border border-trait" aria-hidden="true">
              <i class="pi text-lg" :class="e.icone" />
            </span>
            <span class="titre-large text-3xl text-foret/15 tabular-nums" aria-hidden="true">0{{ i + 1 }}</span>
          </div>
          <h3 class="mt-4 text-lg font-bold text-foret">{{ t(`commentCaMarche.entrees.${e.id}.titre`) }}</h3>
          <p class="mt-1.5 text-sm text-encre-2 leading-relaxed">{{ t(`commentCaMarche.entrees.${e.id}.texte`) }}</p>
          <ul class="mt-4 flex flex-wrap gap-1.5">
            <li
              v-for="s in e.sources"
              :key="s"
              class="rounded-full bg-white border border-trait px-2.5 py-1 text-xs font-semibold text-foret"
            >
              {{ s }}
            </li>
            <li class="rounded-full bg-primary-50 px-2.5 py-1 text-xs font-semibold text-primary">
              {{ t(`commentCaMarche.entrees.${e.id}.badge`) }}
            </li>
          </ul>
        </li>
      </ol>

      <!-- Flux qui convergent (ecrans larges) / fleche (mobile) -->
      <svg
        data-flux
        class="hidden md:block w-full h-16 text-feuille"
        viewBox="0 0 600 64"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path d="M100 0 C 100 36, 300 28, 300 64" />
        <path d="M300 0 L 300 64" />
        <path d="M500 0 C 500 36, 300 28, 300 64" />
      </svg>
      <div class="md:hidden flex justify-center py-3 text-feuille" aria-hidden="true">
        <i class="pi pi-arrow-down text-xl" />
      </div>

      <!-- 2. Le moteur -->
      <div data-revele class="fond-sombre relative overflow-hidden rounded-2xl bg-foret text-white p-6 md:p-8">
        <span aria-hidden="true" class="billons-deco absolute inset-0 opacity-[0.06]" />
        <div class="relative grid gap-6 lg:grid-cols-[minmax(0,22rem)_1fr] lg:items-center">
          <div>
            <p class="sur-titre text-soleil">{{ t('commentCaMarche.moteur.surTitre') }}</p>
            <h3 class="titre-large mt-3 text-2xl md:text-3xl">{{ t('commentCaMarche.moteur.titre') }}</h3>
          </div>
          <ul class="grid gap-3 sm:grid-cols-2">
            <li
              v-for="p in POINTS_MOTEUR"
              :key="p"
              class="flex gap-3 rounded-xl bg-white/5 border border-white/10 p-4 text-sm leading-relaxed text-white/85"
            >
              <i class="pi pi-check-circle text-feuille mt-0.5" aria-hidden="true" />
              <span>{{ p }}</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="flex justify-center py-3 text-feuille" aria-hidden="true">
        <i class="pi pi-arrow-down text-xl" />
      </div>

      <!-- 3. Le resultat -->
      <div
        data-revele
        data-resultat
        class="rounded-2xl border border-trait bg-brume p-6 md:p-8 grid gap-6 lg:grid-cols-[minmax(0,22rem)_1fr] lg:items-center"
      >
        <div>
          <p class="sur-titre text-primary">{{ t('commentCaMarche.resultat.surTitre') }}</p>
          <h3 class="titre-large mt-3 text-2xl md:text-3xl text-foret">{{ t('commentCaMarche.resultat.titre') }}</h3>
          <p class="mt-2 text-sm text-encre-2 leading-relaxed">{{ t('commentCaMarche.resultat.texte') }}</p>
          <NuxtLink
            :to="localePath('/outil')"
            class="mt-6 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-bold text-white hover:bg-primary-700 transition-colors"
          >
            {{ t('commentCaMarche.cta') }}
            <i class="pi pi-arrow-right text-xs" aria-hidden="true" />
          </NuxtLink>
        </div>

        <ol class="space-y-2.5" :aria-label="t('commentCaMarche.resultat.aria')">
          <li
            v-for="(o, i) in OPTIONS"
            :key="i"
            class="grid grid-cols-[2.75rem_1fr] items-center gap-3 rounded-xl bg-white border p-2.5"
            :class="i === 0 ? 'border-primary/40' : 'border-trait'"
          >
            <span class="titre-large text-xl text-foret tabular-nums text-center">{{ o.note }}</span>
            <ol data-bande class="grid grid-cols-4 gap-1" :aria-label="t('commentCaMarche.resultat.option', { n: i + 1, note: o.note })">
              <li
                v-for="([id, duree], j) in o.blocs"
                :key="j"
                class="relative h-10 sm:h-8 rounded px-1.5 flex items-center overflow-hidden"
                :style="{ gridColumn: `span ${duree}`, background: COULEURS_CULTURES[id]?.fond, color: COULEURS_CULTURES[id]?.texte }"
              >
                <span aria-hidden="true" class="billons absolute inset-0" />
                <span class="relative text-[0.62rem] sm:text-[0.68rem] font-semibold leading-tight sm:truncate">{{ t(`cultures.${id}`) }}</span>
              </li>
            </ol>
          </li>
        </ol>
      </div>
    </div>
  </section>
</template>

<style scoped>
[data-flux] path {
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
}
.billons {
  opacity: 0.2;
  background: repeating-linear-gradient(90deg, transparent 0 8px, rgba(0, 0, 0, 0.55) 8px 9px);
}
.billons-deco {
  background: repeating-linear-gradient(115deg, transparent 0 40px, #ffffff 40px 41px);
}
</style>