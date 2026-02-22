# Solution Design: F2 - Microsoft Login

**Requirement:** [../../requirements.md](../../requirements.md)
**Slicing:** [../../slicing.md](../../slicing.md)
**Date:** 2026-02-22
**Bounded Context:** `auth_bc`

---

## Summary

Implement end-to-end Microsoft OAuth2 login: backend command handler that verifies Microsoft ID tokens using OIDC JWKS, plus frontend "Sign in with Microsoft" button using MSAL.js. Follows the same pattern as F1 (Google Login), delegating to the shared OAuthLoginService from F0.

---

## Architecture Decision

Microsoft uses standard OIDC with JWKS for token verification. Unlike Google (which has a dedicated library), we use `PyJWT` (already a project dependency) with Microsoft's OIDC discovery endpoint to fetch public keys. This avoids adding a Microsoft-specific backend library.

On the frontend, Microsoft requires `@azure/msal-browser` for the OAuth popup/redirect flow. Unlike Google Identity Services (which returns an ID token directly), MSAL handles the full authorization flow and returns the ID token after user consent.

**Tenant support:** If `MICROSOFT_TENANT_ID` is `common` (default), any Microsoft account can attempt login — email domain validation against registered companies still applies. If set to a specific tenant ID, the token issuer is validated against that tenant.

---

## Implementation Plan

### 1. Application Layer

#### Microsoft Token Verifier — `src/auth_bc/user/application/services/microsoft_token_verifier.py`

```python
import jwt  # PyJWT
import httpx

MICROSOFT_OIDC_DISCOVERY = "https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration"

class MicrosoftTokenVerifier:
    def __init__(self, client_id: str, tenant_id: str = "common"):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self._jwks_client: jwt.PyJWKClient | None = None

    @property
    def jwks_client(self) -> jwt.PyJWKClient:
        if self._jwks_client is None:
            jwks_uri = self._get_jwks_uri()
            self._jwks_client = jwt.PyJWKClient(jwks_uri)
        return self._jwks_client

    def _get_jwks_uri(self) -> str:
        url = MICROSOFT_OIDC_DISCOVERY.format(tenant=self.tenant_id)
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        return response.json()["jwks_uri"]

    def verify(self, token: str) -> dict:
        """
        Verify Microsoft ID token and return claims.
        Returns: {"oid": str, "email": str, "name": str}
        Raises: InvalidOAuthTokenError on any verification failure.
        """
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Build expected issuer(s)
            if self.tenant_id == "common":
                options = {"verify_iss": False}
            else:
                options = {"verify_iss": True}

            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=(
                    f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
                    if self.tenant_id != "common" else None
                ),
                options=options,
            )

            email = (
                claims.get("preferred_username")
                or claims.get("email")
                or claims.get("upn")
            )
            if not email:
                raise InvalidOAuthTokenError("Microsoft token missing email claim")

            return {
                "oid": claims["oid"],
                "email": email.lower(),
                "name": claims.get("name"),
            }
        except jwt.ExpiredSignatureError:
            raise InvalidOAuthTokenError("Microsoft token expired")
        except jwt.InvalidTokenError:
            raise InvalidOAuthTokenError("Invalid Microsoft token")
        except (httpx.HTTPError, KeyError):
            raise InvalidOAuthTokenError("Failed to verify Microsoft token")
```

**Key design points:**
- `PyJWKClient` caches JWKS keys automatically (built into PyJWT >=2.4)
- For `common` tenant, issuer verification is disabled because each tenant has a different issuer URL — email domain validation against companies provides the security boundary instead
- Email is extracted from `preferred_username` (most common), falling back to `email` and `upn` claims
- Microsoft object ID (`oid`) is used as the persistent provider identifier

#### Microsoft Login Command — `src/auth_bc/user/application/commands/microsoft_oauth_login.py`

```python
@dataclass
class MicrosoftOAuthLoginCommand(Command):
    id_token: str

class MicrosoftOAuthLoginHandler(CommandHandler[MicrosoftOAuthLoginCommand]):
    def __init__(
        self,
        token_verifier: MicrosoftTokenVerifier,
        oauth_login_service: OAuthLoginService,
    ):
        self.token_verifier = token_verifier
        self.oauth_login_service = oauth_login_service

    def handle(self, command: MicrosoftOAuthLoginCommand) -> str:
        """Returns JWT access_token."""
        claims = self.token_verifier.verify(command.id_token)

        return self.oauth_login_service.login_or_create(
            OAuthUserInfo(
                email=claims["email"],
                name=claims["name"],
                provider_id=claims["oid"],
                provider_field="microsoft_id",
            )
        )
```

