<script setup lang="ts"></script>

<template>
  <div class="min-h-screen">
    <header class="border-b border-white/10 mb-8">
      <div class="flex items-center justify-between py-5">
        <RouterLink to="/" class="text-lg font-semibold tracking-tight text-white">
          Persona Classifier <span class="text-cyan-400">/</span>
          <span class="text-white/50 font-normal text-sm"
            >taproom customer scoring, reimagined</span
          >
        </RouterLink>
      </div>
    </header>
    <main>
      <RouterView />
    </main>
  </div>
</template>
