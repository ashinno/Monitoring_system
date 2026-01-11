/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        cyber: {
          900: '#020617',
          800: '#0f172a',
          700: '#1e293b',
          500: '#06b6d4', // Cyan-500
          400: '#22d3ee', // Cyan-400
          accent: '#f43f5e', // Rose-500
        }
      },
      boxShadow: {
        'neon': '0 0 10px rgba(34, 211, 238, 0.5), 0 0 20px rgba(34, 211, 238, 0.3)',
        'neon-red': '0 0 10px rgba(244, 63, 94, 0.5), 0 0 20px rgba(244, 63, 94, 0.3)',
      }
    }
  },
  plugins: [],
}
