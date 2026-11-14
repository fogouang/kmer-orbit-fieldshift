<script setup lang="ts">
import type { Climat } from '~/composables/useFieldShiftApi'
import { fr, jourEnDate, signe } from '~/utils/format'

const props = defineProps<{ climat: Climat }>()

interface Chiffre {
  icone: string
  valeur: string
  texte: string
  source: string
}

// Les trois chiffres sont calcules a partir des donnees, jamais ecrits en dur
const chiffres = computed(() => {
  const liste: Chiffre[] = []
  const c = props.climat

  const a = c.pluie_mensuelle.reduce((s, x) => s + x.periode_a_mm, 0)
  const b = c.pluie_mensuelle.reduce((s, x) => s + x.periode_b_mm, 0)
  if (a > 0) {
    liste.push({
      icone: 'pi-cloud',
      valeur: `${signe(((b - a) / a) * 100)} %`,
      texte: `de pluie par an entre ${c.periode_a} et ${c.periode_b}`,
      source: 'NASA GPM IMERG',
    })
  }

  const jours = c.debut_saison.map((d) => d.jour_imerg).filter((j): j is number => j != null)
  if (jours.length > 1) {
    const min = Math.min(...jours)
    const max = Math.max(...jours)
    liste.push({
      icone: 'pi-calendar',
      valeur: `${fr(max - min)} jours`,
      texte: `d’écart pour le début des pluies selon les années, du ${jourEnDate(min)} au ${jourEnDate(max)}`,
      source: 'NASA GPM IMERG',
    })
  }

  const t = [...c.temperature_annuelle].sort((x, y) => x.annee - y.annee)
  const moitie = Math.floor(t.length / 2)
  if (moitie >= 2) {
    const moyenne = (l: typeof t) => l.reduce((s, x) => s + x.temperature_c, 0) / l.length
    const debut = t.slice(0, moitie)
    const fin = t.slice(-moitie)
    liste.push({
      icone: 'pi-sun',
      valeur: `${signe(moyenne(fin) - moyenne(debut), 1)} °C`,
      texte: `de température moyenne entre ${debut[0]?.annee}-${debut.at(-1)?.annee} et ${fin[0]?.annee}-${fin.at(-1)?.annee}`,
      source: 'NASA POWER',
    })
  }

  return liste
})
</script>

<template>
  <div class="grid gap-3 sm:grid-cols-3">
    <div v-for="ch in chiffres" :key="ch.icone" class="bg-white rounded-xl border border-trait p-4">
      <i class="pi text-encre-2" :class="ch.icone" aria-hidden="true" />
      <p class="mt-2 titre-large text-3xl leading-none tabular-nums">{{ ch.valeur }}</p>
      <p class="mt-1.5 text-sm leading-snug">{{ ch.texte }}</p>
      <p class="mt-2 text-xs text-encre-2">Source : {{ ch.source }}</p>
    </div>
  </div>
</template>