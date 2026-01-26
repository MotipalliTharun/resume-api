/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: "#2563EB",
                secondary: "#06B6D4",
                accent: "#F43F5E",
                light: {
                    bg: "#FFFFFF",
                    card: "#FFFFFF",
                    text: "#1E293B",
                    sub: "#64748B",
                    border: "#E2E8F0",
                },
                dark: {
                    bg: "#020617",
                    card: "rgba(255, 255, 255, 0.05)",
                    text: "#F1F5F9",
                    sub: "#94A3B8",
                    border: "rgba(255, 255, 255, 0.1)",
                },
            },
            fontFamily: {
                heading: ['Outfit', 'sans-serif'],
                sans: ['Inter', 'sans-serif'],
            },
            boxShadow: {
                'premium': '0 10px 40px -10px rgba(0, 0, 0, 0.05)',
                'glow': '0 0 20px rgba(139, 92, 246, 0.15)',
            },
        },
    },
    plugins: [],
}
