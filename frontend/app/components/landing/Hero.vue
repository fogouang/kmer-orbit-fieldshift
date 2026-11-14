<script setup lang="ts">
import gsap from 'gsap'
import { SplitText } from 'gsap/SplitText'
import { COULEURS_CULTURES } from '~/utils/cultures'

gsap.registerPlugin(SplitText)

const { t } = useI18n()
const localePath = useLocalePath()

interface Slide {
  id: string
  image: string
  surTitre: string
  titre: string
  surligne: string
  texte: string
  chiffre: { valeur: string; legende: string }
}

// Textes dans i18n/locales/*.json ; photos dans public/images/hero/
const IDS = [
  { id: 'climat', image: '/images/hero/hero-1.jpg' },
  { id: 'semis', image: '/images/hero/hero-2.jpg' },
  { id: 'validation', image: '/images/hero/hero-3.jpg' },
]
const SLIDES = computed<Slide[]>(() =>
  IDS.map(({ id, image }) => ({
    id,
    image,
    surTitre: t(`hero.slides.${id}.surTitre`),
    titre: t(`hero.slides.${id}.titre`),
    surligne: t(`hero.slides.${id}.surligne`),
    texte: t(`hero.slides.${id}.texte`),
    chiffre: { valeur: t(`hero.slides.${id}.chiffre`), legende: t(`hero.slides.${id}.legende`) },
  })),
)

// Exemple reel : meilleure rotation proposee pour la parcelle de l'IRAD Dschang
const EXEMPLE = {
  note: 89,
  sequence: ['mais', 'haricot', 'pomme_de_terre', 'arachide'],
}

const DUREE_SLIDE = 7 // secondes

const actif = ref(0)
const slide = computed(() => SLIDES.value[actif.value]!)

const racine = ref<HTMLElement | null>(null)
const contenu = ref<HTMLElement | null>(null)
const barres = ref<HTMLElement[]>([])

let progression: gsap.core.Tween | null = null
let animationTexte: gsap.core.Timeline | null = null
let decoupe: SplitText | null = null
let mm: gsap.MatchMedia | null = null
let reduit = false

// Animation d'entree du texte de la slide active
function animerTexte() {
  if (!contenu.value) return
  animationTexte?.kill()
  decoupe?.revert()

  const q = gsap.utils.selector(contenu.value)
  if (reduit) {
    gsap.set(q('[data-anim]'), { opacity: 1, y: 0, x: 0 })
    return
  }

  decoupe = new SplitText(q('[data-titre]'), { type: 'words' })
  const trait = contenu.value.querySelectorAll<SVGPathElement>('[data-trait] path')

  animationTexte = gsap
    .timeline({ defaults: { ease: 'power3.out' } })
    .fromTo(q('[data-anim="sur-titre"]'), { opacity: 0, x: -24 }, { opacity: 1, x: 0, duration: 0.7 })
    .fromTo(
      decoupe.words,
      { opacity: 0, yPercent: 60, rotateX: -50 },
      { opacity: 1, yPercent: 0, rotateX: 0, duration: 0.8, stagger: 0.06 },
      '-=0.4',
    )
    .fromTo(trait, { strokeDashoffset: 320 }, { strokeDashoffset: 0, duration: 0.9, stagger: 0.15, ease: 'power2.inOut' }, '-=0.3')
    .fromTo(q('[data-anim="texte"]'), { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.7 }, '-=0.6')
    .fromTo(q('[data-anim="boutons"]'), { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.7 }, '-=0.5')
}

// Barre de progression de la slide : quand elle est pleine, on passe a la suivante
function lancerProgression() {
  progression?.kill()
  barres.value.forEach((b, i) => gsap.set(b, { scaleX: i < actif.value ? 1 : 0 }))
  const barre = barres.value[actif.value]
  if (!barre || reduit) return
  progression = gsap.to(barre, {
    scaleX: 1,
    duration: DUREE_SLIDE,
    ease: 'none',
    paused: enPause.value,
    onComplete: () => aller(actif.value + 1),
  })
}

