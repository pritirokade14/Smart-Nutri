# SmartNutri AI: Product

**Vision:** every Indian family can tell, in seconds and in their own language, whether a packaged food is right for each person at home.

**Platforms:**
- An **Android app** (Flutter).
- A **web app** (Next.js).
- **Every v1 feature ships on both** (ADR 0008, `docs/FEATURE_PARITY.md`).

## Problem

- **Large health burden.** India has about 101M people with diabetes and 136M with prediabetes (ICMR-INDIAB). 35.5% of adults have hypertension, and about 30% of adults are overweight (NFHS-6).
- **Labels go unread.** Most shoppers read only the expiry date. "Sugar-free", "no added sugar" and "high protein" claims often hide maltodextrin, glucose syrup or a low protein share. FSSAI's front-of-pack warning labels are still only proposed (2026).
- **Barcode apps miss most Indian products.** Open Food Facts has about 15–25k Indian products, and no app gives a verdict per family member in Hindi or Marathi with voice.

Sources: `docs/research/`.

## Target users

**v1 (primary)**
1. **Blood sugar:** diabetes, prediabetes, PCOS. Largest group, clear pain (hidden sugars, false claims), proven willingness to pay.
2. **Family health manager:** parents buying for children, and adult children managing elderly parents' diets. Multiple profiles, multiple conditions, vernacular voice.
3. **Weight loss**, including people on GLP-1 drugs who need enough protein in small portions.

**v1 (Plan 9): user types and focused modes**
- After the Terms screen, the app asks "What brings you to SmartNutri?". The user picks up to 3 of 6 types, or skips:
  - a health condition (diabetes, prediabetes, PCOS, BP)
  - family
  - weight loss
  - gym and fitness
  - food allergy or special diet
  - just eating better
- Each type has a **focused mode**: its own Home cards and 5-tab bar. Everything else is in "More"; nothing is removed. Scan, verdicts and allergy checks are the same in every mode.
- The type is presentation only. It **never changes a verdict**, it is never sent to analytics, and it pre-fills the account holder's profile only after the user confirms (ADR 0019).
- **Gym and fitness** gets a protein guide:
  - a "Build muscle" goal with a daily protein guide (1.6 g/kg, adults, pending clinician review)
  - protein per serving, per 100 g and per 100 kcal on every scan
  - protein and whey claim checks
  - a "higher protein" sort
  - protein columns and a typed-in price per scoop in Compare
- **Supplements** (whey, protein powders) are not given a Nutri-Score grade, are still checked for allergens, diet and claims, get a caution for children, and are never suggested.
- **Not doing:** doses, brand or supplement recommendations, creatine or steroid advice, "you need X g" claims.

**Later**
- Hypertension (partly covered in v1)
- Kidney disease
- Pregnancy and gestational diabetes
- Jain, vrat and halal diets (Jain is in v1)
- Celiac and allergy (allergy checks and an allergy mode are in v1)
- Deeper gym features: amino-spiking checks, protein per rupee (the protein guide is in v1, Plan 9)
- Low-literacy and WhatsApp-first users
- B2B: dietitians, clinics, corporate wellness

## Positioning

| | Barcode scanners (TruthIn, FactsScan, Xume) | Global scanners (Yuka, Fig) | Trackers and coaches (HealthifyMe, MFP, Fitterfly) | **SmartNutri** |
|---|---|---|---|---|
| Works without a barcode match | ✗ (dead end) | ✗ | n/a | **✓ label photo** |
| Verdict per family member | single user | single user | single user | **✓ every member** |
| Medical-condition rules | some (paid) | allergies and diets | diabetes programmes | **✓ diabetes, BP, kids, weight** |
| Claim checker | ✗ | ✗ | ✗ | **✓** |
| Hindi and Marathi voice | ✗ | ✗ | partial | **✓** |
| Log what you ate | partial | ✗ | ✓ | **✓ one tap from the scan** |

## Principles

