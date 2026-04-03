/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aegis: {
          dark: '#0f172a',    // Slate 900 - Main backgrounds
          card: '#17233a',    // Deep slate - card backgrounds
          primary: '#38bdf8', // Sky 400 - Primary buttons/accents
          primaryDark: '#0ea5e9',
          success: '#22c55e', // Emerald 500 - Healthy status
          danger: '#f87171',  // Red 400 - Alerts/Threats
          text: '#e2e8f0',    // Slate 200 - Standard text
          muted: '#94a3b8',   // Slate 400 - Secondary text
          accent: '#7c3aed',  // Violet accent
        }
      },
      boxShadow: {
        aet: '0 20px 45px rgba(15, 23, 42, 0.35)',
      },
      backgroundImage: {
        'aegis-glow': 'radial-gradient(circle at top left, rgba(56, 189, 248, 0.24), transparent 32%), radial-gradient(circle at bottom right, rgba(124, 58, 237, 0.16), transparent 28%)',
      },
    },
  },
  plugins: [],
}
