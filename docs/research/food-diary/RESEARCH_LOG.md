# Food diary study: research log (Phase 1, discovery only)

Date of all entries: 2026-11-07. Nothing was cloned, downloaded or run. Findings from WebSearch snippets or WebFetch summaries; star counts and push dates from the GitHub API at fetch time.

| Source URL | Finding |
|---|---|
| https://api.github.com/search/repositories?q=topic:calorie-tracker&sort=stars | 318 repos in topic. Top: fud-ai (518 stars, MIT, Kotlin), kcal-app/kcal (357, MPL-2.0, PHP), FitBook (177, MIT, Dart), FitBuddy (36, GPL-3.0), macrotrackr (16, AGPL-3.0). Most others are MCP servers or templates. |
| https://github.com/traceapps/nutritrace/ | Self-hosted tracker; Svelte 5 + Express 5 + better-sqlite3, Capacitor Android; AGPL-3.0; fixed/dynamic/adaptive TDEE goals, recipes, custom foods, OFF barcode. |
| https://api.github.com/repos/TraceApps/nutritrace | 372 stars, AGPL-3.0, pushed 2026-11-07. |
| https://github.com/jacobstephens2/macrotracker (via awesome.ecosyste.ms) | Self-hosted PWA, Node/Express/SQLite, OFF+USDA, recipes, weight tracking [unverified: activity, licence]. |
| https://github.com/jancernik/makros | Small self-hosted macro tracker, custom foods, goals [unverified: licence, activity]. |
| https://alternativeto.net/software/myfitnesspal | Alternatives list; names Waistline, FoodYou, Privacy Friendly Food Tracker, OpenNutriTracker, SparkyFitness. No maintenance data. |
| https://api.github.com/repos/CodeWithCJ/SparkyFitness | 6,720 stars, TypeScript, pushed 2026-11-07, licence NOASSERTION (custom). |
| https://raw.githubusercontent.com/CodeWithCJ/SparkyFitness/main/LICENSE | Custom licence: MIT-like wording but non-commercial use only; commercial use needs written permission. NOT open source; cannot be used commercially. |
| https://github.com/CodeWithCJ/SparkyFitness | README says "source-available, not open source". Web frontend + native iOS/Android, Docker/Helm; goals, weight, charts; OFF/USDA/FatSecret/Nutritionix. No Indian food mention. BMR/TDEE, recipes, units not confirmed [unverified]. |
| https://api.github.com/repos/davidhealey/waistline | 757 stars, Cordova/JavaScript, pushed 2026-10-21, GitHub licence field null. |
| https://github.com/davidhealey/waistline | README: GPLv3. Diary by meal, custom foods, OFF/USDA, barcode, import/export. F-Droid and Play (com.waist.line). Recipes not mentioned. |
| https://raw.githubusercontent.com/davidhealey/waistline/master/LICENSE | 404 (LICENSE file path not confirmed; GPLv3 taken from README) [unverified]. |
| https://api.github.com/repos/simonoppowa/OpenNutriTracker | 2,822 stars, Dart, GPL-3.0, pushed 2026-11-06. Topics include food-diary, clean-architecture. |
| https://github.com/simonoppowa/OpenNutriTracker | Flutter, flutter_bloc, get_it, encrypted Hive; clean architecture; targets from height/weight/age/activity (IOM 2005, 2024 MET Compendium); weight goal + rate; custom meals and recipes; OFF + USDA via Supabase; Play, App Store, GitHub APKs. BMR equation not named [unverified]. |
| https://api.github.com/repos/maxkrieger/FoodYou | 404; wrong owner guess. Real repo is maksimowiczm/FoodYou. |
| https://f-droid.org/zh_Hant/packages/com.maksimowiczm.foodyou/ | FoodYou on F-Droid, v3.4.9, GPL-3.0-or-later, OFF + USDA + Swiss DB. Stack (Kotlin) [unverified]. |
| https://helpwanted-dev.pages.dev/projects/maksimowiczm/FoodYou | README: not accepting code contributions; about 379-426 stars (sources disagree). |
| https://github.com/kcal-app/kcal | Laravel (PHP 8.4), MySQL/Postgres, Tailwind, JSON:API; recipes, serving units tied to gram weights, per-weekday goals; MPL-2.0; no charts or Indian food mentioned. |
| https://github.com/brandonp2412/FitBook | Flutter/Dart, Drift (likely), MIT, offline-first, 7,000+ CORGIS foods, OFF barcode, macro graphs, weight history; Play, F-Droid, MS Store; 1,397 commits; 177 stars. |
| https://github.com/apoorvdarshan/fud-ai | 518 stars, MIT, Kotlin, AI calorie tracker iOS+Android, pushed 2026-11-06. Not opened further [unverified: features]. |
| https://github.com/david-x3d/nomi | Kotlin Material 3 nutrition journal, 9 stars, licence "Other" [unverified]. |
| https://github.com/ifct2017/ifct2017 | IFCT 2017 data package, 528 foods, MIT (per Yarn); data layer only. Data copyright/terms of the underlying NIN tables [unverified]. |
| https://glama.ai/mcp/servers/l35f1tg93k | indian-food-nutrition-mcp: IFCT + USDA, "2 rotis and a katori of dal" logging, AGPL-3.0-or-later (reported). Small MCP server, not a full app. |
| https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon/iamcrazy/gainfuel | GainFuel hackathon PWA: 155 Indian foods with katori/bowl/cup units. Repo and licence not found [unverified]. |
| https://macrofactor.com/algorithm-accuracy/ | MacroFactor: starts from standard TDEE equation, then adaptive expenditure from intake + weight trend. Public, general description. |
| https://www.healthifyme.com:443/blog/calculate-calorie-intake-indian-foods | HealthifyMe blog on Indian food calories (not read in full). |
| https://thenationalnews.com/lifestyle/food/healthifyme-app-tracks-nutrition-in-thousands-of-indian-dishes-1.657487 | HealthifyMe: Indian dishes DB built with National Institute of Nutrition; katori serving sizes (press, secondary). |
| https://forums.cronometer.com/discussion/comment/10103/ | Cronometer: Mifflin-St Jeor for BMR, custom BMR option, deficit set separately (moderator post). |
| https://cronometer.com/blog/wp-json/wp/v2/posts/46383 | Cronometer blog confirms Mifflin-St Jeor use. |

