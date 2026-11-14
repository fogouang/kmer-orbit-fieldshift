<script setup lang="ts">
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const { t, locale } = useI18n()
// En anglais, pas d'espace avant % ; en francais, une espace
const sep = computed(() => (locale.value === 'en' ? '' : ' '))

// Chiffres issus de nos analyses (GPM IMERG 2005-2024, NASA POWER) : voir data/processed/
const CHIFFRES = [
  { id: 'pluie', valeur: 12, prefixe: '−', suffixe: '%', icone: 'pi-cloud' },
  { id: 'debut', valeur: 55, prefixe: '', suffixe: '', icone: 'pi-calendar' },
  { id: 'chaleur', valeur: 1, prefixe: '+', suffixe: ' °C', icone: 'pi-sun' },
]

// Mois ou la pluie a le plus baisse, et leur role dans le calendrier agricole
const MOIS_TOUCHES = [
  { mois: 4, baisse: 25, role: 'semis1' },
  { mois: 8, baisse: 27, role: 'semis2' },
  { mois: 11, baisse: 30, role: 'fin2' },
]
const touche = (m: number) => MOIS_TOUCHES.find((x) => x.mois === m)

const racine = ref<HTMLElement | null>(null)
let ctx: gsap.Context | null = null

onMounted(async () => {
  await nextTick()
  if (!racine.value) return
  ctx = gsap.context(() => {
    const mm = gsap.matchMedia()
    mm.add('(prefers-reduced-motion: no-preference)', () => {
      const declencheur = { trigger: racine.value, start: 'top 75%' }
      gsap.from('[data-revele]', { opacity: 0, y: 30, duration: 0.8, stagger: 0.12, ease: 'power3.out', scrollTrigger: declencheur })

      // Les chiffres comptent de 0 a leur valeur
      gsap.utils.toArray<HTMLElement>('[data-compteur]').forEach((el) => {
        const fin = Number(el.dataset.compteur)
        const objet = { v: 0 }
        gsap.to(objet, {
          v: fin,
          duration: 1.6,
          ease: 'power2.out',
          scrollTrigger: { trigger: el, start: 'top 85%' },
          onUpdate: () => (el.textContent = String(Math.round(objet.v))),
        })
      })

      // Les saisons se dessinent sur la frise, puis les mois touches apparaissent
      gsap.from('[data-saison]', {
        scaleX: 0,
        transformOrigin: 'left',
        duration: 1,
        stagger: 0.2,
        ease: 'power2.inOut',
        scrollTrigger: { trigger: '[data-frise]', start: 'top 90%' },
      })
      gsap.from('[data-mois-touche]', {
        opacity: 0,
        y: -12,
        duration: 0.6,
        stagger: 0.15,
        delay: 0.6,
        ease: 'back.out(2)',
        scrollTrigger: { trigger: '[data-frise]', start: 'top 90%' },
      })
    })
  }, racine.value)
})

onBeforeUnmount(() => ctx?.revert())
</script>

