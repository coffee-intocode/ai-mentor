# Frontend CLAUDE.md

Frontend-specific guidance. See root `CLAUDE.md` for full project overview and backend details.

## Commands

```bash
npm install
npm run dev              # Start dev server on :5173 (proxies /api to :8080)
npm run build            # Production build
npm run typecheck        # Type check without emitting
npm run lint             # Run ESLint
npm run lint-fix         # Fix ESLint issues
npm run format           # Format with Prettier
```

## Structure

- `src/Chat.tsx` - Main chat component with conversation state and localStorage persistence
- `src/Part.tsx` - Renders message parts (text, reasoning, tools, sources)
- `src/App.tsx` - Root component with theme provider, sidebar, React Query setup
- `src/components/ai-elements/` - Vercel AI Elements wrappers
- `src/components/ui/` - Radix UI and shadcn/ui components

## Key Patterns

- Conversations stored in localStorage by nanoid ID
- URL routing: `/` for new chat, `/{nanoid}` for existing
- Messages synced to localStorage with 500ms throttle
- Model/tool configuration fetched from `/api/configure`

## Config

- TypeScript paths: `@/*` → `./src/*`
- Dev proxy: `/api` → `localhost:8080`