## Phase 4: feature spec (design only)

Date: 2026-11-07. Output: [FEATURE_SPEC.md](FEATURE_SPEC.md). No code, migration, string or fixture changed; no commits.

Read before designing: AGENTS.md, CONTEXT.md, docs/PRODUCT.md, docs/FEATURE_PARITY.md, ADR 0017 to 0021; the existing `meals` feature (models, schemas, service, summary, router), `scoring/daily_limits.py`, `thresholds.yaml`, `core/{consent,ratelimit,errors,time}.py`, `members` models and schemas, `me/service.py` (`ACCOUNT_OWNED_TABLES`), migrations 0001, 0003, 0006 (head is 0007, so the new migrations start at 0008), `modes/layouts.json`, i18n `en.json`, the web analytics allow-list, and the Android and web meals, protein and history features. docs/ARCHITECTURE.md was skimmed (data model, rate limits, Alembic owns RLS); no conflict with the spec.

| Source URL | Finding |
|---|---|
| https://pubmed.ncbi.nlm.nih.gov/2305711/ | Blocked (cookies required). |
| https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:2305711%20AND%20SRC:MED&resultType=core&format=json | Mifflin et al. 1990 abstract: 498 healthy subjects aged 19 to 78. Combined equation 9.99·W + 6.25·H − 4.92·A + 166·sex − 161; simplified male 10·W + 6.25·H − 5·A + 5 and female ... − 161. Confirms the constants in the spec (abstract only; full text not read). |
| https://www.guidelinecentral.com/calculator/479/ (and other search results) | Secondary confirmation of the simplified Mifflin-St Jeor constants and the citation (Am J Clin Nutr 51(2):241–7). |
| https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html | CDC: gradual loss of "about 1 to 2 pounds a week" is more likely to be kept off. Used as the outer bound for the loss-rate options. |
| https://thesouthfirst.com/news/icmr-releases-dietary-guidelines-for-indians-after-13-years-says-no-to-protein-supplements ; https://theprint.in/india/icmr-calls-for-avoiding-protein-supplements-issues-dietary-guidelines-for-indians/2077477 ; https://telanganatoday.com/why-do-icmr-nins-new-dietary-guidelines-advise-against-protein-supplements | ICMR-NIN DGI 2024 (news coverage): protein above about 1.6 g/kg/day adds no further resistance-training gains; protein supplements discouraged; 0.83 g/kg recommendation. NIN PDF not read [verify]. |

Corrections and notes:
- `apps/nutritrace.md` §3.1 calls NutriTrace's coefficients (9.99, 6.25, 4.92) non-standard. The 1990 abstract shows they are the paper's full-precision combined equation. The spec records the correction (FEATURE_SPEC §2).
- FitBook's MIT licence names "Flexify" as the copyright holder. Flagged again in the spec; nothing reused.
- Still unverified: the primary source of the activity factors (1.2 to 1.725), of the 1,200 and 1,500 kcal floors, the USDA FDC CC0 status, the IFCT 2017 / NIN reuse terms, and katori, cup and glass volumes. Each is marked in the spec and, where it matters, raised as an open question (Q1, Q2, Q6).
