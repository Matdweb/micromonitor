/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#0f172a',
        'panel-bg': '#0f172a',
        'card-bg': '#0f2536',
        'accent': '#38bdf8',
        'accent-2': '#7dd3fc',
        'text-primary': '#e6eef8',
        'text-secondary': '#94a3b8',
      },
      fontFamily: {
        mono: ['"Fira Code"', 'ui-monospace', 'SFMono-Regular', 'monospace']
      }
    },
  },
  plugins: [],
};
