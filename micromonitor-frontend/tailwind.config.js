/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: "#0d1117",
          text: "#c9d1d9",
          accent: "#58a6ff",
          danger: "#f85149",
          success: "#3fb950",
          warning: "#d29922"
        }
      },
      fontFamily: {
        mono: ['"Fira Code"', 'monospace']
      }
    },
  },
  plugins: [],
}
