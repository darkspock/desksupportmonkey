# Tasks: F0 - Project Setup

## Task 1: Scaffold Vite + React + TypeScript
- `npm create vite@latest web/app -- --template react-ts`
- Install deps: tailwindcss, react-router-dom, @tanstack/react-query, recharts, axios

## Task 2: Tailwind CSS setup
- postcss.config, tailwind.config, base styles

## Task 3: API client
- `src/lib/api.ts` — axios instance with baseURL, JWT interceptor, error handling

## Task 4: Auth context
- `src/contexts/AuthContext.tsx` — token storage, user state, login/logout

## Task 5: Router setup
- `src/router.tsx` — role-based route guards, lazy loading

## Task 6: Type definitions
- `src/types/` — API response types matching backend schemas
