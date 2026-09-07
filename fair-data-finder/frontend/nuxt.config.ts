import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

export default defineNuxtConfig({
  imports: {
    autoImport: true,
  },
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  // Barlow is the font used by stars4water.eu; loaded here (rather than
  // self-hosted) to match how the rest of the app already pulls in
  // third-party CSS (see mapbox-gl below).
  app: {
    head: {
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&display=swap' },
      ],
    },
  },

  css: ['mapbox-gl/dist/mapbox-gl.css', '~/assets/css/theme.css'],
  build: {
    transpile: ['vuetify'],
  },
  modules: [
    '@pinia/nuxt',
    'nuxt-open-fetch',
    (_options, nuxt) => {
      nuxt.hooks.hook('vite:extendConfig', (config) => {
        // @ts-expect-error
        config.plugins.push(vuetify({ autoImport: true }))
      })
    }
  ],
  vite: {
    vue: {
      template: {
        transformAssetUrls, // To resolve relative asset URLs
      },
    },
  },

  // Every value below is resolved when the container starts, not when the
  // image is built, so the same image tag can be promoted between
  // environments. Defaults are the neutral "nothing configured" values.
  runtimeConfig: {
    // Server-only; never serialised into the browser payload.
    // Set per environment with NUXT_INTERNAL_API_BASE_URL.
    internalApiBaseUrl: '',

    // Serialised into the browser payload and visible in devtools.
    // Set per environment with NUXT_PUBLIC_*.
    public: {
      aboutTabEnabled: false,
      mapboxToken: '',
      // Opt-out flags: unset keeps the full Fair Data Finder behaviour.
      // Disable per environment with NUXT_PUBLIC_AUTH_ENABLED=false etc.
      authEnabled: true,
      registerTabEnabled: true,
      adminTabsEnabled: true,
    },
  },

  openFetch: {
    clients: {
      api: {
        // Read from the committed schema rather than fetched from a running
        // backend, so the build needs no network access and no deployment URL.
        // Refresh it with `npm run schema:update` when the API changes.
        schema: './openapi/api.json',
        baseURL: '/api',
      },
    },
  },

  nitro: {
    // Dev server only; Nitro drops this from production builds. It serves the
    // browser's relative /api calls while there is no nginx in front of Nuxt.
    // In production nginx owns /api, and SSR goes straight to the backend via
    // runtimeConfig.internalApiBaseUrl.
    devProxy: {
      '/api': {
        target: process.env.NUXT_INTERNAL_API_BASE_URL || 'http://localhost:8000/api',
        changeOrigin: true,
      },
    },
  },

})
