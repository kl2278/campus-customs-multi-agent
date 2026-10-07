# Campus Customs Desk (frontend)

React + Vite + TypeScript dashboard for the Campus Customs agent team.

Start the backend first, then the dashboard:

```
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 (the port is fixed; the backend only allows that origin).

The API address is `http://localhost:8000`, set once in `src/api.ts`. To use another address, set `VITE_API_URL` before starting, for example `VITE_API_URL=http://localhost:8001 npm run dev`.

Other commands: `npm run typecheck` and `npm run build`.
