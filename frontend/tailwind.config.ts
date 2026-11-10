import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        paper: 'var(--paper)',
        'paper-2': 'var(--paper-2)',
        'paper-edge': 'var(--paper-edge)',
        ink: 'var(--ink)',
        'ink-soft': 'var(--ink-soft)',
        vermilion: 'var(--vermilion)',
        indigo: 'var(--indigo)',
        gamboge: 'var(--gamboge)',
        moss: 'var(--moss)',
      },
      fontFamily: {
        display: ['"Instrument Serif"', 'Georgia', 'serif'],
        body: ['Karla', 'ui-sans-serif', 'sans-serif'],
      },
      transitionTimingFunction: {
        paper: 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
}

export default config
