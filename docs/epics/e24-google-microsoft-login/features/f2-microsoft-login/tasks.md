# Tasks: F2 - Microsoft Login

**Design:** [design.md](design.md)
**Depends on:** F0

---

## Backend

- [x] **F2-1** Create `MicrosoftTokenVerifier` in `src/auth_bc/user/application/services/microsoft_token_verifier.py`
- [x] **F2-2** Create `MicrosoftOAuthLoginService` in `src/auth_bc/user/application/commands/microsoft_oauth_login.py`
- [x] **F2-3** Add `POST /auth/oauth/microsoft` endpoint to `adapters/http/api/auth/routers.py`

## Frontend

- [x] **F2-4** Install `@azure/msal-browser` npm package
- [x] **F2-5** Add `getMsalInstance()`, `loginWithMicrosoftPopup()`, and `loginWithMicrosoft()` to `web/app/src/lib/oauth.ts`
- [x] **F2-6** Add `VITE_MICROSOFT_CLIENT_ID` and `VITE_MICROSOFT_TENANT_ID` to `web/app/.env.staging`
- [x] **F2-7** Create `MicrosoftIcon` SVG component at `web/app/src/components/icons/MicrosoftIcon.tsx`
- [x] **F2-8** Update `LoginPage.tsx`: render Microsoft button when provider enabled, `handleMicrosoftLogin` handler
- [x] **F2-9** Add i18n keys EN + ES: `auth.login.microsoft_signin`, `auth.login.error_microsoft_failed`

## Tests

- [x] **F2-T1** Unit: `MicrosoftTokenVerifier.verify()` — valid token, expired token, missing email claim, JWKS fetch failure
- [x] **F2-T2** Unit: `MicrosoftOAuthLoginService.handle()` — delegates to verifier + OAuthLoginService
- [x] **F2-T3** Integration: `POST /api/v1/auth/oauth/microsoft` — existing user, new user, deactivated user, invalid domain, provider conflict (409), provider not configured (501)
- [ ] **F2-T4** Frontend: Microsoft button shown when provider enabled, hidden when not
