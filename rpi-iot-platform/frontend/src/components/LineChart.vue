<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Filler,
} from 'chart.js'

/* Register only the bits we need — keeps the bundle smaller. We use a
   linear scale for the x-axis and treat timestamps as milliseconds, so
   no date adapter is needed. */
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Filler,
)

export interface ChartPoint {
  ts: string
  value: number
}

const props = defineProps<{
  points: ChartPoint[]
  unit: string
  color?: string
}>()

const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

function buildData() {
  const data = props.points.map((p) => ({
    x: new Date(p.ts).getTime(),
    y: p.value,
  }))
  const accent = props.color ?? '#9bd06a' /* pi-green-soft */
  return {
    datasets: [
      {
        data,
        borderColor: accent,
        backgroundColor: accent + '22',
        fill: true,
        tension: 0.25,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2,
      },
    ],
  }
}

function buildOptions() {
  const unit = props.unit
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false as const,
    interaction: { mode: 'nearest' as const, intersect: false },
    scales: {
      x: {
        type: 'linear' as const,
        ticks: {
          color: '#6b7480',
          maxTicksLimit: 5,
          callback: (v: number | string) => {
            const d = new Date(Number(v))
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
          },
        },
        grid: { color: '#2a313a' },
      },
      y: {
        ticks: { color: '#6b7480' },
        grid: { color: '#2a313a' },
        title: {
          display: true,
          text: unit,
          color: '#9aa4b1',
          font: { weight: 'bold' as const },
        },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0d1117',
        borderColor: '#3a424d',
        borderWidth: 1,
        titleColor: '#e6edf3',
        bodyColor: '#e6edf3',
        callbacks: {
          title: (items: { parsed: { x: number } }[]) => {
            return new Date(items[0].parsed.x).toLocaleTimeString()
          },
          label: (ctx: { parsed: { y: number } }) => {
            return `${ctx.parsed.y.toFixed(2)} ${unit}`
          },
        },
      },
    },
  }
}

function render() {
  if (!canvas.value) return
  if (chart) {
    chart.data = buildData() as Chart['data']
    chart.options = buildOptions() as Chart['options']
    chart.update('none')
    return
  }
  chart = new Chart(canvas.value, {
    type: 'line',
    data: buildData() as Chart['data'],
    options: buildOptions() as Chart['options'],
  })
}

onMounted(render)
watch(() => props.points, render, { deep: true })
watch(() => props.unit, render)
onBeforeUnmount(() => {
  if (chart) {
    chart.destroy()
    chart = null
  }
})
</script>

<template>
  <div class="relative w-full h-full min-h-[14rem]">
    <canvas ref="canvas" />
  </div>
</template>
