# Closed food-diary apps: public research

Date: 2026-11-07. Scope: public pages only (no downloads, no logins, no decompiling). Everything is paraphrased. `[unverified]` marks anything not confirmed on a primary source. Depth is uneven: this was a single research pass with a small number of searches and fetches. Gaps are listed per app.

Fetch notes: support.cronometer.com and healthifyme.com/blog returned HTTP 403 to the fetch tool, so Cronometer and HealthifyMe details come from search-result snippets and are thinner. No Reddit threads were retrievable; "complaints" come from review-aggregator summaries (several are competitor blogs or auto-generated, so they are directional only).

---

## 1. MacroFactor

Best documented of the four. Source of the "adaptive" idea.

**Onboarding / targets**
- Starts with a rough energy estimate from its own BMR equations plus activity factors that separate daily-life activity from deliberate exercise. https://macrofactor.com/macrofactors-algorithms-and-core-philosophy/
- User picks lose, maintain or gain. The goal is a rate expressed as a percentage of body weight per week, converted to a deficit or surplus on top of estimated expenditure. https://help.macrofactorapp.com/en/articles/222-how-does-macrofactor-make-adjustments-for-a-weight-gain-or-weight-loss-goal
- Because the rate is a percentage, the kg/week value shrinks as the user loses weight and grows as they gain. Same source.
- Specific rate options and the minimum-calorie floor are not stated on the pages read. [unverified: any numeric calorie floor]. The pages only say that at very low targets it protects fat first, then protein, then carbs, and that fat has a physiological floor. Same sources.
- Protein (coached mode): set from training type (none, endurance, resistance, both) and where the user sits in the recommended range (lower, middle, upper). The numeric g/kg values were not on the pages read [unverified]. https://macrofactor.com/macrofactors-algorithms-and-core-philosophy/
- Two modes: coached (default; protein from training, carbs/fat from preference) and collaborative (app sets calories, user sets macros). Same source.
- Protein is set first; fat and carbs fill the rest by program style (high-carb to keto options reported). https://help.macrofactorapp.com/en/articles/222-how-does-macrofactor-make-adjustments-for-a-weight-gain-or-weight-loss-goal ; style range from a search summary [unverified].
- Bulking surpluses are deliberately modest; there is a help article explaining why. https://help.macrofactorapp.com/en/articles/199-why-does-macrofactor-recommend-smaller-surpluses-for-bulking-than-i-expected

**Adaptive adjustment**
- Weekly check-in. Inputs: expenditure re-estimated from logged intake and trended weight, any change to goal rate, and a smoothing layer. https://help.macrofactorapp.com/en/articles/222-how-does-macrofactor-make-adjustments-for-a-weight-gain-or-weight-loss-goal
- Weight trend is a weighted average favouring recent weigh-ins, which filters water/glycogen noise. https://macrofactor.com/macrofactors-algorithms-and-core-philosophy/
- Smoothing is intentional: a real 500 kcal expenditure shift may move the target only 200-300 kcal; larger changes need roughly 3-4 weeks of a persistent stall or surge. Same help article.
- Each week stands alone; it does not "make up" for missed targets. Same.
- Data sufficiency: nutrition logged on at least 4 of 7 days and weight at least once per week (3 ideal), otherwise expenditure holds. Same.
- Estimate begins moving after about a week and settles in roughly 14-30 days. https://macrofactor.com/macrofactors-algorithms-and-core-philosophy/
- Vendor claims typical formula-based estimates are off by roughly 300-350 kcal/day. This is a marketing claim, not independent. [unverified] (from a search summary of the vendor site).

**Diary UX**
- Barcode scanner and nutrition-label scanner (vendor site). https://macrofactor.com/macrofactor/
- AI food logging by photo, photo plus text hint, or uploaded photo; opens a "plate" review where portions and ingredients are editable before confirming. Warns that it may misjudge quantities (example: rice). Voice input not mentioned on that page. https://help.macrofactorapp.com/en/articles/258-ai-food-logging
- Toolbar is customisable (favorites, shortcuts) per the same article. Copy-previous-day, recents and quick-add details not confirmed [unverified].

**Database**
- Described by third parties as verified rather than crowd-sourced, smaller than crowd-sourced rivals. Third-party only. [unverified] https://trygaya.com/review/macrofactor-review

**Progress features**
- Weight trend, expenditure trend, weekly check-in (above).

**Free vs paid**
- Reported as paid-only with a short trial, about USD 72/year. [unverified] https://www.garagegymreviews.com/equipment/macrofactor

**Complaints (secondary)**
- Price, no free tier, smaller database leading to manual entries, manual logging burden. [unverified, aggregator summaries] https://www.garagegymreviews.com/equipment/macrofactor

**Indian foods / units:** nothing found. [unverified]

**Differentiating ideas for SmartNutri**
1. Expenditure derived from logged intake plus trended weight, with data-sufficiency gates (4 of 7 days).
2. Heavily smoothed weekly changes (about 40-60% of the raw change).
3. Rate as % body weight per week; fat floor, then protein; protein set first.
4. Photo log with an editable plate review before saving (matches our confirm-before-save rule).

