<script setup lang="ts">
const COLONNES = [
  { an: 'An 1', saison: 'saison 1', court: 'S1' },
  { an: 'An 1', saison: 'saison 2', court: 'S2' },
  { seche: true },
  { an: 'An 2', saison: 'saison 1', court: 'S1' },
  { an: 'An 2', saison: 'saison 2', court: 'S2' },
  { seche: true },
] as const
</script>

<template>
  <div class="grid grid-cols-[1fr_1fr_0.45fr_1fr_1fr_0.45fr] gap-1 text-[11px] sm:text-xs text-encre-2" aria-hidden="true">
    <div v-for="(c, i) in COLONNES" :key="i" class="border-l border-trait pl-1.5 leading-tight">
      <template v-if="'seche' in c">
        <span class="hidden sm:inline">Saison sèche</span>
        <span class="sm:hidden">Sèche</span>
      </template>
      <template v-else>
        <span class="font-semibold text-encre">{{ c.an }}</span>
        <span class="hidden sm:inline">, {{ c.saison }}</span>
        <span class="sm:hidden"> {{ c.court }}</span>
      </template>
    </div>
  </div>
</template>