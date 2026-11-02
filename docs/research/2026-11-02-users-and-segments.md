# Users and Segments (India-first)

**Date:** 2026-11-02

**Key takeaways**
- Demand is real:
  - 101M Indians have diabetes, 136M have prediabetes, and 35.5% of adults have hypertension.
  - Most shoppers read only the expiry date.
  - FoodPharmer's "Label Padhega India" movement has ~4.85M followers.
- Barcode databases miss most Indian products. Open Food Facts has ~15–25K Indian products out of ~90K sold, so label-photo scanning is a real advantage.
- v1 targets three groups:
  - **Blood sugar** (diabetes, prediabetes, PCOS)
  - **Family health manager** (kids and elderly parents)
  - **Weight loss** (including GLP-1 users)
- What users need across segments:
  - Several conditions and several family members in one account
  - Numbers per serving, not per 100 g
  - A claim checker
  - Voice in vernacular languages
  - An explained "why", plus a better alternative to buy

## Market context

- **Chronic disease (ICMR-INDIAB):** 101M with diabetes, 136M with prediabetes, hypertension in 35.5% of adults. Chronic kidney disease affects 138M (Lancet/GBD 2023).
- **Overweight or obese (NFHS-6, 2026):** 30.7% of women and 27.3% of men.
- **Label literacy:**
  - Hyderabad study: 90% say they "read labels", but 81% look only at the expiry date.
  - Chennai survey: 2% read the contents.
- **Regulatory pressure:**
  - The Supreme Court pushed FSSAI on front-of-pack (FOP) warnings throughout 2026, and FSSAI proposed red hexagon warnings for foods high in fat, sugar or salt.
  - FSSAI issued notices over "100% natural", "fresh" and "no added sugar" claims (maltodextrin in a "no added sugar" biscuit).
  - Bournvita was removed from the "health drink" category (2024).
  - Cerelac was found to contain ~3 g of added sugar per serving.
- **Demand signals:** TruthIn has 1.3M downloads and 150K MAU. Yuka is not available in India.

## Ranked segments

