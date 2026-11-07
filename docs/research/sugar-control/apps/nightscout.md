# Nightscout (cgm-remote-monitor): clean-room study

Date: 2026-11-07. Licence: AGPL-3.0 (`LICENSE` opened, confirmed). Ideas only; nothing here is copied code, strings or assets. Clone: `scratchpad/sugar-repos/nightscout` (shallow, read only, nothing run).

What it is: a self-hosted Node.js + MongoDB web monitor for CGM data. It is built around live CGM streams, alarms and insulin maths. Most of it is out of scope for SmartNutri; the useful parts are the data shapes, the report set and the API conventions.

## 1. Units: mg/dL vs mmol/L
- One conversion constant, about 18.016 mg/dL per mmol/L (`lib/constants.json`, `lib/units.js`). mg/dL to mmol/L rounds to 1 decimal; mmol/L to mg/dL rounds to a whole number.
- Server-wide display unit setting (`DISPLAY_UNITS`, README). Thresholds are read in the display unit, with a heuristic: on an mmol site a threshold under 30 is taken as mmol/L, 30 or more as mg/dL (README, `BG_*` section). That heuristic is fragile.
- Stored values are always mg/dL internally; the webhook always emits mg/dL whatever the display unit (README, webhook section). Treatments carry an optional per-record `units` string (`docs/data-schemas/treatments-schema.md`).
- Adoptable: store mg/dL as the canonical integer/decimal, convert only at the UI edge, keep the user's preferred unit as a profile setting, and never infer units from magnitude on input. Record the unit the user typed in alongside the canonical value for audit.

## 2. Manual glucose entry and meal context
- Manual finger-stick values are first-class: entries have type `mbg` (meter blood glucose) next to `sgv` (sensor) (`docs/data-schemas/entries-schema.md`). Treatments can also carry `glucose` plus `glucoseType` of Sensor, Finger or Manual (treatments schema).
- The "careportal" event type list includes BG Check, Snack Bolus, Meal Bolus, Correction Bolus, Carb Correction, Combo Bolus, Announcement, Note, Question, Exercise, Site Change and more (`lib/plugins/careportal.js`). There is NO fasting / pre-meal / post-meal / bedtime tag; context is only the event type plus free-text `notes`.
- Validation ranges: I found no explicit min/max validation for manual BG in the paths read (`lib/api/treatments/index.js` mostly parses dates and normalises) [unverified: deeper validators may exist].
- Adoptable: a small closed enum of meal-context tags (fasting, pre-meal, post-meal, bedtime, other) is our own addition; Nightscout shows free text is not queryable. Define plausible-range validation ourselves (soft warning, not a clinical judgement) and mark it PENDING CLINICIAN REVIEW.
- Excluded for SmartNutri: Meal Bolus, Snack Bolus, Correction Bolus, Combo Bolus event types (insulin dosing).

## 3. Carbs and meals linked to glucose on one timeline
- A single `treatments` collection holds carbs, protein, fat (grams, non-negative), `foodType`, `absorptionTime` minutes, `notes`, `enteredBy`, plus `created_at` ISO time and a computed `mills` epoch (treatments schema). Glucose entries live in a separate `entries` collection. The UI draws both on one time axis; linking is by time proximity, not by a foreign key.
- Adoptable: one time-ordered feed that merges glucose readings and meal records by timestamp, with the meal record being SmartNutri's analysed product or logged meal, and an optional "readings within N minutes after" lookup computed at query time. Keep protein and fat as optional fields; they suit Indian mixed meals.
- Excluded for SmartNutri: `insulin`, `splitNow/splitExt`, `preBolus`, `absorptionTime` when used to drive dose maths, plus the carbs-on-board plugin (`lib/plugins/cob.js`) and IOB (`iob.js`), bolus wizard (`boluswizardpreview.js`, `boluscalc.js`), basal fields (`duration`, `percent`, `absolute`), temp targets and profile switches.

## 4. Statistics and AGP-style pattern
- Daily stats report (`lib/report_plugins/dailystats.js`): per day counts of low / normal / high, number of readings, min, max, average, standard deviation, 25th / median / 75th percentiles, and an estimated A1c. A1c is derived from average glucose with a linear formula and shown in both DCCT percent and IFCC units, footnoted as an estimate.
- Percentile chart (`lib/report_plugins/percentile.js`): readings from all selected days are binned by time-of-day in 30-minute windows (window must divide 60); quantiles per bin (10, 25, 50, 75, 90) are drawn as a median line with shaded 25-75 and 10-90 bands, with target low/high lines. This is the AGP idea, described in my words: overlay many days onto one 24-hour axis.
- Glucose distribution (`glucosedistribution.js`): percent of readings low / in / high against user-set range, with an "out of range RMS" metric (root mean square of distance outside range). Report defaults in mmol/L are 3.5 to 10 (`lib/report/reportclient.js` or the glucosedistribution file) and are user-editable in the report form.
- Other reports: hourly stats, day-to-day, week-to-week, treatments, success (range-based goals) (`lib/report_plugins/`).
- Adoptable: time in range (low / in / high percent), mean, SD or coefficient of variation, median and quartile band per time of day, day-by-day small multiples. Minimum-data guards (do not draw a band from a handful of points) are our addition [Nightscout has little of this: unverified].
- Excluded for SmartNutri: estimated A1c from average glucose (SHORTLIST rule: log what the user enters, do not estimate HbA1c). Also excluded: predictions (`ar2.js`, `loop.js`, `openaps.js`, `report/predictions.js`, the 30-minute forecast in README), "loopalyzer", and any "success" score framed as treatment quality. Range lines must be user-set, not Nightscout's defaults presented as clinical targets.

