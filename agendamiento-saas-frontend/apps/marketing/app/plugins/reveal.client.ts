/**
 * GSAP-powered scroll animations.
 *
 * Provides:
 *   - v-reveal           → element fades + rises into view on scroll (ScrollTrigger).
 *                          v-reveal="120" adds a 120ms-equivalent stagger delay.
 *   - v-reveal-stagger   → animates the element's DIRECT CHILDREN in sequence.
 *   - v-count            → counts a number up when it enters view. v-count="549".
 *   - v-parallax         → subtle vertical parallax tied to scroll. v-parallax="40".
 *
 * Client-only: SSR renders content fully visible; GSAP only enhances on mount.
 * Fully disabled under prefers-reduced-motion.
 */
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

export default defineNuxtPlugin((nuxtApp) => {
  if (import.meta.server) return

  gsap.registerPlugin(ScrollTrigger)

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const app = nuxtApp.vueApp

  // ── v-reveal ────────────────────────────────────────────────────────────
  app.directive('reveal', {
    mounted(el: HTMLElement, binding) {
      if (prefersReduced) return
      const delay = (typeof binding.value === 'number' ? binding.value : 0) / 1000

      gsap.set(el, { opacity: 0, y: 28, scale: 0.97, willChange: 'transform, opacity' })
      gsap.to(el, {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.7,
        delay,
        ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 85%', once: true },
        onComplete: () => gsap.set(el, { clearProps: 'willChange' })
      })
    }
  })

  // ── v-reveal-stagger (animates direct children) ───────────────────────────
  app.directive('reveal-stagger', {
    mounted(el: HTMLElement, binding) {
      if (prefersReduced) return
      const children = Array.from(el.children) as HTMLElement[]
      if (!children.length) return
      const each = typeof binding.value === 'number' ? binding.value / 1000 : 0.1

      gsap.set(children, { opacity: 0, y: 32, scale: 0.96 })
      gsap.to(children, {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.7,
        ease: 'power3.out',
        stagger: each,
        scrollTrigger: { trigger: el, start: 'top 80%', once: true }
      })
    }
  })

  // ── v-count (number count-up) ─────────────────────────────────────────────
  app.directive('count', {
    mounted(el: HTMLElement, binding) {
      const target = typeof binding.value === 'number' ? binding.value : parseFloat(el.textContent || '0')
      const prefix = el.dataset.prefix || ''
      const suffix = el.dataset.suffix || ''
      if (prefersReduced) {
        el.textContent = `${prefix}${target}${suffix}`
        return
      }
      const obj = { v: 0 }
      gsap.to(obj, {
        v: target,
        duration: 1.4,
        ease: 'power2.out',
        scrollTrigger: { trigger: el, start: 'top 90%', once: true },
        onUpdate: () => {
          el.textContent = `${prefix}${Math.round(obj.v).toLocaleString('es-MX')}${suffix}`
        }
      })
    }
  })

  // ── v-parallax ────────────────────────────────────────────────────────────
  app.directive('parallax', {
    mounted(el: HTMLElement, binding) {
      if (prefersReduced) return
      const distance = typeof binding.value === 'number' ? binding.value : 30
      gsap.to(el, {
        y: distance,
        ease: 'none',
        scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: true }
      })
    }
  })

  // Recalculate positions after the layout settles (fonts, images).
  nuxtApp.hook('app:mounted', () => {
    requestAnimationFrame(() => ScrollTrigger.refresh())
  })
})
