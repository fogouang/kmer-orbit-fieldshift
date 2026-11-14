import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

// Palette Field Shift : vert feuille #43aa5c (500), foret #164333, soleil #f8c32c.
// Les boutons et liens utilisent la nuance 600 : contraste 5:1 sur fond blanc (AA).
export const FieldShiftPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#effaf1',
      100: '#d9f1de',
      200: '#b4e2be',
      300: '#85cd96',
      400: '#5cbb72',
      500: '#43aa5c',
      600: '#2e7d43',
      700: '#266639',
      800: '#20522f',
      900: '#1b4428',
      950: '#0d2a1f',
    },
    colorScheme: {
      light: {
        primary: {
          color: '{primary.600}',
          contrastColor: '#ffffff',
          hoverColor: '{primary.700}',
          activeColor: '{primary.800}',
        },
      },
    },
  },
})