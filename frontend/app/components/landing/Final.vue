<script setup lang="ts">
const { t } = useI18n()
const localePath = useLocalePath()
const racine = ref<HTMLElement | null>(null)
useRevele(racine)

// Membres de l'equipe Kmer Orbit : ajouter les autres membres ici (nom, role)
const EQUIPE = [{ nom: 'Fogouang-Nangna Loique', role: 'roleDev' }]

// Sources de donnees citees en bas de page
const SOURCES = [
  { nom: 'NASA GPM IMERG', url: 'https://gpm.nasa.gov/data/imerg' },
  { nom: 'NASA POWER', url: 'https://power.larc.nasa.gov' },
  { nom: 'ISRIC SoilGrids', url: 'https://soilgrids.org' },
  { nom: 'IRAD', url: 'https://www.irad-cameroon.org' },
]

const initiales = (nom: string) =>
  nom
    .split(/[\s-]+/)
    .slice(0, 2)
    .map((m) => m.charAt(0))
    .join('')
const annee = new Date().getFullYear()
</script>

<template>
  <section ref="racine" class="fond-sombre relative overflow-hidden bg-foret text-white">
    <span aria-hidden="true" class="billons-deco absolute inset-0 opacity-[0.05]" />

    <!-- Appel a l'action + equipe -->
    <div class="relative mx-auto max-w-7xl px-4 md:px-6 py-20 md:py-28 grid gap-12 lg:grid-cols-[1.2fr_1fr] lg:items-center">
      <div>
        <p data-revele class="sur-titre text-soleil">{{ t('final.surTitre') }}</p>
        <h2 data-revele class="titre-large mt-4 text-3xl sm:text-4xl xl:text-5xl leading-tight">
          {{ t('final.titre') }}
        </h2>
        <p data-revele class="mt-5 text-lg text-white/80 leading-relaxed max-w-xl">{{ t('final.texte') }}</p>
        <div data-revele class="mt-8 flex flex-wrap gap-3">
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

      <div data-revele class="rounded-2xl bg-white/5 border border-white/15 p-6 md:p-7">
        <p class="text-xs uppercase tracking-[0.14em] text-white/60">{{ t('final.equipe.surTitre') }}</p>
        <p class="titre-large mt-2 text-3xl">Kmer Orbit</p>
        <p class="mt-1 text-sm text-white/75">{{ t('final.equipe.evenement') }}</p>
        <ul class="mt-5 space-y-3">
          <li v-for="m in EQUIPE" :key="m.nom" class="flex items-center gap-3">
            <span class="grid size-10 place-items-center rounded-full bg-feuille text-foret text-sm font-bold" aria-hidden="true">
              {{ initiales(m.nom) }}
            </span>
            <span class="text-sm">
              <span class="font-semibold block">{{ m.nom }}</span>
              <span class="text-white/65">{{ t(`final.equipe.${m.role}`) }}</span>
            </span>
          </li>
        </ul>
        <p class="mt-5 flex gap-2 border-t border-white/15 pt-4 text-sm text-white/75">
          <i class="pi pi-heart text-soleil mt-0.5" aria-hidden="true" />
          {{ t('final.equipe.merci') }}
        </p>
      </div>
    </div>

    <!-- Bas de page -->
    <footer class="relative border-t border-white/10 bg-foret-2">
      <div class="mx-auto max-w-7xl px-4 md:px-6 py-8 grid gap-6 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <p class="flex items-center gap-2.5">
            <span class="logo-marque" aria-hidden="true"><span /><span /><span /></span>
            <span class="titre-large text-lg">Field Shift</span>
          </p>
          <p class="mt-2 text-sm text-white/60 max-w-xl">{{ t('final.footer.avertissement') }}</p>
        </div>
        <div class="flex flex-col items-start gap-3 md:items-end">
          <LangSwitch sombre />
          <p class="text-xs text-white/60">
            {{ t('final.footer.donnees') }}
            <template v-for="(s, i) in SOURCES" :key="s.nom">
              <a :href="s.url" target="_blank" rel="noopener" class="underline decoration-white/30 underline-offset-2 hover:text-white">{{ s.nom }}</a><span v-if="i < SOURCES.length - 1"> · </span>
            </template>
          </p>
          <p class="text-xs text-white/45">© {{ annee }} Kmer Orbit · NASA Space Apps Challenge</p>
        </div>
      </div>
    </footer>
  </section>
</template>

<style scoped>
.billons-deco {
  background: repeating-linear-gradient(115deg, transparent 0 46px, #ffffff 46px 47px);
}
.logo-marque {
  display: inline-grid;
  grid-template-columns: repeat(3, 0.4rem);
  gap: 0.14rem;
  height: 1.35rem;
  transform: skewX(-12deg);
}
.logo-marque span { border-radius: 2px; }
.logo-marque span:nth-child(1) { background: var(--color-feuille); }
.logo-marque span:nth-child(2) { background: var(--color-soleil); }
.logo-marque span:nth-child(3) { background: #ffffff; }
</style>