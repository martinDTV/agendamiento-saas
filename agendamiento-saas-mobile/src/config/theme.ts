/**
 * Constantes de tema accesibles desde TS — para componentes que NO pueden usar
 * Tailwind/Nativewind (ActivityIndicator, Ionicons, tabBarActiveTintColor, etc.).
 *
 * Mantener en sync con `tailwind.config.js` → `theme.extend.colors.brand`.
 */
export const BRAND = {
  50: '#F0F4F9',
  100: '#D9E1EC',
  200: '#B3C4D9',
  300: '#7E97B8',
  400: '#4D6B92',
  500: '#2C4870',
  600: '#15263F', // color real del logo NexoSoftDev
  700: '#0F1F3D',
  800: '#0A1830',
  900: '#060F1E',
} as const;

// Alias semánticos
export const COLORS = {
  brand: BRAND[600],
  brandPressed: BRAND[700],
  brandLight: BRAND[100],
  brandDark: BRAND[800],
  // Slate (de Tailwind por defecto, repetido para uso fuera de className)
  slate400: '#94A3B8',
  slate500: '#64748B',
  slate700: '#334155',
  slate900: '#0F172A',
  white: '#FFFFFF',
} as const;
