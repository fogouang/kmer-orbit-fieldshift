<script setup lang="ts">
// Les normes generales de l'IRAD renvoyees par l'API avec les rotations
const { t } = useI18n()
const o = useOutil()

const CLES = ['jachere', 'association', 'amendement', 'travail_du_sol', 'varietes']
const normes = computed(() => o.resultat.value?.normes_irad)
const erreurs = computed(() => {
  const e = normes.value?.erreurs_a_eviter
  return Array.isArray(e) ? e : []
})
</script>

<template>
  <section v-if="normes" class="rounded-2xl bg-white border border-trait p-5 md:p-6">
    <h2 class="titre-large text-2xl text-foret">{{ t('outil.normes.titre') }}</h2>
    <p class="mt-1 text-sm text-encre-2 mb-5 max-w-3xl">{{ t('outil.normes.intro') }}</p>
    <dl class="grid gap-4 md:grid-cols-2">
      <template v-for="cle in CLES" :key="cle">
        <div v-if="typeof normes[cle] === 'string'" class="flex gap-3">
          <i class="pi pi-check-circle text-feuille mt-1" aria-hidden="true" />
          <div>
            <dt class="font-semibold text-foret">{{ t(`outil.normes.libelles.${cle}`) }}</dt>
            <dd class="text-sm text-encre-2">{{ normes[cle] }}</dd>
          </div>
        </div>
      </template>
    </dl>
    <div v-if="erreurs.length" class="mt-5 rounded-xl bg-brume p-4">
      <h3 class="font-semibold text-foret">{{ t('outil.normes.erreurs') }}</h3>
      <ul class="mt-2 space-y-1 text-sm">
        <li v-for="e in erreurs" :key="e" class="flex gap-2">
          <i class="pi pi-times-circle text-[#c2413f] mt-0.5 text-sm" aria-hidden="true" />{{ e }}
        </li>
      </ul>
    </div>
  </section>
</template>