import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchPersonas } from '@/lib/api'
import type { PersonaDefinition } from '@/types'

export const usePersonaStore = defineStore('personas', () => {
  const personas = ref<PersonaDefinition[]>([])
  const loaded = ref(false)
  const error = ref<string | null>(null)

  async function ensureLoaded() {
    if (loaded.value) return
    try {
      personas.value = await fetchPersonas()
      loaded.value = true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load personas'
    }
  }

  function byKey(key: string): PersonaDefinition | undefined {
    return personas.value.find((p) => p.key === key)
  }

  return { personas, loaded, error, ensureLoaded, byKey }
})
