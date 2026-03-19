**Comprehensive Analysis of the Tenma AI Agent Builder Codebase**

I have performed a full review of the provided codebase (all `FILE:` sections from `/tmp/tenma-analysis/`). Below is a structured, evidence-based assessment referencing **specific files and line numbers** where relevant.

---

### 1. Intended Purpose

**What is this project trying to build?**

Tenma is a **plain-language, no-code AI agent builder** that lets users describe agents in natural language and have the system compile them into runnable, testable, and publishable agents. The original vision (see `project-prompt.md`, `replit.md`, and the consolidated "Tenma — Original Intent Reference Prompt" document) is:

- Users specify **what** the agent does (`[role]`, `[guidelines]`), **where** it gets data (`[sources]`, data sources, integrations), **which tools** it uses (`[functions]`, MCPs), and **how** it returns results (`[output]`, `[ui-style]`).
- Core workflow: **Three-panel desktop UI** (left: Tools panel, center: Prompt editor with tabs + "All-in-One" mode, right: Live chat preview).
- **Publishing**: Every agent becomes a dedicated **REST endpoint** (with versioning, rate limiting, CORS) **and/or** an embeddable chat widget.
- **Generative UI**: Optional Thesys integration renders UI components when `[ui-style]` is provided.
- **MCP-first tool ecosystem**: First-class support for Model Context Protocol (SSE, HTTP, STDIO) via `experimental_createMCPClient` from the Vercel AI SDK. Simple "paste MCP JSON" onboarding.
- **Internal tools** to reduce external API dependency: local Firecrawl, Microsoft MarkItDown (for Markdown normalization), zod-gpt for strict JSON output.
- **Monetization** (post-POC): Stripe tiers via Replit, with a free tier and "bring your own key" (BYOK) model.

**Target user**: Both technical and non-technical users who want to build production-grade AI agents without writing code. Emphasis on **Replit-native** development (secrets, integrations, auth).

**Core technical mandates** (repeated across `project-prompt.md:1-19`, `CLAUDE.md`, `AGENTS.md`):
- **Vercel AI SDK** as the single orchestration layer (`LanguageModelV2`).
- **Hero UI + AutoAnimate** (explicitly "Do not use Radix").
- **Replit Auth** (OpenID Connect) for simplicity.

---

### 2. Current Build Status

**Overall**: ~55-65% complete. Strong foundation in architecture and AI/MCP plumbing, but **major deviations** in UI and MCP implementation, plus several critical features are stubs or missing.

#### Frontend (`client/`)
- **Layout**: `client/src/App.tsx:40-90` implements the three-panel desktop layout (`grid-cols-[20rem_1fr_24rem]`) and mobile sheets/drawers (`useIsMobile`). `AgentBuilder.tsx` manages view modes (builder/chat/split) and the CopilotKit sidebar.
- **Core components**:
  - `PromptEditor.tsx`: Tabbed editor (`role`, `sources`, `functions`, `guidelines`, `output`, `ui-style`) + @-mention system (lines 140-220). All-in-One mode and `Review & Enrich` button exist but are stubs (`handleReviewAndEnrich` just logs).
  - `AddToolWizard.tsx` + form components (`AddMcpForm.tsx:1-400`, `AddDataSourceForm.tsx`, `AddIntegrationForm.tsx`, `AddAIProviderForm.tsx`): Multi-step wizards with validation. AI provider wizard is quite complete (model fetching, OpenRouter rich models with `:free` filter).
  - `ChatTestPanel.tsx` and `EmbeddedCopilotChat.tsx`: Live testing and CopilotKit integration work.
  - `AIProvidersSection.tsx` and `FirstRunSetupModal.tsx`: Recent additions (Oct 2025) for BYOK flow.
- **UI Library**: Uses **Radix UI + Shadcn** (`@radix-ui/react-*` in `package.json`, `components/ui/`). This is a **clear violation** of the "Hero UI only" mandate.
- **State**: TanStack Query + custom `useAgentContext`. CopilotKit context provider is present.
- **Status**: Functional but visually and architecturally drifted. Many test IDs are present for e2e testing.

