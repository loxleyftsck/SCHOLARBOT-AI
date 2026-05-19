/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#FAF6F0',
        surface: {
          DEFAULT: '#F5EFEB',
          raised: '#FDFCFA',
          overlay: '#F5EFEB',
        },
        walnut: {
          light: '#5C4535',
          DEFAULT: '#4A3728',
          muted: '#7A6250',
          dark: '#2C2417',
        },
        primary: {
          light: '#C49A3A',
          DEFAULT: '#8B6914',
          dark: '#6D5010',
        },
        secondary: '#4A7C6F',
        border: {
          DEFAULT: '#EADFCF',
          strong: '#C5BAB0',
        },
        divider: '#EAE2D8',
        text: {
          primary: '#1C1814',
          body: '#3D3632',
          muted: '#8A7F74',
          subtle: '#B5A99E',
        }
      },
      fontFamily: {
        serif: ['"DM Serif Display"', 'Georgia', 'serif'],
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        sm: '0 1px 3px rgba(44,36,23,0.05), 0 1px 2px rgba(44,36,23,0.03)',
        md: '0 2px 8px rgba(44,36,23,0.07), 0 1px 3px rgba(44,36,23,0.04)',
        lg: '0 4px 16px rgba(44,36,23,0.09), 0 2px 6px rgba(44,36,23,0.05)',
      }
    },
  },
  plugins: [],
}
