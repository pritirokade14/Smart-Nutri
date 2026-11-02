# Data Sources, Standards and Regulation (India)

**Date:** 2026-11-02 · Many items come from secondary sources. Check anything marked [unverified] against primary texts before launch.

**Key takeaways**
- **Data:**
  - Open Food Facts India has ~15–25K products (ODbL, attribution and share-alike).
  - GS1 DataKart lists 42.8M products, but API access is paid.
  - IFCT and INDB need licence confirmation.
  - **We must build our own product table from confirmed scans.**
- **Scoring:**
  - Implement the **official Nutri-Score 2023** algorithm, labelled "calculated by SmartNutri".
  - FSSAI front-of-pack (FOP) warning labels are proposed but **not yet law**, so keep thresholds pluggable.
  - Use ICMR-NIN 2024 for daily limits.
- **Allergens:**
  - Use a synonym engine with three states: Contains / May contain / Unknown.
  - Never show "safe" when the label read is uncertain.
  - Check veg/vegan status against the ingredient list, not just the green dot.
- **Legal:**
  - DPDP Rules 2025 core duties apply from ~14 May 2027.
  - CDSCO regulates software that has a medical purpose, so avoid "manages/treats disease" claims.
  - Disclaimers and Play's Health apps declaration are required.

## 1. Data sources

| Source | Coverage | Access and licence | How we use it |
|---|---|---|---|
| **Open Food Facts** | India 15K+ products and 3.3K brands (Jun 2025); ~20K and 4.7K brands (Feb 2026); ~25K (tech review) | Free API (v3 for product reads; v2 is the only structured search; `cgi/search.pl` is legacy). Search is limited to 10 requests/min per IP. **User-Agent required.** Database under ODbL, content under DbCL, images under CC BY-SA | Lookup and alternatives only, not ground truth. Keep it in a separate `off_product_cache` table. Show the credit "(c) Open Food Facts contributors". Contribute scans back later. Get a legal review of share-alike [unverified]. |
| **IFCT 2017 (NIN)** | 528 raw foods | Copyright NIN/ICMR, no reuse licence found | Home-food logging (v2) once permission is granted |
| **INDB 2024** | 1,095 raw foods + 1,014 recipes, open access | Licence unclear [unverified]. Check the GitHub repo or ask the authors | Home and thali logging (v2) |
| **USDA FoodData Central** | Ingredients, few Indian foods | CC0, free key, 1,000 requests/hr [from memory, unverified] | Fallback only |
| **GS1 India DataKart** | 42.8M barcoded products, ~33K companies; includes a GTIN-to-FSSAI-licence field | Paid DataKart Premium, no public developer API. Contact datakart@gs1india.org | Possible partnership later |
| **GI tables** (Atkinson 2021) | 4,000+ items, few Indian | Free to read | A hint only, never a per-product score |

## 2. Scoring standards

**Nutri-Score 2023 update**
- Water is the only drink that can get an A.
- Milk and plant drinks now use the beverage algorithm.
- Sweeteners are penalised in drinks.
- Cheese always counts protein.
- Salt and sugar are scored more strictly.
- Fats use the ratio of saturated fat to total fat.
- Implement it from the Santé publique France document or OFF's `Nutriscore.pm`, **not Wikipedia** (which shows the 2017 version).
- Test against grades that OFF has already computed.
- If fibre or protein is unknown, mark the result partial or show "insufficient data".
- Label it "calculated by SmartNutri". Use of the logo in India is unclear [unverified].

**FSSAI front-of-pack labels**
- The 2022 Indian Nutrition Rating (star rating) draft has been shelved.
- **Supreme Court:**
  - 10 Feb 2026: urged warning labels.
  - 13 Aug 2026: questioned FSSAI's delay and reserved judgment.
  - ~28 Aug to Sep 2026: FSSAI proposed red pictorial warnings, rolled out in one phase [single exam-prep source, unverified].
- As of late May 2026 nothing was mandatory.
- **What we do:**
  - Use UK FSA "high" thresholds until FSSAI notifies its own:
    - Food: sugar 22.5, fat 17.5, saturated fat 5, salt 1.5 g/100 g.
    - Drinks: half those values.
  - Show "would get a red warning".
  - Never call our grade an "FSSAI rating".