#### Backend (`server/`)
- **Core**: Express + TypeScript (ESM). `server/index.ts:1-60` sets up routes, Replit Auth, rate limiting, and error middleware. `server/routes.ts` is the main router (~400 lines) with endpoints for agents, mcps, data-sources, integrations, publishing, webhooks, schedules, outputs.
- **Database**: `shared/schema.ts` defines 13+ tables (users, mcps, dataSources, integrations, agents, publishedEndpoints, webhooks, schedules, outputDestinations, executions, chatSessions, sessions). Uses Drizzle ORM + Neon. `server/db.ts` and `server/db-storage.ts` provide the storage layer. Migrations via `drizzle.config.ts`.
- **AI Integration**: `server/services/ai-service.ts` uses Vercel AI SDK (`createOpenAI`, `createAnthropic`, `createGoogleGenerativeAI`). Good `resolveModel` logic with fallback handling. Supports OpenAI, Anthropic, Gemini, OpenRouter.
- **MCP**: `server/services/mcp-manager.ts` has a **custom** implementation (SSE, HTTP, STDIO transports, caching, capability discovery). Does **not** use `experimental_createMCPClient`. This is explicitly called out as a critical gap in `docs/mcp-implementation.md` and `docs/gap-analysis.md`.
- **Agent Execution**: `server/services/agent-executor.ts` + `server/services/output-router.ts` handle streaming, tool calling, and output routing. AG-UI adapter (`agui-adapter.ts`) for CopilotKit.
- **Publishing/Webhooks/Scheduling**: `server/services/agent-publisher.ts`, `webhook-manager.ts`, `schedule-manager.ts` exist with decent coverage. Rate limiting and CORS are implemented.
- **Auth**: Fully migrated to **Replit Auth** (`server/replitAuth.ts`). Uses passport OIDC, Postgres sessions (`sessions` table), and `isAuthenticated` middleware. `server/routes.ts:80-100` protects `/api/*` routes. `client/src/hooks/useAuth.ts` and `Header.tsx` consume it.
- **Error Handling**: Very robust (`server/types/error.ts`, `server/utils/error-formatter.ts`, `error-logger.ts`). Standardized `AppError`, logging, and middleware.
- **Testing**: `vitest.config.ts`, some test files referenced in `attached_assets/Pasted-...txt` (auth tests were failing due to testing the public `/mcp/health` endpoint instead of authenticated JSON-RPC). 22/33 tests passing before fixes.

**Database Schema (`shared/schema.ts`)**: Comprehensive and matches intent (13 tables, proper relationships, JSONB for configs). Good Zod schemas for inserts.

**Testing Coverage**: Low. Mostly manual + a few Vitest/Supertest tests. The auth test plan in the attached asset shows ongoing test fixes.

---

### 3. Drift Analysis

**Has the project drifted? Yes — significantly in two core areas.**

**Original Intent** (`project-prompt.md:1-19`, `replit.md`, `AGENTS.md`, `CLAUDE.md`):
- **UI**: "Hero UI + AutoAnimate. Do not use Radix." (repeated multiple times).
- **MCP**: "Native MCP connectivity through `experimental_createMCPClient` from the Vercel AI SDK."
- **Internal tools**: Local Firecrawl, MarkItDown, zod-gpt for strict JSON.
- **Generative UI**: Thesys integration when `[ui-style]` is provided.
- **Publishing**: Full REST endpoint generation + embeddable chat widget with generative UI support.

**Current Reality**:
- **UI Drift (Major)**: `client/src/components/*` (e.g. `AddToolWizard.tsx:1-300`, `AgentBuilder.tsx:40-120`, all form components) use Radix/Shadcn. `tailwind.config.ts` and `components.json` are configured for Shadcn. `docs/gap-analysis.md` and `docs/implementation-status.md` explicitly call this out as a "Critical Gap".
- **MCP Drift (Major)**: `server/services/mcp-manager.ts:1-400` implements custom transports and a `MCPManager` class. No `experimental_createMCPClient`. This is documented as a deviation in `docs/mcp-implementation.md:30-80` and `docs/ai-integration.md`.
- **Missing Features**: No Thesys integration, no local Firecrawl/MarkItDown, publishing is partial (`agent-publisher.ts` exists but full embeddable widget and advanced routing are incomplete).
- **Positive areas with no drift**: Vercel AI SDK usage (`ai-service.ts`), Replit Auth migration (`replitAuth.ts`, Oct 2025), three-panel layout (`App.tsx`, `AgentBuilder.tsx`), database schema, error handling system (`error-formatter.ts`, `error-logger.ts`).

