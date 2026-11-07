# Food diary study: shortlist (Phase 1)

Date: 2026-11-07. Discovery only; nothing cloned or analysed. Licences taken from README, F-Droid or LICENSE file where noted. GPL/AGPL: learn from, never copy code.

## Ranked open-source candidates (we read real code, Phase 3, with user approval)

| # | App | Platform | Licence | Stars / last push | Stack | Official source | Covers well | Indian food | Copy rule |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OpenNutriTracker | Android, iOS (Flutter) | GPL-3.0 (API) | 2,822 / 2026-11-06 | Flutter, flutter_bloc, get_it, Hive, Supabase food backend; clean architecture | Play, App Store, GitHub APKs | Closest to our Flutter app: targets from height/weight/age/activity, weight goal and rate, custom meals, recipes, OFF + USDA, diary | None found | Learn only |
| 2 | NutriTrace | Web PWA + Android (Capacitor), self-host | AGPL-3.0 (API) | 372 / 2026-11-07 | Svelte 5, Express 5, SQLite | GitHub, GHCR Docker | Web app with fixed/dynamic/adaptive TDEE, recipes, custom foods, barcode, fasting streaks | None found | Learn only |
| 3 | kcal | Web (Laravel) | MPL-2.0 (weak copyleft, file-level) | 357 / 2026-10-24 | PHP 8.4, Laravel, Postgres/MySQL, Tailwind | GitHub | Data model: foods on gram basis, serving units with gram weights, recipes, per-weekday goals | None found | MPL: not copying; ideas OK |
| 4 | FitBook | Android, iOS, desktop, web (Flutter) | MIT (README) | 177 / 2026-11-03 | Flutter, Drift (likely), OFF, CORGIS 7,000 foods | Play, F-Droid, GitHub | Permissive Flutter diary, weight history, macro graphs; safest to adapt patterns | None found | Permissive; still prefer clean-room |
| 5 | Waistline | Android (Cordova) | GPLv3 (README) | 757 / 2026-10-21 | Cordova, Framework7, JS | F-Droid, Play | Mature diary by meal, custom foods, OFF/USDA | None found | Learn only |
| 6 | FoodYou | Android (Kotlin) | GPL-3.0-or-later | ~400 / [unverified] | [unverified] | F-Droid, GitHub | Polished diary UX, OFF/USDA/Swiss DB | None found | Learn only; no contributions accepted |
| 7 | SparkyFitness | Web + iOS + Android | NOT open source: custom non-commercial licence | 6,720 / 2026-11-07 | TypeScript web, Docker, native apps | GitHub, Docker | Full-scope reference (goals, weight, charts, families) | None found | Do not read for reuse; commercial use barred. Docs and screenshots only |
| 8 | IFCT 2017 package + indian-food-nutrition-mcp | Data / MCP | MIT (data pkg, per Yarn); AGPL (MCP) | 4.7k downloads [unverified] | JS | GitHub, npm | Indian food data (528 foods) and "katori/roti" parsing idea | Yes | Check IFCT data terms with NIN before use [unverified] |

Not shortlisted: fud-ai (MIT, Kotlin, AI-first, 518 stars; worth a later look), macrotrackr (AGPL, 16 stars), MCP servers, templates.

## Closed apps for Phase 2 public research only (no downloads)

- **MacroFactor**: adaptive expenditure from intake + weight trend; see https://macrofactor.com/algorithm-accuracy/.
- **Cronometer**: Mifflin-St Jeor BMR, custom BMR, separate deficit; help centre and forums.
- **HealthifyMe**: Indian food DB (NIN-assisted), katori servings; the leading India reference. MyFitnessPal as the baseline.

## Top picks

1. **OpenNutriTracker**: same stack family (Flutter, clean architecture), covers targets, goals and recipes; GPL so learn only.
2. **NutriTrace**: only active web-app candidate with adaptive TDEE and a clear Svelte/Express split; AGPL so learn only.
3. **kcal** (data model for serving units and goals, MPL-2.0), with **FitBook** (MIT) as the permissive Flutter reference.

Gap: no candidate has Indian household units (katori, roti). Plan on IFCT-based data plus our own unit table; verify IFCT licensing.
