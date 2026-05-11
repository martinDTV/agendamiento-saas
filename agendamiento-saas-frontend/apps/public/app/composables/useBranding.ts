/**
 * Public site branding — applies the tenant's primary color to the sage palette.
 */

function hexToHsl(hex: string): [number, number, number] {
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0, 2), 16) / 255
  const g = parseInt(h.slice(2, 4), 16) / 255
  const b = parseInt(h.slice(4, 6), 16) / 255
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let hue = 0, sat = 0
  const lit = (max + min) / 2
  if (max !== min) {
    const d = max - min
    sat = lit > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case r: hue = (g - b) / d + (g < b ? 6 : 0); break
      case g: hue = (b - r) / d + 2; break
      case b: hue = (r - g) / d + 4; break
    }
    hue /= 6
  }
  return [hue * 360, sat * 100, lit * 100]
}

function hslToHex(h: number, s: number, l: number): string {
  const lN = l / 100
  const a = (s * Math.min(lN, 1 - lN)) / 100
  const f = (n: number) => {
    const k = (n + h / 30) % 12
    const c = lN - a * Math.max(Math.min(k - 3, 9 - k, 1), -1)
    return Math.round(255 * c).toString(16).padStart(2, '0')
  }
  return `#${f(0)}${f(8)}${f(4)}`
}

const SHADES: Record<string, number> = {
  '50': 96, '100': 92, '200': 84, '300': 73, '400': 60,
  '500': 48, '600': 39, '700': 31, '800': 24, '900': 18, '950': 11,
}

export function useBranding() {
  const tenant = useTenantStore()

  watch(
    () => tenant.tenant?.settings?.branding?.primaryColor,
    (color) => {
      if (!color || !import.meta.client) return
      if (!/^#[0-9A-Fa-f]{6}$/.test(color)) return
      const [h, s] = hexToHsl(color)
      const sat = Math.max(25, Math.min(70, s))
      const root = document.documentElement
      for (const [shade, lit] of Object.entries(SHADES)) {
        const hex = hslToHex(h, sat, lit)
        root.style.setProperty(`--color-sage-${shade}`, hex)
        root.style.setProperty(`--ui-color-primary-${shade}`, hex)
      }
      root.style.setProperty('--ui-primary', hslToHex(h, sat, SHADES['500']))
    },
    { immediate: true },
  )
}