**Why the drift?** Likely pragmatic development choices during the Replit-based build (easier to use familiar Shadcn components, time pressure on MCP native integration). The attached test-fixing plan and recent auth migration show the team has been iterating, but core architectural mandates were deprioritized.

---

### 4. Documentation vs Reality

The documentation is **mostly accurate and self-aware** — it is analytical rather than aspirational.

- `docs/gap-analysis.md`, `docs/implementation-status.md`, `docs/mcp-implementation.md`, `docs/ai-integration.md`: These are excellent. They correctly identify the **UI library mismatch**, **custom vs native MCP**, missing Thesys/publishing/internal tools, and give realistic completion percentages (55% overall, UI at 40%, publishing at 10%). They reference the exact deviations from `project-prompt.md`.
- `CLAUDE.md`, `GEMINI.md`, `QWEN.md`: These are AI-assistant guidance files. They describe the intended three-layer structure and component layout accurately but do not reflect the Radix usage.
- `replit.md` and `AGENTS.md`: Describe the current monorepo structure and coding style correctly.
- `docs/technical-architecture.md` and `docs/development.md`: Slightly optimistic about completeness but still flag the gaps.

**Verdict**: The `docs/` folder is honest about the current state. It is a good "source of truth" for anyone resuming the project. The drift is **well-documented**.

---

### 5. Resumption Points (Top 3-5 Priorities)

If resuming, tackle these **concrete, high-impact items first**:

1. **UI Library Migration (Hero UI + AutoAnimate)** — Highest priority.
   - Replace all Radix/Shadcn usage in `client/src/components/` (especially `AddToolWizard.tsx:10-400`, `AgentBuilder.tsx:1-200`, all form components, `Header.tsx`, `PromptEditor.tsx`).
   - Update `components.json`, `tailwind.config.ts`, and `client/src/index.css`.
   - Reference: `docs/gap-analysis.md:20-40` and `project-prompt.md:12`.

2. **MCP Native Integration (`experimental_createMCPClient`)**.
   - Refactor `server/services/mcp-manager.ts` (lines 1-350) to use the Vercel AI SDK's native MCP client instead of custom `HttpMcpTransport`/`McpSseClient`/`McpStdioClient`.
   - Update `server/services/agent-executor.ts` and `routes.ts:300-350` accordingly.
   - Reference: `docs/mcp-implementation.md:40-90` and `project-prompt.md:4`.

3. **Complete Thesys Generative UI + Publishing**.
   - Implement Thesys rendering in `PromptEditor.tsx:280-320` and `ChatTestPanel.tsx`.
   - Finish the publishing flow in `server/services/agent-publisher.ts` and expose embeddable chat widget.
   - Reference: `docs/implementation-status.md:50-70`.

4. **Authentication Hardening + Test Fixes**.
   - Ensure Replit Auth is fully production-ready (`server/replitAuth.ts:1-150`, `routes.ts:80-110`).
   - Fix the remaining auth tests (`tests/test_auth_endpoints.py` — the attached plan in `attached_assets/` already outlines the exact changes needed for the 11 failing tests).

5. **Add missing internal tools** (local Firecrawl, MarkItDown) and comprehensive test coverage.

**Immediate next step**: Start with the UI migration — it touches the most files and is the most visible deviation. Then tackle MCP native integration, as it is a core architectural requirement.

---

**Summary**: Tenma has a solid technical core (AI SDK, database, auth, execution engine) but has drifted in its UI stack and MCP implementation. The documentation is refreshingly honest about these gaps. The project is in a **resumable state** — the top priorities above would bring it back in line with the original vision within 4-6 weeks of focused effort.