# Clinician review: SmartNutri scoring thresholds

> **Generated** by `scripts/clinician_review_sheet.py` from `apps/api/app/scoring/data/thresholds.yaml` and `targets.yaml`. Do not edit by hand.
> Scoring version: `85abc9fe4967`. Pending clinician review: **True**.

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
| 42 | `daily_limits.protein_min_age` | 18 | years (minimum age) | SmartNutri working values, pending clinician review (why: WHO/FAO/UNU: protein and amino acid requirements in human nutrition (2007)) | Is this appropriate for Indian adults? |  |  |  |
| 43 | `daily_limits.child_salt_g_by_min_age.2` | 2 | g salt per day (key = minimum age in years) | NHS: salt limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 44 | `daily_limits.child_salt_g_by_min_age.4` | 3 | g salt per day (key = minimum age in years) | NHS: salt limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 45 | `daily_limits.child_salt_g_by_min_age.7` | 5 | g salt per day (key = minimum age in years) | NHS: salt limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 46 | `daily_limits.child_salt_g_by_min_age.11` | 6 | g salt per day (key = minimum age in years) | NHS: salt limits for children | Is this appropriate for Indian children (by age band)? |  |  |  |
| 47 | `daily_limits.infant.sugar_g` | 0 | g per day | WHO guidance: no added sugar or salt under 2 | Is this appropriate for Indian infants under 2? |  |  |  |
| 48 | `daily_limits.infant.salt_g` | 0 | g per day | WHO guidance: no added sugar or salt under 2 | Is this appropriate for Indian infants under 2? |  |  |  |
| 49 | `daily_limits.near_pct` | 80 | % of daily limit | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 50 | `targets.energy.mifflin.weight_kcal_per_kg` | 10 | kcal per kg body weight | Mifflin-St Jeor: a new predictive equation for resting energy expenditure (Am J Clin Nutr 1990) | Is this appropriate for Indian adults? |  |  |  |
| 51 | `targets.energy.mifflin.height_kcal_per_cm` | 6.25 | kcal per cm of height | Mifflin-St Jeor: a new predictive equation for resting energy expenditure (Am J Clin Nutr 1990) | Is this appropriate for Indian adults? |  |  |  |
| 52 | `targets.energy.mifflin.age_kcal_per_year` | 5 | kcal per year of age | Mifflin-St Jeor: a new predictive equation for resting energy expenditure (Am J Clin Nutr 1990) | Is this appropriate for Indian adults? |  |  |  |
| 53 | `targets.energy.mifflin.sex_constant.male` | 5 | kcal per day (constant) | Mifflin-St Jeor: a new predictive equation for resting energy expenditure (Am J Clin Nutr 1990) | Is this appropriate for Indian adults? |  |  |  |
| 54 | `targets.energy.mifflin.sex_constant.female` | -161 | kcal per day (constant) | Mifflin-St Jeor: a new predictive equation for resting energy expenditure (Am J Clin Nutr 1990) | Is this appropriate for Indian adults? |  |  |  |
| 55 | `targets.energy.mifflin.sex_constant.average` | -78 | kcal per day (constant) | SmartNutri working values, pending clinician review (why: Mifflin-St Jeor: a new predictive equation for resting energy expenditure (Am J Clin Nutr 1990)) | Is this appropriate for Indian adults? |  |  |  |
| 56 | `targets.energy.mifflin.valid_age.min` | 18 | years | Mifflin-St Jeor: a new predictive equation for resting energy expenditure (Am J Clin Nutr 1990) | Is this appropriate for Indian adults? |  |  |  |
| 57 | `targets.energy.mifflin.valid_age.max` | 78 | years | Mifflin-St Jeor: a new predictive equation for resting energy expenditure (Am J Clin Nutr 1990) | Is this appropriate for Indian adults? |  |  |  |
| 58 | `targets.energy.activity_factor.sedentary` | 1.2 | multiple of resting energy | SmartNutri working values, pending clinician review | No primary source found: confirm or replace with ICMR-NIN 2020 PAL values |  |  |  |
| 59 | `targets.energy.activity_factor.light` | 1.375 | multiple of resting energy | SmartNutri working values, pending clinician review | No primary source found: confirm or replace with ICMR-NIN 2020 PAL values |  |  |  |
| 60 | `targets.energy.activity_factor.moderate` | 1.55 | multiple of resting energy | SmartNutri working values, pending clinician review | No primary source found: confirm or replace with ICMR-NIN 2020 PAL values |  |  |  |
| 61 | `targets.energy.activity_factor.very` | 1.725 | multiple of resting energy | SmartNutri working values, pending clinician review | No primary source found: confirm or replace with ICMR-NIN 2020 PAL values |  |  |  |
| 62 | `targets.energy.kcal_per_kg_body_weight` | 7700 | kcal per kg of body-weight change | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 63 | `targets.goal_rates.lose.default_pct_bw_per_week` | 0.5 | % of body weight per week | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |
| 64 | `targets.goal_rates.lose.max_kg_per_week` | 1.0 | kg per week | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |
| 65 | `targets.goal_rates.gain.default_pct_bw_per_week` | 0.25 | % of body weight per week | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |
| 66 | `targets.goal_rates.max_deficit_pct_of_maintenance` | 25 | % of maintenance energy | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |
| 67 | `targets.goal_rates.max_deficit_kcal_per_day` | 1000 | kcal per day | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |
| 68 | `targets.goal_rates.taper.weeks` | 4 | weeks | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |
| 69 | `targets.goal_rates.taper.maintenance_band_kg` | 0.5 | kg | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |
| 70 | `targets.goal_rates.target_weight_min_bmi` | 18.5 | BMI | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |
| 71 | `targets.goal_rates.lose_min_current_bmi` | 18.5 | BMI | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |
| 72 | `targets.floors.kcal_by_sex.female` | 1200 | kcal per day | SmartNutri working values, pending clinician review | Widely quoted figure, original source not confirmed: confirm or replace. |  |  |  |
| 73 | `targets.floors.kcal_by_sex.male` | 1500 | kcal per day | SmartNutri working values, pending clinician review | Widely quoted figure, original source not confirmed: confirm or replace. |  |  |  |
| 74 | `targets.floors.kcal_by_sex.average` | 1500 | kcal per day | SmartNutri working values, pending clinician review | Widely quoted figure, original source not confirmed: confirm or replace. |  |  |  |
| 75 | `targets.floors.min_bmr_multiple` | 1.0 | multiple of estimated resting energy | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 76 | `targets.protein.g_per_kg_by_goal.build_muscle` | 1.6 | g per kg body weight per day | ISSN position stand: protein and exercise (2017); Morton et al.: protein supplementation and resistance training gains, meta-analysis (Br J Sports Med 2018) | Is 1.6 g/kg right as a daily protein guide for adults who want to build muscle? Should members with diabetes or hypertension keep it? There is no kidney field. The copy says "If you have kidney disease, ask your doctor before eating more protein." Is that enough? |  |  |  |
| 77 | `targets.protein.g_per_kg_by_goal.weight_loss` | 1.2 | g per kg body weight per day | SmartNutri working values, pending clinician review (why: ISSN position stand: protein and exercise (2017)) | Q8: weight loss now uses 1.2 g/kg (it was 0.83 g/kg). Is 1.2 g/kg right as a daily protein guide for adults losing weight? Is it appropriate with diabetes or hypertension, and should a kidney warning show? |  |  |  |
| 78 | `targets.protein.g_per_kg_by_goal.healthy_eating` | 0.83 | g per kg body weight per day | WHO/FAO/UNU: protein and amino acid requirements in human nutrition (2007) | Is this appropriate for Indian adults? |  |  |  |
| 79 | `targets.protein.g_per_kg_by_goal.weight_gain` | 0.83 | g per kg body weight per day | WHO/FAO/UNU: protein and amino acid requirements in human nutrition (2007) | Is this appropriate for Indian adults? |  |  |  |
| 80 | `targets.protein.default_g_per_kg` | 0.83 | g per kg body weight per day | WHO/FAO/UNU: protein and amino acid requirements in human nutrition (2007) | Is this appropriate for Indian adults? |  |  |  |
| 81 | `targets.protein.lean_mass_g_per_kg_by_goal.build_muscle` | 2.0 | g per kg of lean mass per day | SmartNutri working values, pending clinician review | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 82 | `targets.protein.lean_mass_g_per_kg_by_goal.weight_loss` | 1.5 | g per kg of lean mass per day | SmartNutri working values, pending clinician review | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 83 | `targets.protein.lean_mass_g_per_kg_by_goal.healthy_eating` | 1.0 | g per kg of lean mass per day | SmartNutri working values, pending clinician review | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 84 | `targets.protein.lean_mass_g_per_kg_by_goal.weight_gain` | 1.0 | g per kg of lean mass per day | SmartNutri working values, pending clinician review | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 85 | `targets.protein.lean_mass_g_per_kg_by_goal.default` | 1.0 | g per kg of lean mass per day | SmartNutri working values, pending clinician review | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 86 | `targets.protein.max_g_per_kg` | 2.2 | g per kg body weight per day (ceiling) | SmartNutri working values, pending clinician review (why: ISSN position stand: protein and exercise (2017)) | Is this appropriate for Indian adults? |  |  |  |
| 87 | `targets.protein.max_energy_pct` | 35 | % of the energy target | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 88 | `targets.protein.adjusted_weight.min_bmi` | 30 | BMI | SmartNutri working values, pending clinician review | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 89 | `targets.protein.adjusted_weight.excess_fraction` | 0.25 | fraction of the excess over ideal weight | SmartNutri working values, pending clinician review | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 90 | `targets.protein.ibw.devine.base_kg.male` | 50 | kg | Devine: ideal body weight formula (Drug Intell Clin Pharm 1974) | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 91 | `targets.protein.ibw.devine.base_kg.female` | 45.5 | kg | Devine: ideal body weight formula (Drug Intell Clin Pharm 1974) | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 92 | `targets.protein.ibw.devine.base_kg.average` | 47.75 | kg | Devine: ideal body weight formula (Drug Intell Clin Pharm 1974) | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 93 | `targets.protein.ibw.devine.kg_per_inch_over_60` | 2.3 | kg per inch over 60 inches | Devine: ideal body weight formula (Drug Intell Clin Pharm 1974) | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 94 | `targets.body_fat.min_pct` | 3 | % body fat | SmartNutri working values, pending clinician review | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 95 | `targets.body_fat.max_pct` | 70 | % body fat | SmartNutri working values, pending clinician review | Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range) |  |  |  |
| 96 | `targets.macros.fat_pct_energy.default` | 25 | % of energy | Institute of Medicine: Dietary Reference Intakes for energy, carbohydrate, fibre, fat and protein (2005) | Is this appropriate for Indian adults? |  |  |  |
| 97 | `targets.macros.fat_pct_energy.min` | 20 | % of energy | Institute of Medicine: Dietary Reference Intakes for energy, carbohydrate, fibre, fat and protein (2005) | Is this appropriate for Indian adults? |  |  |  |
| 98 | `targets.macros.fat_pct_energy.max` | 30 | % of energy | ICMR-NIN Dietary Guidelines for Indians 2024 | Is this appropriate for Indian adults? |  |  |  |
| 99 | `targets.macros.carbs_reference_min_g` | 130 | g per day | Institute of Medicine: Dietary Reference Intakes for energy, carbohydrate, fibre, fat and protein (2005) | Is this appropriate for Indian adults? |  |  |  |
| 100 | `targets.macros.kcal_per_g.protein` | 4 | kcal per g | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 101 | `targets.macros.kcal_per_g.carbs` | 4 | kcal per g | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 102 | `targets.macros.kcal_per_g.fat` | 9 | kcal per g | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 103 | `targets.minors.min_age_for_targets` | 18 | years (minimum age) | SmartNutri working values, pending clinician review (why: WHO/FAO/UNU: protein and amino acid requirements in human nutrition (2007)) | Is this appropriate for Indian adults? |  |  |  |
| 104 | `targets.rounding.kcal_step` | 10 | kcal | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 105 | `targets.rounding.macro_g_step` | 1 | g | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 106 | `targets.plausible.height_cm.min` | 120 | cm | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 107 | `targets.plausible.height_cm.max` | 210 | cm | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 108 | `targets.plausible.weight_kg.min` | 30 | kg | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 109 | `targets.plausible.weight_kg.max` | 200 | kg | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 110 | `targets.plausible.weight_change_kg_per_day` | 2.0 | kg per day | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 111 | `targets.trend.min_weigh_ins_for_trend` | 3 | weigh-ins | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 112 | `targets.trend.alpha_per_day` | 0.25 | smoothing weight per day (0 to 1) | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 113 | `targets.trend.outlier_pct_from_trend` | 3.0 | % of trend weight | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 114 | `targets.trend.min_weigh_ins_for_rate` | 3 | weigh-ins | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 115 | `targets.trend.rate_window_days` | 7 | days | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 116 | `targets.projection.min_weigh_ins` | 6 | weigh-ins | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 117 | `targets.projection.min_span_days` | 14 | days | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 118 | `targets.projection.max_horizon_days` | 730 | days | SmartNutri working values, pending clinician review | Is this appropriate for Indian adults? |  |  |  |
| 119 | `targets.safety.rapid_loss_pct_bw_per_week` | 1.5 | % of body weight per week | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |
| 120 | `targets.safety.rapid_loss_weeks` | 3 | weekly check-ins in a row | SmartNutri working values, pending clinician review (why: CDC: losing weight) | Is this appropriate for Indian adults? |  |  |  |

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
| `targets.energy.equation` | mifflin_st_jeor_1990 | Is this rule appropriate? |  |  |  |
| `targets.goal_rates.lose.options_pct_bw_per_week` | 0.25, 0.5, 0.75, 1.0 | Is this rule appropriate? |  |  |  |
| `targets.goal_rates.gain.options_pct_bw_per_week` | 0.1, 0.25, 0.5 | Is this rule appropriate? |  |  |  |
| `targets.protein.ibw.formula` | devine | Is this rule appropriate? |  |  |  |

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
- **Mifflin-St Jeor: a new predictive equation for resting energy expenditure (Am J Clin Nutr 1990)**: https://doi.org/10.1093/ajcn/51.2.241 (link not yet verified)
- **CDC: losing weight**: https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html (link not yet verified)
- **Institute of Medicine: Dietary Reference Intakes for energy, carbohydrate, fibre, fat and protein (2005)**: https://doi.org/10.17226/10490 (link not yet verified)
- **Morton et al.: protein supplementation and resistance training gains, meta-analysis (Br J Sports Med 2018)**: https://pubmed.ncbi.nlm.nih.gov/28698222/ (link not yet verified)
- **Devine: ideal body weight formula (Drug Intell Clin Pharm 1974)** (link not yet verified)
- **SmartNutri working values, pending clinician review** (link not yet verified)

## Sign-off

Name: ____________________  Qualification and registration no.: ____________________

Signature: ____________________  Date: ____________
