<script setup lang="ts">
defineProps<{ numero: number; titre: string; aide?: string; id?: string }>()
</script>

<template>
  <div class="mb-3">
    <h2 :id="id" class="flex items-center gap-2.5 font-bold text-[1.05rem] leading-tight">
      <span
        class="grid size-6 shrink-0 place-items-center rounded-full bg-primary-50 text-xs font-semibold tabular-nums text-primary-700"
        aria-hidden="true"
      >
        {{ numero }}
      </span>
      {{ titre }}
    </h2>
    <p v-if="aide" class="mt-1 pl-8.5 text-xs text-encre-2">{{ aide }}</p>
  </div>
</template>