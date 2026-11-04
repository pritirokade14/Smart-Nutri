# ADR 0018: Consent withdrawal stops processing; erasure is account or member deletion

- **Status:** Accepted, amended by ruling G1 (legal review pending, see Consequences)
- **Date:** 2026-11-03
- **Note:** written as ADR 0017 on the Plan 8 branch; renumbered at the wave 2 merge because Plan 6 also wrote an ADR 0017 (meal logs for Open Food Facts products).

## Context

SmartNutri records three consents per account: `terms`, `health_data` and `ai_processing`. Each has a version (`app/features/consents/policy.py`). Withdrawal has to do something concrete. There are two options:

1. **Stop processing.** Refuse every route that processes health data or sends data to AI models until the user consents again. Keep what is stored.
2. **Stop and erase.** Do the same, and also delete the stored health fields (allergens, conditions, goal, height, weight) or the whole member profiles.

The user decided during Plan 5 (ruling P5, 2026-11-03) that withdrawal does not delete stored health data in M3. Plan 8 Task 1 adds the route gate and the withdraw path. It does not specify erasure.

Users change their minds. If withdrawal erased data, a mis-tap in Settings would wipe a family's allergy profiles. The next scan could then show `ok` to an allergic child, because the allergy would no longer be on file. Keeping the data while refusing to process it avoids that failure.

## Decision

Withdrawal **stops processing and does not erase.**

- **Append-only rows.** Consent rows are append-only. A withdrawal adds a row that copies the version and `granted_at` of the grant it withdraws and sets `withdrawn_at`. Grant rows are never updated. Rows order by `coalesce(withdrawn_at, granted_at)`, and the latest row per purpose decides. Withdrawal is accepted at any version. A second withdrawal adds nothing.
- **Route gate.** `app/core/consent.py` defines `REQUIRED` and `gate_for(feature)`. `create_app()` attaches the gate to every route under `/v1/analyze`, `/v1/scans`, `/v1/voice` and `/v1/meals`, and `products_create` carries it on its route. A missing, withdrawn or old-version consent returns `403 consent_required` with `details.purposes`. The gate runs before the rate limiter, so a refused call costs no quota. The purposes per route are set by ruling G1 (below).
- **Health-field gate stays.** The members gate (ruling P5) still applies: saving health fields needs `health_data`. The explanation still needs `ai_processing`.
- **Erasure.** Erasure is explicit:
  - `DELETE /v1/me` erases the whole account (Plan 8 Task 2).
  - Deleting a member, or clearing its fields, erases that member's data.
- **Retention.** Label photos are deleted after 30 days, whatever the consent state (Plan 8 Task 3). Voice audio is never stored (ADR 0020).
- **Privacy policy.** The policy (`docs/launch/privacy-policy.md`) says all of this in plain words.

## Amendment: ruling G1 (the user's decision, wave 2 integration)

The Plan 8 branch gated analyze and meals on `terms` + `health_data`, and scans and voice on all three. The user narrowed this:

- analyze, scans (upload-url, label), meals and `products_create` need only `terms`.
- voice needs `terms` and `ai_processing`.
- Saving member health fields keeps the members `health_data` check; the analyze explanation keeps its `ai_processing` check.

So withdrawing `health_data` stops new health-field saves, but analyze keeps reading the stored allergies and conditions. Ignoring them would show `ok` to an allergic member, which the rules forbid. `tests/api/test_consent_gate.py` asserts both the scope and this allergy case.

What each consent covers under G1 (safety ruling D1/S2; the privacy notice says the same):

- **`terms` (the core service).** Verdicts, scans, meal logs, product contributions, and **reading label photos**. A label photo goes to the vision model to read the printed values. It carries no member data, and the server strips its EXIF/GPS before the call and in storage (D1/S4). Reading a label is the service the user asked for, so it does not need `ai_processing`.
- **`health_data`.** Saving member health fields (allergies, conditions, goal, height, weight). Verdicts do not need it. They use whatever is stored, so that a saved allergy is never ignored.
- **`ai_processing`.** Sending member context (names and IDs removed) to an AI model: the written explanation of a verdict and voice questions and answers.

**For the lawyer:** confirm that (1) reading a label photo with an AI model can rest on `terms` as part of the core service, and (2) verdicts may keep using stored health data after `health_data` is withdrawn (see DPDP s. 8(7) under Consequences).

## Consequences

- **The 403 can come from any gated route.** Clients must handle `consent_required` on every gated route and send the user to the consent screen with `details.purposes`. Until the Android and web consent screens ship, accounts without consent rows cannot analyze or scan.
- **Possible gap with DPDP Act 2023, s. 8(7).** That section asks a data fiduciary to erase personal data when consent is withdrawn, unless retention is necessary for the specified purpose or required by law. We keep the data so a re-consent restores the profile safely. The lawyer reviewing the privacy policy (Plan 8 Task 1, Step 5, a USER step) must confirm this. If the lawyer says erasure is required, the follow-up is:
  - A scheduled erasure of health fields some days after a `health_data` withdrawal that has not been reversed, with notice in the app.
  - Or an immediate erasure behind a confirmation dialog that warns about the allergy risk above.
- **Consent version.** Versions stay code-owned in `policy.py` (`2026-11-01`), not the env variables the plan proposed (`CONSENT_VERSION_*`). A text change ships with a deploy of the clients' consent copy anyway.
