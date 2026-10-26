/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gqt: {
          navy: {
            DEFAULT: '#001B4D',
            dark: '#001030',
            light: '#0A2A66',
          },
          blue: {
            DEFAULT: '#005BBB',
            vivid: '#0066CC',
            light: '#E6F0FA',
            accent: '#00D2FF',
          },
          charcoal: {
            DEFAULT: '#1E293B',
            dark: '#0F172A',
            muted: '#334155',
          },
          neutral: {
            50: '#F8FAFC',
            100: '#F1F5F9',
            200: '#E2E8F0',
            300: '#CBD5E1',
            400: '#94A3B8',
            500: '#64748B',
            600: '#475569',
            700: '#334155',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
