<script setup lang="ts">
defineProps<{
  title: string
  description: string
  badge?: string
  disabled?: boolean
}>()
defineEmits<{ open: [] }>()
</script>

<template>
  <button
    type="button"
    class="w-full text-left rounded-2xl border bg-slate-800/60 backdrop-blur p-6 min-h-[8rem] transition-all active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-pi-green disabled:opacity-50 disabled:cursor-not-allowed"
    :class="disabled ? 'border-slate-700' : 'border-slate-700 hover:border-pi-red'"
    :disabled="disabled"
    @click="$emit('open')"
  >
    <div class="flex justify-between items-start mb-2">
      <h3 class="text-lg font-extrabold tracking-tight">{{ title }}</h3>
      <span
        v-if="badge"
        class="shrink-0 text-[0.7rem] px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 font-bold uppercase tracking-wider"
      >
        {{ badge }}
      </span>
    </div>
    <p class="text-sm text-slate-400 leading-relaxed">{{ description }}</p>
  </button>
</template>
