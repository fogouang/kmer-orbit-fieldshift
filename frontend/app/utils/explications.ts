import type { Climat, Rotation, Sol } from '~/composables/useFieldShiftApi'
import { NOMS_SAISONS, raisonPositive } from '~/utils/cultures'
import { fr } from '~/utils/format'

const LEGUMINEUSES = ['haricot', 'arachide']

export interface Explications {
  pourquoi: string[]
  donnees: string[]
  benefices: string[]
  inconnu: string[]
  agronome: string[]
}

// Textes des cinq sections depliables, construits a partir des raisons du moteur,
// du climat et du sol de la parcelle
export function expliquer(rotation: Rotation, climat: Climat | null, sol: Sol | null): Explications {
  const ids = rotation.sequence.map((e) => e.culture)
  const nom = (id: string) => rotation.sequence.find((e) => e.culture === id)?.nom ?? id
  const legumineuses = [...new Set(ids.filter((id) => LEGUMINEUSES.includes(id)))]

  const positives = rotation.raisons.filter(raisonPositive)
  const vigilances = rotation.raisons.filter((r) => !raisonPositive(r))

  const pourquoi = positives.length
    ? positives
    : ['Cette rotation équilibre le mieux vos trois priorités parmi les combinaisons testées.']

  const donnees: string[] = []
  for (const s of climat?.saisons ?? []) {
    donnees.push(
      `${NOMS_SAISONS[s.saison] ?? s.saison} : ${fr(s.pluie_moyenne_mm)} mm de pluie en moyenne et ${fr(s.temperature_c, 1)} °C (NASA GPM IMERG, NASA POWER).`,
    )
  }
  if (sol) {
    donnees.push(`Sol : pH ${fr(sol.ph, 1)}, argile ${fr(sol.argile_pct)} % (ISRIC SoilGrids).`)
  }

  const benefices: string[] = []
  if (legumineuses.length) {
    const sujet = legumineuses.map(nom).join(' et ')
    const verbe = legumineuses.length > 1 ? 'ces légumineuses enrichissent' : 'cette légumineuse enrichit'
    benefices.push(`${sujet} : ${verbe} le sol en azote pour la culture suivante.`)
  }
  if (new Set(ids).size >= 3) {
    benefices.push('Plusieurs cultures différentes : les maladies et les ravageurs passent moins facilement d’une saison à l’autre.')
  }
  if (ids.includes('manioc')) {
    benefices.push('Le manioc reste en terre et peut être récolté selon les besoins de la famille.')
  }
  if (!benefices.length) {
    benefices.push('Pas de bénéfice particulier pour le sol avec cette rotation.')
  }

  const inconnu = [
    'La date exacte du début des pluies change chaque année.',
    'Les prix de vente au marché ne sont pas pris en compte.',
    'Les ravageurs et les maladies de l’année ne peuvent pas être prévus.',
    'Le rendement réel dépend aussi de la variété, des engrais et du travail du sol.',
  ]

  const agronome = [...vigilances]
  if (sol && sol.ph < 5.5 && legumineuses.length) {
    agronome.push(
      `Faut-il corriger l’acidité du sol (pH ${fr(sol.ph, 1)}) avant de semer ${legumineuses.map(nom).join(' ou ')} ?`,
    )
  }
  agronome.push('Les variétés et les dates de semis les mieux adaptées à votre village.')

  return { pourquoi, donnees, benefices, inconnu, agronome }
}