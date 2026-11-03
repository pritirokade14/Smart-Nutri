# ADR 0016: Label scan pipeline

- **Status:** Accepted
- **Date:** 2026-11-03

The Plan 4 text called this "ADR 0013", but 0013 was already taken (clients never use the Data API). This is 0016.

## Context

When a barcode is not found, the user photographs the label. A vision model reads it, and the user confirms the values before anything is saved. Wrong numbers lead to wrong verdicts, so the design has to keep model mistakes and client bugs from reaching the rules engine. Photos are large, extraction costs credits, and two clients (Android and web) must behave the same.

## Decision

1. **Signed direct upload.** The client asks the API for a signed upload URL and sends the photo straight to private Supabase Storage (bucket `label-photos`, no policies, 8 MiB, JPEG/PNG/WebP). It then calls `POST /v1/scans/label` with the path. We do not upload multipart through the API. This keeps large bodies off Cloud Run and keeps the bucket closed to clients.
2. **Extraction cache.** The key is the image SHA-256 plus prompt version plus model. We store the raw extraction (not only the draft) in `scans.analysis`, and re-run the normaliser on every cache hit and again at save. Normaliser safety fixes therefore apply to old scans. Rows without a raw extraction count as a miss. The same account, path and hash returns the existing scan.
3. **The server does all nutrient arithmetic (R17).** Clients transcribe the values printed on the pack and send explicit choices: category, basis (per 100 g or per serving), sodium unit, serving size. The server converts units and per-serving values to per 100 g, and checks plausibility on the converted values.
4. **Withheld values are stored only when confirmed (R13, R14, R18, R19).** Values the engine must not trust yet (upper-bound protein or fibre, sodium with no printed unit, anything on a basis mismatch, a serving size) are stored only if the user confirms them. Otherwise they are stored as `None`, which leads to `unknown`, never to a safer-looking verdict.
5. **Server-computed confirm hints and shared draft fixtures (R21).** The draft carries a `confirm` block that tells clients what to ask. It comes from the same code that enforces the save, so clients do not re-derive the rules. Draft fixtures in `packages/test-fixtures/drafts/` (raw extraction, draft, confirm hints, scripted user actions, expected stored values) are asserted by the API, Android and web tests.
6. **Rate-limit buckets (per account, per day).**
   - `scan_uploads`: 60, on the upload URL route.
   - `label_requests`: 200, on `POST /v1/scans/label`, cache hits included.
   - `label_scans`: 30, paid extractions only (cache hits bypass it). It is consumed before the photo is decoded, and refunded when the provider is unavailable and no paid call happened.
   - `product_creates`: 50, on `POST /v1/products`. 422 responses count too.

Model choice is **pending the label eval** (plan 4, Task 6 Step 6). When it has run, record the winning model here or in a follow-up ADR.

## Consequences

- Clients stay thin and cannot re-open the "0.4 g sodium read as mg" class of error on their own.
- A normaliser change between scan and save can make a save fail with 422 (for example a sodium unit with no picker). This is a UX dead end, not a safety problem.
- A heavy user can hit a limit. The limits are settings, so they are cheap to raise.
- The Supabase upload token lives about 2 hours whatever `expires_in` says. Two concurrent first uploads of the same photo may both pay for extraction.
- Drafts are cached across accounts (label data only, no personal data).
- A pending product can squat a barcode. We accept that until the verification work in Plan 8 adds a partial unique index.
- Photos are not deleted yet. A 30-day retention job is planned for Plan 8.
