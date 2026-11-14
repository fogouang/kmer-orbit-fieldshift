<script setup lang="ts">
// Une rotation : note, bande des cultures, 3 notes, raisons et conseils.
// Sert aussi pour la rotation habituelle de l'agriculteur (actuelle), affichee comme point de comparaison.
import type { Rotation } from '~/composables/useFieldShiftApi'
import { raisonPositive } from '~/utils/cultures'

const props = defineProps<{
  rotation: Rotation
  meilleure?: boolean
  actuelle?: boolean
  reference?: number | null // note de la rotation habituelle, pour afficher l'ecart
}>()
const { t } = useI18n()

const ouvert = ref(false)
const regles = computed(() => props.rotation.regles_non_respectees ?? [])
const positives = computed(() => props.rotation.raisons.filter(raisonPositive))
const vigilances = computed(() => props.rotation.raisons.filter((r) => !raisonPositive(r)))
const nbPoints = computed(() => props.rotation.raisons.length + regles.value.length)

const ecart = computed(() =>
  props.reference == null ? null : Math.round(props.rotation.note) - Math.round(props.reference),
)
const texteEcart = computed(() => {
  if (ecart.value == null) return ''
  if (ecart.value > 0) return t('outil.rotations.ecartPlus', ecart.value)
  if (ecart.value < 0) return t('outil.rotations.ecartMoins', -ecart.value)
  return t('outil.rotations.ecartEgal')
})

const aria = computed(() =>
  props.actuelle
    ? t('outil.rotations.votreRotationAria', { note: Math.round(props.rotation.note) })
    : t('outil.rotations.option', { n: props.rotation.rang, note: Math.round(props.rotation.note) }),
)
</script>

<template>
  <article
    class="rounded-2xl border p-4 md:p-5"
    :class="[
      actuelle ? 'bg-brume border-dashed border-encre-2/40' : 'bg-white',
      !actuelle && meilleure ? 'border-primary/50 ring-1 ring-primary/20' : '',
      !actuelle && !meilleure ? 'border-trait' : '',
    ]"
    :aria-label="aria"
  >
    <div class="grid gap-4 md:grid-cols-[8.5rem_1fr] md:items-center">
      <!-- Note globale -->
      <div class="flex md:flex-col items-baseline md:items-start gap-x-3">
        <span class="text-sm" :class="actuelle ? 'font-semibold text-foret' : 'text-encre-2'">
          {{ actuelle ? t('outil.rotations.votreRotation') : t('outil.rotations.optionCourt', { n: rotation.rang }) }}
        </span>
        <span class="titre-large text-4xl leading-none text-foret tabular-nums">
          {{ Math.round(rotation.note) }}<span class="text-base font-medium text-encre-2">/100</span>
        </span>
        <span
          v-if="meilleure && !actuelle"
          class="mt-1 inline-flex items-center gap-1 rounded-full bg-soleil px-2.5 py-0.5 text-xs font-bold text-foret"
        >
          <i class="pi pi-star-fill text-[0.6rem]" aria-hidden="true" />
          {{ t('outil.rotations.meilleure') }}
        </span>
        <span
          v-if="ecart != null"
          class="mt-1 text-xs font-semibold leading-tight"
          :class="ecart > 0 ? 'text-primary' : 'text-encre-2'"
        >
          {{ texteEcart }}
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
            {{ ouvert ? t('outil.rotations.masquer') : t('outil.rotations.voir', { n: nbPoints }) }}
          </button>
          <div :class="ouvert ? 'block' : 'hidden lg:block'" class="space-y-3">
            <!-- Regles de l'IRAD non respectees (seulement possible pour la rotation habituelle) -->
            <ul v-if="regles.length" class="space-y-1.5">
              <li v-for="r in regles" :key="r" class="flex gap-2 leading-snug font-medium text-red-800">
                <i class="pi pi-times-circle mt-0.5 text-sm" aria-hidden="true" />
                <span><span class="sr-only">{{ t('outil.rotations.regleIrad') }} </span>{{ r }}</span>
              </li>
            </ul>
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
            <p v-if="!nbPoints" class="text-encre-2">{{ t('outil.rotations.aucune') }}</p>
          </div>

          <details v-if="rotation.conseils?.length" class="mt-3 rounded-xl px-3.5 py-2.5" :class="actuelle ? 'bg-white' : 'bg-brume'">
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