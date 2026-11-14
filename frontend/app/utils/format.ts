// Nombres et dates au format francais (virgule decimale, "1er mars")

export function fr(n: number, decimales = 0): string {
  return n.toLocaleString('fr-FR', { minimumFractionDigits: decimales, maximumFractionDigits: decimales })
}

// Nombre avec son signe : "+21", "-12", "0"
export function signe(n: number, decimales = 0): string {
  const arrondi = Number(n.toFixed(decimales))
  const prefixe = arrondi > 0 ? '+' : arrondi < 0 ? '-' : ''
  return `${prefixe}${fr(Math.abs(arrondi), decimales)}`
}

// Jour de l'annee (1 a 365) vers une date lisible
export function jourEnDate(jour: number): string {
  const d = new Date(2001, 0, 1)
  d.setDate(d.getDate() + Math.round(jour) - 1)
  const j = d.getDate()
  const mois = d.toLocaleDateString('fr-FR', { month: 'long' })
  return `${j === 1 ? '1er' : j} ${mois}`
}