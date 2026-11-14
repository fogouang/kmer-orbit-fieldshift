<script setup lang="ts">
import type { Climat, Rotation, Sol } from '~/composables/useFieldShiftApi'
import { expliquer } from '~/utils/explications'

const props = defineProps<{ rotation: Rotation; climat: Climat | null; sol: Sol | null }>()

const e = computed(() => expliquer(props.rotation, props.climat, props.sol))

const sections = computed(() => [
  { titre: 'Pourquoi cette rotation', icone: 'pi-question-circle', items: e.value.pourquoi },
  { titre: 'Ce que disent les données', icone: 'pi-chart-line', items: e.value.donnees },
  { titre: 'Bénéfices', icone: 'pi-check-circle', items: e.value.benefices },
  { titre: 'Ce qu’on ne sait pas encore', icone: 'pi-info-circle', items: e.value.inconnu },
  { titre: 'À vérifier avec un agronome', icone: 'pi-user', items: e.value.agronome },
])
</script>

<template>
  <div class="divide-y divide-trait border-t border-trait">
    <details v-for="s in sections" :key="s.titre" class="group">
      <summary class="flex items-center gap-2.5 py-2.5 cursor-pointer list-none text-sm font-semibold rounded-md">
        <i class="pi text-primary" :class="s.icone" aria-hidden="true" />
        <span class="flex-1">{{ s.titre }}</span>
        <i class="pi pi-chevron-down text-xs text-encre-2 transition-transform group-open:rotate-180" aria-hidden="true" />
      </summary>
      <ul class="pb-3 pl-7 space-y-1.5 text-sm leading-snug list-disc marker:text-encre-2">
        <li v-for="item in s.items" :key="item">{{ item }}</li>
      </ul>
    </details>
  </div>
</template>