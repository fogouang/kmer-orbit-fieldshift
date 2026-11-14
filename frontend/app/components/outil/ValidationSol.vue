<script setup lang="ts">
// Comparaison satellite / station IRAD (si la zone a une station)
const { t, locale } = useI18n()
const o = useOutil()
const v = computed(() => o.validation.value)

const nombre = (x: number, d = 2) =>
  x.toLocaleString(locale.value === 'en' ? 'en-US' : 'fr-FR', { minimumFractionDigits: d, maximumFractionDigits: d })
const pct = (x: number | null | undefined) => {
  if (x == null) return 'n.d.'
  const r = Math.round(x)
  const signe = r > 0 ? '+' : r < 0 ? '−' : ''
  return `${signe}${Math.abs(r)}${locale.value === 'en' ? '' : ' '}%`
}
</script>

<template>
  <section v-if="v" class="fond-sombre rounded-2xl bg-foret text-white p-5 md:p-6">
    <h2 class="titre-large text-2xl">{{ t('outil.validation.titre') }}</h2>
    <p class="mt-1 text-sm text-white/75 mb-5 max-w-3xl">{{ t('outil.validation.intro', { periode: v.periode_pluie }) }}</p>
    <dl class="grid gap-3 sm:grid-cols-3">
      <div class="rounded-xl bg-white text-foret p-4">
        <dt class="text-sm text-encre-2">{{ t('outil.validation.imerg') }}</dt>
        <dd class="text-3xl titre-large tabular-nums">{{ nombre(v.pluie_mensuelle.imerg.correlation) }}</dd>
        <dd class="text-sm text-encre-2">
          {{ t('outil.validation.detail', { biais: pct(v.pluie_mensuelle.imerg.biais_pct), mois: v.pluie_mensuelle.imerg.nb_mois }) }}
        </dd>
      </div>
      <div class="rounded-xl bg-white/5 border border-white/15 p-4">
        <dt class="text-sm text-white/70">{{ t('outil.validation.power') }}</dt>
        <dd class="text-3xl titre-large tabular-nums">{{ nombre(v.pluie_mensuelle.power.correlation) }}</dd>
        <dd class="text-sm text-white/70">
          {{ t('outil.validation.detail', { biais: pct(v.pluie_mensuelle.power.biais_pct), mois: v.pluie_mensuelle.power.nb_mois }) }}
        </dd>
      </div>
      <div class="rounded-xl bg-white/5 border border-white/15 p-4">
        <dt class="text-sm text-white/70">{{ t('outil.validation.annuelle') }}</dt>
        <dd class="text-3xl titre-large tabular-nums">{{ Math.round(v.pluie_annuelle.station_moyenne_mm) }} mm</dd>
        <dd class="text-sm text-white/70">
          {{ t('outil.validation.annuelleDetail', { imerg: Math.round(v.pluie_annuelle.imerg_moyenne_mm) }) }}
        </dd>
      </div>
    </dl>
    <p class="text-xs text-white/60 mt-4">
      {{ t('outil.validation.ecartes', { pluie: v.mois_signales.pluie.length, temp: v.mois_signales.temperature.length }) }}
    </p>
  </section>
</template>