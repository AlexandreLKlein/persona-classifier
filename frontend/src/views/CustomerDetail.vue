<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { Radar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'
import { fetchCustomer } from '@/lib/api'
import { usePersonaStore } from '@/stores/personas'
import type { CustomerDetail } from '@/types'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const props = defineProps<{ id: string }>()

const personaStore = usePersonaStore()
const customer = ref<CustomerDetail | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

async function load(customerId: string) {
  loading.value = true
  error.value = null
  try {
    customer.value = await fetchCustomer(Number(customerId))
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load customer'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  personaStore.ensureLoaded()
  load(props.id)
})
watch(() => props.id, load)

const chartData = computed(() => {
  if (!customer.value) return { labels: [], datasets: [] }
  return {
    labels: customer.value.persona_scores.map((p) => p.persona_name),
    datasets: [
      {
        label: customer.value.display_name,
        data: customer.value.persona_scores.map((p) => p.score),
        backgroundColor: 'rgba(34, 211, 238, 0.15)',
        borderColor: 'rgba(34, 211, 238, 0.8)',
        pointBackgroundColor: 'rgba(34, 211, 238, 1)',
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  scales: {
    r: {
      min: 0,
      max: 100,
      ticks: { color: 'rgba(255,255,255,0.4)', backdropColor: 'transparent' },
      grid: { color: 'rgba(255,255,255,0.1)' },
      angleLines: { color: 'rgba(255,255,255,0.1)' },
      pointLabels: { color: 'rgba(255,255,255,0.7)', font: { size: 11 } },
    },
  },
  plugins: {
    legend: { display: false },
  },
}

const topPersona = computed(() => customer.value?.persona_scores[0] ?? null)
</script>

<template>
  <section>
    <RouterLink to="/" class="text-sm text-white/40 hover:text-white/70 transition-colors"
      >&larr; Back to leaderboard</RouterLink
    >

    <div v-if="loading" class="text-white/40 text-sm py-12 text-center">Loading customer...</div>
    <div v-else-if="error" class="text-red-400 text-sm py-12 text-center">{{ error }}</div>

    <template v-else-if="customer">
      <div class="mt-4 mb-8">
        <h1 class="text-2xl font-bold text-white mb-1">{{ customer.display_name }}</h1>
        <p class="text-white/40 text-sm">
          First visit {{ new Date(customer.first_visit_at).toLocaleDateString() }} &middot; Last
          visit {{ new Date(customer.last_visit_at).toLocaleDateString() }}
        </p>
      </div>

      <div class="grid md:grid-cols-2 gap-8">
        <div class="bg-white/[0.03] border border-white/10 rounded-xl p-6">
          <Radar :data="chartData" :options="chartOptions" />
        </div>

        <div class="space-y-3">
          <div
            v-for="p in customer.persona_scores"
            :key="p.persona_key"
            class="border border-white/10 rounded-xl p-4"
            :class="{
              'border-cyan-500/40 bg-cyan-500/5': p.persona_key === topPersona?.persona_key,
            }"
          >
            <div class="flex items-center justify-between mb-1">
              <span class="font-semibold text-white">{{ p.persona_name }}</span>
              <span class="font-mono text-white/80">{{ p.score.toFixed(1) }}</span>
            </div>
            <p class="text-xs text-white/40 mb-3">
              {{ personaStore.byKey(p.persona_key)?.description }}
            </p>
            <div class="space-y-1.5">
              <div
                v-for="(contribution, feature) in p.breakdown"
                :key="feature"
                class="flex items-center gap-2 text-xs"
              >
                <span class="text-white/40 w-40 shrink-0 truncate">{{ feature }}</span>
                <div class="flex-1 bg-white/5 rounded-full h-1.5 overflow-hidden">
                  <div
                    class="h-full bg-cyan-500/60 rounded-full"
                    :style="{ width: `${Math.min(100, (contribution / p.score) * 100 || 0)}%` }"
                  />
                </div>
                <span class="text-white/50 font-mono w-10 text-right">{{
                  contribution.toFixed(1)
                }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>
