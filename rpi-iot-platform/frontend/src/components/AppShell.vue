<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useReadings } from '../composables/useReadings'

const { connected } = useReadings()
const route = useRoute()

const navItems = [
  { to: '/', label: 'Sensors', icon: 'sensors' },
  { to: '/modules', label: 'Modules', icon: 'modules' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
  { to: '/about', label: 'About', icon: 'about' },
]

const pageTitle = computed(() => (route.meta?.title as string) ?? '')
</script>

<template>
  <div class="min-h-screen flex bg-slate-900 text-slate-100">

    <!-- Sidebar — kiosk-friendly: chunky icons, ≥48px touch targets -->
    <nav
      class="w-20 shrink-0 bg-slate-950/80 border-r border-slate-800 flex flex-col items-center py-4 gap-2"
      aria-label="Primary"
    >
      <div
        class="w-12 h-12 rounded-full bg-pi-red flex items-center justify-center text-white font-mono font-bold shadow-lg mb-3"
        aria-hidden="true"
      >
        Pi
      </div>

      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="w-14 h-14 rounded-xl flex flex-col items-center justify-center gap-0.5 transition-colors text-[0.65rem] font-bold uppercase tracking-wider"
        active-class="bg-pi-red/15 text-pi-red-soft"
        :class="route.path === item.to ? '' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'"
      >
        <span class="text-xl" aria-hidden="true">
          <template v-if="item.icon === 'sensors'">◉</template>
          <template v-else-if="item.icon === 'modules'">▦</template>
          <template v-else-if="item.icon === 'settings'">⚙</template>
          <template v-else-if="item.icon === 'about'">i</template>
        </span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>

    <!-- Main column -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Top bar -->
      <header
        class="h-14 px-6 flex items-center justify-between border-b border-slate-800 bg-slate-900/70 backdrop-blur shrink-0"
      >
        <div class="min-w-0">
          <h1 class="text-base font-extrabold tracking-tight truncate">
            {{ pageTitle }}
          </h1>
          <p class="text-[0.7rem] text-slate-500 font-mono">
            Pi IoT Platform
          </p>
        </div>

        <div
          class="font-mono text-[0.7rem] px-3 py-1 rounded-full font-bold uppercase tracking-wider"
          :class="connected
            ? 'bg-pi-green/20 text-pi-green-soft'
            : 'bg-pi-red/20 text-pi-red-soft'"
          :aria-label="`Backend connection: ${connected ? 'connected' : 'disconnected'}`"
        >
          <span
            class="inline-block w-2 h-2 rounded-full mr-1.5 align-middle"
            :class="connected ? 'bg-pi-green animate-pulse' : 'bg-pi-red'"
            aria-hidden="true"
          ></span>
          {{ connected ? 'connected' : 'disconnected' }}
        </div>
      </header>

      <!-- Page content — scrolls -->
      <main
        class="flex-1 overflow-y-auto"
        style="background-image: radial-gradient(circle at 12% 8%, rgba(197, 26, 74, 0.05) 0%, transparent 35%), radial-gradient(circle at 88% 92%, rgba(117, 179, 67, 0.05) 0%, transparent 35%);"
      >
        <slot />
      </main>
    </div>

  </div>
</template>
