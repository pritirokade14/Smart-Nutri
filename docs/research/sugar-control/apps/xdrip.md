# xDrip+ (NightscoutFoundation/xDrip): clean-room study

Date: 2026-11-07. Licence: GPL-3.0 (`LICENSE` opened, confirmed). Ideas only; no code, strings or assets copied. Clone: `scratchpad/sugar-repos/xdrip` (shallow, read only, nothing built). Java, Android, ActiveAndroid on SQLite.

What it is: an Android CGM data hub with alarms, calibration, pump and watch support and an insulin/carb treatment log. README calls it an "enhanced personal research version", which is a useful reminder that it is not a product with a regulatory posture. Only its manual-entry, units, stats and data model patterns are relevant.

## 1. Units: mg/dL vs mmol/L
- One preference `units` ("mgdl" or mmol). All stored glucose is mg/dL; conversion constant about 18.016 (`utilitymodels/Constants.java`, `utilitymodels/Unitized.java`).
- Display helper formats mmol/L with exactly one decimal and mg/dL as integer. It also maps extreme values to text: 400 and above shows "HIGH", values from 13 to 39 show "LOW", tiny values are error codes (`Unitized.java`). That is CGM sensor semantics; for manual entry we should instead reject or confirm out-of-range numbers.
- User-set high / low thresholds (`highValue` default 170, `lowValue` default 70) are stored in the display unit and multiplied back to mg/dL before stats (`stats/StatsResult.java`). Same trap as Nightscout: thresholds stored in display unit breaks when the user switches units. Store thresholds in canonical mg/dL.
- Adoptable: canonical mg/dL, display unit setting, fixed decimals per unit, thresholds stored canonically.

## 2. Manual glucose entry
- `models/BloodTest.java`: manual meter readings. Fields: timestamp (unique), mgdl (double), created_timestamp, state bitfield (valid, calibration, note, undone, overwritten), source, uuid (unique). Notable guards in `create`: reject zero timestamp or zero value; reject timestamps before early 2017 (a sanity floor); reject more than 10 minutes in the future and clamp small future skew to now; treat a reading within 30 seconds of an existing one as a duplicate.
- No meal-context tags (fasting, post-meal) exist on blood tests; notes are free text via treatments. The tag set is something we define.
- The BloodTest path can feed a calibration to the sensor (auto-calibration option). Excluded for SmartNutri: calibration and anything that adjusts CGM values.
- Adoptable: bitfield-or-enum state with "undone" rather than hard delete, unique timestamp plus uuid for idempotency, future-timestamp clamp and ancient-date floor, near-duplicate detection window, undo/redo (`utilitymodels/UndoRedo.java`).
- Validation numbers for plausible glucose range: not found as an explicit manual-entry range [unverified]. Define ours as warnings, PENDING CLINICIAN REVIEW.

## 3. Carbs and meals on a timeline
- `models/Treatments.java`: columns include timestamp, eventType, enteredBy, notes, uuid, carbs (double), insulin (double), insulinJSON (multi-insulin detail), created_at. Carbs and notes sit on the same table as insulin; one record can hold both. Same single-table "treatment" idea as Nightscout.
- Home graph overlays treatment markers on the glucose curve; entry by voice, keypad or watch (README features; `PhoneKeypadInputActivity.java`, `VoiceCommands.java`). Voice parsing of "natural language treatments" is the headline feature [details not read].
- Stats can sum carbs over the window (`StatsResult.getTotal_carbs`), shown beside glucose stats.
- Adoptable: marker overlay of meals on the glucose chart, total carbs per day next to average glucose, voice or quick-entry for a meal note (our Indian-language voice flow already exists).
- Excluded for SmartNutri: `insulin`, `insulinJSON`, insulin type and pen models (`insulin/`, `ui/dialog/ChooseInsulinPenDialog.java`), IOB and COB curves (`models/Iob.java`, `models/CobCalc.java`), dose adjust dialog (`DoseAdjustDialog.java`), profile editor (`profileeditor/`), predictive simulation and "Forecast" (`models/Forecast.java`, `Prediction.java`), AndroidAPS exchange.

