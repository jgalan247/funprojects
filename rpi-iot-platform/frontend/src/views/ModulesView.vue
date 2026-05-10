<script setup lang="ts">
import ModuleTile from '../components/ModuleTile.vue'

/* Phase 7 will populate this from /api/modules. For Phase 5 we show what's
   coming so students see the slot. */
const placeholderModules = [
  {
    id: 'classroom-sensor-hub',
    title: 'Classroom Sensor Hub',
    description: 'Live readings from Micro:bit and ESP32 boards in your classroom, with AI explanations.',
    badge: 'Phase 7',
    disabled: true,
  },
  {
    id: 'weather-station',
    title: 'Weather Station',
    description: 'Outdoor temperature, humidity, and pressure tracked over weeks.',
    badge: 'Future',
    disabled: true,
  },
  {
    id: 'greenhouse-monitor',
    title: 'Greenhouse Monitor',
    description: 'Soil moisture, light levels, and watering alerts.',
    badge: 'Future',
    disabled: true,
  },
]
</script>

<template>
  <div class="p-6 max-w-6xl mx-auto">

    <p class="text-slate-400 text-sm mb-6 max-w-prose">
      Modules are self-contained classroom projects that plug into the
      platform. Each one brings its own sensors, dashboard tiles, and
      lesson plan. None are installed yet — your first one ships in
      Phase&nbsp;7.
    </p>

    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <ModuleTile
        v-for="m in placeholderModules"
        :key="m.id"
        :title="m.title"
        :description="m.description"
        :badge="m.badge"
        :disabled="m.disabled"
        @open="() => {}"
      />
    </section>
  </div>
</template>
