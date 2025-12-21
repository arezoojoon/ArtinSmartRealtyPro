/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Premium Gold Palette
        gold: {
          50: '#FFF9E6',
          100: '#FFF3CC',
          200: '#FFE799',
          300: '#FFDB66',
          400: '#E5C365',
          500: '#D4AF37',
          600: '#C9A962',
          700: '#B8942D',
          800: '#8B7022',
          900: '#5E4C17',
          DEFAULT: '#D4AF37',
        },
        // Navy Dark Palette
        navy: {
          50: '#E8EBF0',
          100: '#C5CCD9',
          200: '#9BA8BE',
          300: '#7184A3',
          400: '#516A8F',
          500: '#31507B',
          600: '#2C4973',
          700: '#243F68',
          800: '#1A2E4A',
          900: '#0F1729',
          950: '#0A0F1A',
          DEFAULT: '#0F1729',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-gold': 'linear-gradient(135deg, #D4AF37 0%, #E5C365 100%)',
        'gradient-gold-dark': 'linear-gradient(135deg, #B8942D 0%, #D4AF37 100%)',
        'gradient-navy': 'linear-gradient(135deg, #0A0F1A 0%, #0F1729 50%, #1A2E4A 100%)',
      },
      boxShadow: {
        'gold': '0 4px 20px rgba(212, 175, 55, 0.15)',
        'gold-lg': '0 10px 40px rgba(212, 175, 55, 0.2)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-in': 'bounceIn 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'slide-up': 'slideUp 0.3s ease-out',
        'fade-in': 'fadeIn 0.4s ease-out',
      },
      keyframes: {
        bounceIn: {
          '0%': { opacity: '0', transform: 'translateY(100px) scale(0.8)' },
          '50%': { transform: 'translateY(-10px) scale(1.02)' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
}
