// Couleur d'identite de chaque culture (toujours accompagnee de son nom a l'ecran).
// Ordre fixe : la couleur suit la culture, jamais son rang dans un classement.
export const COULEURS_CULTURES: Record<
  string,
  { fond: string; texte: string }
> = {
  mais: { fond: "#eda100", texte: "#2b1d00" },
  haricot: { fond: "#c2413f", texte: "#ffffff" },
  arachide: { fond: "#b8642f", texte: "#ffffff" },
  manioc: { fond: "#2f7d32", texte: "#ffffff" },
  pomme_de_terre: { fond: "#6250d6", texte: "#ffffff" },
};

export const NOMS_SAISONS: Record<string, string> = {
  saison_1: "Saison 1 (mars à juillet)",
  saison_2: "Saison 2 (août à novembre)",
};

export const MOIS_COURTS = [
  "Janv.",
  "Févr.",
  "Mars",
  "Avril",
  "Mai",
  "Juin",
  "Juil.",
  "Août",
  "Sept.",
  "Oct.",
  "Nov.",
  "Déc.",
];

// Raisons positives renvoyees par le moteur : azote apporte, succession conseillee par l'IRAD
const MARQUEURS_POSITIFS = [
  "enrichit le sol",
  "conseillée par l’IRAD",
  "conseillée par l'IRAD",
  "enriches the soil",
  "recommended by IRAD",
];
export function raisonPositive(raison: string): boolean {
  return MARQUEURS_POSITIFS.some((m) => raison.includes(m));
}
