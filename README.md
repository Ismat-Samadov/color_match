# ColorMatch 🎨

A fast-paced, mobile-friendly color matching game built with **Next.js 16**, **React 19**, and **Tailwind CSS 4**.

## Gameplay

Race against a 10-second timer to match colors correctly. Three wrong answers (or timeouts) end the game. Chain correct answers to earn score multipliers.

| Streak | Multiplier |
|--------|-----------|
| 1–2    | ×1        |
| 3–5    | ×2        |
| 6+     | ×3        |

## Game Modes

| Mode    | Challenge |
|---------|-----------|
| **Classic** | See a color swatch → pick the correct name |
| **Reverse** | See a color name → find the matching swatch |
| **Mixed**   | Random mix of Classic and Reverse |
| **Stroop**  | See a name written in a *different* color → find the correct swatch (ignore the text color!) |

## Features

- 30 named colors across the full spectrum
- Per-mode high scores persisted in `localStorage`
- Animated timer bar with color urgency cues
- Correct / wrong / timeout feedback with animations
- Fully responsive — works great on mobile and desktop
- Dark, vibrant UI with a custom SVG favicon

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Build for Production

```bash
npm run build
npm start
```

## Tech Stack

- [Next.js 16](https://nextjs.org) — App Router
- [React 19](https://react.dev)
- [Tailwind CSS 4](https://tailwindcss.com)
- TypeScript
