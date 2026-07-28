import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import CustomerDetail from '../CustomerDetail.vue'
import * as api from '@/lib/api'

vi.mock('@/lib/api')

const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', component: { template: '<div />' } }],
})

describe('CustomerDetail', () => {
  const pinia = createPinia()

  beforeEach(() => {
    setActivePinia(pinia)
    vi.mocked(api.fetchPersonas).mockResolvedValue([
      {
        key: 'regular',
        name: 'The Regular',
        description: 'Visits often.',
        weights: { recency_score: 0.4 },
      },
      { key: 'explorer', name: 'The Explorer', description: 'Tries everything.', weights: {} },
    ])
    vi.mocked(api.fetchCustomer).mockResolvedValue({
      customer_id: 1,
      display_name: 'Jane Doe',
      first_visit_at: '2025-01-01T00:00:00',
      last_visit_at: '2026-01-01T00:00:00',
      persona_scores: [
        {
          persona_key: 'regular',
          persona_name: 'The Regular',
          score: 91.2,
          breakdown: { recency_score: 40 },
        },
        { persona_key: 'explorer', persona_name: 'The Explorer', score: 12.5, breakdown: {} },
      ],
    })
  })

  it('renders the customer name and ranked persona scores', async () => {
    // Radar is stubbed -- vue-chartjs/Chart.js needs a real canvas context, which jsdom
    // doesn't provide. The scoring/data layer is what this project actually needs to prove
    // correct, so it's covered by the Python test suite instead of re-testing chart rendering.
    const wrapper = mount(CustomerDetail, {
      props: { id: '1' },
      global: { plugins: [router, pinia], stubs: { Radar: true } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Jane Doe')
    expect(wrapper.text()).toContain('91.2')
    expect(wrapper.text()).toContain('The Regular')
  })

  it('shows an error message when the customer fails to load', async () => {
    vi.mocked(api.fetchCustomer).mockRejectedValue(new Error('not found'))
    const wrapper = mount(CustomerDetail, {
      props: { id: '999' },
      global: { plugins: [router, pinia], stubs: { Radar: true } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('not found')
  })
})
