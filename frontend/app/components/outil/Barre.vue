<script setup lang="ts">
// Barre du haut de l'outil : logo (retour accueil), bascule de langue
const { t } = useI18n()
const localePath = useLocalePath()
</script>

<template>
  <header class="fond-sombre bg-foret text-white">
    <div class="mx-auto max-w-7xl px-4 md:px-6 h-16 flex items-center justify-between gap-4">
      <NuxtLink :to="localePath('/')" class="flex items-center gap-2.5" :aria-label="t('nav.accueil')">
        <span class="logo-marque" aria-hidden="true"><span /><span /><span /></span>
        <span class="titre-large text-lg">Field Shift</span>
      </NuxtLink>
      <div class="flex items-center gap-3">
        <span class="hidden md:inline text-sm text-white/65">{{ t('nav.equipe') }}</span>
        <LangSwitch sombre />
      </div>
    </div>
  </header>
</template>

<style scoped>
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