async function aller(index: number) {
  actif.value = (index + IDS.length) % IDS.length
  await nextTick()
  animerTexte()
  lancerProgression()
}

// Lecture automatique : bouton pause (accessibilite) + pause quand le focus clavier est dans le hero
const enPause = ref(false)
function basculerLecture() {
  enPause.value = !enPause.value
  if (enPause.value) progression?.pause()
  else progression?.resume()
}
const pauseFocus = () => progression?.pause()
const repriseFocus = () => {
  if (!enPause.value) progression?.resume()
}

onMounted(async () => {
  await nextTick()
  if (!racine.value) return
  mm = gsap.matchMedia()
  mm.add({ reduit: '(prefers-reduced-motion: reduce)', normal: '(prefers-reduced-motion: no-preference)' }, (ctx) => {
    reduit = Boolean(ctx.conditions?.reduit)
    if (reduit) return
    const q = gsap.utils.selector(racine.value)
    // Entree de la carte produit et du chiffre cle
    gsap.from(q('[data-agriculteur]'), { opacity: 0, y: 60, duration: 1.2, ease: 'power3.out', delay: 0.2 })
    gsap.from(q('[data-carte]'), { opacity: 0, x: -40, duration: 1, ease: 'power3.out', delay: 0.7 })
    gsap.from(q('[data-chiffre]'), { opacity: 0, scale: 0.6, duration: 0.8, ease: 'back.out(1.7)', delay: 0.9 })
    gsap.from(q('[data-bloc]'), { scaleX: 0, transformOrigin: 'left', duration: 0.6, stagger: 0.12, ease: 'power2.out', delay: 0.8 })
    // Feuilles decoratives qui flottent
    q('[data-flotte]').forEach((el, i) => {
      gsap.to(el, { y: i % 2 ? 14 : -14, rotate: i % 2 ? 8 : -8, duration: 3 + i, ease: 'sine.inOut', yoyo: true, repeat: -1 })
    })
  })
  animerTexte()
  lancerProgression()
})

// Changement de langue : le texte change, on rejoue son animation
const { locale } = useI18n()
watch(locale, async () => {
  await nextTick()
  animerTexte()
})

onBeforeUnmount(() => {
  progression?.kill()
  animationTexte?.kill()
  decoupe?.revert()
  mm?.revert()
})
</script>

