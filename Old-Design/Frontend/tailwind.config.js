/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#020617', // Slate 950 - Deep dark background
        surface: '#0f172a', // Slate 900 - Card background
        primary: '#1e293b', // Slate 800 - UI Elements
        secondary: '#334155', // Slate 700 - Borders/Separators
        accent: '#ef4444', // Red 500 - Critical/Infection
        'accent-dim': '#7f1d1d', // Red 900 - Background for critical
        success: '#10b981', // Emerald 500 - Safe/Recovered
        text: '#f8fafc', // Slate 50 - Primary Text
        'text-dim': '#94a3b8', // Slate 400 - Secondary Text
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', "Liberation Mono", "Courier New", 'monospace'],
        display: ['ui-sans-serif', 'system-ui', 'sans-serif'], // For headers
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}

