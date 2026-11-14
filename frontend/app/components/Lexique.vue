<script setup lang="ts">
const TERMES = [
  {
    terme: 'Légumineuse',
    definition:
      'Plante comme le haricot ou l’arachide qui capte l’azote de l’air grâce à ses racines. Elle laisse un sol plus riche pour la culture suivante.',
  },
  {
    terme: 'Culture de couverture',
    definition:
      'Plante semée surtout pour couvrir le sol entre deux cultures. Elle protège la terre des fortes pluies et du soleil.',
  },
  {
    terme: 'Évapotranspiration',
    definition:
      'L’eau qui quitte le champ vers l’air : une partie s’évapore du sol, une autre sort par les feuilles. Plus il fait chaud, plus elle est forte.',
  },
  {
    terme: 'Humidité du sol',
    definition: 'La quantité d’eau gardée dans la terre et disponible pour les racines.',
  },
  {
    terme: 'Érosion',
    definition:
      'La terre emportée par la pluie ou le vent. Un sol nu pendant les grosses pluies perd sa bonne terre du dessus.',
  },
]
</script>

<template>
  <dl class="grid gap-x-8 gap-y-4 sm:grid-cols-2">
    <div v-for="t in TERMES" :key="t.terme">
      <dt class="font-semibold">{{ t.terme }}</dt>
      <dd class="text-sm text-encre-2 leading-snug mt-0.5">{{ t.definition }}</dd>
    </div>
  </dl>
</template>