<script setup>
defineProps({
  // 'full' = isotipo en pastilla + wordmark en texto; 'mark' = solo isotipo en pastilla
  variant: {
    type: String,
    default: 'full',
    validator: v => ['full', 'mark'].includes(v)
  }
})
</script>

<template>
  <span class="inline-flex items-center gap-2.5">
    <span class="inline-flex items-center justify-center size-8 rounded-lg bg-white ring-1 ring-black/5">
      <img
        src="/brand/isotipo.png"
        alt="NexoSoftDev"
        class="size-6 object-contain select-none"
        draggable="false"
      >
    </span>
    <span
      v-if="variant === 'full'"
      class="text-[15px] font-medium tracking-tight text-highlighted"
    >
      Nexo<span class="text-primary">Soft</span>Dev
    </span>
  </span>
</template>
