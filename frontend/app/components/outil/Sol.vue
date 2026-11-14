<script setup lang="ts">
// Le sol de la parcelle (estimation SoilGrids). Les niveaux sont recalcules ici pour etre traduits.
const { t, locale } = useI18n()
const o = useOutil()
const s = computed(() => o.sol.value)

const niveauPh = (ph: number) =>
  ph < 5 ? 'tresAcide' : ph < 5.5 ? 'acide' : ph < 6.5 ? 'legerementAcide' : ph < 7.5 ? 'neutre' : 'basique'
const niveauCarbone = (c: number) => (c < 10 ? 'faible' : c < 20 ? 'moyen' : 'eleve')
// "Limon argileux" -> "limon_argileux" (cle de traduction)
const cleTexture = (tx: string) =>
  tx.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z]+/g, '_')
const nombre = (x: number) => x.toLocaleString(locale.value === 'en' ? 'en-US' : 'fr-FR')
</script>

<template>
  <section v-if="s" class="rounded-2xl bg-white border border-trait p-5 md:p-6">
    <h2 class="titre-large text-2xl text-foret">{{ t('outil.sol.titre') }}</h2>
    <p class="mt-1 text-sm text-encre-2 mb-5">{{ t('outil.sol.intro') }}</p>
    <dl class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="rounded-xl bg-brume p-4">
        <dt class="text-sm text-encre-2">pH</dt>
        <dd class="text-2xl font-bold tabular-nums text-foret">{{ nombre(s.ph) }}</dd>
        <dd class="text-sm">{{ t(`outil.sol.ph.${niveauPh(s.ph)}`) }}</dd>
      </div>
      <div v-if="s.carbone_organique_g_kg != null" class="rounded-xl bg-brume p-4">
        <dt class="text-sm text-encre-2">{{ t('outil.sol.carbone') }}</dt>
        <dd class="text-2xl font-bold tabular-nums text-foret">{{ nombre(s.carbone_organique_g_kg) }} g/kg</dd>
        <dd class="text-sm">{{ t(`outil.sol.niveaux.${niveauCarbone(s.carbone_organique_g_kg)}`) }}</dd>
      </div>
      <div class="rounded-xl bg-brume p-4">
        <dt class="text-sm text-encre-2">{{ t('outil.sol.argile') }}</dt>
        <dd class="text-2xl font-bold tabular-nums text-foret">{{ Math.round(s.argile_pct) }} %</dd>
        <dd v-if="s.texture" class="text-sm">{{ t(`outil.sol.textures.${cleTexture(s.texture)}`, s.texture) }}</dd>
      </div>
      <div v-if="s.cec_cmol_kg != null" class="rounded-xl bg-brume p-4">
        <dt class="text-sm text-encre-2">{{ t('outil.sol.cec') }}</dt>
        <dd class="text-2xl font-bold tabular-nums text-foret">{{ nombre(s.cec_cmol_kg) }}</dd>
        <dd class="text-sm">cmol(c)/kg</dd>
      </div>
    </dl>
  </section>
</template>