## 5. Doctor report and exports
- Reports are HTML views with a date-range and range-setting form, intended to be printed or screenshotted; I saw no server-side PDF generator in the paths read [unverified].
- CSV and XML output are available on API reads by file extension or Accept header (`lib/api3/doc/formats.md`); JSON is the default.
- Adoptable: server-side PDF built from the same stats functions as the on-screen report, plus a flat CSV (one row per reading or meal, ISO time, canonical mg/dL, unit typed, context tag, notes). Print layout: summary table first, then pattern chart, then per-day table. Footer: "information, not medical advice", user-entered data only.

## 6. Data model and storage
- MongoDB collections `entries`, `treatments`, `profile`, `devicestatus`, `food`, `activity` (README, `lib/server/`). Entries dedupe on the pair (sysTime, type) via upsert; treatments identify with `identifier`, plus legacy ids from other apps (`uuid`, `syncIdentifier`) (schema docs).
- Every record has `srvCreated` and `srvModified`; deletion in API v3 is a soft delete marked `isValid: false` so that sync clients learn about it through a history endpoint (`lib/api3/doc/tutorial.md`).
- Time model: `date` epoch ms plus an ISO string with UTC offset kept (`utcOffset`), so local time-of-day survives time zones. Important for AGP binning.
- Adoptable for Postgres (our Alembic): `glucose_reading(id, member_id, taken_at timestamptz, tz_offset_min, value_mgdl, entered_unit, context, source='manual', note, created_at, updated_at, deleted_at)` and a `meal_log` reference; RLS per member. Soft delete plus `updated_at` for sync. Idempotency key for retries. [Design suggestion, not from the repo.]

## 7. API shapes (described)
- v1: `/api/v1/entries`, `/api/v1/treatments`, `/api/v1/profile`, with Mongo-style query strings (field filters with gte/lte, `count`) (README). The query surface is powerful and has repeatedly needed hardening (`lib/server/query*.js`, `query-operator-allowlist.js`), a lesson: do not expose free-form query operators.
- v3: generic collection CRUD with CREATE, READ, UPDATE, PATCH, DELETE, SEARCH and HISTORY(since lastModified); JSON envelope with `status` and `result`; Swagger/OpenAPI file in `lib/api3/swagger.yaml`; Socket.IO events for create / update / delete (`lib/api3/doc/`).
- Adoptable: a small REST surface (`POST/GET/PATCH/DELETE /glucose`, `/glucose/summary?from&to`, `/glucose/pattern`, `/glucose/export?format=csv|pdf`), cursor or `since` pagination, fixed filters only, and a `since` history for the two clients.

## 8. Retention and privacy
- No built-in data retention or auto-purge found in README or schema docs; data stays until deleted [unverified beyond grep]. Soft delete leaves tombstones.
- Privacy defaults are weak: `AUTH_DEFAULT_ROLES` defaults to `readable`, so anyone with the site address can read everything unless set to `denied` (README, auth section). Tokens, API secret and role-based permissions exist (`lib/authorization/`, `docs/audits/security-audit.md`).
- Adoptable: default-deny, per-member ownership, explicit retention setting with user-initiated export and delete-all, and no health values in analytics (existing rule 6).

## 9. Reminders
- Nightscout has no user-typed-reminder feature of note; its notification plugins are alarms (`simplealarms.js`, `ar2.js`, `treatmentnotify.js`, pushover, alexa and similar). Alarms are excluded for SmartNutri. Nothing to adopt.

## 10. Excluded for SmartNutri (summary)
Insulin and bolus records; bolus wizard and calculator; IOB and COB; basal / temp basal / overrides; profile (insulin sensitivity, carb ratio); Loop, OpenAPS, pump and CGM bridge plugins; high and low alarms and urgent thresholds; glucose prediction (AR2); estimated A1c; Alexa / Google Home read-outs of glucose.

## Sources
- `README.md` (units, BG thresholds, auth roles, API pointers, webhook, prediction statement)
- `docs/data-schemas/entries-schema.md`, `docs/data-schemas/treatments-schema.md`
- `lib/units.js`, `lib/constants.json`
- `lib/plugins/careportal.js`
- `lib/report_plugins/dailystats.js`, `percentile.js`, `glucosedistribution.js`, `index.js`
- `lib/api/treatments/index.js`, `lib/api3/doc/formats.md`, `tutorial.md`, `security.md`, `socket.md`, `lib/api3/swagger.yaml`
- `docs/audits/security-audit.md`, `lib/authorization/`
- `LICENSE` (AGPL-3.0)
