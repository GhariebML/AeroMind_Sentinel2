# AeroMind Sentinel Frontend

Premium React/Vite/Tailwind frontend for **AeroMind Sentinel — AI-Powered Smart Highway Monitoring & Emergency Response System**.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open the Vite localhost URL shown in the terminal, usually `http://localhost:5173`.

## Production build

```bash
npm run lint
npm run build
npm run preview
```

## Python inference integration

The simulation can consume Python backend events from:

```text
/api/highway/events
```

Local Vite automatically proxies `/api` to `http://localhost:5000`. For deployed frontend/backend separation, set:

```text
VITE_SENTINEL_API_URL=https://your-backend-url
```

Then use the **Python Events** toggle inside the simulation.

## Real highway video background mode

The simulation includes a **Video BG** toggle. Add real footage here:

```text
public/videos/highway-demo.mp4
```

If the video is missing, the simulation automatically falls back to the animated highway canvas.

## Judge / demo mode

Use the **Judge Mode** button in the simulation. It auto-plays through all scenarios every few seconds.

## Pitch deck PDF export

Open:

```text
/pitch
```

Click **Export PDF**, then choose **Save as PDF** in the browser print dialog.

## Capture deployed Vercel screenshots

After deployment:

```bash
npm run capture:screenshots -- --url https://your-vercel-url.vercel.app
```

Screenshots are saved to:

```text
docs/screenshots/
```

## Vercel deployment

Deploy this `frontend/` directory as the Vercel project root.

- Framework: Vite
- Build command: `npm run build`
- Output directory: `dist`

`frontend/vercel.json` is included for SPA rewrites.