**ICMR-NIN Dietary Guidelines 2024** (17 guidelines, May 2024)
- Limit salt, sugar and ultra-processed foods high in fat, sugar or salt.
- Jaggery and honey count as sugar.
- Non-sugar sweeteners and protein supplements are discouraged.
- The 5 g salt and ~30 g sugar per day figures appear only in secondary sources [unverified]. Confirm them in the official PDF.
- Use these for daily limits and goal advice. Use Nutri-Score for product grading. Always cite which standard a statement comes from.

**NOVA and glycemic index**
- NOVA comes from OFF's `nova_group` when ingredients are complete. Otherwise label it "estimated".
- Glycemic index is a hint only.

## 3. Allergens, ingredients and veg marks

**FSSAI Labelling & Display Regulations 2020** (gazetted 14 Dec 2020)
- Mandatory allergen declaration covers:
  - cereals containing gluten
  - crustaceans
  - milk, eggs, fish
  - peanuts and tree nuts
  - soy
  - sulphites at 10 mg/kg or more
- "May contain" covers cross-contact.
- A 2022 amendment exempts wheat-based glucose syrup and maltodextrin.
- A 2026 amendment takes effect from 1 Jul 2027 (other topics) [unverified].

**Allergen engine**
- A synonym and derivative map:
  - Milk: whey, casein, ghee, paneer.
  - Peanut: groundnut, arachis oil.
  - Gluten: maida, atta, sooji, malt, compounded hing.
  - Sulphites: INS 220–228.
  - Soy lecithin: INS 322.
  - Hindi names for all of these.
- Parse the ingredients and the Contains / May-contain lines separately.
- Three states: contains, may contain, unknown.
- The user's own allergy list is a hard block that the LLM can't override.

**Additives:** India uses INS codes, which are equivalent to E-numbers. Use OFF's additives taxonomy, with EFSA and IARC for risk [unverified].

**Veg and non-veg marks**
- Green means veg and brown means non-veg (the exact symbol shapes are disputed; verify).
- FSSAI acted in 2019 against green-dot products containing animal ingredients.
- A mandatory "VEGAN" logo is due from 1 Jul 2027.
- **Always cross-check against ingredients:** gelatin, carmine (E120), shellac (E904), rennet, lard, fish sauce, bone phosphate, and D3 from lanolin.

**Jain and halal:** there is no FSSAI mark for either.
- Jain excludes onion, garlic and root vegetables.
- Halal is certified privately.
- Treat both as best-effort ingredient filters and say so in the app.

## 4. Regulation and legal

**DPDP Act 2023 and DPDP Rules 2025** (notified 13–14 Nov 2025, phased)
- Board provisions applied immediately. Consent managers apply from ~14 Nov 2026.
- **The main duties apply from ~14 May 2027:**
  - notice and consent
  - breach reporting
  - security safeguards
  - verifiable parental consent for under-18s (Rule 10)
- I could not confirm a special health-data category [unverified].
- Processing health data at scale could lead to designation as a Significant Data Fiduciary.
- **Build now:**
  - A purpose-specific consent notice in English and Hindi, with easy withdrawal.
  - An 18+ account holder, with children as profiles.
  - A retention and deletion policy.
  - A breach plan.
  - No identifiable health data sent to an LLM without consent; strip identifiers.
  - No behavioural ads aimed at children.

**CDSCO** (guidance CDSCO/MD/GD/MDSW/01/2026)
- Software is a medical device when its intended use is medical (diagnosis, treatment or management of disease), classified under MDR 2017.
- **Position the app as general nutrition information.** Avoid claims that it "manages diabetes". Get a regulatory opinion before shipping condition profiles beyond general guidance (kidney disease, pregnancy).

**FSSAI Advertising & Claims Regulations 2018**
- They govern food businesses' claims. Our copy must not imply that products prevent or cure disease.
- The claim checker uses the Schedule I thresholds (verify the exact values).

**Disclaimers** (our recommendation; no statute found)
- "Not medical advice; consult your doctor or dietitian."
- Extra caution for pregnancy, children and kidney disease.

**App stores**
- Google Play requires the **Health apps declaration**, and Health Connect data is sensitive.
- Apple 5.1.3 forbids using HealthKit data for ads or data mining, and forbids storing it in iCloud [secondary, unverified].

