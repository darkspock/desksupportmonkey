# Tasks: F1 - Google Login

**Design:** [design.md](design.md)
**Depends on:** F0

---

## Backend

- [x] **F1-1** Add `google-auth>=2.38.0` to `pyproject.toml`
- [x] **F1-2** Create `GoogleTokenVerifier` in `src/auth_bc/user/application/services/google_token_verifier.py`
- [x] **F1-3** Create `GoogleOAuthLoginService` in `src/auth_bc/user/application/commands/google_oauth_login.py`
- [x] **F1-4** Add `POST /auth/oauth/google` endpoint to `adapters/http/api/auth/routers.py`

## Frontend

- [x] **F1-5** Install `@react-oauth/google` npm package
- [x] **F1-6** Create `web/app/src/lib/oauth.ts` with `fetchOAuthProviders()` and `loginWithGoogle()`
- [x] **F1-7** Add `VITE_GOOGLE_CLIENT_ID` to `web/app/.env.staging`
- [x] **F1-8** Update `LoginPage.tsx`: fetch providers on mount, render `GoogleOAuthProvider` + Google button when enabled
- [x] **F1-9** Add i18n keys EN + ES: `auth.login.or`, `auth.login.google_signin`, `auth.login.error_google_failed`, `auth.login.error_oauth_generic`

## Tests

- [x] **F1-T1** Unit: `GoogleTokenVerifier.verify()` — valid token, invalid token, unverified email
- [x] **F1-T2** Unit: `GoogleOAuthLoginService.handle()` — delegates to verifier + OAuthLoginService
- [x] **F1-T3** Integration: `POST /api/v1/auth/oauth/google` — existing user, new user, deactivated user, invalid domain, provider conflict (409), provider not configured (501)
- [ ] **F1-T4** Frontend: Google button shown when provider enabled, hidden when not