1. **Independent of brands.** No brand money, no paid placement, no sponsored alternatives. Revenue comes from users and B2B services only.
2. **The rules decide; the AI explains.** Verdicts come from a deterministic, tested rules engine. The LLM only explains them in plain language.
3. **Unknown is not safe.** If the label is unclear or data is missing, we say so, especially for allergies. We never guess.
4. **Transparent methodology.** A public "How we score" page lists every rule, threshold and source.
5. **No dark patterns.**
   - Show the price before onboarding.
   - Trials never auto-enrol.
   - Cancelling takes one tap.
   - The core scan and verdict stay free.
6. **Vernacular and voice-first.** English, हिंदी and मराठी at launch, with voice questions and answers. Large text and simple colours for elderly users.
7. **Not medical advice.** We inform and do not diagnose or treat. We recommend consulting a doctor or dietitian.

## v1 features (15 days)

See the spec, `docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md` §2, items F1–F17:
- Accounts (Google, email OTP; phone OTP ready)
- Family members with custom alerts
- Barcode, then label-photo fallback
- User-confirmed extraction
- Rules engine (Nutri-Score 2023, high-in warnings, allergens, diet, hidden sugars, claim checker, conditions)
- A red/amber/green verdict per member with a one-line reason
- AI explanation in en/hi/mr
- Scan-to-log with weekly totals
- Alternatives
- Voice Q&A
- "How we score" page
- Report a problem
- Share to WhatsApp
- Consent and account deletion
- User types, focused modes and the gym protein guide (Plan 9, F18–F20)

## Roadmap

**v2 (next 1–2 months)**
- Dietitian web dashboard (B2B)
- Real-time voice agent
- WhatsApp bot and caregiver alerts
- Photo logging of home-cooked meals (needs an INDB licence)
- Rewards and streaks for adding products
- Alternatives ranked by price
- Cart-level insights
- An offline pack of top products
- Micro-lessons
- More Indian languages
- Health Connect

**v3**
- Kidney and pregnancy modes (after a regulatory opinion)
- CGM and diabetes-programme partners
- Quick-commerce links
- Contributing data back to Open Food Facts
- iOS

## Monetisation hypothesis (to validate)

- **Free forever:** scan, verdict for every member, claim checker, basic log.
- **Family plan:** around ₹99–149/month (unverified guess). Includes unlimited voice, full history and reports, weekly family summary, caregiver alerts and more members.
- **B2B (v2+):** per-seat dietitian and clinic dashboard, and corporate wellness.
- **Startup credits:** CallMissed offers $1,000 in API credits on application, and 50% off for DPIIT-recognised startups. Apply early.

## Growth channel: public web pages

The Next.js web app serves Google-indexable public pages:
- **Product pages** at `/p/[barcode]`, in en, hi and mr. They show generic facts only: Nutri-Score "calculated by SmartNutri", "high in" warnings, the claim check ("Sugar-free? Contains maltodextrin"), ingredients and OFF attribution. No personal verdict is shown.
- **"How we score"**.
- **A landing page**.

Searches such as "is <brand> healthy for diabetics" can land on a product page. A "Check for my family" button then leads to sign-up. Open Food Facts gets much of its traffic this way.

Pages are statically generated or ISR for speed on low-end phones, with `sitemap.xml` and `hreflang` links.

## v1 success metrics

| Metric | Target (first 4 weeks after launch) |
|---|---|
| Scan to verdict, barcode hit | p50 < 2 s |
| Scan to verdict, label photo | p50 < 8 s |
| Scans resolved to a verdict (not dead-ended) | ≥ 95% |
| Label-extraction accuracy on the eval set (≥ 50 Indian labels), per nutrient within ±5% | ≥ 90% |
| Allergen recall on the eval set | 100% (no missed declared allergen) |
| D7 retention | ≥ 25% |
| Organic search visits to public product pages (by week 4) | growing week over week; baseline set in week 1 |
| Scans per weekly active user | ≥ 5 |
| Scans followed by "I ate this" | ≥ 20% |
| "Report a problem" per 100 scans | < 3 (falling) |
