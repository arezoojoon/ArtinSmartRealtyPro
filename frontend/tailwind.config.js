/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#0f1729',
          light: '#1a2744',
          lighter: '#243352',
        },
        gold: {
          DEFAULT: '#D4AF37',
          light: '#e6c84a',
        },
      },
    },
  },
  plugins: [],
}
