# SafePath AI — Hackwell 2.0 / Smart Cities

> **Not just the fastest route — the safest explainable route.**

SafePath AI is a demo-ready, safety-first routing prototype for travellers and trusted guardians. **Safety Scores are estimates from available data; SafePath AI does not guarantee safety or prevent crime.**

## Status
| Feature | Status |
| --- | --- |
| Authentication, route comparison, trip/SOS REST APIs | Implemented demo MVP |
| Map tiles, persistent PostGIS/Redis state, guardian live dashboard | Prototype wiring / planned persistence |
| Scikit-learn model trained on pilot labels | Proposed — no accuracy claim is made |

## Architecture
```text
React + TypeScript (browser) -> FastAPI /api/v1 -> PostgreSQL/PostGIS + Redis
                             -> ORS / Nominatim / Overpass (backend only)
```

The browser talks only to the API. MapTiler's browser key is the sole permitted browser key. In this MVP, in-memory demo state makes the app immediately runnable; the `docker-compose` topology includes the production-targeted PostGIS and Redis services.

## Quick start
```bash
cp .env.example .env
docker compose up --build
# in another terminal
make seed
```
Open `http://localhost:5173`, create an account, and use **Compare safe routes**. API docs: `http://localhost:8000/docs`.

## Frontend–backend connection
The React application calls the FastAPI service exclusively through `VITE_API_URL`; it never calls PostGIS, Redis, or third-party map/routing services from the browser. For local development, copy `frontend/.env.example` to `frontend/.env` and keep its localhost URL. For a hosted frontend, set `VITE_API_URL` in that platform's environment settings to the deployed backend's `/api/v1` URL. `VITE_` variables are public build-time values, so never put API keys, JWT secrets, SMTP credentials, or database URLs in them.

## Three-minute demo
1. Register a traveller account and compare Demo Campus Gate to Metro Station.
2. Contrast the **Fastest route (41)** with its unlit stretch against the **Recommended safest route (88)** with lamps, shops, and a nearby police booth.
3. Start the recommended trip, record a check-in, then press **SOS** to demonstrate escalation.

## Safety score (transparent baseline)
`0.30 lighting + 0.25 incident + 0.20 crowd + 0.15 emergency proximity + 0.10 traffic exposure`; route scores are intended to be length-weighted segment means in the persistent scoring service. Missing lighting data uses a neutral score and `low_data`, never an assumed-dark value. Incident data is reports-only until a legitimate local source is configured.

## Keys and limitations
Set `ORS_API_KEY` from OpenRouteService, `MAPTILER_KEY` from MapTiler, and a descriptive `NOMINATIM_USER_AGENT`; absent keys fall back to deterministic demo routes. Location sharing is opt-in and trip-limited. Browsers can throttle geolocation in the background; users are prompted to keep the screen on. Email/SMS delivery is not claimed in this prototype.
