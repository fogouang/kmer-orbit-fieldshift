<script setup lang="ts">
// Langue de la page (<html lang>) et liens hreflang selon la langue active
const head = useLocaleHead()
useHead(() => ({
  htmlAttrs: { lang: head.value.htmlAttrs?.lang },
  link: [...(head.value.link ?? [])],
  meta: [...(head.value.meta ?? [])],
}))
</script>

<template>
  <NuxtPage />
</template>