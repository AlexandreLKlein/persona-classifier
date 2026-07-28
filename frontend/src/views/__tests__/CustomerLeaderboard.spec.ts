import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import CustomerLeaderboard from '../CustomerLeaderboard.vue'
import * as api from '@/lib/api'

vi.mock('@/lib/api')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: CustomerLeaderboard },
    { path: '/customers/:id', component: { template: '<div />' } },
  ],
})

describe('CustomerLeaderboard', () => {
  const pinia = createPinia()

  beforeEach(() => {
    setActivePinia(pinia)
    vi.mocked(api.fetchPersonas).mockResolvedValue([
      { key: 'regular', name: 'The Regular', description: 'Visits often.', weights: {} },
    ])
    vi.mocked(api.fetchCustomers).mockResolvedValue([
      {
        customer_id: 1,
        display_name: 'Jane Doe',
        top_persona_key: 'regular',
        top_persona_name: 'The Regular',
        top_persona_score: 87.3,
        filtered_persona_score: null,
        last_visit_at: '2026-01-01T00:00:00',
      },
    ])
  })

  it('renders the loaded customer list', async () => {
    const wrapper = mount(CustomerLeaderboard, { global: { plugins: [router, pinia] } })
    await flushPromises()

    expect(wrapper.text()).toContain('Jane Doe')
    expect(wrapper.text()).toContain('The Regular')
    expect(wrapper.text()).toContain('87.3')
  })

  it('shows an error message when the API call fails', async () => {
    vi.mocked(api.fetchCustomers).mockRejectedValue(new Error('boom'))
    const wrapper = mount(CustomerLeaderboard, { global: { plugins: [router, pinia] } })
    await flushPromises()

    expect(wrapper.text()).toContain('boom')
  })

  it('shows an empty state when there are no customers', async () => {
    vi.mocked(api.fetchCustomers).mockResolvedValue([])
    const wrapper = mount(CustomerLeaderboard, { global: { plugins: [router, pinia] } })
    await flushPromises()

    expect(wrapper.text()).toContain('No customers found')
  })
})