| # | Segment | Size in India | Core pains | Features they need | Willingness to pay |
|---|---|---|---|---|---|
| 1 | **Diabetes, prediabetes** (plus PCOS and gestational diabetes) | 101M + 136M; urban rate ~2× | "Sugar-free" packs hide maltodextrin, dextrose and glucose syrup; can't convert per-100 g to per-portion carbs | Net carbs per serving and per pack; glycemic-load flag; hidden-sugar detector; claim checker against FSSAI limits; post-meal glucose log tied to scans; monthly report for the doctor | **High.** Sugar.fit, BeatO and Fitterfly prove people pay; the need lasts for life |
| 2 | **Weight loss, incl. GLP-1 users** | ~30% of adults overweight; GLP-1 sales 333K units in Jul 2026 (~₹2,215 Cr/yr); generic semaglutide since Mar 2026 at ₹1,290–4,200/month | Low protein intake on GLP-1 (target 1.2–2.0 g/kg); small appetite | Protein per 100 kcal; satiety score; daily protein target; nausea-friendly lists; check on "protein-packed" claims | **High.** B2B route via pharma and clinics (Zydus) |
| 3 | **Parents buying kids' food** | Child obesity projected to rise from 3.3 crore (2020) to 8.3 crore (2035); ultra-processed food sales +150% (2009–2023) | "Health drink" image of products like Bournvita; sugar in baby food; confusing serving sizes | Child profiles with age-based limits; sugar shown as teaspoons; lunchbox swaps; baby mode (no added sugar or salt under 2); shared family list | **Medium.** Highly engaged, price-sensitive |
| 4 | **Adult children caring for elderly parents** | 150M aged 60+; 75% have ≥1 chronic disease (LASI) | Several conditions at once, poor eyesight, English-only apps, can't supervise from a distance | One account with many profiles; parent scans by voice in hi/mr; WhatsApp alert to the child; rules that combine conditions; food–drug warnings; large-text mode | **High.** The child (often abroad) pays |
| 5 | **Hypertension and heart health** | 35.5% of adults; intake 8–11 g salt/day (~2× WHO) [primary source unverified] | Hidden salt in namkeen, pickles, papad and noodles; labels show sodium, not salt | Sodium shown as salt; daily salt budget; flags for MSG, benzoate and soda; saturated- and trans-fat flags | **Medium.** Better bundled with segments 1 and 4 |
| 6 | **Chronic kidney disease** | 138M, mostly stages 1–3 | Potassium and phosphorus aren't on labels | Phosphate additive flags (E338–E452); warnings on potassium salt substitutes; protein limits by stage; potassium/phosphorus budget | **High per user, small diagnosed base.** Reach via nephrologists |
| 7 | **Women's health** (PCOS, pregnancy, gestational diabetes) | PCOS 7.2–19.6% of women aged 18–40; gestational diabetes 13–22% | Insulin resistance, pregnancy food safety | Low-GI verdicts; pregnancy flags (caffeine, saccharin, unpasteurised foods); iron and folate; carb counting | **Medium-high** |
| 8 | **Gym and high-protein** | Supplements ~$913M (2025); "75M gym users" [unverified] | ~70% of 36 protein supplements mislabelled (2024 study, method disputed); "protein" snacks that are mostly sugar | Protein per ₹ and per 100 kcal; amino-spiking flag; macros per serving | **Medium.** Crowded; don't lead with this segment |
| 9 | **Religious and cultural diets** (Jain, vrat, halal, strict veg) | Jain ~4.5M, Muslim ~14% [Census 2011, unverified] | The green dot doesn't reveal onion/garlic in "spices", rennet, gelatin, E120 or E471 | Jain, vrat and halal filters; E-number origin lookup; "check the veg dot" | **Low–medium**, but strong word of mouth and almost no competition |
| 10 | **Celiac disease and allergies** | Celiac ~0.67% (4–8M); NIN found 9.8% of "gluten-free" products contained gluten; 33M with food allergies in the US | Hidden gluten (hing mixed with wheat, maida, malt); "may contain" warnings | Hidden-gluten detection; "may contain" parsing; sesame, tree nuts and mustard; shareable "safe" lists | **High per user.** Small in India, large globally |
| 11 | **Vernacular and low-literacy shoppers** | 958M internet users, 57% rural; 98% use Indian languages | Dense technical labels | Voice-first answers in regional languages; traffic-light and emoji results; WhatsApp bot; low-end and offline use | **Low.** Revenue through government, CSR or NGOs |
| 12 | **B2B: dietitians, clinics, corporate wellness, insurers** | ~1 dietitian per 2 lakh people; corporate wellness $0.7–2.5B | No visibility into what clients eat | Dashboard of client scans; dietitian-set rules that drive verdicts; adherence tracking; insurer exports | **High per seat.** Fastest revenue |

Global extensions: GLP-1 users in the US and UK, families managing allergies, and the Indian diaspora shopping at Indian grocers.

## Cross-cutting needs

1. **Indian product coverage.** Photo and text scanning by default, with every scan growing our own database.
2. **Claim checker** for "natural", "no added sugar" and "protein-packed", against FSSAI rules.
3. **Several conditions per profile and several members per account.**
4. **Per serving and per pack, in household units** (teaspoons of sugar, grams of salt).
5. **Unpackaged and home food** (thali, roti, dal). Without it users eventually leave. This is v2.
6. **Voice, vernacular languages and WhatsApp sharing.**
7. **An explained "why" plus a better alternative**, and a report a doctor can read.
8. **Readiness for FSSAI's red warning labels.**

## v1 focus and why

1. **Blood sugar (diabetes, prediabetes, PCOS, gestational diabetes).**
   - Largest group (~237M), mostly urban and on smartphones.
   - Clear pain: hidden sugars and false "sugar-free" claims.
   - People already pay.
   - Paid rivals sell coaching and continuous glucose monitors (CGMs). None of them judges a product at the shelf.
2. **Family health manager (kids plus elderly parents).**
   - Turns a one-person scanner into a household tool.
   - Solves the multi-condition problem and uses our Hindi/Marathi voice.
   - Gives a strong reason to pay (the child abroad pays).
   - Rides the parent-led label-reading movement (Bournvita, Cerelac).
3. **Weight management, including GLP-1 users.**
   - Obesity is rising, and GLP-1 users are a new, motivated, paying group with a specific need: enough protein.

