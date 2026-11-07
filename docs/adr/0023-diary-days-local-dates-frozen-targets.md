# ADR 0023: Diary days: local dates and frozen daily targets

- **Status:** Accepted (Plan 11, Rulings E5-E7, 2026-11-07). Clinician review of the target numbers is still pending, as for ADR 0022.
- **Date:** 2026-11-07

## Context

A diary groups entries by the day the person ate them, and shows each day against that day's guide. Two things make "the day" hard:

- A fixed time zone (IST) puts a dinner logged at 22:00 in New York on the wrong day. Offline entries sync after midnight, and people travel.
- Settings, weight and birth year change. If yesterday's guide were recomputed from today's weight, last week's history would shift under the user's feet.

## Decision

- **Local dates in the account's zone.** `accounts.timezone` (an IANA name, default `Asia/Kolkata`, validated by the API through `PUT /v1/me/timezone`) is the zone for local dates. Each entry stores `meal_logs.local_date`, computed once from `eaten_at` and the zone at log time. **Changing the zone never moves a stored date.** Clients never work out a date boundary: the API returns `today`, and accepts `local_date` to log onto a past day.
- **Today is live, the past is frozen.** While `health_data` is active, today's `diary_days` row is recomputed and upserted on every read or log of today, so settings, weight, birth year and time-zone changes reach it without hooks. A past row is never recomputed; only `partial_logged` changes.
- **Never back-filled.** A past day with no row is `none` and has no target. Opening an old day does not compute a guide for it with today's body data.
- **`health_data` is needed to compute a row.** Without it nothing is computed or written (a day marked partial gets a `none` row with no numbers). The diary itself works on `terms`; only the `targets` part of the day and week views needs `health_data`.
- **Storage.** The target numbers are columns; the unrounded explanation decimals are strings in `inputs`, with `rate_kg_per_week`, `missing_fields` and `yaml_version`. `rate_options` are not frozen. Redaction always uses the **current** numbers display, so hiding numbers also hides frozen ones.
- Targets stay information: `analyze` and the verdict modules never import `diary`.

## Consequences

- History is stable: a weight change today never changes a past day's guide, and a past day logged before the guide existed shows no guide rather than an invented one.
- A user who travels sees entries on the date they were logged in the zone then in force; a day can have more or fewer than 24 hours of entries around a zone change.
- The weekly family share text and the legacy summary default dates still read `eaten_at` bounds in IST in a few places (`week_counts`); moving them to local dates is a follow-up.
- Reading today writes a row, so the read routes commit.
