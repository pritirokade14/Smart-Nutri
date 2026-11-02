# Competitors and Ideas to Adopt

**Date:** 2026-11-02 · Public sources only (see [competitor-research-method](2026-11-02-competitor-research-method.md))

**Key takeaways**
- Indian label scanners (TruthIn, FactsScan, Xume, OpenLabel) are mostly **barcode-only**, with small databases (~20K products). Calorie apps (HealthifyMe, MyFitnessPal) don't judge packaged-food quality. **Nobody connects "is this right for each family member?" with "what did we actually eat?"**
- Yuka, with ~80M users, is the model for trust: a public methodology, independence from brands, and alternatives. It is **not available in India**.
- The most common failure across competitors is an empty or wrong product database. Always offer a recovery path when a product isn't found.
- Hindi/Marathi voice, verdicts for several family members, and claim checking are open gaps.
- Avoid dark patterns: a price revealed only after the quiz, hidden cancellation, and core features moved behind a paywall.

## Landscape

| App | Region | Core | Distinctive hook | Price | Notable complaints |
|---|---|---|---|---|---|
| **TruthIn** | India | Barcode; 1–5 rating (45% nutrition, 45% ingredients, 10% processing); MatchMeter personalisation; TIA chatbot | Photographers capture labels in shops; rewards for adding missing products | US store $0.99/mo, $3.99–4.99/yr; premium food features made free in 2026 | "No items showed product info"; "completely inaccurate" |
| **FactsScan** | India (Ahmedabad) | Barcode; score out of 100 plus A–E grade; processing level; alternatives | Aligned to FSSAI/ICMR; featured by NITI Aayog; 19,939 user-added products | Not stated | Small, Gujarat-heavy database; 93K downloads claimed against ~22.5K Play installs |
| **Xume** | India (Mumbai) | Barcode; personalised 0–100 score (60+ parameters) | Alternatives ranked by score **and price** | ₹299/mo, ₹699/quarter, ₹1,999/yr; challenges ₹999–3,999 | 3.1★ (143 ratings); last update Aug 2024 |
| **OpenLabel** | India (indie) | Barcode or ingredients; 0–10 score using Nutri-Score | Offline-first, bundled Indian product set plus Open Food Facts | Free | Unverified, very new |
| **Nutrimate** | India | Calorie tracker; 1 lakh+ Indian foods | WhatsApp meal logging | ? | Unverified |
| **HealthifyMe** (Snap, Ria) | India | Photo logging of Indian dishes (vendor says 60–90% accuracy); AI coach Ria; CGM; human coaches | Largest Indian nutrition app | Smart ~₹2,499/yr; Pro ₹5,500–8,000/mo; CGM ~₹4,099 [unverified] | Trustpilot 2.9/518; generic diet charts; trouble getting refunds; doesn't judge packaged food |
| **Fitterfly** | India | Diabetes programme: app, coach, CGM | Clinical evidence (JMIR 2023, n=109) | ₹19,999 for 12 months, ₹15,999 for 6 months (incl. Libre CGM) | Not a label scanner |
| **Sugar.fit** | India | Diabetes reversal: CGM, coach, doctor | Programme model | Subscription unknown; CGM ₹5,799–13,499 [unverified] | Mixed; "waste of money" |
| **Ultrahuman M1** | India/global | Food score from your own glucose response (CGM) | Personal biology | Hardware | Needs a sensor |
| **Zomato / Swiggy** | India | Dish health scores, "Protein Drops" (Sep 2025) | Mass reach | Free | Restaurant food only |
| **Yuka** | FR/global (~80M users) | Barcode; 0–100 score (60% nutrition, 30% additives, 10% organic; a high-risk additive caps the score at 49) | Public methodology; "revenues from users, never brands"; ~$11.9M premium revenue in 2025 | Free; premium ~$10/yr, pay what you want | "Fear-mongering"; no portion context (oats judged "too caloric"); method not explained clearly enough (Italian competition authority [unverified]) |
| **Open Food Facts** | Global, open | Nutri-Score, NOVA, Green-Score; 4M+ products | Open data; users add products | Free | Thin India coverage; grades "may not be fully accurate" |
| **MyFitnessPal + Cal AI** | US/global | Logging, barcode, photo logging (bought Cal AI in Mar 2026) | Speed, huge database | MFP ~$79.99–99.99/yr; Cal AI ~$29.99–49.99/yr, price shown after the quiz | Inaccurate Indian data; inconsistent photo accuracy; billing after trial cancellation |
| **Fig** | US | 2,500+ diet and allergy restrictions; colour verdict | Explicit "review further" (yellow) for uncertain items | ~$50–60/yr; 4.5–4.6★ | Trial auto-enrols |
| **Fooducate** | US | Grade plus reasons, alternatives | Dietitian-style explanations [unverified] | $1.99–49.99/yr (sources conflict) | — |
| **Foodvisor / Lifesum** | EU | Meal photo tracking, diet plans | Design, coaching | $6.99–14.99/mo; ~$25/yr | Trackers, not verdict scanners |
| **Noom** | US | Psychology lessons plus coaching; GLP-1 programmes | Behaviour change | $17.42/mo on a 12-month plan; GLP-1 $79–129 | Hidden cancellation, BBB complaints |
| **GLP-1 apps** (MyNetDiary GLP-1 Companion, Plantein, GLP-1 Sidekick) | US | Protein-first tracking, injection reminders, meal scan | Condition-specific metric | $9.99/mo or $59.99/yr; Plantein 1 free AI scan/day then $49.99/yr | — |
| **FoodPharmer / Label Padhega India** | India (movement) | Creator campaign, 2.7–4.85M followers | Cultural momentum; **not an app** | — | — |

