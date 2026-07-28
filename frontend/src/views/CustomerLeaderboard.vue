<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { fetchCustomers, recomputeScores } from '@/lib/api'
import { usePersonaStore } from '@/stores/personas'
import type { CustomerSummary, SortOption } from '@/types'

const personaStore = usePersonaStore()

const customers = ref<CustomerSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const selectedPersona = ref<string>('')
const sort = ref<SortOption>('score_desc')
const recomputing = ref(false)
const recomputeMessage = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    customers.value = await fetchCustomers({
      persona: selectedPersona.value || null,
      sort: sort.value,
      pageSize: 50,
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load customers'
  } finally {
    loading.value = false
  }
}

async function handleRecompute() {
  recomputing.value = true
  recomputeMessage.value = null
  try {
    const result = await recomputeScores()
    recomputeMessage.value = `Recomputed ${result.persona_scores_written} scores.`
    await load()
  } catch (e) {
    recomputeMessage.value = e instanceof Error ? e.message : 'Recompute failed'
  } finally {
    recomputing.value = false
  }
}

onMounted(() => {
  personaStore.ensureLoaded()
  load()
})

watch([selectedPersona, sort], load)
</script>

<template>
  <section>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-white mb-1">Customer leaderboard</h1>
      <p class="text-white/50 text-sm max-w-2xl">
        Every customer here is synthetic. Scores are recomputed from behavioral features (recency,
        frequency, spend, diversity, event attendance) against an
        <RouterLink to="/" class="underline decoration-dotted">original persona rubric</RouterLink>
        -- see the README for why.
      </p>
    </div>

    <div class="flex flex-wrap items-center gap-3 mb-5">
      <select
        v-model="selectedPersona"
        class="bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
        style="color-scheme: dark"
      >
        <option value="" class="bg-slate-800 text-white">All personas (rank by top persona)</option>
        <option
          v-for="p in personaStore.personas"
          :key="p.key"
          :value="p.key"
          class="bg-slate-800 text-white"
        >
          {{ p.name }}
        </option>
      </select>

      <select
        v-model="sort"
        class="bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
        style="color-scheme: dark"
      >
        <option value="score_desc" class="bg-slate-800 text-white">Score: high to low</option>
        <option value="score_asc" class="bg-slate-800 text-white">Score: low to high</option>
        <option value="name_asc" class="bg-slate-800 text-white">Name: A-Z</option>
      </select>

      <button
        class="ml-auto bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-sm px-3 py-2 rounded-lg transition-colors disabled:opacity-50"
        :disabled="recomputing"
        @click="handleRecompute"
      >
        {{ recomputing ? 'Recomputing...' : 'Recompute scores' }}
      </button>
    </div>

    <p v-if="recomputeMessage" class="text-xs text-white/40 mb-4">{{ recomputeMessage }}</p>

    <div v-if="loading" class="text-white/40 text-sm py-12 text-center">Loading customers...</div>
    <div v-else-if="error" class="text-red-400 text-sm py-12 text-center">{{ error }}</div>
    <div v-else-if="customers.length === 0" class="text-white/40 text-sm py-12 text-center">
      No customers found.
    </div>

    <div v-else class="border border-white/10 rounded-xl overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-white/5 text-left text-white/50 uppercase text-xs tracking-wider">
            <th class="px-4 py-3 font-medium">Customer</th>
            <th class="px-4 py-3 font-medium">Top persona</th>
            <th class="px-4 py-3 font-medium text-right">Score</th>
            <th class="px-4 py-3 font-medium text-right">Last visit</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="customer in customers"
            :key="customer.customer_id"
            class="border-t border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
            @click="$router.push(`/customers/${customer.customer_id}`)"
          >
            <td class="px-4 py-3 text-white">{{ customer.display_name }}</td>
            <td class="px-4 py-3">
              <span
                class="bg-cyan-500/10 text-cyan-300 text-xs px-2 py-0.5 rounded-full border border-cyan-500/20"
              >
                {{ customer.top_persona_name }}
              </span>
            </td>
            <td class="px-4 py-3 text-right font-mono text-white/80">
              {{
                (selectedPersona
                  ? customer.filtered_persona_score
                  : customer.top_persona_score
                )?.toFixed(1)
              }}
            </td>
            <td class="px-4 py-3 text-right text-white/40 text-xs">
              {{ new Date(customer.last_visit_at).toLocaleDateString() }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
