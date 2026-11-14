// Etat et actions de la page /outil, partages entre ses composants.
// La page cree l'etat (creerOutil) et le fournit ; chaque composant le recupere avec useOutil().
import type { InjectionKey } from 'vue'
import type { Climat, Culture, Priorites, RotationResponse, Sol, Validation, Zone } from '~/composables/useFieldShiftApi'
import { messageErreur } from '~/composables/useFieldShiftApi'

export const PARCELLE_LIBRE = 'aucune' // PrimeVue Select n'affiche pas une option de valeur null

export function creerOutil() {
  const api = useFieldShiftApi()
  const { locale } = useI18n()

  // Donnees de reference
  const cultures = ref<Culture[]>([])
  const zone = ref<Zone | null>(null)
  const climat = ref<Climat | null>(null)
  const sol = ref<Sol | null>(null)
  const validation = ref<Validation | null>(null)
  const erreurChargement = ref<string | null>(null)

  // Choix de l'agriculteur
  const precedent = ref<string>(PARCELLE_LIBRE)
  const priorites = reactive<Priorites>({ rendement: 3, eau: 3, sol: 3 })
  const analyseSol = ref(false)
  const phSaisi = ref<number | null>(null)
  const argileSaisie = ref<number | null>(null)

  // Resultats
  const resultat = ref<RotationResponse | null>(null)
  const calcul = ref(false)
  const erreurCalcul = ref<string | null>(null)

  const latitude = computed(() => zone.value?.latitude ?? sol.value?.latitude ?? 5.4429)
  const longitude = computed(() => zone.value?.longitude ?? sol.value?.longitude ?? 10.0697)
  const nomZone = computed(() => (zone.value?.nom ?? 'dschang').replace(/^\w/, (c) => c.toUpperCase()))

  async function comparer() {
    if (!zone.value) return
    calcul.value = true
    erreurCalcul.value = null
    try {
      resultat.value = await api.rotations({
        zone: zone.value.nom,
        priorites: { ...priorites },
        precedent: precedent.value === PARCELLE_LIBRE ? null : precedent.value,
        nb: 3,
        sol: analyseSol.value ? { ph: phSaisi.value, argile_pct: argileSaisie.value } : null,
        // raisons, conseils et normes renvoyes dans la langue de la page
        langue: locale.value === 'en' ? 'en' : 'fr',
      })
    } catch (e) {
      erreurCalcul.value = messageErreur(e)
    } finally {
      calcul.value = false
    }
  }

  async function charger(messageAucuneZone: string) {
    erreurChargement.value = null
    try {
      const [c, zones] = await Promise.all([api.cultures(), api.zones()])
      cultures.value = c
      zone.value = zones[0] ?? null
      if (!zone.value) {
        erreurChargement.value = messageAucuneZone
        return
      }
      const [cl, so, va] = await Promise.all([
        api.climat(zone.value.nom),
        api.sol(zone.value.nom),
        api.validation(zone.value.nom),
      ])
      climat.value = cl
      sol.value = so
      validation.value = va
      await comparer()
    } catch (e) {
      erreurChargement.value = messageErreur(e)
    }
  }

  // Changement de langue : on redemande les rotations, deja calculees, dans la nouvelle langue
  watch(locale, () => {
    if (resultat.value) comparer()
  })

  return {
    cultures, zone, climat, sol, validation, erreurChargement,
    precedent, priorites, analyseSol, phSaisi, argileSaisie,
    resultat, calcul, erreurCalcul,
    latitude, longitude, nomZone,
    charger, comparer,
  }
}

export type Outil = ReturnType<typeof creerOutil>
export const CLE_OUTIL: InjectionKey<Outil> = Symbol('outil')

export function fournirOutil() {
  const outil = creerOutil()
  provide(CLE_OUTIL, outil)
  return outil
}

export function useOutil(): Outil {
  const outil = inject(CLE_OUTIL)
  if (!outil) throw new Error('useOutil() doit etre utilise dans la page /outil')
  return outil
}