**Health platforms**
- Health Connect: Android 9+, built in on Android 14+. Use in v2.
- CGM integrations: none found in India, and they raise medical-device risk. Defer.
- ABDM: milestones are ABHA, then acting as a Health Information Provider (HIP), then a Health Information User (HIU); sandbox at sandbox.abdm.gov.in. Optional; skip at launch.

## Must do before launch

1. Implement the official Nutri-Score 2023. Test it against OFF grades. Label it "calculated by SmartNutri".
2. Allergen synonym engine with three states. Never "safe" when the label read is uncertain.
3. Cross-check veg and vegan status against ingredients, not just the dot.
4. OFF attribution and User-Agent, with OFF data kept separate. Get an ODbL legal review.
5. Confirm IFCT and INDB licences with ICMR-NIN before using them.
6. Medical disclaimer and a "consult a doctor" flow. Get a regulatory opinion before kidney or pregnancy modes. Make no treatment claims.
7. DPDP readiness: consent, an 18+ gate, deletion, a breach plan, minimal data sent to the LLM.
8. Play Health apps declaration. Re-check the FSSAI FOP ruling before launch.
9. Verify [unverified] items against primary sources: the FSSAI gazette, the ICMR-NIN PDF and the DPDP Rules text.

## Sources

- **Open Food Facts:**
  - India stats: https://indiafoodstats.blogspot.com/2025/06/open-food-facts-june-2025-stats.html
  - Licences: https://huggingface.co/datasets/openfoodfacts/product-database/blob/main/README.md · https://wiki.openfoodfacts.org/ODBL_License
  - Reuse terms: https://support.openfoodfacts.org/help/en-gb/12-api-data-reuse/94-are-there-conditions-to-use-the-api
  - Product attributes: https://openfoodfacts.github.io/openfoodfacts-server/api/explain-product-attributes
- **INDB and IFCT:** https://pmc.ncbi.nlm.nih.gov/articles/PMC11277795 · https://nin.res.in/ebooks/IFCT2017.pdf
- **GS1 India:** https://gs1india.org/datakart/datakart-premium
- **Nutri-Score 2023:** https://www.santepubliquefrance.fr/import/nutri-score-2023-update · https://www.nature.com/articles/s43016-024-00920-3
- **FSSAI front-of-pack:**
  - https://theprint.in/judiciary/fssai-puts-brakes-on-star-rating-of-packaged-food-underlines-need-for-more-research-before-sc/2857081
  - https://www.livelaw.in/top-stories/why-one-year-needed-to-place-front-of-pack-labels-on-packaged-food-supreme-court-asks-fssai-reserves-judgment-552122
  - https://www.drishtiias.com/daily-updates/daily-news-analysis/fssai-proposes-front-of-pack-warning-labels-for-packaged-foods/print_manually
- **ICMR-NIN 2024:** https://thesouthfirst.com/news/icmr-releases-dietary-guidelines-for-indians-after-13-years-says-no-to-protein-supplements
- **GI tables:** https://nutrition.org/ajcn-publishes-international-tables-of-glycemic-index-and-glycemic-load-values-2021-a-systematic-review/
- **Allergen labelling:** https://foodsafetyworks.com/insights/allergen-labelling-changes-are-your-labels-updated
- **Veg and vegan marks:**
  - https://www.mondaq.com:443/india/corporate-and-company-law/1145070/green-or-brown-an-overview-of-the-fssai39s-labelling-regulations
  - https://fssai.gov.in/upload/media/FSSAI_News_Animal_FNB_11_10_2019.pdf
  - https://vegconomist.com/politics-law/india-require-standardized-vegan-logo-food-packaging-2027/
- **DPDP:** https://www.mondaq.com/india/data-protection/1713500/regulatory-update-notification-of-the-digital-personal-data-protection-rules-2025 · https://www.azbpartners.com/bank/update-indias-digital-personal-data-protection-framework-comes-into-effect/
- **CDSCO:** https://www.cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/Guidance-document-on-Medical-Device-Software-under-MDR-2017.pdf
- **FSSAI claims:** https://mail.fssai.gov.in/upload/uploadfiles/files/Compendium_Advertising_Claims_Regulations_14_12_2022.pdf
- **Google Play:** https://support.google.com/googleplay/android-developer/answer/14738291 · https://developer.android.com/health-and-fitness/health-connect/availability
- **ABDM:** https://abdm.gov.in:8081/uploads/HIP_HIU_Guidelines_f85df336ec.pdf
