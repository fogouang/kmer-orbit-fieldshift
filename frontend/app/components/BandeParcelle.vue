<script setup lang="ts">
import type { EtapeSequence } from '~/composables/useFieldShiftApi'
import { COULEURS_CULTURES } from '~/utils/cultures'

const props = defineProps<{ sequence: EtapeSequence[]; libelle?: string; delai?: number }>()

// 6 colonnes : saison 1, saison 2, saison seche, puis la meme chose pour l'an 2
const COLONNE: Record<string, number> = {
  'An 1|saison_1': 1,
  'An 1|saison_2': 2,
  'An 2|saison_1': 4,
  'An 2|saison_2': 5,
}

const blocs = computed(() =>
  props.sequence
    .map((e) => {
      const cols = e.periodes
        .map((p) => COLONNE[`${p.annee}|${p.saison}`])
        .filter((c): c is number => c != null)
      if (!cols.length) return null
      return {
        ...e,
        debut: Math.min(...cols),
        fin: Math.max(...cols),
        couleurs: COULEURS_CULTURES[e.culture] ?? { fond: '#7a8a80', texte: '#ffffff' },
        texteSaisons: e.periodes.map((p) => `${p.annee} ${p.saison.replace('_', ' ')}`).join(' et '),
      }
    })
    .filter((b): b is NonNullable<typeof b> => b !== null),
)

// Saison seche affichee seulement si aucune culture ne reste en terre (ex. manioc)
const saisonsSeches = computed(() =>
  [3, 6].filter((c) => !blocs.value.some((b) => b.debut <= c && b.fin >= c)),
)
</script>

<template>
  <div
    class="grid grid-cols-[1fr_1fr_0.45fr_1fr_1fr_0.45fr] gap-1"
    :class="{ 'bande-pousse': delai != null }"
    :style="delai != null ? { animationDelay: `${delai}ms` } : undefined"
    role="list"
    :aria-label="libelle ?? 'Cultures saison par saison'"
  >
    <div
      v-for="b in blocs"
      :key="`${b.culture}-${b.debut}`"
      role="listitem"
      class="relative h-16 rounded-md px-2 flex items-end pb-1.5 overflow-hidden"
      :style="{
        gridColumn: `${b.debut} / ${b.fin + 1}`,
        gridRow: 1,
        background: b.couleurs.fond,
        color: b.couleurs.texte,
      }"
    >
      <span aria-hidden="true" class="billons absolute inset-0" />
      <span class="relative text-xs sm:text-sm font-semibold leading-tight">{{ b.nom }}</span>
      <span class="sr-only">, {{ b.texteSaisons }}</span>
    </div>

    <div
      v-for="c in saisonsSeches"
      :key="`sec-${c}`"
      class="sol-nu h-16 rounded-md"
      :style="{ gridColumn: c, gridRow: 1 }"
      aria-hidden="true"
    />
  </div>
</template>