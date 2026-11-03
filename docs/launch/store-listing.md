# Google Play store listing (DRAFT)

> Plan 8 Task 13 Step 2, drafted by Claude. The **USER** pastes this into Play Console → Grow → Store presence → Main store listing.
>
> - The Hindi text is a machine draft and needs a native-speaker review (see `packages/i18n/NATIVE_REVIEW.md`).
> - Never add medical claims. Do not say the app treats, manages, controls or cures anything.

| Field | Value |
|---|---|
| App name | **SmartNutri AI** |
| Default language | English (India), `en-IN` |
| Category | Health & Fitness |
| Tags | Nutrition, Food, Family |
| Contact email | [support email] |
| Website | `https://app.<domain>` |
| Privacy policy | `https://app.<domain>/en/privacy` |
| App or game | App · Free · No ads · Target audience 18+ |

## English (India)

**Short description** (80 characters max)

> Check packaged food for each family member: allergies, diet, sugar and salt.

**Full description**

> SmartNutri AI reads the packaged foods you buy and tells you, for each person in your family, whether a product looks OK, needs caution, or is best avoided.
>
> **Scan a barcode or the label.** If the barcode is not known, take a photo of the nutrition label. You check the values before anything is saved.
>
> **One answer per family member.** Add profiles for yourself, your children and your parents, with their diet (veg, Jain, eggetarian, vegan) and allergies. You can add health details if you choose. Every person gets their own colour and a short reason.
>
> **Clear when the label is unclear.** If the ingredients can't be read, SmartNutri says "Label unclear". It never guesses "OK".
>
> **Claim checker.** Is "sugar free" or "high protein" on the pack really true? SmartNutri checks it against the values on the label.
>
> **Ask by voice** in English, Hindi or Marathi.
>
> **Track what you eat** and see simple daily summaries.
>
> **How we score.** The rules and their sources are public in the app. Nutri-Score grades are calculated by SmartNutri.
>
> Your data stays private:
> - It is stored in India.
> - Label photos are deleted after 30 days.
> - You can withdraw consent or delete your account at any time.
>
> SmartNutri gives information, not medical advice. Ask your doctor or dietitian about your diet.
>
> Some product data comes from Open Food Facts (ODbL).

## Hindi (`hi-IN`), machine draft

**Short description**

> परिवार के हर सदस्य के लिए पैकेट वाला खाना जाँचें: एलर्जी, आहार, चीनी और नमक।

**Full description**

> SmartNutri AI आपके खरीदे पैकेट वाले खाने को पढ़ता है और परिवार के हर सदस्य के लिए बताता है कि उत्पाद ठीक लगता है, सावधानी चाहिए, या उससे बचना बेहतर है।
>
> **बारकोड या लेबल स्कैन करें।** बारकोड न मिले तो पोषण लेबल की फ़ोटो लें। कुछ भी सहेजने से पहले आप मान जाँचते हैं।
>
> **हर सदस्य के लिए अलग जवाब।** अपने, बच्चों और माता-पिता के प्रोफ़ाइल जोड़ें: आहार (शाकाहारी, जैन, अंडा, वीगन) और एलर्जी। चाहें तो स्वास्थ्य जानकारी भी जोड़ें।
>
> **लेबल साफ़ न हो तो साफ़ बताता है।** सामग्री पढ़ी न जा सके तो SmartNutri "लेबल अस्पष्ट" कहता है। वह कभी "ठीक" का अनुमान नहीं लगाता।
>
> **दावा जाँच**, **आवाज़ से पूछें** (हिंदी, मराठी, अंग्रेज़ी), और **खाने का रिकॉर्ड**।
>
> आपका डेटा निजी रहता है:
> - यह भारत में रखा जाता है।
> - लेबल की फ़ोटो 30 दिन बाद हट जाती हैं।
> - आप कभी भी सहमति वापस ले सकते हैं या खाता हटा सकते हैं।
>
> SmartNutri जानकारी देता है, चिकित्सा सलाह नहीं। अपने आहार के बारे में डॉक्टर या डाइटीशियन से पूछें।
>
> कुछ उत्पाद डेटा Open Food Facts (ODbL) से है।

## Screenshots (phone, captured from the emulator)

Capture each one with `adb exec-out screencap -p > docs/launch/screenshots/<n>.png`. Screenshots are git-ignored if they show real data: use the seeded demo family only.

1. Home with the scan button
2. Result for a biscuit: one verdict per member (OK, Caution, Avoid), with the disclaimer visible
3. "Label unclear" (unknown) example, shown not green
4. Label confirm screen
5. Claim checker on a "sugar free" product
6. Voice answer sheet (Hindi)
7. Daily summary
8. "How we score" page

Feature graphic: 1024 × 500, with the app name and the tagline "Right food for every family member". Do not use health-claim wording.
