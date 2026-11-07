# Clinician review: SmartNutri scoring thresholds

> **Generated** by `scripts/clinician_review_sheet.py` from `apps/api/app/scoring/data/thresholds.yaml`. Do not edit by hand.
> Scoring version: `f23144a00d68`. Pending clinician review: **True**.

**For the reviewer.** SmartNutri shows packaged-food verdicts per family member: `ok`, `caution`, `unknown` or `avoid`. It is information, not medical advice. Values are per 100 g (food) or per 100 ml (drink) unless the unit says otherwise. For each row, tick Approved, or write the value you recommend in Change to, then initial the Signed column. Sign and date the bottom of the sheet.

**Daily limits** (`daily_limits.*`) are amounts per day. The food log compares them with each member's day totals; a week uses the daily limit x the days with something logged. Labels give TOTAL sugars, not free sugars, so the sugar comparison can over-warn but never under-warns. Protein is a target, not a limit.

## Numeric thresholds

| # | Path | Value | Unit | Source | Question | Approved | Change to | Signed |
|---|---|---|---|---|---|---|---|---|
| 1 | `min_extraction_confidence` | 0.7 | model confidence, 0 to 1 | SmartNutri working value (no external source) | Is this appropriate for Indian adults? |  |  |  |
| 2 | `high_in.food.sugars_g` | 22.5 | g per 100 g | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 3 | `high_in.food.fat_g` | 17.5 | g per 100 g | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 4 | `high_in.food.sat_fat_g` | 5.0 | g per 100 g | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 5 | `high_in.food.salt_g` | 1.5 | g per 100 g | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 6 | `high_in.drink.sugars_g` | 11.25 | g per 100 ml | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 7 | `high_in.drink.fat_g` | 8.75 | g per 100 ml | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 8 | `high_in.drink.sat_fat_g` | 2.5 | g per 100 ml | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 9 | `high_in.drink.salt_g` | 0.75 | g per 100 ml | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 10 | `claims.sugar_free_max_g` | 0.5 | g per 100 g | FSSAI (Advertising & Claims) Regulations 2018 | Is this appropriate for Indian adults? |  |  |  |
| 11 | `claims.low_sugar_max_g.food` | 5.0 | g per 100 g | FSSAI (Advertising & Claims) Regulations 2018 | Is this appropriate for Indian adults? |  |  |  |
| 12 | `claims.low_sugar_max_g.drink` | 2.5 | g per 100 ml | FSSAI (Advertising & Claims) Regulations 2018 | Is this appropriate for Indian adults? |  |  |  |
| 13 | `claims.low_fat_max_g.food` | 3.0 | g per 100 g | FSSAI (Advertising & Claims) Regulations 2018 | Is this appropriate for Indian adults? |  |  |  |
| 14 | `claims.low_fat_max_g.drink` | 1.5 | g per 100 ml | FSSAI (Advertising & Claims) Regulations 2018 | Is this appropriate for Indian adults? |  |  |  |
| 15 | `claims.low_sodium_max_mg` | 120 | mg per 100 g | FSSAI (Advertising & Claims) Regulations 2018 | Is this appropriate for Indian adults? |  |  |  |
| 16 | `claims.source_of_protein_min_energy_pct` | 10 | % of energy | FSSAI (Advertising & Claims) Regulations 2018 | Is this appropriate for Indian adults? |  |  |  |
| 17 | `claims.high_protein_min_energy_pct` | 20 | % of energy | FSSAI (Advertising & Claims) Regulations 2018 | Is this appropriate for Indian adults? |  |  |  |
| 18 | `claims.protein_amount_shortfall_pct` | 10 | % below the claimed protein amount | SmartNutri working values, pending clinician review (why: FSSAI Labelling & Display Regulations 2020) | How far below a stated protein amount (e.g. "24 g protein per scoop") may the nutrition table be before we show the claim as not matching? Is 10 % in line with the FSSAI Labelling and Display Regulations 2020 tolerance? |  |  |  |
| 19 | `conditions.blood_sugar.avoid_sugars_g.food` | 22.5 | g per 100 g | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 20 | `conditions.blood_sugar.avoid_sugars_g.drink` | 5.0 | g per 100 ml | UK Soft Drinks Industry Levy (5 g sugar per 100 ml) | Is this appropriate for Indian adults? |  |  |  |
| 21 | `conditions.blood_sugar.caution_sugars_g.food` | 5.0 | g per 100 g | FSSAI (Advertising & Claims) Regulations 2018 | Is this appropriate for Indian adults? |  |  |  |
| 22 | `conditions.blood_sugar.caution_sugars_g.drink` | 2.5 | g per 100 ml | FSSAI (Advertising & Claims) Regulations 2018 | Is this appropriate for Indian adults? |  |  |  |
| 23 | `conditions.blood_sugar.caution_carbs_per_serving_g` | 30 | g per serving | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 24 | `conditions.hypertension.avoid_salt_g` | 1.5 | g per 100 g | UK FSA front-of-pack guidance (high thresholds) (why: ICMR-NIN Dietary Guidelines for Indians 2024) | Is this appropriate for Indian adults? |  |  |  |
| 25 | `conditions.hypertension.caution_salt_g` | 0.3 | g per 100 g | UK FSA front-of-pack guidance (high thresholds) (why: ICMR-NIN Dietary Guidelines for Indians 2024) | Is this appropriate for Indian adults? |  |  |  |
| 26 | `conditions.weight_loss.caution_energy_kcal` | 400 | kcal per 100 g | SmartNutri working values, pending clinician review (why: ICMR-NIN Dietary Guidelines for Indians 2024) | Is this appropriate for Indian adults? |  |  |  |
| 27 | `conditions.weight_loss.good_protein_g_per_100kcal` | 5 | g per 100 kcal | SmartNutri working values, pending clinician review (why: ICMR-NIN Dietary Guidelines for Indians 2024) | Is this appropriate for Indian adults? |  |  |  |
| 28 | `conditions.build_muscle.good_protein_g_per_100kcal` | 5 | g per 100 kcal | SmartNutri working values, pending clinician review (why: ISSN position stand: protein and exercise (2017)) | Is this appropriate for Indian adults? |  |  |  |
| 29 | `conditions.child.max_age` | 13 | years (exclusive upper bound) | SmartNutri working values, pending clinician review (why: NHS: sugar limits for children) | Is this appropriate for Indian children (by age band)? |  |  |  |
| 30 | `conditions.child.free_sugar_daily_limit_g.2` | 19 | g free sugar per day (key = minimum age in years) | NHS: sugar limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 31 | `conditions.child.free_sugar_daily_limit_g.7` | 24 | g free sugar per day (key = minimum age in years) | NHS: sugar limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 32 | `conditions.child.free_sugar_daily_limit_g.11` | 30 | g free sugar per day (key = minimum age in years) | NHS: sugar limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 33 | `conditions.child.caution_pct_of_limit` | 25 | % of daily limit | SmartNutri working values, pending clinician review (why: NHS: sugar limits for children) | Is this appropriate for Indian children (by age band)? |  |  |  |
| 34 | `conditions.child.avoid_pct_of_limit` | 50 | % of daily limit | SmartNutri working values, pending clinician review (why: NHS: sugar limits for children) | Is this appropriate for Indian children (by age band)? |  |  |  |
| 35 | `conditions.infant.max_age` | 2 | years (exclusive upper bound) | WHO guidance: no added sugar or salt under 2 | Is this appropriate for Indian infants under 2? |  |  |  |
| 36 | `conditions.infant.avoid_sugars_g` | 5.0 | g per 100 g | SmartNutri working values, pending clinician review (why: WHO guidance: no added sugar or salt under 2) | Is this appropriate for Indian infants under 2? |  |  |  |
| 37 | `conditions.infant.avoid_salt_g` | 0.3 | g per 100 g | SmartNutri working values, pending clinician review (why: WHO guidance: no added sugar or salt under 2) | Is this appropriate for Indian infants under 2? |  |  |  |
| 38 | `supplements.child_max_age` | 18 | years (maximum age, exclusive) | SmartNutri working values, pending clinician review (why: ICMR-NIN Dietary Guidelines for Indians 2024) | Supplements (protein powders, whey, health supplements) get no Nutri-Score grade and are never suggested. Is caution right for ages 2 to 17? Is avoid right under 2? Should adults with conditions (diabetes, high blood pressure) get a caution? |  |  |  |
| 39 | `supplements.suspect_min_protein_g` | 50 | g per 100 g | SmartNutri working values, pending clinician review (why: ICMR-NIN Dietary Guidelines for Indians 2024) | Is this appropriate for Indian adults? |  |  |  |
| 40 | `daily_limits.adult.sugar_g` | 25 | g per day | WHO guideline: sugars intake for adults and children | Is this appropriate for Indian adults? |  |  |  |
| 41 | `daily_limits.adult.salt_g` | 5 | g per day | WHO guideline: sodium intake for adults and children | Is this appropriate for Indian adults? |  |  |  |
| 42 | `daily_limits.adult.protein_g_per_kg` | 0.83 | g per kg body weight per day | WHO/FAO/UNU: protein and amino acid requirements in human nutrition (2007) | Is this appropriate for Indian adults? |  |  |  |
| 43 | `daily_limits.protein_min_age` | 18 | years (minimum age) | SmartNutri working values, pending clinician review (why: WHO/FAO/UNU: protein and amino acid requirements in human nutrition (2007)) | Is this appropriate for Indian adults? |  |  |  |
| 44 | `daily_limits.protein_g_per_kg_by_goal.build_muscle` | 1.6 | g per kg body weight per day | ISSN position stand: protein and exercise (2017) | Is 1.6 g/kg right as a daily protein guide for adults who want to build muscle? Should members with diabetes or hypertension keep it? There is no kidney field. The copy says "If you have kidney disease, ask your doctor before eating more protein." Is that enough? Should weight loss get 1.2 g/kg (it now keeps 0.83 g/kg)? |  |  |  |
| 45 | `daily_limits.child_salt_g_by_min_age.2` | 2 | g salt per day (key = minimum age in years) | NHS: salt limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 46 | `daily_limits.child_salt_g_by_min_age.4` | 3 | g salt per day (key = minimum age in years) | NHS: salt limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 47 | `daily_limits.child_salt_g_by_min_age.7` | 5 | g salt per day (key = minimum age in years) | NHS: salt limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 48 | `daily_limits.child_salt_g_by_min_age.11` | 6 | g salt per day (key = minimum age in years) | NHS: salt limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 49 | `daily_limits.infant.sugar_g` | 0 | g per day | WHO guidance: no added sugar or salt under 2 | Is this appropriate for Indian infants under 2? |  |  |  |
| 50 | `daily_limits.infant.salt_g` | 0 | g per day | WHO guidance: no added sugar or salt under 2 | Is this appropriate for Indian infants under 2? |  |  |  |
| 51 | `daily_limits.near_pct` | 80 | % of daily limit | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |

