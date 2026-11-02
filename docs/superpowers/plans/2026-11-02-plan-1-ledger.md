# SDD ledger — plan: docs/superpowers/plans/2026-11-02-plan-1-rules-engine.md

Spec: docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md (§6). Branch v1-rebuild (not main; no separate worktree — isolated branch is the workspace).
Start commit: 5f943ff. Models: implementers sonnet; task reviewers opus (user CLAUDE.md: Opus for code review); re-reviews sonnet; final review opus.

## Pre-flight scan

### Shared files / interfaces (producer → consumer)
| Tasks | Produced | Consumed | Finding |
|---|---|---|---|
| 1→all | apps/api pyproject, app/scoring pkg | every task imports app.scoring.* | ok |
| 2→3..10 | models.py names (Nutrients, Product, Member, Reason, Status.rank, enums) | all | ok — names identical in every Interfaces block |
| 2→5 | tests/unit/scoring/conftest.py | Task 5 adds `cfg` fixture to same conftest | ok — additive edit |
| 3→5,6,7,8 | find_terms(texts, terms, exclude), normalize, ScoringConfig fields | warnings/allergens/diet/claims | ok — longest-first + plural rule pinned in Task 3 |
| 4→9,10 | NutriScoreResult(grade, points, partial, approximated, reason) | conditions (grade), verdict | ok |
| 5→8,9 | added_sugar_terms, hidden_sugars, sodium_additives, ingredient_hits, high_in | claims (no_added_sugar), conditions | Task 8 test compares params["ingredients"] to a LIST; Task 5 returns tuples → Ruling R3 |
| 6→7,8,10 | ingredients_known, detect_allergens, allergen_reasons | diet, claims, verdict | ok — ordering 6 before 7/8 correct |
| 8→9,10 | ClaimCheck, check_claims | conditions (misleading_sugar_claim), verdict | ok |
| 9→10 | condition_reasons(product, member, nutriscore, claims, cfg) | evaluate_member | evaluate_member signature has no nutriscore/claims args → take from report |
| 2 (sanitized)→10 | Nutrients.sanitized() | build_report | evaluate_member must also see the sanitized product → Ruling R4 |

### Per-task self-consistency
| Task | Check | Finding |
|---|---|---|
| 1 | git rm list vs current apps/api (also has AGENTS/CLAUDE/README/.env*) | ok — only listed prototype paths removed; .env* ignored |
| 2 | fixture table vs Task 4/5/6/9/10 expectations (recomputed by hand) | ok |
| 2 | sanitized() bounds hard-coded vs Global Constraint "nothing threshold-like in .py" | conflict → Ruling R1 |
| 3 | tests vs normalize/find_terms rules (INS codes, Devanagari sort order, longest-first) | ok |
| 4 | expected grades/points recomputed from pinned tables (curd B/1, biscuit D/15, namkeen E/25, oats A/-5, cola E/11) | ok; Step 0 may change tables → implementer recomputes |
| 5 | high_in expectations vs thresholds.yaml | ok |
| 6 | soy MAY_CONTAIN via ins322, may-contain statement, kiwi literal | ok |
| 7 | jain longest-first → ("garlic powder","onion powder") | ok |
| 8 | oats 13.37% < 20 → contradicted/below_minimum; pattern order | ok |
| 9 | child band for age 8 → 24 g; 31.8 g = 132% | ok; child upper age 13 not in thresholds.yaml → Ruling R2 |
| 10 | goldens recomputed (biscuit AVOID/AVOID/CAUTION, namkeen AVOID×3, curd OK/AVOID/AVOID, unknown, dropped sugars→UNKNOWN) | ok given R4 |

### Rulings
- Ruling R1: Task 2 plausibility bounds ([0,100] g, sodium ≤40000 mg, kcal ≤900, fvl ≤100) stay as named module constants in models.py — they are physical plausibility limits, not health thresholds, and Task 2 precedes the config loader — cost if wrong: small refactor to move them into YAML.
- Ruling R2: Task 9 adds `max_age: 13` under `conditions.child` in thresholds.yaml and reads child range as `infant.max_age <= age < child.max_age` — spec says thresholds live in YAML; plan text hard-coded 13 — cost if wrong: one YAML key.
- Ruling R3: ClaimCheck params lists are Python lists (e.g. `{"ingredients": ["maltodextrin"]}`) — Task 8 test asserts list equality and JSON output wants lists — cost if wrong: none (to_dict normalises anyway).
- Ruling R4: Task 10 `analyze()` sanitizes the product once and passes the sanitized product to both build_report and evaluate_member; build_report also sanitizes idempotently so it is safe standalone — spec §6 says implausible values become missing → unknown; plan's golden test requires it — cost if wrong: none observable.

