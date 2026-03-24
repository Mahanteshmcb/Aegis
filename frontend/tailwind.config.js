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
          card: '#1e293b',    // Slate 800 - Card backgrounds
          primary: '#3b82f6', // Blue 500 - Primary buttons/accents
          success: '#10b981', // Emerald 500 - Healthy status
          danger: '#ef4444',  // Red 500 - Alerts/Threats
          text: '#f8fafc',    // Slate 50 - Standard text
          muted: '#94a3b8',   // Slate 400 - Secondary text
        }
      }
    },
  },
  plugins: [],
}
