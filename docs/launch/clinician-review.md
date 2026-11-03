# Clinician review: SmartNutri scoring thresholds

> **Generated** by `scripts/clinician_review_sheet.py` from `apps/api/app/scoring/data/thresholds.yaml`. Do not edit by hand.
> Scoring version: `b3b3e5e11d94`. Pending clinician review: **True**.

**For the reviewer.** SmartNutri shows packaged-food verdicts per family member: `ok`, `caution`, `unknown` or `avoid`. It is information, not medical advice. Values are per 100 g (food) or per 100 ml (drink) unless the unit says otherwise. For each row, tick Approved, or write the value you recommend in Change to, then initial the Signed column. Sign and date the bottom of the sheet.

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
| 18 | `conditions.blood_sugar.avoid_sugars_g.food` | 22.5 | g per 100 g | UK FSA front-of-pack guidance (high thresholds); FSSAI (Advertising & Claims) Regulations 2018; UK Soft Drinks Industry Levy (5 g sugar per 100 ml) | Is this appropriate for Indian adults? |  |  |  |
| 19 | `conditions.blood_sugar.avoid_sugars_g.drink` | 5.0 | g per 100 ml | UK FSA front-of-pack guidance (high thresholds); FSSAI (Advertising & Claims) Regulations 2018; UK Soft Drinks Industry Levy (5 g sugar per 100 ml) | Is this appropriate for Indian adults? |  |  |  |
| 20 | `conditions.blood_sugar.caution_sugars_g.food` | 5.0 | g per 100 g | UK FSA front-of-pack guidance (high thresholds); FSSAI (Advertising & Claims) Regulations 2018; UK Soft Drinks Industry Levy (5 g sugar per 100 ml) | Is this appropriate for Indian adults? |  |  |  |
| 21 | `conditions.blood_sugar.caution_sugars_g.drink` | 2.5 | g per 100 ml | UK FSA front-of-pack guidance (high thresholds); FSSAI (Advertising & Claims) Regulations 2018; UK Soft Drinks Industry Levy (5 g sugar per 100 ml) | Is this appropriate for Indian adults? |  |  |  |
| 22 | `conditions.blood_sugar.caution_carbs_per_serving_g` | 30 | g per serving | UK FSA front-of-pack guidance (high thresholds); FSSAI (Advertising & Claims) Regulations 2018; UK Soft Drinks Industry Levy (5 g sugar per 100 ml) | Is this appropriate for Indian adults? |  |  |  |
| 23 | `conditions.hypertension.avoid_salt_g` | 1.5 | g per 100 g | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 24 | `conditions.hypertension.caution_salt_g` | 0.3 | g per 100 g | UK FSA front-of-pack guidance (high thresholds) | Is this appropriate for Indian adults? |  |  |  |
| 25 | `conditions.weight_loss.caution_energy_kcal` | 400 | kcal per 100 g | SmartNutri working values, pending clinician review; Nutri-Score 2023 update (Santé publique France) | Is this appropriate for Indian adults? |  |  |  |
| 26 | `conditions.weight_loss.good_protein_g_per_100kcal` | 5 | g per 100 kcal | SmartNutri working values, pending clinician review; Nutri-Score 2023 update (Santé publique France) | Is this appropriate for Indian adults? |  |  |  |
| 27 | `conditions.child.max_age` | 13 | years (exclusive upper bound) | NHS: sugar limits for children; SmartNutri working values, pending clinician review | Is this appropriate for Indian children (by age band)? |  |  |  |
| 28 | `conditions.child.free_sugar_daily_limit_g.2` | 19 | g free sugar per day (key = minimum age in years) | NHS: sugar limits for children; SmartNutri working values, pending clinician review | Is this appropriate for Indian children (by age band)? |  |  |  |
| 29 | `conditions.child.free_sugar_daily_limit_g.7` | 24 | g free sugar per day (key = minimum age in years) | NHS: sugar limits for children; SmartNutri working values, pending clinician review | Is this appropriate for Indian children (by age band)? |  |  |  |
| 30 | `conditions.child.free_sugar_daily_limit_g.11` | 30 | g free sugar per day (key = minimum age in years) | NHS: sugar limits for children; SmartNutri working values, pending clinician review | Is this appropriate for Indian children (by age band)? |  |  |  |
| 31 | `conditions.child.caution_pct_of_limit` | 25 | % of daily limit | NHS: sugar limits for children; SmartNutri working values, pending clinician review | Is this appropriate for Indian children (by age band)? |  |  |  |
| 32 | `conditions.child.avoid_pct_of_limit` | 50 | % of daily limit | NHS: sugar limits for children; SmartNutri working values, pending clinician review | Is this appropriate for Indian children (by age band)? |  |  |  |
| 33 | `conditions.infant.max_age` | 2 | years (exclusive upper bound) | SmartNutri working values, pending clinician review | Is this appropriate for Indian infants under 2? |  |  |  |
| 34 | `conditions.infant.avoid_sugars_g` | 5.0 | g per 100 g | SmartNutri working values, pending clinician review | Is this appropriate for Indian infants under 2? |  |  |  |
| 35 | `conditions.infant.avoid_salt_g` | 0.3 | g per 100 g | SmartNutri working values, pending clinician review | Is this appropriate for Indian infants under 2? |  |  |  |

## Other rule settings

| Path | Setting | Question | Approved | Change to | Signed |
|---|---|---|---|---|---|
| `allergen_may_contain_status` | avoid | Is this rule appropriate? |  |  |  |
| `conditions.blood_sugar.cardio_high_in` | salt, sat_fat | Is this rule appropriate? |  |  |  |
| `conditions.weight_loss.caution_nutriscore` | D, E | Is this rule appropriate? |  |  |  |

## Sources

- **Nutri-Score 2023 update (Santé publique France)**: https://www.santepubliquefrance.fr/nutri-score-2023-update (link not yet verified)
- **UK FSA front-of-pack guidance (high thresholds)**: https://www.food.gov.uk/safety-hygiene/check-the-label (link not yet verified)
- **FSSAI (Advertising & Claims) Regulations 2018**: https://www.fssai.gov.in/upload/uploadfiles/files/Compendium_Advertising_Claims_Regulations_14_12_2022.pdf (link not yet verified)
- **FSSAI Labelling & Display Regulations 2020**: https://www.fssai.gov.in/cms/food-safety-and-standards-regulations.php (link not yet verified)
- **ICMR-NIN Dietary Guidelines for Indians 2024**: https://www.nin.res.in/dietaryguidelines/ (link not yet verified)
- **NHS: sugar limits for children**: https://www.nhs.uk/live-well/eat-well/food-types/how-does-sugar-in-our-diet-affect-our-health/ (link not yet verified)
- **WHO guidance: no added sugar or salt under 2**: https://www.who.int/news-room/fact-sheets/detail/healthy-diet (link not yet verified)
- **UK Soft Drinks Industry Levy (5 g sugar per 100 ml)**: https://www.gov.uk/guidance/soft-drinks-industry-levy (link not yet verified)
- **SmartNutri working values, pending clinician review** (link not yet verified)

## Sign-off

Name: ____________________  Qualification and registration no.: ____________________

Signature: ____________________  Date: ____________
