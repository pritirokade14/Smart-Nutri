# ADR 0017: Consent withdrawal stops processing; erasure is account or member deletion

- **Status:** Accepted (legal review pending, see Consequences)
- **Date:** 2026-11-03

## Context

SmartNutri records three consents per account: `terms`, `health_data` and `ai_processing`. Each has a version (`app/features/consents/policy.py`). Withdrawal has to do something concrete. There are two options:

1. **Stop processing.** Refuse every route that processes health data or sends data to AI models until the user consents again. Keep what is stored.
2. **Stop and erase.** Do the same, and also delete the stored health fields (allergens, conditions, goal, height, weight) or the whole member profiles.

The user decided during Plan 5 (ruling P5, 2026-11-03) that withdrawal does not delete stored health data in M3. Plan 8 Task 1 adds the route gate and the withdraw path. It does not specify erasure.

Users change their minds. If withdrawal erased data, a mis-tap in Settings would wipe a family's allergy profiles. The next scan could then show `ok` to an allergic child, because the allergy would no longer be on file. Keeping the data while refusing to process it avoids that failure.

## Decision

Withdrawal **stops processing and does not erase.**

- **Append-only rows.** Consent rows are append-only. A withdrawal adds a row that copies the version and `granted_at` of the grant it withdraws and sets `withdrawn_at`. Grant rows are never updated. Rows order by `coalesce(withdrawn_at, granted_at)`, and the latest row per purpose decides. Withdrawal is accepted at any version. A second withdrawal adds nothing.
- **Route gate.** `app/core/consent.py` defines `REQUIRED` and `gate_for(feature)`. `create_app()` attaches the gate to every route under `/v1/analyze` (`terms`, `health_data`), `/v1/scans` (all three), `/v1/voice` (all three) and `/v1/meals` (`terms`, `health_data`). A missing, withdrawn or old-version consent returns `403 consent_required` with `details.purposes`. The gate runs before the rate limiter, so a refused call costs no quota.
- **Health-field gate stays.** The members gate (ruling P5) still applies: saving health fields needs `health_data`. The explanation still needs `ai_processing`.
- **Erasure.** Erasure is explicit:
  - `DELETE /v1/me` erases the whole account (Plan 8 Task 2).
  - Deleting a member, or clearing its fields, erases that member's data.
- **Retention.** Label photos are deleted after 30 days and voice answers after 24 hours, whatever the consent state (Plan 8 Task 3).
- **Privacy policy.** The policy (`docs/launch/privacy-policy.md`) says all of this in plain words.

## Consequences

- **The 403 can come from any gated route.** Clients must handle `consent_required` on every gated route and send the user to the consent screen with `details.purposes`. Until the Android and web consent screens ship, accounts without consent rows cannot analyze or scan.
- **Possible gap with DPDP Act 2023, s. 8(7).** That section asks a data fiduciary to erase personal data when consent is withdrawn, unless retention is necessary for the specified purpose or required by law. We keep the data so a re-consent restores the profile safely. The lawyer reviewing the privacy policy (Plan 8 Task 1, Step 5, a USER step) must confirm this. If the lawyer says erasure is required, the follow-up is:
  - A scheduled erasure of health fields some days after a `health_data` withdrawal that has not been reversed, with notice in the app.
  - Or an immediate erasure behind a confirmation dialog that warns about the allergy risk above.
- **Consent version.** Versions stay code-owned in `policy.py` (`2026-11-01`), not the env variables the plan proposed (`CONSENT_VERSION_*`). A text change ships with a deploy of the clients' consent copy anyway.
