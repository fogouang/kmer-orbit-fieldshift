<script setup lang="ts">
import { COULEURS_CULTURES } from '~/utils/cultures'

defineEmits<{ demo: [] }>()

const SOURCES = ['NASA GPM IMERG', 'NASA POWER', 'ISRIC SoilGrids']
const COULEURS = Object.values(COULEURS_CULTURES).map((c) => c.fond)

// Courbes de niveau stylisees : les terrasses des hautes terres de l'Ouest
const COURBES = Array.from({ length: 10 }, (_, i) => {
  const y = 20 + i * 22
  return `M -20 ${y + 10} C 120 ${y - 12}, 220 ${y + 40}, 340 ${y + 8} S 520 ${y - 20}, 640 ${y + 18}`
})
</script>

<template>
  <header class="entete-sombre relative overflow-hidden bg-primary-900 text-white">
    <svg
      class="absolute inset-y-0 right-0 h-full w-full md:w-2/3 text-primary-300 opacity-30 mask-[linear-gradient(to_left,black_40%,transparent)]"
      viewBox="0 0 600 240"
      preserveAspectRatio="xMaxYMid slice"
      aria-hidden="true"
    >
      <path v-for="(d, i) in COURBES" :key="i" :d="d" fill="none" stroke="currentColor" stroke-width="1" />
    </svg>

    <div
      class="relative mx-auto max-w-7xl px-4 md:px-6 py-7 md:py-10 flex flex-col md:flex-row md:items-end md:justify-between gap-6"
    >
      <div class="max-w-2xl">
        <p class="text-xs font-semibold text-primary-200">Équipe Kmer Orbit, NASA Space Apps 2026</p>
        <h1 class="titre-large text-4xl md:text-5xl mt-1">Field Shift</h1>
        <p class="mt-2 text-lg text-white/85 leading-snug">
          Comparez des rotations de cultures adaptées au climat et au sol de votre parcelle
        </p>
        <div class="mt-4 flex flex-wrap items-center gap-2">
          <span class="text-xs text-white/70">Données :</span>
          <ul class="flex flex-wrap gap-2" aria-label="Sources des données">
            <li v-for="s in SOURCES" :key="s" class="rounded-full border border-white/25 px-3 py-1 text-xs">
              {{ s }}
            </li>
          </ul>
        </div>
      </div>

      <button
        type="button"
        class="self-start md:self-auto inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2.5 font-semibold text-primary-800 transition-colors hover:bg-primary-50"
        @click="$emit('demo')"
      >
        <i class="pi pi-play text-sm" aria-hidden="true" />
        Démo Dschang
      </button>
    </div>
  </header>
</template>