<template>
  <section id="probleme" ref="racine" class="bg-brume py-20 md:py-28">
    <div class="mx-auto max-w-7xl px-4 md:px-6">
      <!-- En-tete -->
      <div class="max-w-3xl">
        <p data-revele class="sur-titre text-primary">{{ t('probleme.surTitre') }}</p>
        <h2 data-revele class="titre-large mt-4 text-3xl sm:text-4xl xl:text-5xl leading-tight text-foret">
          {{ t('probleme.titre') }}
        </h2>
        <p data-revele class="mt-5 text-lg text-encre-2 leading-relaxed">{{ t('probleme.intro') }}</p>
      </div>

      <!-- 3 chiffres -->
      <ul class="mt-12 grid gap-4 md:grid-cols-3">
        <li
          v-for="c in CHIFFRES"
          :key="c.id"
          data-revele
          class="relative overflow-hidden rounded-2xl bg-white border border-trait p-6 md:p-7"
        >
          <span class="grid size-11 place-items-center rounded-full bg-primary-50 text-primary" aria-hidden="true">
            <i class="pi text-lg" :class="c.icone" />
          </span>
          <p class="mt-5 titre-large text-5xl md:text-6xl text-foret tabular-nums leading-none">
            {{ c.prefixe }}<span :data-compteur="c.valeur">{{ c.valeur }}</span>{{ c.suffixe === '%' ? sep + '%' : c.suffixe }}
          </p>
          <p class="mt-3 font-semibold text-foret">{{ t(`probleme.chiffres.${c.id}.titre`) }}</p>
          <p class="mt-1.5 text-sm text-encre-2 leading-relaxed">{{ t(`probleme.chiffres.${c.id}.texte`) }}</p>
          <p class="mt-4 text-xs text-encre-2/80">{{ t(`probleme.chiffres.${c.id}.source`) }}</p>
          <!-- Liseré de couleur en bas de carte -->
          <span aria-hidden="true" class="absolute inset-x-0 bottom-0 h-1 bg-feuille" />
        </li>
      </ul>

      <!-- Frise : le calendrier agricole touche aux pires moments -->
      <div data-revele class="mt-6 rounded-2xl bg-foret text-white p-6 md:p-8 fond-sombre">
        <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-2">
          <h3 class="titre-large text-xl md:text-2xl">{{ t('probleme.frise.titre') }}</h3>
          <p class="text-sm text-white/65">{{ t('probleme.frise.source') }}</p>
        </div>

        <div data-frise class="mt-8">
          <!-- Saisons de culture -->
          <div class="relative grid grid-cols-12 gap-1 h-9" aria-hidden="true">
            <div data-saison class="col-start-3 col-span-5 rounded-md bg-feuille/85 flex items-center px-2 text-xs font-semibold text-foret">
              <span class="sm:hidden">S1</span>
              <span class="hidden sm:inline truncate">{{ t('probleme.frise.saison1') }}</span>
            </div>
            <div data-saison class="col-start-8 col-span-4 rounded-md bg-soleil flex items-center px-2 text-xs font-semibold text-foret">
              <span class="sm:hidden">S2</span>
              <span class="hidden sm:inline truncate">{{ t('probleme.frise.saison2') }}</span>
            </div>
          </div>

          <!-- Les 12 mois -->
          <ol class="mt-2 grid grid-cols-12 gap-1 text-center" :aria-label="t('probleme.frise.aria')">
            <li v-for="m in 12" :key="m" class="relative">
              <span
                class="block rounded-md py-2 text-[0.65rem] sm:text-xs font-semibold uppercase"
                :class="touche(m) ? 'bg-white text-foret' : 'text-white/55'"
              >
                <span class="sm:hidden" aria-hidden="true">{{ t(`mois.${m}`).charAt(0) }}</span>
                <span class="hidden sm:inline">{{ t(`mois.${m}`) }}</span>
                <span class="sr-only sm:hidden">{{ t(`moisLong.${m}`) }}</span>
              </span>
              <span v-if="touche(m)" class="sr-only">
                : {{ t('probleme.frise.baisse', { pct: touche(m)!.baisse }) }}, {{ t(`probleme.frise.roles.${touche(m)!.role}`) }}
              </span>
              <!-- Etiquette de baisse sous le mois (ecrans moyens et +) -->
              <span
                v-if="touche(m)"
                data-mois-touche
                aria-hidden="true"
                class="absolute left-1/2 top-full mt-2 -translate-x-1/2 hidden md:block whitespace-nowrap rounded-md bg-soleil px-2 py-1 text-sm font-bold text-foret tabular-nums"
              >
                −{{ touche(m)!.baisse }}{{ sep }}%
              </span>
            </li>
          </ol>

          <!-- Legende des mois touches -->
          <ul class="mt-6 md:mt-16 grid gap-3 sm:grid-cols-3" aria-hidden="true">
            <li v-for="x in MOIS_TOUCHES" :key="x.mois" class="flex items-start gap-3 rounded-lg bg-white/5 border border-white/10 p-3">
              <span class="rounded-md bg-soleil px-2 py-1 text-sm font-bold text-foret tabular-nums whitespace-nowrap">−{{ x.baisse }}{{ sep }}%</span>
              <span class="text-sm leading-snug">
                <span class="font-semibold block">{{ t(`moisLong.${x.mois}`) }}</span>
                <span class="text-white/70">{{ t(`probleme.frise.roles.${x.role}`) }}</span>
              </span>
            </li>
          </ul>
        </div>

        <p class="mt-6 text-white/85 leading-relaxed max-w-3xl">{{ t('probleme.conclusion') }}</p>
      </div>
    </div>
  </section>
</template>