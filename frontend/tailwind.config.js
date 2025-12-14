/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // رنگهای سفارشی طرح لوکس
        navy: {
          DEFAULT: '#0f1729',
          light: '#1a2744',
          lighter: '#243352',
          800: '#1a2236', // رنگ پسزمینه کارتها (کمی روشنتر)
          900: '#0f1729', // رنگ پسزمینه اصلی (سرمهای عمیق)
        },
        gold: {
          DEFAULT: '#D4AF37',
          light: '#e6c84a',
          400: '#E5C365', // طلایی روشن برای هاور
          500: '#D4AF37', // طلایی اصلی (متالیک)
          600: '#B8962E', // طلایی تیرهتر برای سایه/بوردر
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'], // فونت مدرن پیشنهادی
      }
    },
  },
  plugins: [],
}
