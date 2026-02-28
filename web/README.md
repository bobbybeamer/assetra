# Assetra Web UI

Minimal React + TypeScript frontend scaffold for the Assetra backend API.

## Prerequisites

- Node.js 20+
- Backend API running at `http://127.0.0.1:8000` (or set custom base URL)

## Setup

```bash
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173.

## Environment

- `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`)

## Scripts

- `npm run dev` – start local dev server
- `npm run build` – type-check and build production assets
- `npm run preview` – preview production build
- `npm run lint` – run ESLint