**Next wave:** kidney disease and dietitian tools. Both have few competitors and pay well.

## Sources

- **ICMR-INDIAB:** https://www.downtoearth.org.in/health/india-s-diabetes-epidemic-just-got-more-grim-lancet-report-reveals-why-89946 · https://m.tribuneindia.com/news/health/60-pc-diabetes-reversible-icmr-chief-on-finding-101-mn-diabetics-in-india-515676
- **NFHS-6:** https://theprint.in/health/gaining-weight-losing-health-national-survey-finds-india-trapped-between-obesity-undernutrition/2945717/ · https://www.nextias.com/ca/current-affairs/30-05-2026/nfhs-6-obesity-diabetes-india
- **Chronic kidney disease:** https://www.theweek.in/wire-updates/national/2025/11/08/lst1-research-kidney-disease-estimates.html · https://www.frontiersin.org/articles/10.3389/fnut.2024.1312581/full
- **Salt intake:** https://www.businesstoday.in/india/story/indians-eating-too-much-salt-icmr-warns-of-silent-epidemic-rising-risk-of-stroke-heart-484420-2025-07-13
- **PCOS:** https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11581580/
- **Gestational diabetes:** https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10902981/ · https://thesouthfirst.com/news/one-in-four-pregnant-women-in-south-india-lives-with-gestational-diabetes/
- **Celiac disease:** https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3875923/ · https://www.millenniumpost.in/nation/celiac-disease-needs-wide-spread-awareness-aiims-400867
- **Food allergy:** https://doaj.org/article/34cbaf7b1b604d1b83c679262270b13a · https://www.foodallergy.org/media-room/fare-releases-national-indicator-report-food-allergy
- **Elderly (LASI):** https://www.policycircle.org/opinion/indias-elder-care-policy/ · https://lasi.hsph.harvard.edu/about
- **Kids and ultra-processed food:** https://www.downtoearth.org.in/food/economic-survey-2026-flags-surge-in-ultra-processed-food-consumption-recommends-higher-gst
- **Bournvita:** https://www.theweek.in/news/biz-tech/2024/04/13/latest-news-bournvita-not-health-drink-centre-directs-e-commerce-platform-to-remove-beverage-from-category.amp.html
- **Cerelac:** https://www.downtoearth.org.in/health/nestle-adds-almost-3-grams-of-sugar-in-every-serving-of-baby-food-cerelac-sold-in-india-95625
- **FOP and the Supreme Court:** https://www.livelaw.in/top-stories/after-supreme-court-rap-fssai-proposes-pictorial-front-of-pack-warning-labels-for-packaged-foods-high-in-sugar-salt-fat-547714
- **FSSAI claims crackdown:** https://agronfoodprocessing.com/fssai-cracks-down-on-100-food-label-claims-calls-them-misleading-and-unverifiable/ · https://www.downtoearth.org.in/food/food-labels-misleading-india-s-new-dietary-guidelines-warn-96069
- **Label reading:** https://cambridge.org/core/services/aop-cambridge-core/content/view/S1368980013002231 · https://mail.fssai.gov.in/upload/media/FSSAI_news_Sugar_TOI_13_05_2019.pdf
- **GLP-1:**
  - Market: https://biospectrumindia.com/news/16/28274/glp-1-agonist-market-rebounds-in-july-reaches-rs-2215-crore-mat-sales-sheetal-sapale.html
  - Generic semaglutide: https://www.businesstoday.in/industry/pharma/story/generic-semaglutide-hits-india-prices-fall-90-as-companies-compete-for-diabetic-patients-521707-2026-03-21
  - Protein study: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12419545/
- **Protein supplements:** https://pmc.ncbi.nlm.nih.gov/articles/PMC10994440/ · https://www.imarcgroup.com/india-protein-supplements-market
- **Internet use:** https://yourstory.com/2026/01/indias-internet-user-base-crosses-950-million-2025-iamai-report
- **Open Food Facts India:** https://wiki.openfoodfacts.org/Dashboard/India · **TruthIn:** https://biovoicenews.com/?p=64521

**Unverified:** the 75M gym users figure, the ~0.3M monthly GLP-1 users estimate, Jain/Muslim/vrat population sizes, the PHFI nutritionist-shortage figure, and all willingness-to-pay ratings (my judgement).
