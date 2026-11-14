<script setup lang="ts">
const model = defineModel<number>({ required: true })
defineProps<{ labelId: string }>()

const NIVEAUX = ['Peu important', 'Secondaire', 'Important', 'Très important', 'Essentiel']
const boutons = ref<HTMLButtonElement[]>([])

function choisir(n: number, focus = false) {
  model.value = n
  if (focus) nextTick(() => boutons.value[n - 1]?.focus())
}

// Fleches, Debut et Fin : comportement standard d'un groupe radio
function clavier(e: KeyboardEvent) {
  const m = model.value
  let n: number
  if (e.key === 'ArrowRight' || e.key === 'ArrowUp') n = Math.min(5, m + 1)
  else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') n = Math.max(1, m - 1)
  else if (e.key === 'Home') n = 1
  else if (e.key === 'End') n = 5
  else return
  e.preventDefault()
  choisir(n, true)
}
</script>

<template>
  <div role="radiogroup" :aria-labelledby="labelId" class="grid grid-cols-5 gap-1.5" @keydown="clavier">
    <button
      v-for="(niveau, i) in NIVEAUX"
      :key="niveau"
      :ref="(el) => { if (el) boutons[i] = el as HTMLButtonElement }"
      type="button"
      role="radio"
      :aria-checked="model === i + 1"
      :aria-label="niveau"
      :title="niveau"
      :tabindex="model === i + 1 ? 0 : -1"
      class="flex h-11 items-end justify-center rounded-lg border pb-2 transition-colors"
      :class="i + 1 <= model ? 'border-primary bg-primary' : 'border-trait bg-white hover:border-primary/50'"
      @click="choisir(i + 1)"
    >
      <!-- La tige grandit avec l'importance -->
      <span
        aria-hidden="true"
        class="w-1.5 rounded-full"
        :class="i + 1 <= model ? 'bg-white/85' : 'bg-trait'"
        :style="{ height: `${8 + i * 4}px` }"
      />
    </button>
  </div>
</template>