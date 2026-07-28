import type {
  CustomerDetail,
  CustomerSummary,
  LeaderboardEntry,
  PersonaDefinition,
  SortOption,
} from '@/types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`)
  if (!response.ok) {
    const body = await response.text()
    throw new Error(`API error ${response.status} on ${path}: ${body}`)
  }
  return response.json() as Promise<T>
}

export function fetchPersonas(): Promise<PersonaDefinition[]> {
  return request('/api/personas')
}

export function fetchCustomers(options: {
  persona?: string | null
  sort?: SortOption
  page?: number
  pageSize?: number
}): Promise<CustomerSummary[]> {
  const params = new URLSearchParams()
  if (options.persona) params.set('persona', options.persona)
  params.set('sort', options.sort ?? 'score_desc')
  params.set('page', String(options.page ?? 1))
  params.set('page_size', String(options.pageSize ?? 25))
  return request(`/api/customers?${params.toString()}`)
}

export function fetchCustomer(customerId: number): Promise<CustomerDetail> {
  return request(`/api/customers/${customerId}`)
}

export function fetchPersonaLeaderboard(
  personaKey: string,
  limit = 10,
): Promise<LeaderboardEntry[]> {
  return request(`/api/personas/${personaKey}/leaderboard?limit=${limit}`)
}

export async function recomputeScores(): Promise<{ persona_scores_written: number }> {
  const response = await fetch(`${BASE_URL}/api/admin/recompute`, { method: 'POST' })
  if (!response.ok) throw new Error(`Recompute failed: ${response.status}`)
  return response.json()
}
