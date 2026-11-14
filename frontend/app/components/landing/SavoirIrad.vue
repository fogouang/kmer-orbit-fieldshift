<script setup lang="ts">
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { COULEURS_CULTURES } from '~/utils/cultures'

gsap.registerPlugin(ScrollTrigger)

const { t } = useI18n()
const localePath = useLocalePath()

// Alternance recommandee par l'IRAD (2 tours)
const ALTERNANCE = ['legumineuse', 'cerealeTubercule', 'legumineuse', 'cerealeTubercule'] as const

// Successions interdites par l'IRAD : [culture precedente, culture suivante]
const INTERDITS = [
  { id: 'maisMais', avant: 'mais', apres: 'mais' },
  { id: 'haricotArachide', avant: 'arachide', apres: 'haricot' },
  { id: 'maniocManioc', avant: 'manioc', apres: 'manioc' },
  { id: 'pdtPdt', avant: 'pomme_de_terre', apres: 'pomme_de_terre' },
]

// Fiche IRAD Dschang (crops.json v0.3) : eau, pH, campagne conseillee
const FICHE = ['haricot', 'mais', 'manioc', 'arachide', 'pomme_de_terre'] as const
const COLONNES = ['eau', 'ph', 'campagne'] as const

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
      gsap.from('[data-alternance] > li', {
        opacity: 0,
        x: -16,
        duration: 0.5,
        stagger: 0.15,
        ease: 'power2.out',
        scrollTrigger: { trigger: '[data-alternance]', start: 'top 85%' },
      })
    })
  }, racine.value)
})

onBeforeUnmount(() => ctx?.revert())
</script>

