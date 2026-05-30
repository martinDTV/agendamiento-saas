<script setup>
/**
 * Cursor-following spotlight backdrop.
 *
 * A soft navy/violet glow tracks the pointer across the hero, over a faint
 * dotted field that gives the light something to play against. The position is
 * driven by CSS custom properties updated on pointermove (rAF-throttled).
 *
 * Honors prefers-reduced-motion: the glow parks at center and stops tracking.
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'

const root = ref(null)

onMounted(() => {
  const el = root.value
  if (!el) return

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    el.style.setProperty('--x', '50%')
    el.style.setProperty('--y', '38%')
    return
  }

  let raf = 0
  let tx = 50
  let ty = 38
  let cx = 50
  let cy = 38

  const onMove = (e) => {
    const r = el.getBoundingClientRect()
    tx = ((e.clientX - r.left) / r.width) * 100
    ty = ((e.clientY - r.top) / r.height) * 100
    if (!raf) raf = requestAnimationFrame(tick)
  }

  const tick = () => {
    // Ease toward the target so the light glides rather than snaps.
    cx += (tx - cx) * 0.12
    cy += (ty - cy) * 0.12
    el.style.setProperty('--x', `${cx}%`)
    el.style.setProperty('--y', `${cy}%`)
    if (Math.abs(tx - cx) > 0.1 || Math.abs(ty - cy) > 0.1) {
      raf = requestAnimationFrame(tick)
    } else {
      raf = 0
    }
  }

  window.addEventListener('pointermove', onMove, { passive: true })
  onBeforeUnmount(() => {
    window.removeEventListener('pointermove', onMove)
    if (raf) cancelAnimationFrame(raf)
  })
})
</script>

<template>
  <div ref="root" class="spotlight" aria-hidden="true">
    <div class="dots" />
    <div class="glow" />
  </div>
</template>

<style scoped>
.spotlight {
  --x: 50%;
  --y: 38%;
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

/* Faint dotted field for the light to reveal. */
.dots {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(
    color-mix(in oklch, var(--color-navy-600) 14%, transparent) 1px,
    transparent 1px
  );
  background-size: 26px 26px;
  -webkit-mask-image: radial-gradient(120% 90% at 50% 30%, #000 50%, transparent 100%);
  mask-image: radial-gradient(120% 90% at 50% 30%, #000 50%, transparent 100%);
}

/* The travelling glow: two stacked radial gradients, navy core + violet halo. */
.glow {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(
      420px circle at var(--x) var(--y),
      color-mix(in oklch, var(--color-violet-400) 26%, transparent),
      transparent 60%
    ),
    radial-gradient(
      640px circle at var(--x) var(--y),
      color-mix(in oklch, var(--color-navy-400) 20%, transparent),
      transparent 65%
    );
  transition: background 0.08s linear;
}

@media (prefers-reduced-motion: reduce) {
  .glow {
    transition: none;
  }
}
</style>