Same pattern as Google — verify provider-specific token, then delegate to shared service.

### 2. HTTP Layer

#### Endpoint — `adapters/http/api/auth/routers.py`

```python
@router.post("/auth/oauth/microsoft")
def microsoft_oauth_login(
    body: OAuthLoginRequest,
    oauth_settings: OAuthSettings = Depends(get_oauth_settings),
    oauth_login_service: OAuthLoginService = Depends(get_oauth_login_service),
):
    if not oauth_settings.MICROSOFT_CLIENT_ID:
        raise HTTPException(501, "Microsoft login is not configured")

    verifier = MicrosoftTokenVerifier(
        client_id=oauth_settings.MICROSOFT_CLIENT_ID,
        tenant_id=oauth_settings.MICROSOFT_TENANT_ID,
    )
    handler = MicrosoftOAuthLoginHandler(verifier, oauth_login_service)

    try:
        access_token = handler.handle(
            MicrosoftOAuthLoginCommand(id_token=body.id_token)
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

### 3. Frontend

#### Dependency

```bash
npm install @azure/msal-browser
```

No need for `@azure/msal-react` — we only need the popup login flow on the login page, not a full MSAL provider wrapper. Direct use of `PublicClientApplication` is simpler.

#### MSAL Configuration — `web/app/src/lib/oauth.ts`

Extend the existing `oauth.ts` created in F1:

```typescript
import { PublicClientApplication } from '@azure/msal-browser';

let msalInstance: PublicClientApplication | null = null;

function getMsalInstance(): PublicClientApplication {
  if (!msalInstance) {
    const clientId = import.meta.env.VITE_MICROSOFT_CLIENT_ID;
    const tenantId = import.meta.env.VITE_MICROSOFT_TENANT_ID || 'common';
    msalInstance = new PublicClientApplication({
      auth: {
        clientId,
        authority: `https://login.microsoftonline.com/${tenantId}`,
        redirectUri: window.location.origin + '/auth/login',
      },
      cache: { cacheLocation: 'sessionStorage' },
    });
  }
  return msalInstance;
}

export async function loginWithMicrosoftPopup(): Promise<string> {
  const msal = getMsalInstance();
  await msal.initialize();
  const result = await msal.loginPopup({
    scopes: ['openid', 'profile', 'email'],
  });
  return result.idToken;
}

