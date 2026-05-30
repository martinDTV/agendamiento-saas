<script setup>
/**
 * Browser-window chrome around a product screenshot.
 *
 * The raw screenshots include their own browser bar (with an internal dev
 * domain). We hide that by clipping the top of the image and drawing our own
 * chrome with the real public domain.
 */
defineProps({
  src: { type: String, required: true },
  alt: { type: String, default: '' },
  // Public domain shown in the fake address bar.
  url: { type: String, default: 'tuconsultorio.agendamiento.nexosoftdev.com' },
  // How much of the screenshot's own top bar to clip away (px of the source).
  clipTop: { type: Number, default: 48 }
})
</script>

<template>
  <div class="overflow-hidden rounded-2xl border border-default bg-default shadow-xl">
    <!-- Our chrome -->
    <div class="flex items-center gap-1.5 border-b border-default bg-elevated/50 px-4 py-3">
      <span class="size-2.5 rounded-full bg-error/60" />
      <span class="size-2.5 rounded-full bg-warning/60" />
      <span class="size-2.5 rounded-full bg-success/60" />
      <span class="ml-3 inline-flex items-center gap-1.5 truncate text-xs text-muted">
        <UIcon name="i-lucide-lock" class="size-3" />
        {{ url }}
      </span>
    </div>
    <!-- Screenshot, with its own bar clipped off the top -->
    <div class="overflow-hidden">
      <img
        :src="src"
        :alt="alt"
        class="w-full select-none"
        :style="{ marginTop: `-${clipTop}px` }"
        draggable="false"
        loading="lazy"
      >
    </div>
  </div>
</template>
