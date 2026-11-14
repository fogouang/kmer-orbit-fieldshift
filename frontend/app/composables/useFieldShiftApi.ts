// Types et appels de l'API Field Shift (backend FastAPI)

export interface Culture {
  id: string;
  nom: string;
  famille: string;
  type: string;
  ph_optimum: { min: number; max: number };
}

export interface Zone {
  nom: string;
  latitude: number | null;
  longitude: number | null;
}

export interface SaisonClimat {
  saison: string;
  mois: number[];
  pluie_moyenne_mm: number;
  pluie_min_mm: number;
  pluie_max_mm: number;
  temperature_c: number;
}

export interface Climat {
  zone: string;
  sources: Record<string, string>;
  annees_reference: number[];
  saisons: SaisonClimat[];
  periode_a: string;
  periode_b: string;
  pluie_mensuelle: {
    mois: number;
    periode_a_mm: number;
    periode_b_mm: number;
    ecart_pct: number;
  }[];
  debut_saison: {
    annee: number;
    date_imerg: string | null;
    jour_imerg: number | null;
    jour_power: number | null;
  }[];
  temperature_annuelle: { annee: number; temperature_c: number }[];
}

export interface Sol {
  zone: string;
  latitude?: number | null;
  longitude?: number | null;
  ph: number;
  ph_niveau?: string | null;
  carbone_organique_g_kg?: number | null;
  carbone_niveau?: string | null;
  argile_pct: number;
  limon_pct?: number | null;
  sable_pct?: number | null;
  texture?: string | null;
  cec_cmol_kg?: number | null;
}

export interface Priorites {
  rendement: number;
  eau: number;
  sol: number;
}

export interface RotationRequest {
  zone: string;
  priorites: Priorites;
  precedent: string | null;
  nb?: number;
  sol?: { ph: number | null; argile_pct: number | null } | null;
  langue?: "fr" | "en";
  // Rotation habituelle, saison par saison (An 1 s1, An 1 s2, An 2 s1, An 2 s2), null = repos
  actuelle?: (string | null)[] | null;
}

// Une culture placee dans la rotation (peut occuper plusieurs saisons, ex. manioc)
export interface EtapeSequence {
  culture: string;
  nom: string;
  periodes: { annee: string; saison: string }[];
}

export interface Rotation {
  rang: number;
  note: number;
  rendement: number;
  eau: number;
  sante_sol: number;
  sequence: EtapeSequence[];
  raisons: string[];
  conseils?: string[];
  regles_non_respectees?: string[];
}

export interface RotationResponse {
  zone: string;
  priorites: Priorites;
  precedent: string | null;
  sol_utilise: { ph: number; argile_pct: number; source: string };
  nb_rotations_evaluees: number;
  rotations: Rotation[];
  normes_irad?: Record<string, string | string[]>;
  actuelle?: Rotation | null;
}

export interface StatsComparaison {
  nb_mois: number;
  correlation: number;
  biais_moyen: number;
  biais_pct: number | null;
  erreur_absolue_moyenne: number;
}

// Satellite compare a la station meteo au sol (scripts/station_irad.py)
export interface Validation {
  station: string;
  periode_pluie: string;
  pluie_mensuelle: { imerg: StatsComparaison; power: StatsComparaison };
  pluie_annuelle: {
    station_moyenne_mm: number;
    imerg_moyenne_mm: number;
    power_moyenne_mm: number;
  };
  pluie_par_saison: Record<
    string,
    { station_moyenne_mm: number; imerg_moyenne_mm: number; ecart_pct: number }
  >;
  temperature_mensuelle_power: StatsComparaison;
  mois_signales: { pluie: string[]; temperature: string[] };
}

export function useFieldShiftApi() {
  const base = useRuntimeConfig().public.apiBase as string;

  const get = <T>(chemin: string) => $fetch<T>(`${base}${chemin}`);

  return {
    cultures: () => get<Culture[]>("/cultures"),
    zones: () => get<Zone[]>("/zones"),
    climat: (zone: string) => get<Climat>(`/zones/${zone}/climat`),
    sol: (zone: string) => get<Sol>(`/zones/${zone}/sol`),
    // 404 si la zone n'a pas de station au sol : ce n'est pas une erreur
    validation: (zone: string) =>
      get<Validation>(`/zones/${zone}/validation`).catch(() => null),
    rotations: (body: RotationRequest) =>
      $fetch<RotationResponse>(`${base}/rotations`, { method: "POST", body }),
  };
}

// Message lisible a partir d'une erreur $fetch
export function messageErreur(e: unknown): string {
  const err = e as { data?: { detail?: unknown }; message?: string };
  const detail = err?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((d: { msg?: string }) => d.msg).join(", ");
  if (err?.message?.includes("fetch")) {
    return "Impossible de joindre l'API. Vérifiez que le backend tourne (uv run uvicorn app.main:app --reload --app-dir backend).";
  }
  return err?.message ?? "Erreur inconnue";
}
