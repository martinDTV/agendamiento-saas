export default defineAppConfig({
  ui: {
    colors: {
      primary:   'sage',
      secondary: 'slate',
      success:   'emerald',
      info:      'sky',
      warning:   'amber',
      error:     'red',
      neutral:   'slate'
    },
    // transition-transform da la curva al scale(0.97) de :active (main.css).
    // active:scale-[0.97] como fallback si el reset global no aplica al slot.
    button: {
      base: 'transition-transform duration-150 ease-out active:scale-[0.97]'
    }
  }
})
