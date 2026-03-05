# Feature: AI Support Assistant

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 1
**Dependencies:** None
**Complexity:** M

## Scope

### Included

- Floating AI chat button visible on all authenticated pages (ADMIN and TECHNICIAN roles only)
- Slide-in chat panel with conversational UI
- Multi-provider AI backend: `SupportAIProvider` interface with `AnthropicProvider` and `GroqProvider` implementations
- System prompt built from DSM help content (i18n `help.*` keys) + company context (name, plan tier, enabled modules)
- Session-scoped conversation history (cleared on logout/refresh)
- Rate limiting: max 20 AI queries per user per hour
- Provider failover: if primary fails, retry with secondary; if both fail, show fallback message
- Backend endpoint `POST /api/v1/my/ai-support` — proxies to AI provider, protects API keys
- "Create support ticket" escalation button in chat (disabled/hidden until F2 is deployed)
- i18n: all chat widget text in English and Spanish

### Excluded (in other features)

- Support ticket creation (F2) — the escalation button exists but ticket creation requires F2
- Ticket management dashboard (F3)
- Satisfaction rating (F4)
- RAG or vector-based retrieval (future iteration)
- File/image attachments in chat (future iteration)
- Per-company provider configuration by Super Admin (future iteration)

## User Value

When this feature is complete, admins and technicians can ask product-related questions in natural language directly from the app and receive accurate, contextual answers immediately — without emailing support or searching documentation. This deflects 70%+ of support queries.

## Acceptance Criteria

- [ ] Floating chat button visible on all authenticated pages for ADMIN and TECHNICIAN roles
- [ ] Clicking the button opens a slide-in chat panel
- [ ] User can type a question and receive an AI-generated response
- [ ] AI responses reference DSM features and workflows accurately
- [ ] Conversation supports follow-up questions within the same session
- [ ] Loading state shown while AI generates a response
- [ ] "Create support ticket" button/link shown in AI chat (disabled until F2)
- [ ] Rate limit enforced: max 20 queries per user per hour, clear message when exceeded
- [ ] Provider failover works: if primary provider fails, secondary is tried automatically
- [ ] If both providers fail, user sees "AI assistant is temporarily unavailable" with suggestion to create a ticket
- [ ] System prompt includes company name, plan tier, and enabled modules
- [ ] All UI text available in English and Spanish

## Technical Scope

### Entities (owned by this feature)

- `AIConversation` — ephemeral, session-only (not persisted to DB). Exists only in frontend state.

### Entities (used from dependencies)

- None (F1 is independent)

### Key Components

**Backend:**
- `src/support_bc/ai_assistant/domain/services.py` — `SupportAIProvider` abstract class with `chat(messages, system_prompt) -> str`
- `src/support_bc/ai_assistant/infrastructure/anthropic_provider.py` — `AnthropicProvider` implementation
- `src/support_bc/ai_assistant/infrastructure/groq_provider.py` — `GroqProvider` implementation (uses `groq` SDK)
- `src/support_bc/ai_assistant/infrastructure/provider_factory.py` — Factory to instantiate provider from config
- `src/support_bc/ai_assistant/application/commands/chat.py` — `AIChatCommand` + handler with rate limiting and failover
- `adapters/http/api/my/ai_support_router.py` — `POST /api/v1/my/ai-support` endpoint
- System prompt builder: loads `help.*` i18n keys + company context

**Frontend:**
- `web/app/src/components/support/AIChatWidget.tsx` — floating button + slide-in panel
- `web/app/src/components/support/AIChatMessage.tsx` — individual message bubble
- `web/app/src/lib/api.ts` — new API call for AI chat

**Configuration:**
- Environment variables: `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `AI_SUPPORT_PROVIDER`, `AI_SUPPORT_MODEL`
- Python dependency: `groq` SDK in `pyproject.toml`

## Notes

- The AI chat is stateless on the backend — conversation history is sent with each request from the frontend. The backend doesn't store AI conversations.
- Provider selection is global (env var), not per-company. Per-company override is a future enhancement.
- The escalation button ("Create support ticket") should be rendered but disabled with a tooltip like "Coming soon" until F2 ships. When F2 is deployed, it becomes active and pre-fills the ticket form with the AI conversation summary.