## Tasks
- Ruling R5: `cfg` fixture moves from Task 5 to Task 3 (plan text edited) — user asked for parallel execution; Task 5 and Task 6 both need it and would otherwise race on conftest.py — cost if wrong: none.
- Ruling R6 (user instruction 2026-11-03 overrides skill's "never parallel implementers"): run independent tasks in parallel waves, each parallel implementer in its own git worktree (Agent isolation=worktree); controller cherry-picks their commits onto v1-rebuild in task order, then reviews. Waves: [T1] → [T2] → [T3 ∥ T4] → [T5 ∥ T6] → [T7 ∥ T8] → [T9] → [T10]. Reviews of a wave run in parallel too — cost if wrong: a cherry-pick conflict, resolved by re-running the later task on the merged head.
Task 1: implemented 331a6d1 (review pending)
Task 1: complete (commits 5f943ff..331a6d1, review clean)
Task 1: minor (deferred): tests/ has no __init__.py and pytest uses prepend import mode — duplicate test basenames would collide; consider --import-mode=importlib
Task 2: implemented a67bc4d (review pending); note: RED run showed missing-fixture errors rather than ModuleNotFoundError (models written first)
Task 2: complete (commits 331a6d1..a67bc4d, review clean)
Task 2: minor (deferred): sanitized() applies grams bound to any unnamed field — prefer explicit {field: upper} map
Task 2: minor (deferred): sanitized() tests lack negative/sodium/fvl/inclusive-boundary cases
Task 2: minor (deferred): Reason.params is a mutable dict in a frozen dataclass (unhashable) — only matters if later code hashes Reasons
Task 4: implemented 7925f34 on branch worktree-agent-a7a49a8c14d867118 (review pending)
- Ruling R7: Task 4 beverage sugar thresholds use the official OFF 2023 values (0.5,2,3.5,5,6,7,8,9,10,11), not the plan's — spec §6 says official Nutri-Score 2023; plan explicitly said "if any value differs, use the official value"; cola expectation 11→12 (still E) — cost if wrong: none, matches source.
- Ruling R8: isolated worktrees are created from main (b7dc35e), not v1-rebuild; every worktree implementer must `git reset --hard <base>` first; worktree agents cannot write into the main checkout, so the controller transcribes their reports — cost if wrong: a task built on the wrong base (caught by review package base).
Task 3: implemented 8fb439c → cherry-picked 63aa6eb (review pending)
Task 4: cherry-picked 7925f34 → 035ef29 (review pending). Combined suite after picks: 24 passed, ruff clean.
Task 5: implemented a586591 → cherry-picked 3dc7b22 (review pending)
Task 6: implemented 3f095d7 → cherry-picked de9420b (review pending)
Task 4: complete (commits a67bc4d..7925f34 → 035ef29, review clean; tables verified vs official OFF Nutriscore.pm)
Task 4: minor (deferred): untested branches — beverage sweetener +4, non-zero FVL points, salt from sodium_mg, missing energy/salt, partial=False, beverage protein
Task 4: minor (deferred): water returns grade A with points=None (contract: grade set ⇒ points set?) — decide/document
Task 4: minor (deferred): avoidable `# type: ignore[arg-type]` — type _grade as Literal
Task 4: minor (deferred): insufficient_data results always approximated=False even for CHEESE/FAT
Task 4: minor (deferred): FAT category approximated (official fats/oils/nuts/seeds rules not implemented); CHEESE flagged approximated though effectively exact
Task 3: review — Needs fixes: CRITICAL exclude phrases match across ingredient boundaries (["desiccated coconut","milk powder"] → milk lost; "Almond, Milk"; "Peanut, Butter"); IMPORTANT INS/E formats "(220, 223)", "E 220", "INS. 223", "ins: 220", "(322, 471)" not normalised (sulphite/soy missed)
- Ruling R9: find_terms must not let any term or exclude phrase span an ingredient boundary — split every input text into segments on , ; : ( ) [ ] / | । and on item boundaries, and run exclude-removal + term matching per segment; plan text "replace punctuation with spaces / remove excludes first" is overridden by spec safety ("unknown ≠ safe"; allergen synonyms must be detected) — cost if wrong: a multi-word term that legitimately contains a separator stops matching (none in current data).
- Ruling R10: normalize also rewrites `e 220`, `ins. 223`, `ins: 220`, and every 3–4 digit code inside a parenthesised code list like `(220, 223)` / `(322, 471)` to `ins<digits>`, guarded so ordinary numbers (e.g. "vitamin e 1000 iu", "500 g") are not rewritten — cost if wrong: false allergen flags on odd numeric text (safe side).
- Ruling R11: allergen 'possible' terms found in allergen_statement → at least MAY_CONTAIN (security review finding; e.g. 'Contains: nuts') — folded into Task 6 fix round — cost if wrong: extra warnings (safe side).
Task 7: implemented 54e74fd → cherry-picked 648585c (review pending)
Task 5: complete (commits 035ef29..a586591 → 3dc7b22, review clean)
Task 5: minor (deferred): add tests for sodium_mg fallback via high_in, exact-at-threshold, added_sugar_terms overlap ("invert sugar" not also "sugar") — all behave correctly when probed
Task 5: minor (deferred): ingredient_hits raises bare KeyError on unknown list_name (fail-fast, acceptable)
Task 8: implemented ae02eaf → cherry-picked 88c8d8d (review pending)
Task 3: fix round 1 implemented a649165 → cherry-picked af289e9 (re-review pending)
Task 6: review — Needs fixes: CRITICAL cross-boundary excludes (covered by Task 3 R9 fix — verify); CRITICAL canonical allergen names in statements not detected ("Contains: Gluten", "TREE NUTS", "Crustaceans", "Shellfish", "Sulphur dioxide", "May contain gluten"); IMPORTANT blank strings count as known ingredients; IMPORTANT member key variants ("tree nut","tree-nut","dairy","nuts","shellfish") fall through to literal matching
- Ruling R12: canonical/category names are added to allergens.yaml contains lists (gluten; tree nut/tree nuts/nuts→ stays possible; crustacean/shellfish; sulphur dioxide/sulfur dioxide/so2; plus Hindi where standard); member-key normalisation (strip, lower, spaces/hyphens→_) + alias map {dairy→milk, lactose→milk, nuts→tree_nut, tree nuts→tree_nut, shellfish→crustacean, wheat→gluten, groundnut→peanut, soya→soy, sulfite→sulphite} kept as a module constant in allergens.py (data-like but not a health threshold) — cost if wrong: alias table moves to YAML later.
Task 7: review — Needs fixes: CRITICAL veg_mark=="non_veg" ignored (tuna/salmon + brown dot pass for VEG/JAIN); CRITICAL allergen_statement not searched for diet terms ("Contains: Egg, Milk" passes VEG/VEGAN); IMPORTANT (matcher/data) nukta प्याज़ not matching, -ies plurals (anchovies), अंडे, "albumen" missing; MINOR blank ingredients known (covered by Task 6 fix), duplicate assertion in test_diet.py:31-33, missing eggetarian tests
- Ruling R13: veg_mark=="non_veg" → diet_violation AVOID {"diet","ingredients": [...found], "mark":"non_veg"} for VEG/VEGAN/JAIN even when no term matched; EGGETARIAN with brown dot and no non-veg term found → diet_unknown UNKNOWN {"diet":"eggetarian","mark":"non_veg"} (brown dot also covers egg-only) — cost if wrong: over-warning (safe side).
- Ruling R14: diet checks search ingredients + allergen_statement (not may_contain_statement — cross-contact is not a diet violation) — cost if wrong: none.
- Ruling R15: normalize strips the Devanagari nukta (U+093C) so nukta/no-nukta spellings match; plural tolerance adds y→ies; data adds "albumen" (diet.yaml egg + allergens.yaml egg) and "अंडे" (diet.yaml egg + allergens.yaml egg) — split: ingredients.py + diet.yaml → Task 3 round 2; allergens.yaml egg terms → Task 6 fix agent — cost if wrong: none.
Task 3: fix round 1/5 (2 addressed, 0 open — R9 boundary-safe matching, R10 INS formats; commits de9420b..a649165→af289e9); fix round 2 in progress (R15 nukta, -ies plurals, egg synonyms — from Task 7 review)
Task 3: minor (deferred): newline is a segment separator — OCR-wrapped multi-word ingredients ("skimmed\nmilk powder") split; INS letter suffix (150d) dropped (pre-existing)
Task 8: review — Needs fixes: CRITICAL "No Sugar Added" matches sugar_free pattern (sugars-only) → maltodextrin product SUPPORTED; IMPORTANT "high in protein"/"rich in protein" fall to source_of_protein; IMPORTANT missing tests (drink limits, salt×400 fallback, no_added_sugar SUPPORTED path, ≤/≥ boundaries); MINOR rounding 2dp makes 0.504 look like 0.5
- Ruling R16: claim patterns amended — no_added_sugar row (tried first) gains "no sugar added", "zero added sugar", "without added sugar", "no added sugars"; high_protein row gains "high in protein", "rich in protein"; params rounded to 3 dp (exceeds → never shown equal to limit) — spec authority: misleading sugar claims must be caught for diabetic users — cost if wrong: none.
Task 9: implemented 04a147c → cherry-picked bacfe3e (review pending)
Task 6: fix round 1 implemented cbf0895 → cherry-picked ae4e170 (re-review pending)
Task 3: fix round 2 implemented e324e36 → cherry-picked 8af171d (re-review pending)
Task 7: fix round 1 implemented 20ec32c → cherry-picked 95a8e45 (re-review pending)
Task 3: fix round 2/5 (3 addressed, 0 open — nukta, -ies plurals, egg synonyms; commits af289e9..e324e36→8af171d)
Task 3: complete (commits a67bc4d..e324e36 → 63aa6eb, af289e9, 8af171d; 2 fix rounds, review clean)
Task 3: minor (deferred): nukta strip makes "गुड" (no nukta) match "गुड़" (intended consequence)
Task 6: fix round 1/5 (6 addressed, 0 open — cross-boundary excludes, canonical names, blank ingredients, key aliases, possible-terms in statement, egg synonyms; commits af289e9..cbf0895→ae4e170)
Task 6: complete (commits 035ef29..cbf0895 → de9420b, ae4e170; 1 fix round, review clean)
Task 6: minor (deferred): alias wheat→gluten / lactose→milk over-inclusive; reason params show canonical key ("gluten") not member's word — UI should map back
Task 6: minor (deferred): multi-word unknown member key ("kiwi fruit") only matched as literal phrase (pre-existing)
Task 8: fix round 1 implemented 573828f → cherry-picked be9d8cb (re-review pending)
Task 7: fix round 1/5 (3 addressed, 0 open — brown dot R13, allergen statement R14, tests; commits af289e9..20ec32c→95a8e45)
Task 7: complete (commits de9420b..20ec32c → 648585c, 95a8e45; 1 fix round, review clean)
Task 7: minor (deferred): brown-dot VEG/VEGAN/JAIN + unknown ingredients emits AVOID plus redundant diet_unknown (AVOID dominates)
Task 10: implemented 34f5b86 → cherry-picked fb8193d (review pending)
Task 8: fix round 1/5 (4 addressed, 0 open — No Sugar Added, high in protein, tests, 3dp; commits 8af171d..573828f→be9d8cb)
Task 8: complete (commits de9420b..573828f → 88c8d8d, be9d8cb; 1 fix round, review clean)
Task 8: minor (deferred): "No Refined Sugar Added" matches no pattern (unverified, not misjudged); "Added Sugar Free" → sugar_free sugars-only
Task 10: full suite on main line after pick: 134 passed, ruff clean
Task 9: review — Needs fixes: CRITICAL caffeine never checked for infants (diet cola/coffee → OK for age <2); CRITICAL infant/child ingredient rules pass when ingredients unknown; IMPORTANT condition/goal matching case-sensitive ("Diabetes", "Weight Loss" → []); IMPORTANT child group: missing salt gives no nutrient_missing; IMPORTANT carbs_per_serving silently skipped without serving size; MINOR child salt_high lacks salt_g param (two shapes for one code); MINOR missing tests (sodium-only hypertension, band edges 2/7/11, child no serving, infant honey/salt, prediabetes/pcos)
- Ruling R17: (a) infant group also applies the caffeine rule → ("infant_caffeine", AVOID); (b) when infant group active, or child group active (for its caffeine check), and allergens.ingredients_known(product, cfg) is False → ("ingredients_missing", UNKNOWN, {"rule": group}) once per group; (c) member.conditions and goal normalised (strip, lower, spaces/hyphens→"_") before matching applies_to; (d) child group calls need("salt") so missing salt → nutrient_missing UNKNOWN; (e) carbs_per_serving falls back to per-100 g carbs when serving_size_g is None, params gain {"basis": "per_100g"|"per_serving"}; (f) child salt_high reason carries {"salt_g"} like hypertension's — spec authority: unknown ≠ safe; infants are the most vulnerable members — cost if wrong: more CAUTION/UNKNOWN for infants and diabetics (safe side).
Task 10: review — Needs fixes: CRITICAL dedupe key (code, severity, nutrient, allergen, diet) drops distinct reasons (3 contradicted sugar claims → 1 misleading_sugar_claim); IMPORTANT nutrient_missing for same nutrient under different rules collapsed; IMPORTANT test_no_duplicate_reasons locks in lossy key; MINOR `cfg = cfg or load_config()` → `if cfg is None`; MINOR ProductReport holds plain dicts (noted only); MINOR standalone build_report lacks member custom allergen keys (verdicts unaffected)
- Ruling R18: dedupe only exact duplicates — key (code, severity, frozen params) with dicts→sorted item tuples, lists→tuples — controller dispatch already required exact-duplicate semantics — cost if wrong: none.
Task 10: fix round 1 implemented c47d8fc → cherry-picked 02106dd (re-review pending)
Task 9: fix round 1 implemented 5a926e4 → cherry-picked 81b9ceb (re-review pending)
Task 10: fix round 1/5 (4 addressed, 0 open — exact-duplicate dedupe R18, nutrient_missing per rule, test rewrite, cfg is None; commits fb8193d..c47d8fc→02106dd)
Task 10: complete (commits 8af171d..c47d8fc → fb8193d, 02106dd; 1 fix round, review clean)
Task 10: minor (deferred): _freeze treats 1 / 1.0 / True as equal (negligible); ProductReport holds plain dicts (mutable)
Task 9: fix round 1/5 (7 addressed, 0 open — R17 infant caffeine, unknown ingredients, normalisation, child salt, carbs basis, params, tests; commits fb8193d..5a926e4→81b9ceb)
Task 9: complete (commits 88c8d8d..5a926e4 → bacfe3e, 81b9ceb; 1 fix round, review clean)
ALL TASKS COMPLETE at 81b9ceb — 148 passed, ruff clean. Final review range 5f943ff..81b9ceb

## Final review
Nutrition-safety review (opus): BLOCK — B1 separators (& + " and " ". ") let excludes hide allergens + "almond milk chocolate"; B2 allergen term gaps (dairy whitener, mawa, lactitol/ins966, milk fat/butter oil, cashewnut, chironji, chilgoza/pine nut, brazil nut, peanut.possible nuts/nut, rawa, vermicelli, couscous, तिल, tahini, salmon, mackerel, सोयाबीन, tofu, सरसों, ins1105, chandrabindu U+0901 fold, Marathi शेंगदाणा/गहू); B3 free-text member allergen keys fail silently ("peanut allergy", "nut", "celiac", "cow's milk", "prawns", "seafood", "sesame seeds"); B4 placeholder ingredients ("-", "N/A", "see pack", "Ingredients:") count as known; B5 extraction_confidence ignored by nutrient rules; B6 unrecognised conditions dropped ("Type 2 Diabetes", "T2DM", "diabetic", "pre-diabetes", "PCOD", "high bp", "gestational diabetes"); B7 serving_size_g not sanitised (0/-10/NaN → ok); B8 drinks use food sugar bands for diabetics (cola → caution only); B9 diet list gaps (tuna, salmon, ins441 gelatin, bacon, ham, turkey, squid, lobster, oyster sauce, cod liver oil, collagen, seafood, keema, animal fat, चिकन, मछली; dairy drift vs milk terms; Jain aloo/kanda/pyaz/lehsun/adrak/gajar/आलू/अदरक/कांदा/लसूण/shallots/leek); B10 infant/child list gaps (शहद, मध, साखर, khandsari, apple juice (concentrate), sodium chloride, green tea extract, tea/chai/चाय, kola nut; infant nutrient-based rules).
Should-fix S1 salt() prefers salt_g over conflicting sodium; S2 no cross-field checks (sugars>carbs, sat>fat, macro sum>100); S3 claim patterns sugarfree/0% sugar/0g sugar/sugarless, no_refined_sugar, diabetic friendly/low GI; S4 child per-100g floor; S5 YAML term lists lack PENDING headers/sources; S6 WATER category with sugar graded A; S7 age None + caffeine; S8 Jain mushroom/yeast/spices/natural flavour, sonth, sabudana.
Final code review (opus): merge WITH FIXES — C1 Hindi coverage; I1 nuts→peanut; I2 serving_size not sanitised (inf breaks JSON); I3 bare-str tuple fields + unrecognised conditions; I4 diabetic cola only caution; I5 multi-word custom allergens; I6 low confidence ignored by nutrient rules; minors M1–M11; triage: T6 multi-word key + T8 "Added Sugar Free" fix-before-merge, rest can wait.
- Rulings R19–R28 (separators/partial excludes, free-text allergen keys + allergen_unrecognised, placeholder ingredients, salt = max(salt_g, sodium-derived), cross-field plausibility, condition aliases + condition_unrecognised, low confidence → nutrient_missing, drink sugar bands for diabetics, infant nutrient rules, added_sugars caution + claim pattern additions) — full text in final-fix-wave.md — cost if wrong: more UNKNOWN/CAUTION/AVOID (safe side), all thresholds pending clinician review.
- Ruling (parked) S7 age None + caffeine — Plan 5 contract requires birth_year for every member — cost if wrong: adult-default for an ageless child.
- Ruling (parked) S8 Jain spices/natural flavour/sonth/sabudana — needs community/dietitian decision — cost if wrong: Jain members may see an unlabelled garlic/onion in "spices".
- Ruling (parked) M1 deep-freeze config → Plan 2; M6 negated statements over-warn (safe side) → Plan 4 extraction; child total vs free sugar → clinician.
Fix wave dispatched as 3 parallel fixers (user instruction: parallel) with disjoint files: A matcher+allergens (opus), B term data (sonnet), C models/conditions/claims/nutriscore/verdict (opus).
- Ruling R29: added_sugars must NOT include plain 'apple juice' / 'fruit juice' (a 100% juice may lawfully claim 'no added sugar' under FSSAI); keep 'juice concentrate', 'apple juice concentrate', 'fruit juice concentrate' (added sugars). Juice's own sugar is still caught by blood_sugar drink bands (R26) and infant_sugar_high (R27) — cost if wrong: juice-sweetened products without the word 'concentrate' escape the no_added_sugar check (still caught by sugar numbers).
Final fix B: f68b99f+1f39062 → cherry-picked (head 90e2efd); B1–B6 + R29; 219 passed in worktree
Final fix A: a109010 → cherry-picked 0b32f50; A1–A7; 264 passed in worktree
- Ruling (accept deviation) A1: partial exclude raises MAY_CONTAIN only when the exclude phrase itself contains one of that allergen's terms (avoids "desiccated coconut"/"eggplant" false AVOIDs) — cost if wrong: none observed.
- Ruling (accept deviation) A4: partly recognised member keys also keep literal phrase matching (e.g. "coconut milk") — cost if wrong: extra warnings.
- Ruling R30: peanut.possible keeps only "nuts" (drop singular "nut"); peanut.exclude += tree nuts, cashew nuts, pine nuts, brazil nuts, hazel nuts, macadamia nuts, pecan nuts, mixed tree nuts — generic "contains nuts" still warns peanut-allergic users, but named tree nuts no longer AVOID them — cost if wrong: a label saying only "cashew nuts" while also containing peanut traces relies on the may-contain line.
- Parked: "vermicelli" flags rice vermicelli as gluten CONTAINS; "cocoa butter equivalent" milk MAY_CONTAIN; member key "E220" literal — dietitian review list. New reason codes allergen_unrecognised, condition_unrecognised (and others from Fixer C) need i18n keys + fixtures → Plan 2/3 (added to CROSS-PLAN-NOTES).
Final fix C: 0b16a2c → cherry-picked 9db6f77; C1–C14; 230 passed + 1 strict xfail (diabetic+cola AVOID) in worktree
- Ruling (accept deviations) C: added_sugars reason excludes terms already reported as hidden_sugars; low_sodium claim uses higher of sodium_mg and salt×400 (consistent with R22); refined_sugar_terms in thresholds.yaml.
- Ruling R31: blood_sugar drink bands: avoid_sugars_g.drink 5.0 (basis: UK Soft Drinks Industry Levy 5 g/100 ml), caution_sugars_g.drink 2.5 — diabetic + cola → AVOID; xfail becomes a real test — cost if wrong: 100% juices also AVOID for diabetics (defensible; pending clinician).
- Ruling R32: infant_sugar_high (numeric) applies only when ingredients are NOT known; with known ingredients the infant_added_sugar term rule decides (avoids flagging infant formula lactose) — cost if wrong: naturally very sweet infant foods with known ingredients rely on term rules.
- Ruling R33: no_refined_sugar matching excludes unrefined sugars (coconut sugar, palm sugar, date sugar, jaggery, gur, khandsari) via a YAML exclude list — cost if wrong: none.
- Ruling R34: unrecognised GOALS are ignored (not condition_unrecognised); only unrecognised CONDITIONS yield UNKNOWN — goals are preferences, conditions are safety — cost if wrong: none.
- Ruling R35: Category.WATER with contains_sweeteners is also scored as BEVERAGE (official 2023: sweetened waters are beverages) — cost if wrong: none.
Final fix A follow-up: 54c9edc → cherry-picked 32dd1ad (R30 + dairy sync + modifier_excludes)
- Ruling R36 (accept narrowing of R19): a partial exclude raises MAY_CONTAIN only when more words follow the excluded phrase in the segment ("almond milk chocolate", "peanut butter cookies"); an exclude ending the segment stays excluded ("roasted cashew nuts", "light coconut milk") — cost if wrong: a product named "<something> coconut milk" that also contains dairy relies on its other ingredients.
Final fix C follow-up: cd0d03e → cherry-picked 9ce5f28 (R31–R35); main line: 437 passed in 0.38s
Scoped safety re-review (opus): BLOCK on 2 residuals — infant + plain fruit juice OK (R29×R32 interaction); singular "nut" detected for nobody. All of B1–B10, S1–S6, C1, I1–I6 ADDRESSED or PARKED. Minors: modifier rule makes "cashew nuts pieces" peanut MAY_CONTAIN; "Refined sugar free" → sugar_free; water with unknown nutrients graded A; blood_sugar lacks unknown-ingredients guard; infant thresholds cite only a ruling; excluded_hits dead code; condition variants (Diabetes Type 2, HTN, मधुमेह) → UNKNOWN. Over-warning list recorded for dietitian (rice vermicelli/rava gluten; pistachio/almond "nuts" peanut; coconut cream/butter beans milk; soya keema veg; chai masala/herbal tea caffeine; plain milk 250 ml age 2 AVOID; coconut water diabetic; infant rice cereal salt).
- Ruling R37: infant-only free-sugar term list `infant_free_sugars` (juice, fruit juice, apple/orange/grape/mango juice, fruit puree concentrate, fruit concentrate) in ingredients.yaml, checked in the infant group → infant_added_sugar AVOID (params {"ingredients"}) — closes the R29×R32 gap — cost if wrong: infant-safe 100% juice flagged (WHO advises against juice under 2 anyway).
- Ruling R38: add `nut` to tree_nut.possible and peanut.possible; rewrite peanut excludes in singular form (tree nut, cashew nut, pine nut, brazil nut, hazel nut, macadamia nut, pecan nut, mixed tree nut, pistachio nut, almond nut) so plurals are still covered; the modifier rule must not let these excludes raise peanut MAY_CONTAIN ("cashew nuts pieces" → no peanut) — cost if wrong: none.
- Ruling: residual minors 3–9 and the over-warning list are PARKED for the dietitian review / Plan 5 condition picker (recorded in CONTEXT.md open items) — no second fix wave per process beyond the two load-bearing residuals.
Residual fix: 67db27f → cherry-picked (R37 infant juice, R38 singular nut); controller probe verified: infant+apple juice AVOID; 'May contain nut traces'/'Contains: Milk, Nut' → peanut & tree_nut AVOID; 'cashew nuts pieces' → peanut OK, tree_nut AVOID; 572 passed.
PLAN 1 COMPLETE.
