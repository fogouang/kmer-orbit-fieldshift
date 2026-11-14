<script setup lang="ts">
// Une rotation proposee : note, bande des cultures, 3 notes, raisons et conseils
import type { Rotation } from '~/composables/useFieldShiftApi'
import { raisonPositive } from '~/utils/cultures'

const props = defineProps<{ rotation: Rotation; meilleure?: boolean }>()
const { t } = useI18n()

const ouvert = ref(false)
const positives = computed(() => props.rotation.raisons.filter(raisonPositive))
const vigilances = computed(() => props.rotation.raisons.filter((r) => !raisonPositive(r)))
</script>

<template>
  <article
    class="rounded-2xl bg-white border p-4 md:p-5"
    :class="meilleure ? 'border-primary/50 ring-1 ring-primary/20' : 'border-trait'"
    :aria-label="t('outil.rotations.option', { n: rotation.rang, note: Math.round(rotation.note) })"
  >
    <div class="grid gap-4 md:grid-cols-[8.5rem_1fr] md:items-center">
      <!-- Note globale -->
      <div class="flex md:flex-col items-baseline md:items-start gap-x-3">
        <span class="text-sm text-encre-2">{{ t('outil.rotations.optionCourt', { n: rotation.rang }) }}</span>
        <span class="titre-large text-4xl leading-none text-foret tabular-nums">
          {{ Math.round(rotation.note) }}<span class="text-base font-medium text-encre-2">/100</span>
        </span>
        <span
          v-if="meilleure"
          class="mt-1 inline-flex items-center gap-1 rounded-full bg-soleil px-2.5 py-0.5 text-xs font-bold text-foret"
        >
          <i class="pi pi-star-fill text-[0.6rem]" aria-hidden="true" />
          {{ t('outil.rotations.meilleure') }}
        </span>
      </div>

      <OutilBandeRotation :sequence="rotation.sequence" />
    </div>

    <div class="mt-5 grid gap-5 md:grid-cols-[8.5rem_1fr]">
      <div class="hidden md:block" />
      <div class="grid gap-5 lg:grid-cols-[minmax(0,18rem)_1fr]">
        <div class="space-y-1.5">
          <ScoreBar :label="t('outil.criteres.rendement.label')" :valeur="rotation.rendement" couleur="var(--color-ble)" />
          <ScoreBar :label="t('outil.criteres.eau.label')" :valeur="rotation.eau" couleur="var(--color-eau)" />
          <ScoreBar :label="t('outil.criteres.sol.label')" :valeur="rotation.sante_sol" couleur="var(--color-andosol)" />
        </div>

        <div class="text-sm">
          <button
            type="button"
            class="lg:hidden mb-2 text-primary font-semibold"
            :aria-expanded="ouvert"
            @click="ouvert = !ouvert"
          >
            {{ ouvert ? t('outil.rotations.masquer') : t('outil.rotations.voir', { n: rotation.raisons.length }) }}
          </button>
          <div :class="ouvert ? 'block' : 'hidden lg:block'" class="space-y-3">
            <ul v-if="positives.length" class="space-y-1.5">
              <li v-for="r in positives" :key="r" class="flex gap-2 leading-snug">
                <i class="pi pi-check-circle mt-0.5 text-sm text-primary" aria-hidden="true" />
                <span><span class="sr-only">{{ t('outil.rotations.pointFort') }} </span>{{ r }}</span>
              </li>
            </ul>
            <ul v-if="vigilances.length" class="space-y-1.5">
              <li v-for="r in vigilances" :key="r" class="flex gap-2 leading-snug text-encre-2">
                <i class="pi pi-exclamation-circle mt-0.5 text-sm text-ble" aria-hidden="true" />
                <span><span class="sr-only">{{ t('outil.rotations.vigilance') }} </span>{{ r }}</span>
              </li>
            </ul>
            <p v-if="!rotation.raisons.length" class="text-encre-2">{{ t('outil.rotations.aucune') }}</p>
          </div>

          <details v-if="rotation.conseils?.length" class="mt-3 rounded-xl bg-brume px-3.5 py-2.5">
            <summary class="cursor-pointer font-semibold text-primary">
              {{ t('outil.rotations.conseils', { n: rotation.conseils.length }) }}
            </summary>
            <ul class="mt-2 space-y-1.5 list-disc pl-5 marker:text-primary">
              <li v-for="c in rotation.conseils" :key="c" class="leading-snug">{{ c }}</li>
            </ul>
          </details>
        </div>
      </div>
    </div>
  </article>
</template>