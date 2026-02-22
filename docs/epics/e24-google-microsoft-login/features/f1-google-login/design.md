# Solution Design: F1 - Google Login

**Requirement:** [../../requirements.md](../../requirements.md)
**Slicing:** [../../slicing.md](../../slicing.md)
**Date:** 2026-02-22
**Bounded Context:** `auth_bc`

---

## Summary

Implement end-to-end Google OAuth2 login: backend command handler that verifies Google ID tokens and delegates to OAuthLoginService (from F0), plus frontend "Sign in with Google" button using Google Identity Services.

---

## Architecture Decision

Google Identity Services (GIS) uses a **one-tap / button** flow where the frontend receives an ID token directly from Google (no authorization code exchange needed). The frontend sends this ID token to our backend, which verifies it using Google's public keys via the `google-auth` library. This is simpler and more secure than the authorization code flow for ID-only verification.

The backend does NOT need a Google client secret — it only verifies the ID token's signature against Google's public JWKS.

---

## Implementation Plan

### 1. Backend Dependency

Add `google-auth` to `pyproject.toml`:

```toml
dependencies = [
    # ... existing ...
    "google-auth>=2.38.0",
]
```

`google-auth` provides `google.oauth2.id_token.verify_oauth2_token()` which handles:
- Fetching and caching Google's public keys from `https://www.googleapis.com/oauth2/v3/certs`
- Verifying JWT signature, expiration, audience, issuer
- Returning decoded claims

### 2. Application Layer

#### Google Token Verifier — `src/auth_bc/user/application/services/google_token_verifier.py`

```python
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

class GoogleTokenVerifier:
    def __init__(self, client_id: str):
        self.client_id = client_id

    def verify(self, token: str) -> dict:
        """
        Verify Google ID token and return claims.
        Returns: {"sub": str, "email": str, "name": str, "email_verified": bool}
        Raises: InvalidOAuthTokenError on any verification failure.
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                self.client_id,
            )
            if not idinfo.get("email_verified", False):
                raise InvalidOAuthTokenError("Google email is not verified")
            return {
                "sub": idinfo["sub"],
                "email": idinfo["email"].lower(),
                "name": idinfo.get("name"),
            }
        except ValueError:
            raise InvalidOAuthTokenError("Invalid Google token")
```

Isolated behind a class so it can be mocked in tests without calling Google APIs.

#### Google Login Command — `src/auth_bc/user/application/commands/google_oauth_login.py`

```python
@dataclass
class GoogleOAuthLoginCommand(Command):
    id_token: str

class GoogleOAuthLoginHandler(CommandHandler[GoogleOAuthLoginCommand]):
    def __init__(
        self,
        token_verifier: GoogleTokenVerifier,
        oauth_login_service: OAuthLoginService,
    ):
        self.token_verifier = token_verifier
        self.oauth_login_service = oauth_login_service

    def handle(self, command: GoogleOAuthLoginCommand) -> str:
        """Returns JWT access_token."""
        claims = self.token_verifier.verify(command.id_token)

        return self.oauth_login_service.login_or_create(
            OAuthUserInfo(
                email=claims["email"],
                name=claims["name"],
                provider_id=claims["sub"],
                provider_field="google_id",
            )
        )
```

### 3. HTTP Layer

#### Endpoint — `adapters/http/api/auth/routers.py`

```python
@router.post("/auth/oauth/google")
def google_oauth_login(
    body: OAuthLoginRequest,
    oauth_settings: OAuthSettings = Depends(get_oauth_settings),
    oauth_login_service: OAuthLoginService = Depends(get_oauth_login_service),
):
    if not oauth_settings.GOOGLE_CLIENT_ID:
        raise HTTPException(501, "Google login is not configured")

    verifier = GoogleTokenVerifier(oauth_settings.GOOGLE_CLIENT_ID)
    handler = GoogleOAuthLoginHandler(verifier, oauth_login_service)

    try:
        access_token = handler.handle(
            GoogleOAuthLoginCommand(id_token=body.id_token)
        )
    except InvalidOAuthTokenError as e:
        raise HTTPException(401, str(e))
    except OAuthProviderAlreadyLinkedError as e:
        raise HTTPException(409, str(e))
    except InvalidEmailDomainError:
        raise HTTPException(403, "Only corporate email addresses are allowed")
    except CompanyRestrictedError:
        raise HTTPException(403, "Company access is currently restricted")
    except UserDeactivatedError:
        raise HTTPException(403, "User account is deactivated")

    return SingleResponse(data=TokenResponse(access_token=access_token))
```

### 4. Frontend

#### Dependency

Add Google Identity Services SDK. No npm package needed — load via script tag for smaller bundle and official support:

```html
<!-- In index.html -->
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

Alternatively, use the `@react-oauth/google` wrapper:

```bash
npm install @react-oauth/google
```

**Decision:** Use `@react-oauth/google` — provides React hooks, TypeScript types, and handles script loading. Cleaner integration.

#### Google Provider Setup — `web/app/src/lib/oauth.ts`

```typescript
import { api } from './api';

export async function fetchOAuthProviders(): Promise<{google: boolean; microsoft: boolean}> {
  const res = await api.get('/auth/oauth/providers');
  return res.data.data;
}

export async function loginWithGoogle(idToken: string): Promise<string> {
  const res = await api.post('/auth/oauth/google', { id_token: idToken });
  return res.data.data.access_token;
}
```

#### Login Page Changes — `web/app/src/pages/auth/LoginPage.tsx`

Add Google button below the existing login form:

```tsx
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

