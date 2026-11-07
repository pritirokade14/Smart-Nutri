# ADR 0025: Weight trend and the weight used for daily guides

- **Status:** Accepted (Plan 12, Rulings G24-G28, 2026-11-07). The constants are PENDING CLINICIAN REVIEW, like ADR 0022.
- **Date:** 2026-11-07

## Context

A daily weigh-in swings by 1 to 2 kg from water, salt and timing. If the daily guide followed the latest weigh-in, the target would jump around. A wrong entry (a typo or a different scale) would also move it. The app needs a steady weight for the target maths and a chart that does not lurch.

## Decision

- **Time-aware exponential average on calendar days (G24).** `T = T + (1 - (1 - alpha) ** g) * (w - T)`, with `g` the days since the previous accepted weigh-in (at least 1), so skipped days are not treated as consecutive. `alpha_per_day = 0.25` gives a mean lag of (1 - alpha) / alpha = 3 days, which matches a centred 7-day moving average.
- **Why 0.25 and not 0.1.** The design spec's 0.1 belongs to the adaptive TDEE in slice 7 (a much slower average over weeks). The display trend needs to follow a real change within about a week. Slice 7 adds its own keys and does not change these.
- **Outliers.** A weigh-in more than `outlier_pct_from_trend` (3 %) from the trend is an outlier: kept and shown hollow, left out of the trend and of the target weight. A second weigh-in in a row beyond the band **on the same side** means a real change, and both are accepted. A weigh-in in the band, or on the other side, clears the wait.
- **Weight for the guides (G25).** With at least 3 non-outlier weigh-ins up to the target date, `W` is the trend on that date. Otherwise it is `members.weight_kg`. The 4-week taper near the goal therefore follows the trend. `TargetsOut.explanation.weight_source` records `trend` or `latest`.
- **One source of weight (G26).** `weights_put` and the profile weight write both stay in step in one transaction (Task 21 and Task 23).
- **Rate and projection.** The weekly rate is `T(last) - T(last - 7 days)` in kg and as a % of `T(last)`, needing 3 weigh-ins. A projection needs 6 non-outlier weigh-ins over at least 14 days, a rate in the direction of the target, and a date within 730 days. Inside the 0.5 kg maintenance band the target counts as reached.
- **Rapid loss.** Three weekly windows in a row at 1.5 % of body weight per week or faster set an information flag. It never changes the target.
- **Hidden numbers (G15).** The chart keeps its shape under `hide_all` through a normalised `y`.
- **Where it lives.** `app/scoring/weight_trend.py` (pure, `Decimal`), constants in `app/scoring/data/targets.yaml`. The verdict rules and `analyze` never import it. Golden cases are in `packages/test-fixtures/weights/`.

## Consequences

- A single water swing or typo does not move the guide, and a real change is accepted after the second weigh-in.
- The trend over the full history is recomputed on read. This is cheap at one row per day.
- Clinician review may change the constants (alpha, band, the rapid-loss line). Each change needs updated fixtures.
