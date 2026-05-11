<script setup lang="ts">
const model = defineModel<string>({ required: true })
const open = ref(false)

const SUGGESTED = [
  'i-lucide-calendar-heart', 'i-lucide-calendar-plus', 'i-lucide-calendar-days', 'i-lucide-calendar-check',
  'i-lucide-clock', 'i-lucide-mail', 'i-lucide-phone', 'i-lucide-shield-check',
  'i-lucide-check', 'i-lucide-check-circle-2', 'i-lucide-clipboard-list', 'i-lucide-clipboard-check',
  'i-lucide-stethoscope', 'i-lucide-heart-pulse', 'i-lucide-activity', 'i-lucide-pill',
  'i-lucide-syringe', 'i-lucide-user-round', 'i-lucide-users', 'i-lucide-baby',
  'i-lucide-sparkles', 'i-lucide-star', 'i-lucide-award', 'i-lucide-badge-check',
  'i-lucide-map-pin', 'i-lucide-building-2', 'i-lucide-home', 'i-lucide-info',
  'i-lucide-bell', 'i-lucide-message-circle', 'i-lucide-thumbs-up', 'i-lucide-zap',
] as const

function pick(name: string) {
  model.value = name
  open.value = false
}
</script>

<template>
  <div class="relative">
    <div class="flex gap-2 items-center">
      <button
        type="button"
        class="w-10 h-10 flex items-center justify-center rounded-lg border border-slate-300 bg-white hover:border-sage-500 transition-colors flex-shrink-0"
        @click="open = !open"
      >
        <UIcon :name="model || 'i-lucide-image'" class="w-5 h-5 text-sage-600" />
      </button>
      <UInput v-model="model" class="flex-1 font-mono text-xs" placeholder="i-lucide-..." />
    </div>

    <div
      v-if="open"
      class="absolute z-30 mt-2 w-80 max-h-72 overflow-y-auto bg-white rounded-xl border border-slate-200 shadow-lg p-3"
    >
      <p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-2">Sugeridos</p>
      <div class="grid grid-cols-8 gap-1.5">
        <button
          v-for="name in SUGGESTED"
          :key="name"
          type="button"
          class="aspect-square flex items-center justify-center rounded-md hover:bg-sage-100 transition-colors"
          :class="model === name ? 'bg-sage-100 ring-1 ring-sage-500' : ''"
          :title="name"
          @click="pick(name)"
        >
          <UIcon :name="name" class="w-4 h-4 text-slate-700" />
        </button>
      </div>
      <p class="text-[10px] text-slate-400 mt-3 leading-tight">
        Puedes escribir cualquier icono Lucide en el input. Lista completa en
        <a href="https://lucide.dev/icons" target="_blank" class="text-sage-600 underline">lucide.dev/icons</a>
        — usa el formato <code>i-lucide-nombre</code>.
      </p>
    </div>
  </div>
</template>