// In LoginPage component:
const [providers, setProviders] = useState({ google: false, microsoft: false });

useEffect(() => {
  fetchOAuthProviders().then(setProviders).catch(() => {});
}, []);

// After the existing form, before "Need a workspace?":
{providers.google && googleClientId && (
  <div className="mt-6">
    <div className="relative mb-4">
      <div className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-zinc-200" />
      </div>
      <div className="relative flex justify-center text-sm">
        <span className="bg-white px-2 text-zinc-500">{t('auth.login.or')}</span>
      </div>
    </div>
    <GoogleLogin
      onSuccess={(response) => handleGoogleLogin(response.credential)}
      onError={() => setError(t('auth.login.error_google_failed'))}
      width="100%"
    />
  </div>
)}
```

The `GoogleOAuthProvider` wrapper goes in `App.tsx` (conditionally rendered only when GOOGLE_CLIENT_ID is available) or directly in LoginPage.

**Google Client ID delivery to frontend:** Add `VITE_GOOGLE_CLIENT_ID` env var. The providers endpoint already tells the frontend which buttons to show, but the Google SDK needs the actual client ID to initialize.

#### Environment Variables (Frontend)

Add to `web/app/.env.example` (or `.env.staging`):

```bash
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

#### i18n Keys

**English:**
```
auth.login.or: "or"
auth.login.google_signin: "Sign in with Google"
auth.login.error_google_failed: "Google sign-in failed"
auth.login.error_oauth_generic: "Authentication failed. Please try again."
```

**Spanish:**
```
auth.login.or: "o"
auth.login.google_signin: "Iniciar sesión con Google"
auth.login.error_google_failed: "Error al iniciar sesión con Google"
auth.login.error_oauth_generic: "Error de autenticación. Inténtalo de nuevo."
```

---

## Login Flow Sequence

```
User                    Frontend                    Backend                     Google
 │                         │                           │                          │
 │ Click "Sign in          │                           │                          │
 │  with Google"           │                           │                          │
 │────────────────────────>│                           │                          │
 │                         │ Google account picker      │                          │
 │                         │──────────────────────────────────────────────────────>│
 │                         │                           │                          │
 │  Select account         │                           │                          │
 │<────────────────────────│                           │                          │
 │                         │ Receive ID token          │                          │
 │                         │<─────────────────────────────────────────────────────│
 │                         │                           │                          │
 │                         │ POST /auth/oauth/google   │                          │
 │                         │  { id_token: "..." }      │                          │
 │                         │──────────────────────────>│                          │
 │                         │                           │ verify_oauth2_token()    │
 │                         │                           │─────────────────────────>│
 │                         │                           │ claims {sub, email, name}│
 │                         │                           │<────────────────────────│
 │                         │                           │                          │
 │                         │                           │ OAuthLoginService        │
 │                         │                           │  .login_or_create()      │
 │                         │                           │                          │
 │                         │ { access_token: "jwt..." }│                          │
 │                         │<──────────────────────────│                          │
 │                         │                           │                          │
 │                         │ login(token)              │                          │
 │                         │ GET /auth/me              │                          │
 │                         │──────────────────────────>│                          │
 │                         │ { user data }             │                          │
 │                         │<──────────────────────────│                          │
 │                         │                           │                          │
 │  Redirect to dashboard  │                           │                          │
 │<────────────────────────│                           │                          │
```

---

## Files Created / Modified

| File | Action | Description |
|---|---|---|
| `src/auth_bc/user/application/services/google_token_verifier.py` | Create | Google ID token verification |
| `src/auth_bc/user/application/commands/google_oauth_login.py` | Create | Command + handler |
| `adapters/http/api/auth/routers.py` | Modify | Add `POST /auth/oauth/google` |
| `pyproject.toml` | Modify | Add `google-auth` dependency |
| `web/app/package.json` | Modify | Add `@react-oauth/google` |
| `web/app/src/lib/oauth.ts` | Create | OAuth API helpers |
| `web/app/src/pages/auth/LoginPage.tsx` | Modify | Add Google button |
| `web/app/src/lib/i18n.tsx` | Modify | Add OAuth i18n keys (EN + ES) |
| `web/app/.env.staging` | Modify | Add `VITE_GOOGLE_CLIENT_ID` |
| `.env.example` | Already done in F0 | — |

---

## Testing Strategy

| Test Type | Scope | Priority |
|---|---|---|
| Unit | `GoogleTokenVerifier` — valid token, invalid token, unverified email | High |
| Unit | `GoogleOAuthLoginHandler` — delegates to verifier + OAuthLoginService | High |
| Integration | `POST /api/v1/auth/oauth/google` — mock verifier, test full HTTP flow: existing user, new user, deactivated user, invalid domain, provider conflict, provider not configured (501) | High |
| Frontend | Google button visibility — shown when provider enabled, hidden when not | Medium |
| Frontend | Google login flow — mock `@react-oauth/google` callback, verify token sent to backend | Medium |

**Mocking approach:** In tests, mock `GoogleTokenVerifier.verify()` to return fake claims. Never call real Google APIs in CI.

---

## Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Google key rotation during verification | Very Low | Low | `google-auth` caches keys and refreshes automatically |
| `@react-oauth/google` loads external script | Low | Low | Script is loaded from Google CDN; fails gracefully if blocked |
| Google ID token has short lifetime (~5 min) | Low | Low | Frontend sends token immediately after receiving it |
