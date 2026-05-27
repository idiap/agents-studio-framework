// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          dark: "#1F3257",
          main: "#4DB1DD",
          light: "#69C3E2",
          extralight: "#80CAE4",
        },
        button: {
          gradient:
            "linear-gradient(90deg, #4DB1DD 0%, #4DB1DD 24%, #69C3E2 100%)",
          hovered: "linear-gradient(90deg, #24C8E2 0%, #3AA8B4 100%)",
        },
        text: {
          primary: {
            DEFAULT: "#0D181C",
            dark: "#FFFFFF",
          },
          secondary: {
            DEFAULT: "#0D181C99",
            dark: "#FFFFFFB2",
          },
          disabled: {
            DEFAULT: "#0D181C4D",
            dark: "#FFFFFF4D",
          },
        },
        background: {
          footer: "#0D181C",
          default: {
            light: "#FFFFFF",
            dark: "#0D181C",
          },
          highlight: {
            light: "#FAFAFA",
            dark: "#0A1215",
          },
        },
        header: {
          light: "#FFFFFFCC",
          dark: "#0D181CCC",
        },
        white: {
          100: "#FFFFFF",
          60: "#FFFFFF99",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        heading: ["Kantumruy Pro", "sans-serif"],
      },
      fontSize: {
        slogan: ["80px", { lineHeight: "normal" }],
        "slogan-sm": ["45px", { lineHeight: "normal" }],
        title: ["60px", { lineHeight: "normal" }],
        "title-sm": ["32px", { lineHeight: "normal" }],
        "smaller-title": ["40px", { lineHeight: "normal" }],
        "smaller-title-sm": ["30px", { lineHeight: "normal" }],
        subtitle: ["24px", { lineHeight: "normal" }],
        "subtitle-sm": ["20px", { lineHeight: "normal" }],
        body: ["16px", { lineHeight: "24px" }], // 133.333%
        "body-sm": ["16px", { lineHeight: "24px" }], // 150%
        details: ["15px", { lineHeight: "24px" }], // 160%
        "details-sm": ["14px", { lineHeight: "24px" }], // 171.429%
        link: ["15px", { lineHeight: "15px" }], // 100%
      },
      fontWeight: {
        normal: "400",
        medium: "500",
        semibold: "600",
        bold: "700",
      },
      boxShadow: {
        "custom-soft": "0px 4px 20px 0px rgba(30, 50, 87, 0.1)",
      },
    },
  },
  plugins: [
    // ...
  ],
  corePlugins: {
    preflight: false, // <== disable this!
  },
};
