<script setup lang="ts">
const props = defineProps<{
  label: string
  valeur: number
  couleur: string
}>()

const { t } = useI18n()

const v = computed(() => Math.round(Math.max(0, Math.min(100, props.valeur))))

// Un mot en plus de la couleur et du chiffre
const niveau = computed(() => {
  if (v.value >= 85) return t('outil.niveauxNote.tresBon')
  if (v.value >= 70) return t('outil.niveauxNote.bon')
  if (v.value >= 50) return t('outil.niveauxNote.moyen')
  return t('outil.niveauxNote.faible')
})
</script>

<template>
  <div>
    <div class="flex items-baseline justify-between gap-2">
      <span class="text-sm text-encre-2">{{ label }}</span>
      <span class="font-bold tabular-nums">{{ v }}</span>
    </div>
    <div
      class="mt-1.5 h-2 overflow-hidden rounded-full bg-brume"
      role="meter"
      :aria-label="label"
      :aria-valuenow="v"
      :aria-valuetext="t('outil.niveauxNote.surCent', { v, niveau })"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div class="h-full rounded-full" :style="{ width: `${v}%`, background: couleur }" />
    </div>
    <span class="mt-1 block text-xs text-encre-2">{{ niveau }}</span>
  </div>
</template>