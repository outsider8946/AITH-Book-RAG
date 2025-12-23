# Frontend (Vite + React + React Query)

Simple chat UI that talks to the FastAPI backend (`/api/messages`). Includes optimistic pending messages and basic loading/error handling.

## Prerequisites
- Node 18+
- pnpm (`npm i -g pnpm`)
- Backend running on `http://localhost:8000` (proxy is set in `vite.config.ts`)

## Setup
```bash
cd frontend
pnpm install
```

## Run in dev
```bash
pnpm dev
```
Then open the printed Vite URL (default `http://localhost:5173`). Requests to `/api/*` are proxied to the backend.

## Useful scripts
- `pnpm dev` — start Vite dev server
- `pnpm build` — type-check and build for production
- `pnpm preview` — preview the production build
- `pnpm lint` — run ESLint

## Notes
- Chat state is managed with `@tanstack/react-query`. Queries live under `src/lib/queries`, and the shared mutation context is in `src/lib/contexts`.
- Message shape is defined in `src/lib/types/message.ts`.

## Docker

You can run the frontend containerized.

### Using Docker Compose (Recommended)
Run from the project root:
```bash
docker-compose up --build
```

### Standalone
Build the frontend image (run from project root):
```bash
docker build -t frontend-app -f frontend/Dockerfile .
```

Run the container (pointing to backend on host):
```bash
# For Windows/Mac (Docker Desktop)
docker run -p 5173:5173 -e BACKEND_URL="http://host.docker.internal:8000" frontend-app

# For Linux
docker run -p 5173:5173 --add-host=host.docker.internal:host-gateway -e BACKEND_URL="http://host.docker.internal:8000" frontend-app
```



