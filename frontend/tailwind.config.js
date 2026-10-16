/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#EEF1F4",
        card: "#FFFFFF",
        ink: { DEFAULT: "#14202B", soft: "#4B5B69", faint: "#8A97A3" },
        line: "#D5DCE3",
        signal: { DEFAULT: "#0F6E6E", dark: "#0A5252", tint: "#DDEFEE" },
        amber: { bar: "#E3A72F" },
        danger: { DEFAULT: "#B3261E", tint: "#FBE9E7" },
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['"Public Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