## 4. Statistics
- `stats/StatsResult.java` (window = last 24 h sliding or since midnight): counts in / below / above user range, percentages rounded to whole numbers (low, in, high), average, standard deviation (computed in SQL from sums), total carbs, total steps, plus two variability measures (a glycemic variability index and a patient glycemic status value, described as based on a public article about line length) and estimated A1c in DCCT and IFCC forms from average.
- `stats/PercentileFragment.java` / `PercentileView.java`: a time-of-day percentile chart, the AGP-style view (the file comments say the idea follows Nightscout's report) [detail unverified, only file names and the StatsResult comment read].
- Readings expected per window are computed from a 5-minute cadence (possibleCaptures), used to show data completeness. Adoptable idea: show "N of M expected readings" so users see how thin the data is; for manual logs, show count of days with data instead.
- Adoptable: time in range percent, average, SD, a data-completeness note.
- Excluded for SmartNutri: estimated A1c; GVI/PGS "scores" presented as health scores (treat as unproven; skip in v1); anything shown as a target or goal without user setting it.

## 5. Export and doctor report
- Data leaves the app as a zipped SQLite database export and import (`utils/DatabaseUtil.java`, `utils/SdcardImportExport.java`, `ImportDatabaseActivity.java`), plus uploads to Nightscout, Tidepool, MongoDB and InfluxDB, and a Grafana example in `Documentation/grafana`. I found no PDF doctor report or CSV writer in the paths read [unverified].
- Adoptable: user-triggered full export of their own data (our "download my data"), with a plain CSV beside it. The PDF layout idea should come from Nightscout's report set instead.

## 6. Data model and storage
- ActiveAndroid tables with `@Column` annotations; unique timestamp and uuid constraints with "ignore on conflict" for idempotent imports; migrations by raw `ALTER TABLE` (see Reminder.java). Sync via an uploader queue with insert / update / delete ops (`utilitymodels/UploaderQueue.java`).
- Adoptable: uuid per record created on the client so offline entries and retries do not duplicate; server dedupe by (member, taken_at, source).

## 7. API shapes (described)
- Not an API server. It speaks the Nightscout treatment and entry JSON shapes when uploading (`utilitymodels/NightscoutUploader.java`, `NightscoutTreatments.java`) and has an Android broadcast/intents interface for other apps (`utilitymodels/Intents.java`, `BroadcastGlucose.java`). Nothing to copy for our REST contract beyond field naming overlap with Nightscout.

## 8. Retention and privacy
- Local-first: "No registration or Internet access required" (README ethos). Data stays on device unless the user enables sync. A health-data opt-in screen exists (`HealthPrivacy.java`, `healthconnect/`) [content unread]. No retention policy found [unverified]. Crash reporting and telemetry exist (`utils/Telemetry.java`, `SentryCrashReporting.java`): a reminder that no health values should flow into SmartNutri's analytics.

## 9. Reminders (user-typed only)
- `models/Reminder.java`: user-created reminders with a title, optional alternate title, next-due time, repeat period (hours to weeks, bucketed), enabled flag, weekdays-only / weekends-only / home-only switches, speak or chime-only, optional graph icon, and a global "disable at night" and "all disabled" prefs. Content is whatever the user typed; the app does not generate medical advice in them.
- Adoptable: repeat period buckets, weekday/weekend flags, night quiet hours, snooze and a global pause. Content must stay user-typed (matches SHORTLIST rule). Add copy "reminder you set, not medical advice".
- Excluded for SmartNutri: glucose alerts and alarms (`alert/`, `AlertPlayer.java`, `AlertList.java`, `MissedReadingActivity.java`, snooze for BG alarms), low prediction alerts, "did you cancel alarm" dialog.

## 10. Excluded for SmartNutri (summary)
Insulin treatments and pens; IOB / COB curves; dose adjust; profile editor; alarms (high, low, urgent, missed reading, predicted low); forecast and predictive simulation; calibration and algorithm code (BloodTest to calibration, `calibrations/`, Libre OOP); CGM, pump and glucometer integrations and bluetooth meter import (later separate decision); AndroidAPS exchange; estimated A1c.

## Sources
- `README.md`, `LICENSE` (GPL-3.0), `Documentation/` listing
- `app/src/main/java/com/eveningoutpost/dexdrip/models/BloodTest.java`, `Treatments.java`, `Reminder.java`
- `.../utilitymodels/Constants.java`, `Unitized.java`, `UploaderQueue.java`, `NightscoutUploader.java`, `UndoRedo.java`
- `.../stats/StatsResult.java`, `PercentileFragment.java`, `PercentileView.java`
- `.../utils/DatabaseUtil.java`, `SdcardImportExport.java`
