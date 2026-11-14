<script setup lang="ts">
// Bande de la parcelle sur 2 ans : saison 1, saison 2, saison seche, puis la meme chose pour l'an 2.
// Une culture qui reste en terre (manioc) couvre aussi la saison seche ; sinon le sol est nu.
import type { EtapeSequence } from '~/composables/useFieldShiftApi'
import { COULEURS_CULTURES } from '~/utils/cultures'

const props = defineProps<{ sequence: EtapeSequence[]; libelle?: string }>()
const { t } = useI18n()

const COLONNE: Record<string, number> = {
  'An 1|saison_1': 1,
  'An 1|saison_2': 2,
  'An 2|saison_1': 4,
  'An 2|saison_2': 5,
}

const blocs = computed(() =>
  props.sequence
    .map((e) => {
      const cols = e.periodes.map((p) => COLONNE[`${p.annee}|${p.saison}`]).filter((c): c is number => c != null)
      if (!cols.length) return null
      return {
        ...e,
        debut: Math.min(...cols),
        fin: Math.max(...cols),
        couleurs: COULEURS_CULTURES[e.culture] ?? { fond: '#7a8a80', texte: '#ffffff' },
        texteSaisons: e.periodes
          .map((p) => `${t(p.annee === 'An 1' ? 'outil.annee1' : 'outil.annee2')} ${t(`outil.saisonsCourt.${p.saison}`)}`)
          .join(', '),
      }
    })
    .filter((b): b is NonNullable<typeof b> => b !== null),
)

// Saison seche affichee comme sol nu, sauf si une culture reste en terre
const saisonsSeches = computed(() => [3, 6].filter((c) => !blocs.value.some((b) => b.debut <= c && b.fin >= c)))
</script>

<template>
  <div
    class="grid grid-cols-[1fr_1fr_0.45fr_1fr_1fr_0.45fr] gap-1"
    role="list"
    :aria-label="libelle ?? t('outil.rotations.bande')"
  >
    <div
      v-for="b in blocs"
      :key="`${b.culture}-${b.debut}`"
      role="listitem"
      class="relative h-14 sm:h-16 rounded-md px-2 flex items-end pb-1.5 overflow-hidden"
      :style="{ gridColumn: `${b.debut} / ${b.fin + 1}`, gridRow: 1, background: b.couleurs.fond, color: b.couleurs.texte }"
    >
      <span aria-hidden="true" class="billons absolute inset-0" />
      <span class="relative text-xs sm:text-sm font-semibold leading-tight">{{ t(`cultures.${b.culture}`) }}</span>
      <span class="sr-only">, {{ b.texteSaisons }}</span>
    </div>

    <div
      v-for="c in saisonsSeches"
      :key="`sec-${c}`"
      class="sol-nu h-14 sm:h-16 rounded-md"
      :style="{ gridColumn: c, gridRow: 1 }"
      :title="t('outil.rotations.solNu')"
      aria-hidden="true"
    />
  </div>
</template>

<style scoped>
.billons {
  opacity: 0.2;
  background: repeating-linear-gradient(90deg, transparent 0 10px, rgba(0, 0, 0, 0.55) 10px 11px);
}
/* Saison seche : terre nue (andosol), en hachures */
.sol-nu {
  background: repeating-linear-gradient(135deg, #e8ddd2 0 6px, #f3ece4 6px 12px);
  border: 1px dashed #c9b7a5;
}
</style>