## Per-competitor notes

- **TruthIn**
  - Barcode only. Data is about 80% captured in shops and 20% from the web, plus user corrections.
  - The result shows a rating, tags (high sodium, high sugar), allergen and additive alerts, and nutrient tracking.
  - Cart-level insights. A "Buy on Amazon" button was added in Sep 2026.
  - Personalisation: MatchMeter (age, gender, conditions). Plus tier adds goals, red/yellow/green flags and filters.
  - Points for scan streaks and for uploading missing products.
- **FactsScan.** Barcode plus user-added products that the team verifies. Score out of 100 plus A–E, covering nutrition, ingredient safety and processing. Plain-language ingredient explanations. Target of 5 lakh products. Tied to government programmes [unverified].
- **Xume.** Score bands: red 0–29, orange 30–54, yellow 55–69, green 70–100 [unverified]. "Better matches" ranked by score and price; search and compare. Independent of brands.
- **HealthifyMe.** Snap photo logging (portion size is the weak point). The free tier gives limited Ria answers, as a funnel to paid. Human coach plans are the main revenue (₹206.8 Cr in FY24).
- **Yuka.** Scan → coloured 0–100 score → negatives and positives → additives with risk dots → better alternatives. Premium: search, offline use, palm oil/gluten/lactose alerts. No condition or family profiles. Includes a tool to complain to the brand.
- **Fig.** Colour verdict against your restrictions. Uncertain items are yellow with "review further", so it never guesses.
- **Open Food Facts.** When a product isn't found, users add it with photos, which grows the shared database.
- **Cal AI / MyFitnessPal.** One-tap photo logging. Pricing shown only after onboarding; billing complaints.
- **Noom.** Daily micro-lessons build the habit. Hard cancellation hurts trust.

## Top ideas to adopt (merged and de-duplicated)

