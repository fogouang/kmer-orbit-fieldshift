<script setup lang="ts">
const { t } = useI18n()
useHead(() => ({
  title: t('meta.titre'),
  meta: [{ name: 'description', content: t('meta.description') }],
}))
</script>

<template>
  <div>
    <LandingHero />
    <LandingProbleme />
    <LandingCommentCaMarche />
    <LandingValidation />
    <LandingSavoirIrad />
    <LandingPourQui />
    <LandingLimites />
    <LandingFinal />
  </div>
</template>