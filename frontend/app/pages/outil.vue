<script setup lang="ts">
// Page de l'outil : chaque bloc est un composant de app/components/outil/
const { t } = useI18n();
const o = fournirOutil();

useHead(() => ({ title: t("outil.metaTitre") }));
onMounted(() => o.charger(t("outil.aucuneZone")));
</script>

<template>
  <div class="min-h-screen bg-brume">
    <OutilBarre />

    <!-- Bandeau d'introduction -->
    <div class="fond-sombre bg-foret text-white border-t border-white/10">
      <div class="mx-auto max-w-7xl px-4 md:px-6 pt-8 pb-10 md:pt-10 md:pb-12">
        <p class="sur-titre text-soleil">{{ t("outil.surTitre") }}</p>
        <h1 class="titre-large mt-3 text-3xl md:text-4xl">
          {{ t("outil.titre") }}
        </h1>
        <p class="mt-3 max-w-2xl text-white/80">{{ t("outil.intro") }}</p>
      </div>
    </div>

    <main
      class="mx-auto max-w-7xl px-4 md:px-6 pt-6 pb-16 grid gap-6 lg:grid-cols-[22rem_1fr] lg:items-start"
    >
      <Message
        v-if="o.erreurChargement.value"
        severity="error"
        class="lg:col-span-2"
      >
        {{ o.erreurChargement.value }}
      </Message>

      <OutilPanneau />

      <div class="space-y-8 min-w-0">
        <OutilRotations />
        <OutilAssistant />
        <OutilNormesIrad />
        <OutilClimat />
        <OutilValidationSol />
        <OutilSol />
        <p class="flex gap-2 text-xs text-encre-2 leading-relaxed">
          <i class="pi pi-info-circle mt-0.5" aria-hidden="true" />
          {{ t("final.footer.avertissement") }}
        </p>
      </div>
    </main>
  </div>
</template>
