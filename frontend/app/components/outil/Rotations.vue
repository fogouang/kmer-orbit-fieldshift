<script setup lang="ts">
// Les rotations proposees, avec l'en-tete des saisons aligne sur les bandes
const { t, locale } = useI18n();
const decimal = (x: number) =>
  x.toLocaleString(locale.value === "en" ? "en-US" : "fr-FR");
const o = useOutil();

const COLONNES = [
  { annee: "annee1", saison: "saison_1", sec: false },
  { annee: "annee1", saison: "saison_2", sec: false },
  { annee: "", saison: "seche", sec: true },
  { annee: "annee2", saison: "saison_1", sec: false },
  { annee: "annee2", saison: "saison_2", sec: false },
  { annee: "", saison: "seche", sec: true },
];
</script>

<template>
  <section aria-live="polite" :aria-busy="o.calcul.value">
    <div
      class="flex flex-col md:flex-row md:items-end md:justify-between gap-1 mb-4"
    >
      <h2 class="titre-large text-2xl md:text-3xl text-foret">
        {{
          o.resultat.value?.actuelle
            ? t("outil.rotations.titreAvecActuelle")
            : t("outil.rotations.titre")
        }}
      </h2>
      <p v-if="o.resultat.value" class="text-sm text-encre-2">
        {{
          t("outil.rotations.evaluees", {
            n: o.resultat.value.nb_rotations_evaluees,
          })
        }}
        {{
          t("outil.rotations.solUtilise", {
            ph: decimal(o.resultat.value.sol_utilise.ph),
          })
        }}
      </p>
    </div>

    <Message v-if="o.erreurCalcul.value" severity="error" class="mb-4">{{
      o.erreurCalcul.value
    }}</Message>

    <!-- En-tete des saisons, aligne sur les bandes -->
    <div
      class="hidden md:grid md:grid-cols-[8.5rem_1fr] gap-4 px-5 mb-2"
      aria-hidden="true"
    >
      <div />
      <div
        class="grid grid-cols-[1fr_1fr_0.45fr_1fr_1fr_0.45fr] gap-1 text-xs text-encre-2"
      >
        <div
          v-for="(c, i) in COLONNES"
          :key="i"
          class="border-l border-trait pl-2 truncate"
        >
          <template v-if="c.sec">{{
            t("outil.saisonsCourt.secheCourt")
          }}</template>
          <template v-else>
            <span class="font-semibold text-foret">{{
              t(`outil.${c.annee}`)
            }}</span
            >,
            {{ t(`outil.saisonsCourt.${c.saison}`) }}
          </template>
        </div>
      </div>
    </div>

    <div v-if="!o.resultat.value && !o.erreurCalcul.value" class="space-y-3">
      <Skeleton v-for="i in 3" :key="i" height="10rem" border-radius="1rem" />
    </div>
    <div
      v-else-if="o.resultat.value"
      class="space-y-3 transition-opacity"
      :class="{ 'opacity-60': o.calcul.value }"
    >
      <!-- La rotation habituelle d'abord : c'est le point de comparaison -->
      <OutilCarteRotation
        v-if="o.resultat.value.actuelle"
        :rotation="o.resultat.value.actuelle"
        actuelle
      />
      <OutilCarteRotation
        v-for="r in o.resultat.value.rotations"
        :key="r.rang"
        :rotation="r"
        :meilleure="r.rang === 1"
        :reference="o.resultat.value.actuelle?.note ?? null"
      />
    </div>

    <p class="text-xs text-encre-2 mt-3">{{ t("outil.rotations.legende") }}</p>
  </section>
</template>
