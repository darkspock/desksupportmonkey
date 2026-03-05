# Feature: Referral Link

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 3
**Dependencies:** F2 (Account Creation — owns ResellerClient entity)
**Complexity:** S

## Scope

### Included

- Referral link display: reseller can copy their unique referral URL from the dashboard
- Registration flow hook: check for `ref` query parameter or `dsm_ref` cookie on company registration
- Referral attribution: if valid referral code found, create `ResellerClient` with `source = referral`
- Cookie-based attribution: set `dsm_ref` cookie with 30-day expiry on register page load
- Client list: referral-originated clients distinguished from manually created ones (source column)
- Super admin: referral clients visible in reseller's client list

### Excluded (in other features)

- Reseller entity and auth → F1
- Manual account creation and ResellerClient entity → F2
- Commission tracking → F4
- Payout requests → F5

## User Value

- Resellers can share a referral link with prospects for passive client acquisition
- Prospects who register through a referral link are automatically attributed to the reseller — the registration experience is identical to normal
- Attribution persists for 30 days via cookie even if the prospect doesn't register immediately
- Resellers can see which clients came from referral links vs. manual creation

## Acceptance Criteria

- [ ] Reseller dashboard shows referral link with copy-to-clipboard button
- [ ] Referral URL format: `https://{domain}/auth/register?ref={referral_code}`
- [ ] Registration page sets `dsm_ref` cookie (30-day expiry) when `ref` parameter present
- [ ] On company registration: if `ref` param or `dsm_ref` cookie has valid referral code, create ResellerClient with `source = referral`
- [ ] Only `active` resellers get attribution (suspended/deactivated reseller codes are ignored)
- [ ] A company already linked to a reseller cannot be re-attributed (first wins)
- [ ] Referral registration is identical to normal registration from the prospect's perspective
- [ ] Client list shows `source` column (manual vs referral)
- [ ] Cookie expires after 30 days — registration after that gets no attribution
- [ ] Frontend: referral link section on dashboard with copy button

## Technical Scope

### Entities (owned by this feature)

- None (uses ResellerClient from F2)

### Entities (used from dependencies)

- `Reseller` from F1 (referral_code field)
- `ResellerClient` from F2 (creates records with source=referral)

### Key Components

**Backend (`src/reseller_bc/`):**
- `client/application/commands/create_referral_attribution.py` — Creates ResellerClient from referral code

**Collateral (outside reseller_bc):**
- `adapters/http/api/registration/routers.py` — Add referral code check on `POST /auth/register`
- Or wherever company registration is handled — add hook to check `ref` parameter and create attribution

**Frontend:**
- Update `web/app/src/pages/reseller/DashboardPage.tsx` — Add referral link section with copy button
- Update registration page — Set `dsm_ref` cookie from URL `ref` parameter

## Notes

- This is the only touch point between the reseller system and the main registration flow. The change is minimal: after successful company registration, check for a referral code and create a ResellerClient record if valid.
- The referral code is already generated as part of F1 (it's a field on the Reseller entity). This feature just adds the attribution hook and the UI for copying the link.
- Care must be taken not to break the existing registration flow — the referral check is optional and should fail silently if the code is invalid or the reseller is inactive.
