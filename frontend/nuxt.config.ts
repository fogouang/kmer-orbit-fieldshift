import tailwindcss from "@tailwindcss/vite";
import { FieldShiftPreset } from "./app/utils/theme";

export default defineNuxtConfig({
  compatibilityDate: "2026-10-01",
  ssr: false, // outil interactif : rendu cote client (carte, graphiques)
  devtools: { enabled: false },

  modules: ["@primevue/nuxt-module", "@nuxtjs/i18n"],
  css: [
    "~/assets/css/main.css",
    "primeicons/primeicons.css",
    "leaflet/dist/leaflet.css",
  ],

  vite: {
    plugins: [tailwindcss()],
  },

  primevue: {
    options: {
      theme: {
        preset: FieldShiftPreset,
        options: {
          darkModeSelector: ".fs-dark",
          cssLayer: { name: "primevue", order: "theme, base, primevue" },
        },
      },
    },
  },

  // Francais par defaut sur /, anglais sur /en (jury international de la NASA)
  i18n: {
    defaultLocale: "fr",
    strategy: "prefix_except_default",
    locales: [
      { code: "fr", language: "fr-FR", name: "Français", file: "fr.json" },
      { code: "en", language: "en-US", name: "English", file: "en.json" },
    ],
    // Un navigateur en anglais arrive directement sur /en (une seule fois, puis le choix est memorise)
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: "fieldshift_langue",
      redirectOn: "root",
    },
  },
  runtimeConfig: {
    public: {
      // URL de l'API FastAPI (surchargeable avec NUXT_PUBLIC_API_BASE)
      apiBase: "http://127.0.0.1:8000/api/v1",
    },
  },

  app: {
    head: {
      htmlAttrs: { lang: "fr" },
      title: "Field Shift : rotations de cultures et données NASA",
      meta: [
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        {
          name: "description",
          content:
            "Comparer des rotations de cultures adaptées au climat et au sol de sa parcelle, à partir des données d'observation de la Terre de la NASA.",
        },
      ],
      link: [
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        {
          rel: "preconnect",
          href: "https://fonts.gstatic.com",
          crossorigin: "",
        },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&display=swap",
        },
      ],
    },
  },
});
