<script setup lang="ts">
// Le climat de la parcelle : pluie par campagne + 2 graphiques
const { t, locale } = useI18n()
const decimal = (x: number) => x.toLocaleString(locale.value === 'en' ? 'en-US' : 'fr-FR', { maximumFractionDigits: 1, minimumFractionDigits: 1 })
const o = useOutil()
const c = computed(() => o.climat.value)
</script>

<template>
  <section v-if="c">
    <h2 class="titre-large text-2xl text-foret">{{ t('outil.climat.titre') }}</h2>
    <p class="mt-1 text-sm text-encre-2 mb-4 max-w-2xl">
      {{ t('outil.climat.intro', { debut: c.annees_reference[0], fin: c.annees_reference.at(-1) }) }}
    </p>

    <div class="grid gap-3 sm:grid-cols-2 mb-4">
      <div v-for="s in c.saisons" :key="s.saison" class="rounded-2xl bg-white border border-trait p-5">
        <h3 class="font-semibold text-foret">{{ t(`outil.saisons.${s.saison}`) }}</h3>
        <p class="mt-2 text-3xl titre-large tabular-nums text-foret">{{ Math.round(s.pluie_moyenne_mm) }} mm</p>
        <p class="text-sm text-encre-2">
          {{
            t('outil.climat.saison', {
              min: Math.round(s.pluie_min_mm),
              max: Math.round(s.pluie_max_mm),
              temp: decimal(s.temperature_c),
            })
          }}
        </p>
      </div>
    </div>

    <div class="grid gap-4 xl:grid-cols-2">
      <figure class="rounded-2xl bg-white border border-trait p-5">
        <figcaption class="mb-3">
          <span class="font-semibold block text-foret">{{ t('outil.climat.debutTitre') }}</span>
          <span class="text-sm text-encre-2">{{ t('outil.climat.debutTexte') }}</span>
        </figcaption>
        <OutilGraphiqueDebutPluies :climat="c" />
      </figure>
      <figure class="rounded-2xl bg-white border border-trait p-5">
        <figcaption class="mb-3">
          <span class="font-semibold block text-foret">{{ t('outil.climat.moisTitre') }}</span>
          <span class="text-sm text-encre-2">{{ t('outil.climat.moisTexte') }}</span>
        </figcaption>
        <OutilGraphiquePluieMensuelle :climat="c" />
      </figure>
    </div>
  </section>
</template>