<template>
  <section id="irad" ref="racine" class="bg-brume py-20 md:py-28">
    <div class="mx-auto max-w-7xl px-4 md:px-6">
      <!-- En-tete -->
      <div class="max-w-3xl">
        <p data-revele class="sur-titre text-primary">{{ t('irad.surTitre') }}</p>
        <h2 data-revele class="titre-large mt-4 text-3xl sm:text-4xl xl:text-5xl leading-tight text-foret">
          {{ t('irad.titre') }}
        </h2>
        <p data-revele class="mt-5 text-lg text-encre-2 leading-relaxed">{{ t('irad.intro') }}</p>
      </div>

      <div class="mt-12 grid gap-4 lg:grid-cols-2">
        <!-- La regle d'or -->
        <article data-revele class="rounded-2xl bg-white border border-trait p-6 md:p-7">
          <h3 class="text-lg font-bold text-foret">{{ t('irad.regle.titre') }}</h3>
          <p class="mt-1.5 text-sm text-encre-2 leading-relaxed">{{ t('irad.regle.texte') }}</p>
          <ol data-alternance class="mt-5 flex flex-wrap items-center gap-2" :aria-label="t('irad.regle.aria')">
            <li v-for="(a, i) in ALTERNANCE" :key="i" class="flex items-center gap-2">
              <span
                class="rounded-full px-3 py-1.5 text-sm font-semibold"
                :class="a === 'legumineuse' ? 'bg-primary-50 text-primary-700' : 'bg-soleil-pale text-foret'"
              >
                {{ t(`irad.regle.${a}`) }}
              </span>
              <i class="pi pi-arrow-right text-xs text-encre-2" aria-hidden="true" />
            </li>
            <li class="text-sm text-encre-2">…</li>
          </ol>
          <ul class="mt-6 space-y-3 border-t border-trait pt-5">
            <li v-for="n in ['delai', 'jachere', 'association']" :key="n" class="flex gap-3 text-sm leading-relaxed">
              <i class="pi pi-check-circle text-feuille mt-0.5" aria-hidden="true" />
              <span>
                <span class="font-semibold text-foret">{{ t(`irad.normes.${n}.titre`) }}</span>
                {{ t(`irad.normes.${n}.texte`) }}
              </span>
            </li>
          </ul>
        </article>

        <!-- Les successions interdites -->
        <article data-revele class="rounded-2xl bg-white border border-trait p-6 md:p-7">
          <h3 class="text-lg font-bold text-foret">{{ t('irad.jamais.titre') }}</h3>
          <p class="mt-1.5 text-sm text-encre-2 leading-relaxed">{{ t('irad.jamais.texte') }}</p>
          <ul class="mt-5 space-y-2.5">
            <li
              v-for="x in INTERDITS"
              :key="x.id"
              class="grid grid-cols-[auto_1fr] items-center gap-4 rounded-xl bg-brume p-3"
            >
              <span class="flex items-center gap-1.5" aria-hidden="true">
                <span
                  class="grid size-9 place-items-center rounded-md text-[0.6rem] font-bold uppercase"
                  :style="{ background: COULEURS_CULTURES[x.avant]?.fond, color: COULEURS_CULTURES[x.avant]?.texte }"
                >
                  {{ t(`cultures.${x.avant}`).slice(0, 3) }}
                </span>
                <i class="pi pi-arrow-right text-[0.65rem] text-encre-2" />
                <span
                  class="relative grid size-9 place-items-center rounded-md text-[0.6rem] font-bold uppercase"
                  :style="{ background: COULEURS_CULTURES[x.apres]?.fond, color: COULEURS_CULTURES[x.apres]?.texte }"
                >
                  {{ t(`cultures.${x.apres}`).slice(0, 3) }}
                  <span class="absolute -right-1.5 -top-1.5 grid size-5 place-items-center rounded-full bg-white text-[#c2413f] shadow">
                    <i class="pi pi-times text-[0.6rem]" />
                  </span>
                </span>
              </span>
              <span class="text-sm leading-snug">
                <span class="font-semibold text-foret block">{{ t(`irad.jamais.${x.id}.titre`) }}</span>
                <span class="text-encre-2">{{ t(`irad.jamais.${x.id}.consequence`) }}</span>
              </span>
            </li>
          </ul>
        </article>
      </div>

      <!-- La fiche des 5 cultures -->
      <figure data-revele class="mt-4 rounded-2xl bg-white border border-trait p-6 md:p-7">
        <figcaption class="flex flex-col md:flex-row md:items-end md:justify-between gap-1">
          <span class="text-lg font-bold text-foret">{{ t('irad.fiche.titre') }}</span>
          <span class="text-sm text-encre-2">{{ t('irad.fiche.source') }}</span>
        </figcaption>

        <!-- Ecrans moyens et + : tableau -->
        <table class="mt-5 hidden md:table w-full text-sm">
          <thead>
            <tr class="text-left text-encre-2 border-b border-trait">
              <th scope="col" class="py-2.5 pr-4 font-semibold">{{ t('irad.fiche.culture') }}</th>
              <th v-for="c in COLONNES" :key="c" scope="col" class="py-2.5 pr-4 font-semibold">
                {{ t(`irad.fiche.colonnes.${c}`) }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="id in FICHE" :key="id" class="border-b border-trait last:border-0">
              <th scope="row" class="py-3 pr-4 text-left">
                <span class="inline-flex items-center gap-2.5 font-semibold text-foret">
                  <span class="size-3 rounded-sm" :style="{ background: COULEURS_CULTURES[id]?.fond }" aria-hidden="true" />
                  {{ t(`cultures.${id}`) }}
                </span>
              </th>
              <td v-for="c in COLONNES" :key="c" class="py-3 pr-4 text-encre-2 tabular-nums">
                {{ t(`irad.fiche.cultures.${id}.${c}`) }}
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Mobile : une carte par culture -->
        <ul class="mt-5 grid gap-3 md:hidden">
          <li v-for="id in FICHE" :key="id" class="rounded-xl bg-brume p-4">
            <p class="flex items-center gap-2.5 font-semibold text-foret">
              <span class="size-3 rounded-sm" :style="{ background: COULEURS_CULTURES[id]?.fond }" aria-hidden="true" />
              {{ t(`cultures.${id}`) }}
            </p>
            <dl class="mt-2 grid gap-1 text-sm">
              <div v-for="c in COLONNES" :key="c" class="grid grid-cols-[7rem_1fr] gap-2">
                <dt class="text-encre-2">{{ t(`irad.fiche.colonnes.${c}`) }}</dt>
                <dd class="text-foret">{{ t(`irad.fiche.cultures.${id}.${c}`) }}</dd>
              </div>
            </dl>
          </li>
        </ul>
      </figure>

      <!-- Exemple concret : la parcelle de l'IRAD -->
      <article
        data-revele
        class="fond-sombre mt-4 grid overflow-hidden rounded-2xl bg-foret text-white md:grid-cols-[minmax(0,20rem)_1fr]"
      >
        <img
          src="/images/hero/hero-2.jpg"
          :alt="t('irad.exemple.photoAlt')"
          class="h-48 w-full object-cover md:h-full"
          loading="lazy"
          width="596"
          height="335"
        />
        <div class="p-6 md:p-8">
          <p class="sur-titre text-soleil">{{ t('irad.exemple.surTitre') }}</p>
          <h3 class="titre-large mt-3 text-2xl">{{ t('irad.exemple.titre') }}</h3>
          <p class="mt-3 text-white/80 leading-relaxed">{{ t('irad.exemple.texte') }}</p>
          <div class="mt-5 flex gap-3 rounded-xl bg-white/5 border border-white/10 p-4">
            <i class="pi pi-lightbulb text-soleil mt-0.5" aria-hidden="true" />
            <p class="text-sm leading-relaxed">
              <span class="font-semibold block">{{ t('irad.exemple.conseilTitre') }}</span>
              <span class="text-white/80">{{ t('irad.exemple.conseil') }}</span>
            </p>
          </div>
          <NuxtLink
            :to="localePath('/outil')"
            class="mt-6 inline-flex items-center gap-2 rounded-full bg-soleil px-5 py-3 text-sm font-bold text-foret hover:bg-white transition-colors"
          >
            {{ t('irad.exemple.cta') }}
            <i class="pi pi-arrow-right text-xs" aria-hidden="true" />
          </NuxtLink>
        </div>
      </article>
    </div>
  </section>
</template>