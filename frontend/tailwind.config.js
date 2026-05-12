/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Outfit', 'sans-serif'],
        mono: ['Space Mono', 'monospace'],
      },
      colors: {
        sentinel: {
          bg: '#020617',
          panel: 'rgba(15, 23, 42, 0.72)',
          cyan: '#22d3ee',
          green: '#22c55e',
          blue: '#3b82f6',
          purple: '#a855f7',
          orange: '#f97316',
          red: '#ef4444',
        },
      },
      boxShadow: {
        glow: '0 0 34px rgba(34, 211, 238, 0.28)',
        greenGlow: '0 0 34px rgba(34, 197, 94, 0.25)',
        redGlow: '0 0 34px rgba(239, 68, 68, 0.30)',
      },
      keyframes: {
        scan: { '0%': { transform: 'translateY(-20%)' }, '100%': { transform: 'translateY(120%)' } },
        pulseGlow: { '0%, 100%': { opacity: '.45' }, '50%': { opacity: '1' } },
        roadFlow: { '0%': { transform: 'translateY(0)' }, '100%': { transform: 'translateY(46px)' } },
        float: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-12px)' } },
        drive: { '0%': { transform: 'translateY(140%)' }, '100%': { transform: 'translateY(-180%)' } },
      },
      animation: {
        scan: 'scan 3.8s linear infinite',
        pulseGlow: 'pulseGlow 2.4s ease-in-out infinite',
        roadFlow: 'roadFlow 1.3s linear infinite',
        float: 'float 6s ease-in-out infinite',
        drive: 'drive 5.5s linear infinite',
      },
    },
  },
  plugins: [],
};
