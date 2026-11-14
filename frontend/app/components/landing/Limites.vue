<script setup lang="ts">
const { t } = useI18n()
const racine = ref<HTMLElement | null>(null)
useRevele(racine)

const LIMITES = ['aide', 'notes', 'sol', 'zone']
const SUITE = [
  { id: 'zones', icone: 'pi-map' },
  { id: 'smap', icone: 'pi-globe' },
  { id: 'prevision', icone: 'pi-chart-line' },
  { id: 'terrain', icone: 'pi-check-square' },
]
</script>

<template>
  <section id="limites" ref="racine" class="bg-brume py-20 md:py-28">
    <div class="mx-auto max-w-7xl px-4 md:px-6 grid gap-4 lg:grid-cols-2">
      <!-- Limites : ce que l'outil n'est pas -->
      <article data-revele class="rounded-2xl bg-white border border-trait p-6 md:p-8">
        <p class="sur-titre text-primary">{{ t('limites.surTitre') }}</p>
        <h2 class="titre-large mt-4 text-2xl sm:text-3xl text-foret">{{ t('limites.titre') }}</h2>
        <ul class="mt-6 space-y-4">
          <li v-for="l in LIMITES" :key="l" class="flex gap-3 text-sm leading-relaxed">
            <i class="pi pi-info-circle text-ble mt-0.5" aria-hidden="true" />
            <span>
              <span class="font-semibold text-foret">{{ t(`limites.points.${l}.titre`) }}</span>{{ ' ' }}
              <span class="text-encre-2">{{ t(`limites.points.${l}.texte`) }}</span>
            </span>
          </li>
        </ul>
      </article>

      <!-- La suite -->
      <article data-revele class="fond-sombre rounded-2xl bg-foret text-white p-6 md:p-8">
        <p class="sur-titre text-soleil">{{ t('limites.suite.surTitre') }}</p>
        <h2 class="titre-large mt-4 text-2xl sm:text-3xl">{{ t('limites.suite.titre') }}</h2>
        <ol class="mt-6 space-y-3">
          <li
            v-for="(s, i) in SUITE"
            :key="s.id"
            class="grid grid-cols-[2.5rem_1fr] gap-3 rounded-xl bg-white/5 border border-white/10 p-4"
          >
            <span class="grid size-10 place-items-center rounded-lg bg-soleil text-foret" aria-hidden="true">
              <i class="pi" :class="s.icone" />
            </span>
            <span class="text-sm leading-relaxed">
              <span class="font-semibold block">
                <span class="sr-only">{{ i + 1 }}. </span>{{ t(`limites.suite.etapes.${s.id}.titre`) }}
              </span>
              <span class="text-white/75">{{ t(`limites.suite.etapes.${s.id}.texte`) }}</span>
            </span>
          </li>
        </ol>
      </article>
    </div>
  </section>
</template>