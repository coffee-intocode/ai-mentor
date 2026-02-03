# Frontend Agent Notes

## Purpose
- React + Vite chat UI for AI Mentor using Vercel AI SDK and Supabase Auth.
- Tailwind CSS 4 with shadcn/ui and AI Elements wrappers.

## Quick start
- Install deps: `npm install`
- Run dev: `npm run dev` (Vite proxy sends `/api` to `http://localhost:8080`)
- Build: `npm run build`

## Entry points
- `src/main.tsx`: wires `ThemeProvider`, `AuthProvider`, and React Router.
- `src/router.tsx`: routes for `/` (private) and `/auth/*` flows.
- `src/App.tsx`: layout with sidebar and chat panel.
- `src/Chat.tsx`: chat flow using `useChat` and `DefaultChatTransport`.
- `src/Part.tsx`: renders message parts (text, reasoning, tool output).
- `src/components/app-sidebar.tsx`: conversation list and local navigation.
- `src/context/AuthContext.tsx`: Supabase auth state and actions.
- `src/lib/supabase/client.ts`: Supabase client setup (PKCE).
- `src/config.ts`: API base URL and endpoints.

## Chat flow
- `Chat.tsx` fetches `/api/configure` to populate model and tool selectors.
- Messages stream via `/api/chat` with a Bearer token from Supabase session.
- Message parts include text, reasoning, tool calls, and source URLs.
- `Part.tsx` handles tool rendering with `ToolInput`/`ToolOutput` and JSON previews.

## Local storage and navigation
- Conversation IDs are stored in URL path and `localStorage` (`conversationIds`).
- Messages are throttled (500ms) and persisted to `localStorage` by conversation ID.
- `useConversationIdFromUrl` listens for `popstate` and a custom `history-state-changed` event.
- `AppSidebar` uses those events to keep the list in sync and do local navigation.

## Auth flow
- `AuthContext` uses Supabase session, provides sign up/in/out and password reset.
- `PrivateRoute` redirects unauthenticated users to `/auth/login`.
- Supabase env vars are required at build/runtime.

## Configuration
- `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` are required.
- `VITE_API_BASE_URL` optional for production; empty string uses Vite proxy.

## Notes and gotchas
- Routes are defined for `/` and `/auth/*` only; conversation IDs are pushed into history without explicit routes.
- `/api/configure` requires auth; the frontend expects a valid Supabase access token.