export async function loginWithMicrosoft(idToken: string): Promise<string> {
  const res = await api.post('/auth/oauth/microsoft', { id_token: idToken });
  return res.data.data.access_token;
}
```

**Popup vs redirect:** Using popup flow to avoid leaving the login page. The popup closes automatically after consent, returning the ID token. This matches Google's one-tap behavior for a consistent UX.

#### Login Page Changes — `web/app/src/pages/auth/LoginPage.tsx`

Add Microsoft button alongside the Google button (in the same OAuth section):

```tsx
{providers.microsoft && microsoftClientId && (
  <button
    onClick={handleMicrosoftLogin}
    disabled={loading}
    className="w-full flex items-center justify-center gap-3 rounded-lg
               border border-zinc-300 bg-white px-4 py-2.5 text-sm
               font-medium text-zinc-700 hover:bg-zinc-50
               disabled:opacity-50"
  >
    <MicrosoftIcon className="h-5 w-5" />
    {t('auth.login.microsoft_signin')}
  </button>
)}
```

Handler:

```typescript
async function handleMicrosoftLogin() {
  try {
    setLoading(true);
    setError(null);
    const idToken = await loginWithMicrosoftPopup();
    const accessToken = await loginWithMicrosoft(idToken);
    await login(accessToken);
    navigate(returnTo ?? getDefaultRouteForRole(), { replace: true });
  } catch (err) {
    setError(getAuthErrorMessage(err, t('auth.login.error_microsoft_failed'), ''));
  } finally {
    setLoading(false);
  }
}
```

#### Microsoft Icon Component — `web/app/src/components/icons/MicrosoftIcon.tsx`

Simple SVG icon (Microsoft four-square logo):

```tsx
export function MicrosoftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 21 21" fill="none">
      <rect x="1" y="1" width="9" height="9" fill="#F25022" />
      <rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
      <rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
      <rect x="11" y="11" width="9" height="9" fill="#FFB900" />
    </svg>
  );
}
```

#### Environment Variables (Frontend)

Add to `web/app/.env.staging`:

```bash
VITE_MICROSOFT_CLIENT_ID=your-microsoft-app-client-id
VITE_MICROSOFT_TENANT_ID=common
```

#### i18n Keys

**English:**
```
auth.login.microsoft_signin: "Sign in with Microsoft"
auth.login.error_microsoft_failed: "Microsoft sign-in failed"
```

**Spanish:**
```
auth.login.microsoft_signin: "Iniciar sesión con Microsoft"
auth.login.error_microsoft_failed: "Error al iniciar sesión con Microsoft"
```

---

## Login Flow Sequence

```
User                    Frontend                    Backend                   Microsoft
 │                         │                           │                          │
 │ Click "Sign in          │                           │                          │
 │  with Microsoft"        │                           │                          │
 │────────────────────────>│                           │                          │
 │                         │ MSAL popup                │                          │
 │                         │──────────────────────────────────────────────────────>│
 │                         │                           │                          │
 │  Select account         │                           │    login.microsoft.com   │
 │  + consent              │                           │                          │
 │<────────────────────────│                           │                          │
 │                         │ Popup returns ID token    │                          │
 │                         │<─────────────────────────────────────────────────────│
 │                         │                           │                          │
 │                         │ POST /auth/oauth/microsoft│                          │
 │                         │  { id_token: "..." }      │                          │
 │                         │──────────────────────────>│                          │
 │                         │                           │ Fetch JWKS from          │
 │                         │                           │  Microsoft OIDC endpoint │
 │                         │                           │─────────────────────────>│
 │                         │                           │ Public keys              │
 │                         │                           │<────────────────────────│
 │                         │                           │ Verify token signature   │
 │                         │                           │ Extract {oid, email, name}│
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
| `src/auth_bc/user/application/services/microsoft_token_verifier.py` | Create | Microsoft ID token verification via OIDC JWKS |
| `src/auth_bc/user/application/commands/microsoft_oauth_login.py` | Create | Command + handler |
| `adapters/http/api/auth/routers.py` | Modify | Add `POST /auth/oauth/microsoft` |
| `web/app/package.json` | Modify | Add `@azure/msal-browser` |
| `web/app/src/lib/oauth.ts` | Modify | Add MSAL config + Microsoft login helpers |
| `web/app/src/pages/auth/LoginPage.tsx` | Modify | Add Microsoft button |
| `web/app/src/components/icons/MicrosoftIcon.tsx` | Create | Microsoft logo SVG icon |
| `web/app/src/lib/i18n.tsx` | Modify | Add Microsoft i18n keys (EN + ES) |
| `web/app/.env.staging` | Modify | Add `VITE_MICROSOFT_CLIENT_ID`, `VITE_MICROSOFT_TENANT_ID` |

---

## Differences from F1 (Google)

| Aspect | F1 (Google) | F2 (Microsoft) |
|---|---|---|
| Backend library | `google-auth` (dedicated) | `PyJWT` + OIDC discovery (standard) |
| Frontend library | `@react-oauth/google` | `@azure/msal-browser` |
| Frontend flow | One-tap / button (ID token returned directly) | Popup (MSAL handles OAuth flow) |
| Token claim for ID | `sub` | `oid` |
| Token claim for email | `email` | `preferred_username` / `email` / `upn` |
| Issuer validation | Handled by `google-auth` | Manual: skip for `common`, validate for specific tenant |
| Multi-tenant | N/A (Google is always multi-tenant) | Configurable via `MICROSOFT_TENANT_ID` |

---

## Testing Strategy

| Test Type | Scope | Priority |
|---|---|---|
| Unit | `MicrosoftTokenVerifier` — valid token, expired token, missing email claim, JWKS fetch failure | High |
| Unit | `MicrosoftOAuthLoginHandler` — delegates to verifier + OAuthLoginService | High |
| Integration | `POST /api/v1/auth/oauth/microsoft` — mock verifier, test full HTTP flow: existing user, new user, deactivated user, invalid domain, provider conflict, provider not configured (501) | High |
| Frontend | Microsoft button visibility — shown when provider enabled, hidden when not | Medium |
| Frontend | Microsoft login flow — mock MSAL popup, verify token sent to backend | Medium |

**Mocking approach:** Mock `MicrosoftTokenVerifier.verify()` in backend tests. Mock `PublicClientApplication.loginPopup()` in frontend tests. Never call real Microsoft APIs in CI.

---

## Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Microsoft OIDC discovery endpoint slow/down | Very Low | Medium | `PyJWKClient` caches keys; first request may be slow; add timeout (10s) |
| `preferred_username` claim absent in some tenant configs | Low | Medium | Fallback chain: `preferred_username` → `email` → `upn`; fail if all absent |
| MSAL popup blocked by browser | Low | Medium | Show user-friendly error message suggesting to allow popups; consider redirect fallback in future |
| `@azure/msal-browser` bundle size (~30KB gzipped) | N/A | Low | Loaded only on login page; tree-shaking removes unused MSAL features |
