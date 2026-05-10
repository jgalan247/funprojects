<script setup lang="ts">
const stack = [
  { name: 'Mosquitto', role: 'MQTT broker' },
  { name: 'Node-RED', role: 'Automation + debug' },
  { name: 'FastAPI', role: 'API + WebSocket' },
  { name: 'SQLite', role: 'Durable storage' },
  { name: 'Vue 3 + Tailwind', role: 'Touchscreen UI (this page)' },
  { name: 'Anthropic Claude', role: 'Sensor explanations (Phase 6)' },
]
</script>

<template>
  <div class="p-6 max-w-3xl mx-auto space-y-8">

    <section>
      <h2 class="text-2xl font-extrabold mb-2">Pi IoT Platform</h2>
      <p class="text-slate-400 leading-relaxed">
        A modular portable terminal for classroom IoT and AI demonstrations,
        built on a Raspberry Pi&nbsp;4B with the official 5″ touchscreen.
        Designed by Coderra.je for Haute Vallée School, Year&nbsp;8–9.
      </p>
    </section>

    <section>
      <h3 class="text-sm font-extrabold uppercase tracking-widest text-slate-500 mb-3">
        Stack
      </h3>
      <ul class="rounded-xl border border-slate-800 bg-slate-900/40 divide-y divide-slate-800">
        <li
          v-for="item in stack"
          :key="item.name"
          class="p-4 flex justify-between"
        >
          <span class="font-bold">{{ item.name }}</span>
          <span class="text-slate-400 text-sm">{{ item.role }}</span>
        </li>
      </ul>
    </section>

    <section>
      <h3 class="text-sm font-extrabold uppercase tracking-widest text-slate-500 mb-3">
        Phases
      </h3>
      <ol class="space-y-2 text-sm text-slate-300 list-decimal pl-5">
        <li>Build the Pi (hardware, OS, touchscreen).</li>
        <li>Install the platform (Docker Compose).</li>
        <li>Talk over MQTT (live sensor stream).</li>
        <li>Save your data (SQLite + retention).</li>
        <li><strong class="text-pi-green-soft">Design the dashboard</strong> (this).</li>
        <li>Ask Claude (AI explanations).</li>
        <li>First module: Classroom Sensor Hub.</li>
      </ol>
    </section>

    <p class="font-mono text-[0.7rem] text-slate-600">
      &copy; Coderra.je &middot; Pi IoT Academy
    </p>
  </div>
</template>
