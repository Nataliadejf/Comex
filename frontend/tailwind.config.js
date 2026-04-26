/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {},
  },
  // Evita conflito com Ant Design no dashboard principal (Preflight reseta estilos de componentes).
  corePlugins: {
    preflight: false,
  },
  plugins: [],
};
