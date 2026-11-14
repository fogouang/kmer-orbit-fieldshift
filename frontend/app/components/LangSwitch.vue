<script setup lang="ts">
// Bascule FR / EN : garde la page courante, change seulement la langue
const props = defineProps<{ sombre?: boolean }>()
const { locale, locales, t } = useI18n()
const switchLocalePath = useSwitchLocalePath()
</script>

<template>
  <nav
    class="inline-flex rounded-full border p-0.5 text-xs font-semibold"
    :class="props.sombre ? 'border-white/30' : 'border-trait bg-white'"
    :aria-label="t('langue.choisir')"
  >
    <NuxtLink
      v-for="l in locales"
      :key="l.code"
      :to="switchLocalePath(l.code)"
      :lang="l.language"
      :aria-label="l.name"
      :aria-current="l.code === locale ? 'true' : undefined"
      class="rounded-full px-2.5 py-1 uppercase transition-colors"
      :class="
        l.code === locale
          ? props.sombre ? 'bg-white text-foret' : 'bg-primary text-white'
          : props.sombre ? 'text-white/75 hover:text-white' : 'text-encre-2 hover:text-encre'
      "
    >
      {{ l.code }}
    </NuxtLink>
  </nav>
</template>