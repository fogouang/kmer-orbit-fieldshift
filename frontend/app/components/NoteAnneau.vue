<script setup lang="ts">
const props = defineProps<{ note: number; reference?: boolean }>()

const RAYON = 30
const CIRCONFERENCE = 2 * Math.PI * RAYON

const valeur = computed(() => Math.round(Math.max(0, Math.min(100, props.note))))
const trait = computed(() => `${(valeur.value / 100) * CIRCONFERENCE} ${CIRCONFERENCE}`)
</script>

<template>
  <div class="relative grid size-19 shrink-0 place-items-center" role="img" :aria-label="`Note ${valeur} sur 100`">
    <svg viewBox="0 0 72 72" class="absolute inset-0 -rotate-90" aria-hidden="true">
      <circle cx="36" cy="36" :r="RAYON" fill="none" stroke="currentColor" stroke-width="6" class="text-brume" />
      <circle
        cx="36"
        cy="36"
        :r="RAYON"
        fill="none"
        stroke="currentColor"
        stroke-width="6"
        stroke-linecap="round"
        :stroke-dasharray="trait"
        :class="reference ? 'text-encre-2' : 'text-primary'"
      />
    </svg>
    <div class="relative flex flex-col items-center leading-none" aria-hidden="true">
      <span class="titre-large text-2xl tabular-nums">{{ valeur }}</span>
      <span class="mt-0.5 text-[10px] text-encre-2">sur 100</span>
    </div>
  </div>
</template>