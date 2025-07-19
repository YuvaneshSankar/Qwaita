// tailwind.config.js
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      animation: {
        'ping-slow': 'ping 4s cubic-bezier(0, 0, 0.2, 1) infinite',
        'border-pulse': 'pulseBorder 2s infinite',
      },
      keyframes: {
        pulseBorder: {
          '0%, 100%': { boxShadow: '0 0 10px #a855f7' },
          '50%': { boxShadow: '0 0 20px #9333ea' },
        },
      },
    },
  },
  plugins: [],
};