| # | Idea | Seen in | Why it matters for our users | Effort | When |
|---|---|---|---|---|---|
| 1 | Verdict for each family member, with a one-line "why for this person" | Fig, Yuka, TruthIn MatchMeter, Xume | Families share one pack but have different needs | M | **v1** |
| 2 | Explicit "unknown / label unclear" state, never a guess | Fig | Indian labels are messy; trust | M | **v1** |
| 3 | When a product isn't found, read the label photo for an instant result and queue it for verification | Open Food Facts, Yuka, TruthIn | The most common competitor failure | M | **v1** |
| 4 | Red/yellow/green plus a grade on top of the numbers | TruthIn, Xume, FactsScan | Fast for elderly users | S | **v1** |
| 5 | Public methodology page: weights, thresholds, sources (ICMR-NIN, FSSAI, WHO) | Yuka, TruthIn, FactsScan | Counters complaints about opaque scores | S | **v1** |
| 6 | Claim checker ("sugar-free" with maltodextrin) | Gap (FoodPharmer demand) | Timely, given FSSAI enforcement | S | **v1** |
| 7 | Portion-aware verdicts (per serving and per day) | Yuka complaints | Fixes "oats are too caloric" | M | **v1** |
| 8 | Hard caps (for example, added sugar or maida means avoid for diabetics) | Yuka's additive cap | Easy to explain | S | **v1** |
| 9 | Scan-to-log in one tap, with a weekly view for each member | Cal AI; gap in Indian scanners | Turns a one-off check into a daily habit | M | **v1** |
| 10 | Alternatives in the same category, ranked by score **and price** | Xume, Yuka, Fooducate | Budget-conscious families | M | **v1** (basic), price later |
| 11 | Report-a-mistake button on each product | TruthIn | Cheap quality loop | S | **v1** |
| 12 | "Would get FSSAI red warning" badge | Gap | Regulatory tailwind | S | **v1** |
| 13 | Clear pricing before onboarding; trial ends without auto-enrolment | Lesson from Cal AI and Fig | Trust | S | **v1** (copy), launch |
| 14 | Independence pledge (no brand money) | Yuka | Differentiator in India | S | Launch |
| 15 | Daily protein target for weight loss and GLP-1 users | MyNetDiary, Plantein | GLP-1 group need | M | v1.1 |
| 16 | Custom ingredient alerts (palm oil, maida, added sugar) | Yuka Premium | Simple personalisation | S | v1.1 |
| 17 | Hindi/Marathi voice for scanning and logging | Gap | Literacy and elderly users | M | **v1** (push-to-talk), real-time later |
| 18 | Family weekly report and caregiver alerts on WhatsApp | Noom/Lifesum reports; Nutrimate | WhatsApp is the default channel | M | v2 |
| 19 | Rewards for adding products and scan streaks | TruthIn | Fills the long tail | M | v2 |
| 20 | Micro-lessons attached to verdicts ("what is maltodextrin") | Noom, Fooducate | Builds understanding | M | v2 |
| 21 | Cart-level insights across several scans | TruthIn | Family shopping | M | v2 |
| 22 | Offline-first bundle of top products | OpenLabel | Tier-2/3 connectivity | M | v2 |
| 23 | Limited free AI chat, more in the paid tier | HealthifyMe Ria, TruthIn TIA | Funnel to paid | M | v2 |
| 24 | Links to Blinkit, Zepto and BigBasket; "complain to brand / FSSAI" draft | Yuka; TruthIn → Amazon | Next action at buying time | M | v2 |
| 25 | Partnerships with condition programmes and CGMs | Sugar.fit, Fitterfly | Higher-value revenue | L | Later |
| 26 | Open data contribution back to Open Food Facts | Open Food Facts | Goodwill plus coverage | L | Later |

## Mistakes to avoid

