/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Teal green. 'leaf' keeps its semantic name so no component needs touching.
        leaf:   { DEFAULT: '#0F8A72', dark: '#0A5A4A', light: '#5FCBB0', mist: '#E2F5F0' },
        grain:  { DEFAULT: '#F5B301', dark: '#D69A00' },
        soil:   { DEFAULT: '#4F5D58', dark: '#2C3835', light: '#8A9A94' },
        field:  '#F2F7F5',
        danger: '#C62828',
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', 'Noto Sans', 'Noto Sans Telugu', 'Noto Sans Devanagari', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(10,90,74,.07), 0 8px 24px -12px rgba(10,90,74,.24)',
        lift: '0 12px 32px -12px rgba(15,138,114,.38)',
      },
      screens: { xs: '375px', '3xl': '1920px' },
      keyframes: {
        sprout: { '0%': { transform: 'scaleY(.2)', opacity: '0' }, '100%': { transform: 'scaleY(1)', opacity: '1' } },
        drift:  { '0%': { transform: 'translate3d(0,-12vh,0) rotate(0deg)' }, '100%': { transform: 'translate3d(0,112vh,0) rotate(300deg)' } },
        flutter:{ '0%,100%': { transform: 'translateX(-26px)' }, '50%': { transform: 'translateX(26px)' } },
        sway:   { '0%,100%': { transform: 'rotate(-3deg)' }, '50%': { transform: 'rotate(3deg)' } },
        rain:   { '0%': { transform: 'translateY(-20%)', opacity: '0' }, '30%': { opacity: '.7' }, '100%': { transform: 'translateY(120%)', opacity: '0' } },
      },
      animation: {
        sprout: 'sprout .7s cubic-bezier(.2,.8,.2,1) both',
        drift: 'drift linear infinite',
        sway: 'sway 4s ease-in-out infinite',
        flutter: 'flutter ease-in-out infinite alternate',
        rain: 'rain 1.1s linear infinite',
      },
    },
  },
  plugins: [],
}
