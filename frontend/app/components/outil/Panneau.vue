<script setup lang="ts">
// Panneau de gauche : la parcelle et les choix de l'agriculteur
const { t } = useI18n()
const o = useOutil()

const CRITERES = ['rendement', 'eau', 'sol'] as const

const optionsPrecedent = computed(() => [
  { label: t('outil.panneau.parcelleLibre'), value: PARCELLE_LIBRE },
  ...o.cultures.value.map((c) => ({ label: t(`cultures.${c.id}`), value: c.id })),
])
</script>

<template>
  <aside class="rounded-2xl bg-white border border-trait p-5 space-y-6 lg:sticky lg:top-6" :aria-label="t('outil.panneau.aria')">
    <!-- Parcelle -->
    <section>
      <h2 class="font-bold text-lg text-foret">{{ t('outil.panneau.parcelle') }}</h2>
      <p class="text-sm text-encre-2 mb-3 tabular-nums">
        {{ o.nomZone.value }}, {{ o.latitude.value.toFixed(4) }} N, {{ o.longitude.value.toFixed(4) }} E
      </p>
      <ParcelleMap :latitude="o.latitude.value" :longitude="o.longitude.value" :nom="o.nomZone.value" />
    </section>

    <!-- Culture en place -->
    <section>
      <label for="precedent" class="font-semibold block mb-1.5 text-foret">{{ t('outil.panneau.precedent') }}</label>
      <Select
        v-model="o.precedent.value"
        input-id="precedent"
        :options="optionsPrecedent"
        option-label="label"
        option-value="value"
        class="w-full"
      />
      <p class="text-xs text-encre-2 mt-1.5">{{ t('outil.panneau.precedentAide') }}</p>
    </section>

    <!-- Priorites -->
    <section>
      <h2 class="font-semibold mb-3 text-foret">{{ t('outil.panneau.priorites') }}</h2>
      <div class="space-y-5">
        <div v-for="c in CRITERES" :key="c">
          <div class="flex justify-between items-baseline gap-2">
            <span :id="`label-${c}`" class="font-medium">{{ t(`outil.criteres.${c}.label`) }}</span>
            <span class="text-sm text-primary font-semibold">{{ t(`outil.importance.${o.priorites[c]}`) }}</span>
          </div>
          <p class="text-xs text-encre-2 mb-3">{{ t(`outil.criteres.${c}.aide`) }}</p>
          <Slider v-model="o.priorites[c]" :min="1" :max="5" :step="1" :aria-labelledby="`label-${c}`" class="mx-1" />
        </div>
      </div>
    </section>

    <!-- Analyse de sol -->
    <section>
      <div class="flex items-center justify-between gap-3">
        <label for="analyse-sol" class="font-semibold text-foret">{{ t('outil.panneau.analyseSol') }}</label>
        <ToggleSwitch v-model="o.analyseSol.value" input-id="analyse-sol" />
      </div>
      <p class="text-xs text-encre-2 mt-1">
        {{ t('outil.panneau.analyseSolAide') }}
        <template v-if="o.sol.value">
          ({{ t('outil.panneau.estimation', { ph: o.sol.value.ph, argile: Math.round(o.sol.value.argile_pct) }) }})
        </template>
      </p>
      <div v-if="o.analyseSol.value" class="grid grid-cols-2 gap-3 mt-3">
        <div>
          <label for="ph" class="text-sm block mb-1">{{ t('outil.panneau.ph') }}</label>
          <InputNumber
            v-model="o.phSaisi.value"
            input-id="ph"
            :min="3"
            :max="10"
            :min-fraction-digits="1"
            :max-fraction-digits="1"
            :placeholder="o.sol.value ? String(o.sol.value.ph) : ''"
            fluid
          />
        </div>
        <div>
          <label for="argile" class="text-sm block mb-1">{{ t('outil.panneau.argile') }}</label>
          <InputNumber
            v-model="o.argileSaisie.value"
            input-id="argile"
            :min="0"
            :max="100"
            :placeholder="o.sol.value ? String(Math.round(o.sol.value.argile_pct)) : ''"
            fluid
          />
        </div>
      </div>
    </section>

    <Button
      :label="t('outil.panneau.comparer')"
      icon="pi pi-sync"
      class="w-full"
      :loading="o.calcul.value"
      :disabled="!o.zone.value"
      @click="o.comparer"
    />
  </aside>
</template>