## Other rule settings

| Path | Setting | Question | Approved | Change to | Signed |
|---|---|---|---|---|---|
| `allergen_may_contain_status` | avoid | Is this rule appropriate? |  |  |  |
| `conditions.blood_sugar.cardio_high_in` | salt, sat_fat | Is this rule appropriate? |  |  |  |
| `conditions.weight_loss.caution_nutriscore` | D, E | Is this rule appropriate? |  |  |  |
| `supplements.child_status` | caution | Is this rule appropriate? |  |  |  |
| `supplements.infant_status` | avoid | Is this rule appropriate? |  |  |  |
| `supplements.suspect_whole_food_categories` | cheese | Is this rule appropriate? |  |  |  |
| `supplements.suspect_protein_words` | protein, proteins, casein, caseinate, calcium caseinate, milk protein, प्रोटीन, प्रथिने | Is this rule appropriate? |  |  |  |

## Sources

- **Nutri-Score 2023 update (Santé publique France)**: https://www.santepubliquefrance.fr/nutri-score-2023-update (link not yet verified)
- **Update of the Nutri-Score algorithm: Scientific Committee report 2022 (foods; fats, oils, nuts and seeds)**: https://www.santepubliquefrance.fr/en/nutri-score (link not yet verified)
- **Update of the Nutri-Score algorithm for beverages: Scientific Committee report 2023**: https://www.santepubliquefrance.fr/en/nutri-score (link not yet verified)
- **Open Food Facts: reference implementation of Nutri-Score 2023 (Nutriscore.pm)**: https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/Nutriscore.pm (link not yet verified)
- **UK FSA front-of-pack guidance (high thresholds)**: https://www.food.gov.uk/safety-hygiene/check-the-label (link not yet verified)
- **FSSAI (Advertising & Claims) Regulations 2018**: https://www.fssai.gov.in/upload/uploadfiles/files/Compendium_Advertising_Claims_Regulations_14_12_2022.pdf (link not yet verified)
- **FSSAI Labelling & Display Regulations 2020**: https://www.fssai.gov.in/cms/food-safety-and-standards-regulations.php (link not yet verified)
- **ICMR-NIN Dietary Guidelines for Indians 2024**: https://www.nin.res.in/dietaryguidelines/ (link not yet verified)
- **NHS: sugar limits for children**: https://www.nhs.uk/live-well/eat-well/food-types/how-does-sugar-in-our-diet-affect-our-health/ (link not yet verified)
- **WHO guidance: no added sugar or salt under 2**: https://www.who.int/news-room/fact-sheets/detail/healthy-diet (link not yet verified)
- **UK Soft Drinks Industry Levy (5 g sugar per 100 ml)**: https://www.gov.uk/guidance/soft-drinks-industry-levy (link not yet verified)
- **American Diabetes Association: Standards of Care in Diabetes, Section 5**: https://diabetesjournals.org/care/issue/48/Supplement_1 (link not yet verified)
- **WHO guideline: sugars intake for adults and children**: https://www.who.int/publications/i/item/9789241549028 (link not yet verified)
- **WHO guideline: sodium intake for adults and children**: https://www.who.int/publications/i/item/9789241504836 (link not yet verified)
- **WHO/FAO/UNU: protein and amino acid requirements in human nutrition (2007)**: https://www.who.int/publications/i/item/9789241209359 (link not yet verified)
- **ISSN position stand: protein and exercise (2017)**: https://pubmed.ncbi.nlm.nih.gov/28642676/ (link not yet verified)
- **NHS: salt limits for children**: https://www.nhs.uk/live-well/eat-well/food-types/salt-nutrition/ (link not yet verified)
- **SmartNutri working values, pending clinician review** (link not yet verified)

## Sign-off

Name: ____________________  Qualification and registration no.: ____________________

Signature: ____________________  Date: ____________
