/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,jsx,ts,tsx}', './src/**/*.{js,jsx,ts,tsx}'],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        // Paleta NexoSoftDev — azul marino del isotipo (#15263F).
        // Escala construida alrededor del 600 (color real del logo).
        // El 700 es ligeramente más oscuro/saturado para estados pressed.
        brand: {
          50: '#F0F4F9',
          100: '#D9E1EC',
          200: '#B3C4D9',
          300: '#7E97B8',
          400: '#4D6B92',
          500: '#2C4870',
          600: '#15263F',  // ← color del logo
          700: '#0F1F3D',
          800: '#0A1830',
          900: '#060F1E',
        },
      },
      fontFamily: {
        sans: ['Inter_400Regular', 'System'],
        medium: ['Inter_500Medium', 'System'],
        semibold: ['Inter_600SemiBold', 'System'],
        bold: ['Inter_700Bold', 'System'],
      },
    },
  },
  plugins: [],
};
