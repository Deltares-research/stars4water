// import this after install `@mdi/font` package
import '@mdi/font/css/materialdesignicons.css'

import 'vuetify/styles'
import { createVuetify } from 'vuetify'

export default defineNuxtPlugin((app) => {
  const vuetify = createVuetify({
    // Vuetify components measure the viewport internally (v-app-bar,
    // v-data-table, v-dialog). Without this the server assumes a desktop
    // viewport and the client re-measures, causing hydration mismatches.
    ssr: true,
    theme: {
      defaultTheme: 'light',
      themes: {
        // Overrides the built-in Vuetify "light" theme with the
        // STARS4Water palette; unspecified tokens (error, success, ...)
        // keep Vuetify's defaults.
        light: {
          colors: {
            background: '#F8FAFC',
            surface: '#FFFFFF',
            primary: '#005AA9',
            secondary: '#27B6D6',
            'on-background': '#1F2937',
            'on-surface': '#1F2937',
          },
        },
      },
    },
  })
  app.vueApp.use(vuetify)
})