---

## 2. Cronometer

Thin coverage: help centre blocked (403).

**Targets**
- Macro and micronutrient targets come from profile inputs plus Dietary Reference Intakes. https://cronometer.com/blog/?p=53701 (snippet)
- Ratio mode splits the energy target by chosen percentages; gram targets move when energy target changes. A support article also says that in ratio mode it caps protein from lean body mass, caps carbs, and gives the remainder to fat. https://support.cronometer.com/hc/en-us/articles/360060119292 (snippet only; page blocked) [unverified detail]
- Fixed (gram) mode can disagree with the energy target if a weight goal is also set. Same.
- Mifflin-St Jeor as Cronometer's formula: only third-party calculators tie it to Cronometer. [unverified]
- Rate options, floors, protein per kg: not found.

**Adaptive adjustment:** a dynamic target feature exists per forum/support titles (e.g. https://support.cronometer.com/hc/en-us/articles/33231653421588 and the forum thread "Help with macro targets") but contents not read. [unverified]

**Database**
- Third parties describe it as verified government-sourced (USDA/NCCDB) with 80+ nutrients. Whether crowd-sourced entries exist was not resolved. [unverified] https://nutrola.app/en/blog/cronometer-review-2026 (competitor blog)

**Diary UX / progress:** not confirmed. Gold reportedly adds diary groups, timestamps, recipe importer, custom reports, fasting timers. [unverified]

**Free vs paid:** free tier with ads; Gold roughly USD 9-11/month or about 50-60/year, sources conflict. Barcode appears free but not confirmed. [unverified] https://nutrola.app/en/blog/how-much-does-cronometer-cost-now-2026

**Complaints:** not found.

**Indian foods:** not found. [unverified]

**Differentiating ideas**
1. Micronutrient-first, verified-source data (DRI-driven targets).
2. Ratio mode and fixed-gram mode as two target styles.
3. Targets stored per nutrient, not just macros.

---

## 3. HealthifyMe

Thin coverage: blog blocked (403); mostly snippets.

**Onboarding / targets**
- Asks age, gender, height, weight to compute BMI, pick a goal, and output a calorie intake and burn budget. Formula not published in what I found. [unverified: formula] https://www.healthifyme.com/blog/calculate-calorie-intake-indian-foods (snippet)
- Rate, floors, protein per kg, adaptive adjustment: not found.

**Diary UX / Indian foods**
- Official blog says the app supports Indian serving units such as katori and chapati. Same source (snippet).
- AI image recognition for Indian food was announced. https://ca.news.yahoo.com/khosla-backed-healtifyme-introduces-ai-100012355.html (snippet, date not checked)
- Katori size varies by household (third parties cite 120 ml and 200 ml); a chapati is often quoted around 70 kcal at 30 g flour. These are third-party rules of thumb, not HealthifyMe data. [unverified]
- Voice, copy-meal, favourites, barcode: not confirmed.

**Database:** praised for Indian coverage; some users report inaccurate or incomplete entries. [unverified, aggregator] https://kimola.com/reports/unlock-insights-healthifyme-user-feedback-analysis-report-app-store-in-154445 ; verified vs crowd-sourced split not found.

**Free vs paid:** freemium; a third-party review says core logging, macros and AI coach need Pro from about INR 999/month. [unverified] https://nutribalance-eo0.pages.dev/blog/calorie-tracker-app-india

**Complaints (aggregators/Trustpilot):** subscription cost, auto-renewal and billing disputes, rigid plans, poor support. https://www.trustpilot.com/review/www.healthifyme.com?page=2 (snippet)

**Differentiating ideas**
1. Household units as first-class servings (katori, roti/chapati count, glass).
2. Photo recognition tuned to Indian plates.
3. Human-coach layer (paid), which we will not replicate.

---

## 4. MyFitnessPal

Coverage is mostly third-party; the official help page was not retrieved.

**Targets**
- Asks goal (lose, maintain, gain), activity level, weight, height, age, sex, and applies a calorie change per week (about 500 kcal/day per lb/week). Formula not confirmed. [unverified] https://www.myfitnesspal.com/
- Free: a single daily goal; exercise calories are added back automatically. Premium: choose whether to add exercise back, custom calorie and macro goals, per-weekday goals, per-meal goals. [unverified, third-party] https://reviewed.com/health/content/my-fitness-pal-review-can-help-you-lose-weight
- Adaptive weekly adjustment: none found. [unverified]

**Diary UX:** meals plus snacks; barcode scanning moved behind Premium on 1 Oct 2022, still reported as paywalled in a 2026 review. https://news.slashdot.org/story/22/08/25/1955238/myfitnesspal-paywalls-barcode-scanner-that-made-counting-calories-easy ; Meal Scan and voice availability conflict across sources. [unverified]

**Database:** very large, largely user-submitted; duplicates and wrong entries are the main complaint. An academic claim of underestimated saturated fat is unchecked. [unverified] https://nutrola.app/en/blog/why-is-myfitnesspal-so-bad-now (competitor blog)

**Free vs paid:** free with ads; Premium about USD 20/month or 80/year, sources conflict. [unverified] https://issuu.com/ohsu3/docs/mfp_tips

**Complaints:** barcode paywall, ads, upsells, inaccurate crowd entries, a 2026 release reported to cause data-entry bugs. https://mwm.ai/articles/myfitnesspal-calorie-counter-v26-15-0-causes-data-loss-and-entry-bugs-april-2026 [unverified]

**Indian foods:** not found.

**Differentiating ideas**
1. Per-weekday and per-meal calorie budgets.
2. Exercise-calorie add-back as a user option (we should default off).
3. A cautionary example: crowd data without a verified tier erodes trust.

---

## 5. Guidance and formulas

ALL numbers here must stay marked PENDING CLINICIAN REVIEW in SmartNutri. Where only secondary sources were reached, they are marked.

**Protein for muscle gain**
- ISSN position stand (Jager et al., J Int Soc Sports Nutr 14:20, 2017, DOI 10.1186/s12970-017-0177-8): 1.4-2.0 g/kg/day for building and maintaining muscle; per-meal about 0.25 g/kg or 20-40 g; higher intakes (2.3-3.1 g/kg) may help retain lean mass in resistance-trained people while in a calorie deficit. https://nutrition-evidence.com/article/266162/international-society-of-sports-nutrition-position-stand-protein-and-exercise ; DOI https://doi.org/10.1186/s12970-017-0177-8 (abstract only; full text not read)
- Morton et al., Br J Sports Med 52(6):376-384, 2018: benefit of added protein plateaus around 1.62 g/kg/day (CI wide; critics argue the true breakpoint may be higher). https://bjsm.bmj.com/content/52/6/376.abstract ; https://pubmed.ncbi.nlm.nih.gov/28698222/
- Suggested SmartNutri default range for Build Muscle: 1.6-2.2 g/kg is a common practice figure from secondary sources only [unverified]; cite ISSN 1.4-2.0 as the primary range.

**Weight-loss rate and calorie floors**
- 0.5-1 kg/week (about 500-750 kcal/day deficit) appears on calculator sites; attributed to CDC but the CDC page was not retrieved. [unverified; fetch https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html to confirm]
- Floors 1,200 kcal (women) and 1,500 kcal (men) are widely quoted without medical supervision; original source not confirmed. [unverified]
- MacroFactor's alternative approach: percentage of body weight per week, with fat and protein protected. (Section 1.)

**Mifflin-St Jeor and activity factors**
- Mifflin MD, St Jeor ST, et al. Am J Clin Nutr 1990;51(2):241-247. BMR = 10 x kg + 6.25 x cm - 5 x age + 5 (men) or - 161 (women). The constants +5 and -161 are from my memory of the paper, not shown in the search results. [unverified: verify at https://pubmed.ncbi.nlm.nih.gov/2305711/]
- Activity multipliers 1.2 / 1.375 / 1.55 / 1.725 / 1.9 are from calculator sites; no primary source found. [unverified] e.g. https://hacecuentas.com/en/tdee-calorie-calculator
- A 2005 Academy review said Mifflin-St Jeor predicted RMR within 10% for more people than other equations (secondhand). [unverified]

**Indian guidance**
- ICMR-NIN Dietary Guidelines for Indians 2024: food-group based; discourages high protein and protein powders; says protein above about 1.6 g/kg/day adds no further resistance-training muscle gain; fat at or below 30% of energy; cereals about 45% of energy or less; sugar under 5% of energy; salt under 5 g/day; 30-45 min moderate activity for adults. Via news coverage, not the 148-page report. [unverified] https://thesouthfirst.com/news/icmr-releases-dietary-guidelines-for-indians-after-13-years-says-no-to-protein-supplements ; https://www.dailypioneer.com/2024/columnists/key-takeaways-from-icmr---s-new-dietary-guidelines.html
- ICMR-NIN RDA 2020: protein 0.83 g/kg/day (about 54 g reference man 65 kg, 46 g reference woman 55 kg); energy 2,110 kcal sedentary man, 1,660 kcal sedentary woman; 2,710 kcal moderate-activity man. From a single study-notes page. [unverified] https://open-exam-prep.com/study-guides/in-osssc-staff-nurse/basic-nursing-sciences/nutrition-dietetics ; primary: NIN RDA 2020 report (https://www.nin.res.in), not fetched.
- Conflict to flag: ICMR's protein-powder caution and 1.6 g/kg ceiling sit below ISSN's upper range; the product should show the range with sources and not push supplements.

**Gaps for a follow-up pass:** MacroFactor numeric protein and rate options; Cronometer and HealthifyMe help centres (blocked); MFP official goal-setting page; primary CDC, NIN and Mifflin text; Reddit complaints; the Indian-unit data model of HealthifyMe.
