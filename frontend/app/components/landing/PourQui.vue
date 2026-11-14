<script setup lang="ts">
const { t } = useI18n()
const racine = ref<HTMLElement | null>(null)
useRevele(racine)

const PUBLICS = [
  { id: 'agriculteurs', icone: 'pi-user' },
  { id: 'techniciens', icone: 'pi-compass' },
  { id: 'cooperatives', icone: 'pi-users' },
  { id: 'chercheurs', icone: 'pi-book' },
]
</script>

<template>
  <section id="pour-qui" ref="racine" class="bg-white py-20 md:py-28">
    <div class="mx-auto max-w-7xl px-4 md:px-6">
      <div class="max-w-3xl">
        <p data-revele class="sur-titre text-primary">{{ t('pourQui.surTitre') }}</p>
        <h2 data-revele class="titre-large mt-4 text-3xl sm:text-4xl xl:text-5xl leading-tight text-foret">
          {{ t('pourQui.titre') }}
        </h2>
      </div>

      <ul class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <li
          v-for="p in PUBLICS"
          :key="p.id"
          data-revele
          class="group rounded-2xl border border-trait bg-brume p-6 transition-colors hover:border-primary/40 hover:bg-white"
        >
          <span
            class="grid size-12 place-items-center rounded-xl bg-foret text-soleil transition-transform group-hover:-translate-y-0.5"
            aria-hidden="true"
          >
            <i class="pi text-lg" :class="p.icone" />
          </span>
          <h3 class="mt-5 text-lg font-bold text-foret">{{ t(`pourQui.publics.${p.id}.titre`) }}</h3>
          <p class="mt-2 text-sm text-encre-2 leading-relaxed">{{ t(`pourQui.publics.${p.id}.texte`) }}</p>
        </li>
      </ul>
    </div>
  </section>
</template>