- **An empty product database with no way forward.** The top complaint about TruthIn and others.
- **Inaccurate data shown with confidence.** False certainty ruins trust (Cal AI accuracy, TruthIn "completely inaccurate").
- **Putting basics behind a paywall.** TruthIn had to make premium food features free again.
- **Dark patterns:** a price revealed only after the quiz, trials that auto-enrol, hidden cancellation (Cal AI, Fig, Noom).
- **Opaque, one-size scoring** without portion context (criticism of Yuka).
- **Neglecting the app.** Xume is at 3.1★ with no update since Aug 2024.
- **Generic coaching and difficult refunds** (HealthifyMe).
- **Overclaiming "first", "unbiased" or accuracy** without validation, and health claims without a disclaimer.

## Sources

- **Yuka:**
  - Scoring: https://help.yuka.io/l/en/article/ijzgfvi1jq
  - Independence: https://yuka.io/en/independence
  - Pricing: https://help.yuka.io/l/en/article/b5wkrfepnp-why-are-there-different-tariffs
  - Reviews: https://ie.trustpilot.com/review/yuka.io
  - Reformulation coverage: https://www.foodnavigator.com/Article/2026/02/09/yuka-drives-reformulation-but-shuts-out-food-makers/
- **TruthIn:** https://thebetterindia.com/372834/truthin-app-healthy-food-choices-scan-barcode-easy-food-labels-foodpharmer · https://apps.apple.com/us/app/truthin/id6450003063
- **FactsScan:** https://frontiertech.niti.gov.in/story/helping-indians-eat-healthier-the-app-that-demystified-food-labels-in-its-first-year/ · https://appgoblin.info/apps/com.dws.factsscan
- **Xume:** https://apps.apple.com/in/app/xume/id1279728797 · https://indianstartupnews.com/stories/with-xume-users-can-get-detailed-food-ingredient-insights-and-personalised-health-scores-3664301
- **OpenLabel:** https://peerlist.io/helloarmaanux/project/openlabel
- **HealthifyMe:** https://techcrunch.com/2023/09/21/khosla-backed-healthifyme-introduces-ai-powered-image-recognition-for-indian-food · https://nutriscan.app/blog/posts/healthifyme-worth-it-2026-ria-ai-indian-food-tracker-f3167114ef · https://subger.com/en/service/healthifyme
- **Fitterfly:** https://fitterfly.com/diabefly · https://www.fiercebiotech.com/medtech/fitterflys-diabetes-digital-therapeutic-cuts-blood-sugar-weight-real-world-trial
- **Sugar.fit:** https://apps.apple.com/us/app/-/id1568271882 · https://nz.trustpilot.com/review/sugar.fit
- **MyFitnessPal / Cal AI:** https://pulse2.com/myfitnesspal-acquires-cal-ai-to-expand-ai-powered-nutrition-tracking-portfolio · https://nutrola.app/en/blog/cal-ai-review-2026 · https://kimola.com/reports/unlock-insights-with-myfitnesspal-calorie-counter-user-feedback-report-app-store-in-154446
- **Fig:** https://apps.apple.com/app/id1564434726 · https://play.google.com/store/apps/details?id=com.fig
- **Noom:** https://www.noom.com/plans · https://unstar.app/blog/noom-cost-charged-after-cancelling-refund-reviews-2026
- **GLP-1 apps:** https://digital-release.kxan.com/business/press-releases/cision/20260505FL48085/mynetdiary-launches-glp-1-companion-for-ozempic-wegovy-and-mounjaro-users · https://apps.apple.com/us/app/-/id6779978351
- **Open Food Facts India:** https://indiafoodstats.blogspot.com/2026/02/wikipedia-of-food-in-india-just-got.html
- **FoodPharmer:** https://en.wikipedia.org/wiki/FoodPharmer
- **Zomato/Swiggy:** https://startuptalky.com/news/zomato-and-swiggy-introduce-food-health-scores
- **Quick-commerce study:** https://bwretailworld.com/food-beverage/half-of-packaged-foods-on-quick-commerce-apps-junk-and-ultra-processed

**Not covered:** Play Store and Reddit reviews (not retrievable), SafeScan, competitors' onboarding question lists, and their language support. Many price figures come from affiliate sites, so re-check them on official pages.
