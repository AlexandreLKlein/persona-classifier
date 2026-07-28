export interface PersonaDefinition {
  key: string
  name: string
  description: string
  weights: Record<string, number>
}

export interface CustomerSummary {
  customer_id: number
  display_name: string
  top_persona_key: string | null
  top_persona_name: string | null
  top_persona_score: number
  filtered_persona_score: number | null
  last_visit_at: string
}

export interface PersonaScoreEntry {
  persona_key: string
  persona_name: string
  score: number
  breakdown: Record<string, number>
}

export interface CustomerDetail {
  customer_id: number
  display_name: string
  first_visit_at: string
  last_visit_at: string
  persona_scores: PersonaScoreEntry[]
}

export interface LeaderboardEntry {
  customer_id: number
  display_name: string
  score: number
  breakdown: Record<string, number>
}

export type SortOption = 'score_desc' | 'score_asc' | 'name_asc'
