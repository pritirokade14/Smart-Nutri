# ADR 0011: Deliver in vertical slices with feature parity

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

The original plan order was horizontal: engine, then API, then app. With that order, the first end-to-end run would come around day 10–12, too late to find integration problems. Adding a second client (ADR 0008) increases that risk.

## Decision

After the foundation (Plan 1 rules engine and Plan 2 foundation), deliver **milestones that each cut through API, Android and web**:

| Milestone | Target day | Slice |
|---|---|---|
| M1 | 4–5 | Barcode → OFF → rules engine → verdict |
| M2 | 6–7 | Label photo → draft → confirm → verdict; not-found flow |
| M3 | 8–9 | Family members, per-member verdicts, claims, custom alerts, explanations |
| M4 | 10–11 | Scan-to-log, summaries, share, alternatives, compare |
| M5 | 12–13 | Voice, "How we score", report a problem, public product pages |
| M6 | 14–15 | Hardening, consent and deletion, limits, observability, release |

**A feature is done only when all of these hold:**
- it works on Android **and** web
- the shared fixtures pass in API, Flutter and web tests
- its strings exist in en, hi and mr
- it passed the safety review, if it touches verdicts or allergies

## Consequences

- Something demoable on both platforms by day 4–5. Integration bugs surface early.
- Each milestone needs coordinated work. Run one builder per client in parallel against the frozen contract (`api-builder`, `flutter-builder`, web builder).
- If time runs short, the cut is made **by milestone**, keeping parity, never by dropping a platform. The founder has asked for no features to be removed, so any slip moves dates, not scope. Flag it early.