<template>
  <section
    ref="racine"
    class="fond-sombre relative isolate overflow-hidden bg-foret text-white min-h-[100svh] flex flex-col"
    :aria-roledescription="t('hero.carrousel')"
    :aria-label="t('hero.aria')"
    @focusin="pauseFocus"
    @focusout="repriseFocus"
  >
    <!-- Photos de fond : fondu + lent zoom (Ken Burns) -->
    <div class="absolute inset-0 -z-10" aria-hidden="true">
      <div
        v-for="(s, i) in SLIDES"
        :key="s.id"
        class="fond-slide absolute inset-0 bg-cover bg-center transition-opacity duration-[1400ms]"
        :class="i === actif ? 'opacity-100 actif' : 'opacity-0'"
        :style="{ backgroundImage: `url('${s.image}')` }"
      />
      <!-- Voile foret : lisibilite du texte + teinte de marque -->
      <div class="absolute inset-0 voile" />
      <!-- Billons en filigrane -->
      <div class="absolute inset-0 billons-fond opacity-[0.07]" />
    </div>

    <!-- Barre de navigation -->
    <header class="relative z-10 mx-auto w-full max-w-7xl px-4 md:px-6 pt-5 flex items-center justify-between gap-4">
      <NuxtLink :to="localePath('/')" class="flex items-center gap-2.5" :aria-label="t('nav.accueil')">
        <span class="logo-marque" aria-hidden="true">
          <span /><span /><span />
        </span>
        <span class="titre-large text-xl">Field Shift</span>
      </NuxtLink>
      <div class="flex items-center gap-3">
        <span class="hidden md:inline text-sm text-white/70">{{ t('nav.equipe') }}</span>
        <LangSwitch sombre />
        <NuxtLink
          :to="localePath('/outil')"
          class="rounded-full border border-white/30 px-4 py-2 text-sm font-semibold hover:bg-white hover:text-foret transition-colors"
        >
          {{ t('nav.essayer') }}
        </NuxtLink>
      </div>
    </header>

    <!-- Contenu -->
    <div
      class="relative z-10 mx-auto w-full max-w-7xl flex-1 px-4 md:px-6 py-12 md:py-16 grid gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-center"
    >
      <!-- Texte de la slide -->
      <div :key="actif" ref="contenu" aria-live="polite">
        <p data-anim="sur-titre" class="sur-titre text-soleil">{{ slide.surTitre }}</p>

        <h1 class="titre-large mt-5 text-4xl sm:text-5xl xl:text-6xl leading-[1.05] [perspective:600px]">
          <span data-titre>{{ slide.titre }}</span>
          {{ ' ' }}
          <span class="relative inline-block whitespace-nowrap text-soleil">
            <span data-titre>{{ slide.surligne }}</span>
            <!-- Trait de pinceau sous le mot mis en avant -->
            <svg
              data-trait
              class="absolute left-0 -bottom-[0.18em] w-full h-[0.32em] overflow-visible"
              viewBox="0 0 300 24"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <path d="M5 15 C 80 6, 170 4, 295 10" pathLength="320" />
              <path d="M45 20 C 120 14, 200 13, 268 16" pathLength="320" class="fin" />
            </svg>
          </span>
        </h1>

        <p data-anim="texte" class="mt-7 max-w-xl text-lg text-white/80 leading-relaxed">{{ slide.texte }}</p>

        <div data-anim="boutons" class="mt-9 flex flex-wrap gap-3">
          <NuxtLink
            :to="localePath('/outil')"
            class="inline-flex items-center gap-2 rounded-full bg-soleil px-6 py-3.5 font-bold text-foret hover:bg-white transition-colors"
          >
            {{ t('hero.cta') }}
            <i class="pi pi-arrow-right text-sm" aria-hidden="true" />
          </NuxtLink>
          <a
            href="#comment-ca-marche"
            class="inline-flex items-center gap-2 rounded-full border border-white/35 px-6 py-3.5 font-semibold hover:border-white hover:bg-white/10 transition-colors"
          >
            {{ t('hero.commentCaMarche') }}
          </a>
        </div>
      </div>

      <!-- Visuel : l'agriculteur et ses 5 cultures, une rotation proposee par l'outil -->
      <div class="relative mx-auto w-full max-w-md lg:max-w-none lg:self-end">
        <!-- Disque de lumiere derriere l'agriculteur -->
        <div aria-hidden="true" class="halo absolute left-1/2 bottom-6 -translate-x-1/2 aspect-square w-[85%] rounded-full" />

        <!-- Feuilles decoratives -->
        <svg data-flotte class="feuille-deco hidden md:block top-6 left-4 w-14" viewBox="0 0 64 64" aria-hidden="true">
          <path d="M8 56 C 8 24, 28 6, 58 6 C 58 36, 40 56, 8 56 Z" />
          <path d="M10 54 L 50 14" class="nervure" />
        </svg>
        <svg data-flotte class="feuille-deco hidden md:block top-1/3 right-0 w-9 rotate-90" viewBox="0 0 64 64" aria-hidden="true">
          <path d="M8 56 C 8 24, 28 6, 58 6 C 58 36, 40 56, 8 56 Z" />
          <path d="M10 54 L 50 14" class="nervure" />
        </svg>

        <img
          data-agriculteur
          src="/images/hero/agriculteur.webp"
          :alt="t('hero.agriculteurAlt')"
          class="agriculteur relative z-[1] block mx-auto w-auto max-h-[22rem] sm:max-h-[28rem] lg:max-h-[34rem] object-contain"
          width="900"
          height="1129"
        />

        <!-- Mini carte : la rotation proposee pour la parcelle de l'IRAD -->
        <div
          data-carte
          class="carte-verre relative z-[2] -mt-16 mx-auto w-[19.5rem] max-w-full rounded-2xl p-4 sm:absolute sm:mt-0 sm:left-0 sm:bottom-4 lg:-left-6"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-[0.68rem] uppercase tracking-[0.14em] text-white/65">{{ t('hero.carte.parcelle') }}</p>
              <p class="text-sm font-semibold">{{ t('hero.carte.titre') }}</p>
            </div>
            <p class="titre-large text-3xl leading-none tabular-nums">
              {{ EXEMPLE.note }}<span class="text-xs font-medium text-white/60">/100</span>
            </p>
          </div>
          <ol class="mt-3 grid grid-cols-4 gap-1" :aria-label="t('hero.carte.sequence')">
            <li
              v-for="id in EXEMPLE.sequence"
              :key="id"
              data-bloc
              class="relative h-11 rounded px-1.5 pb-1 flex items-end overflow-hidden"
              :style="{ background: COULEURS_CULTURES[id]?.fond, color: COULEURS_CULTURES[id]?.texte }"
            >
              <span aria-hidden="true" class="billons absolute inset-0" />
              <span class="relative text-[0.66rem] font-semibold leading-tight">{{ t(`cultures.${id}`) }}</span>
            </li>
          </ol>
          <p class="mt-3 flex gap-1.5 text-xs text-white/80 leading-snug">
            <i class="pi pi-check-circle text-feuille text-xs mt-0.5" aria-hidden="true" />
            {{ t('hero.carte.alternance') }}
          </p>
        </div>

        <!-- Chiffre cle de la slide -->
        <div
          data-chiffre
          class="relative z-[2] mt-3 mx-auto w-fit rounded-xl bg-soleil sm:absolute sm:mt-0 sm:right-0 sm:top-4 lg:-right-2 text-foret px-5 py-3 shadow-[0_18px_40px_-12px_rgba(0,0,0,0.45)] max-w-[15rem]"
        >
          <p :key="`${actif}-${slide.chiffre.valeur}`" class="titre-large text-3xl leading-none tabular-nums apparition">{{ slide.chiffre.valeur }}</p>
          <p class="mt-1 text-sm font-medium leading-snug">{{ slide.chiffre.legende }}</p>
        </div>
      </div>
    </div>

    <!-- Pied du hero : sources + navigation du carrousel -->
    <div class="relative z-10 mx-auto w-full max-w-7xl px-4 md:px-6 pb-6 pt-10">
      <div class="flex flex-col-reverse gap-5 md:flex-row md:items-center md:justify-between border-t border-white/15 pt-5">
        <p class="text-xs sm:text-sm text-white/60">
          {{ t('hero.sources') }}
        </p>
        <div class="flex items-center gap-4">
          <div class="flex gap-2" role="tablist" :aria-label="t('hero.choisirSlide')">
            <button
              v-for="(s, i) in SLIDES"
              :key="i"
              type="button"
              role="tab"
              :aria-selected="i === actif"
              :aria-label="t('hero.slide', { numero: i + 1, titre: s.surTitre })"
              class="relative h-1 w-12 sm:w-16 rounded-full bg-white/20 overflow-hidden"
              @click="aller(i)"
            >
              <span ref="barres" class="absolute inset-0 origin-left scale-x-0 bg-soleil" />
            </button>
          </div>
          <div class="flex gap-1.5">
            <button
              type="button"
              class="grid size-10 place-items-center rounded-full border border-white/25 hover:bg-white hover:text-foret transition-colors"
              :aria-label="enPause ? t('hero.reprendre') : t('hero.pause')"
              :aria-pressed="enPause"
              @click="basculerLecture"
            >
              <i class="pi text-sm" :class="enPause ? 'pi-play' : 'pi-pause'" aria-hidden="true" />
            </button>
            <button
              type="button"
              class="grid size-10 place-items-center rounded-full border border-white/25 hover:bg-white hover:text-foret transition-colors"
              :aria-label="t('hero.precedente')"
              @click="aller(actif - 1)"
            >
              <i class="pi pi-arrow-left text-sm" aria-hidden="true" />
            </button>
            <button
              type="button"
              class="grid size-10 place-items-center rounded-full border border-white/25 hover:bg-white hover:text-foret transition-colors"
              :aria-label="t('hero.suivante')"
              @click="aller(actif + 1)"
            >
              <i class="pi pi-arrow-right text-sm" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* Fond : la slide active zoome doucement */
