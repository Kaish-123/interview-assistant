import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme inspired by VS Code
        'dark': {
          '50': '#f7f7f8',
          '100': '#ececf1',
          '200': '#d9d9e3',
          '300': '#c5c5d2',
          '400': '#acacbe',
          '500': '#8e8ea0',
          '600': '#565869',
          '700': '#40414f',
          '800': '#343541',
          '900': '#202123',
          '950': '#0d0d0f',
        },
        // Accent colors
        'accent': {
          'blue': '#3b82f6',
          'green': '#10b981',
          'amber': '#f59e0b',
          'red': '#ef4444',
          'purple': '#8b5cf6',
          'cyan': '#06b6d4',
        }
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        'sans': ['Inter', 'SF Pro Display', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'recording': 'recording 1.5s ease-in-out infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
      },
      keyframes: {
        recording: {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.1)', opacity: '0.7' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

export default config





