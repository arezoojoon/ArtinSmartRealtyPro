/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // رنگ‌های سفارشی طرح لوکس
        navy: {
          50: '#f0f1f9',
          100: '#e1e4f3',
          200: '#c3c9e7',
          300: '#a5aedb',
          400: '#8793cf',
          500: '#6978c3',
          600: '#4b5db7',
          700: '#3a4a8f',
          800: '#1a2236', // کارت‌ها (کمی روشن‌تر)
          900: '#0f1729', // پس‌زمینه اصلی (سرمه‌ای عمیق)
        },
        gold: {
          50: '#fdfbf7',
          100: '#fbf7ef',
          200: '#f7efdf',
          300: '#f3e7cf',
          400: '#E5C365', // طلایی روشن برای هاور
          500: '#D4AF37', // طلایی اصلی (متالیک)
          600: '#B8962E', // طلایی تیره‌تر
          700: '#a18527',
          800: '#7e6b1f',
          900: '#5b5117',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-navy': 'linear-gradient(135deg, #0f1729 0%, #1a2742 100%)',
        'gradient-gold': 'linear-gradient(135deg, #D4AF37 0%, #F4D03F 100%)',
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(212, 175, 55, 0.1)',
        'gold': '0 8px 24px rgba(212, 175, 55, 0.3)',
      },
    },
  },
  plugins: [],
}