.fond-slide.actif {
  animation: ken-burns 9s ease-out both;
}
@keyframes ken-burns {
  from { transform: scale(1); }
  to { transform: scale(1.12); }
}

/* Voile : foret dense a gauche (texte), plus leger a droite (photo) */
.voile {
  background:
    linear-gradient(100deg, rgba(13, 42, 31, 0.96) 0%, rgba(22, 67, 51, 0.88) 45%, rgba(22, 67, 51, 0.55) 100%),
    radial-gradient(60rem 30rem at 85% 20%, rgba(67, 170, 92, 0.25), transparent 70%);
}

/* Lignes de culture en filigrane */
.billons-fond {
  background: repeating-linear-gradient(115deg, transparent 0 46px, #ffffff 46px 47px);
}
.billons {
  opacity: 0.2;
  background: repeating-linear-gradient(90deg, transparent 0 10px, rgba(0, 0, 0, 0.55) 10px 11px);
}

/* Trait de pinceau */
[data-trait] path {
  fill: none;
  stroke: currentColor;
  stroke-width: 7;
  stroke-linecap: round;
  stroke-dasharray: 320;
}
[data-trait] path.fin {
  stroke-width: 3.5;
  opacity: 0.7;
}

/* Halo derriere l'agriculteur : soleil + feuille */
.halo {
  background:
    radial-gradient(circle at 50% 55%, rgba(248, 195, 44, 0.32), transparent 62%),
    radial-gradient(circle at 50% 50%, rgba(67, 170, 92, 0.35), transparent 70%);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

/* Le bas de la photo se fond dans le decor (pas de coupure nette) */
.agriculteur {
  -webkit-mask-image: linear-gradient(to bottom, #000 78%, transparent 100%);
  mask-image: linear-gradient(to bottom, #000 78%, transparent 100%);
  filter: drop-shadow(0 30px 40px rgba(0, 0, 0, 0.35));
}

/* Carte en verre depoli */
.carte-verre {
  background: rgba(13, 42, 31, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(14px);
  box-shadow: 0 30px 60px -20px rgba(0, 0, 0, 0.5);
}

/* Logo : trois bandes de cultures */
.logo-marque {
  display: inline-grid;
  grid-template-columns: repeat(3, 0.45rem);
  gap: 0.15rem;
  height: 1.6rem;
  transform: skewX(-12deg);
}
.logo-marque span {
  border-radius: 2px;
}
.logo-marque span:nth-child(1) { background: var(--color-feuille); }
.logo-marque span:nth-child(2) { background: var(--color-soleil); }
.logo-marque span:nth-child(3) { background: #ffffff; }

.feuille-deco {
  position: absolute;
  z-index: 1;
  fill: var(--color-feuille);
}
.feuille-deco .nervure {
  fill: none;
  stroke: var(--color-foret);
  stroke-width: 2.5;
  stroke-linecap: round;
}

.apparition {
  animation: apparition 0.6s ease-out both;
}
@keyframes apparition {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}
</style>
