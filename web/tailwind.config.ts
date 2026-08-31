import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        primary: "#7A1730",
        "primary-dark": "#5c1124",
      },
    },
  },
  plugins: [],
};

export default config;