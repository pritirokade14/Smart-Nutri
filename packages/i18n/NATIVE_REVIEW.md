# Native-speaker review: hi and mr

**Status: none of the Hindi (`hi.json`) or Marathi (`mr.json`) strings have been reviewed by a native speaker.** Every key in both files needs a review before release. Health wording comes first: `common.disclaimer`, `verdict.*`, `status.*`, `reason.*`, `reason_variant.*`, `claim_reason.*`, `allergen.*`, `diet.*` and `nutrient.*`.

Reviewers should check that the tone stays informational ("may not suit", "check with your doctor"). Nothing should read as a diagnosis or a definite medical instruction, and no string should say the app treats, manages or cures anything.

Tick an item once a native speaker has signed it off, and note who signed it off in the PR.

## Specific flags

### Tone ("may not", not "does not")
- [ ] **hi**: `diet_violation`, `reason_variant.diet_violation_mark_only`, `carbs_per_serving_high` and `age_unknown` now use the "शायद … न हो" construction. The old "उपयुक्त नहीं हो सकता" and "मेल नहीं खा सकता" read as more definite than "may not". Confirm the new wording reads naturally and stays tentative.
- [ ] **mr**: the same keys use "कदाचित … नसेल / जुळणार नाही". Confirm the tone.

### Allergen labels
- [ ] **hi/mr `allergen.tree_nut`**: the old "सूखे मेवे" and "सुकामेवा" also mean dried fruit (raisins, dates). That is misleading for someone with a nut allergy. These are now "ट्री नट्स (बादाम, काजू, अखरोट आदि)" and "ट्री नट्स (बदाम, काजू, अक्रोड इ.)". Check whether "ट्री नट्स" is understood, or whether a listed-examples label alone is clearer.
- [ ] **hi `allergen_contains` / `allergen_may_contain`**: "बचने वाली सूची" ("avoid list") sounds awkward. "परहेज़ की सूची" may be better.
- [ ] **hi gender agreement with `{allergen}`**: "इसमें {allergen} हो सकता है, जो …" is masculine, but some allergens are feminine (मूँगफली, सरसों). Rephrase the sentence so it does not agree with the interpolated noun.

### Marathi grammar and vocabulary
- [ ] **mr जे/जो/जी agreement**: `allergen_contains`, `allergen_may_contain`, `child_caffeine`, `infant_*` and `infant_honey` use a relative pronoun whose gender must match the noun. With `{allergen}` that noun is interpolated, so it can be दूध (n.), मोहरी (f.) or तीळ (m.). Rephrase these to avoid agreement with the placeholder.
- [ ] **mr `auth.verify` "पडताळा"**: check that it is natural as a button label ("पडताळणी करा"?).
- [ ] **mr `error.validation_error` "अधोरेखित"**: this means "underlined", but the UI highlights fields. Consider "ठळक केलेली" or "चिन्हांकित".

### Terms
- [ ] **hi/mr `diet.eggetarian` "अंडाहारी"**: this is a coinage. Check whether users understand it, or whether "एगिटेरियन" or the descriptive form is better.
- [ ] **hi "अतिरिक्त चीनी" / "अतिरिक्त शर्करा" for "added sugar"**: compare with the Hindi wording on Indian (FSSAI) labels. Also, the file mixes चीनी (`infant_added_sugar`, `claim.no_added_sugar`, `claim_reason.added_sugar_ingredient`) with शर्करा (`added_sugars`). Pick one.
- [ ] **hi/mr `nutrient.*`**: these labels are interpolated mid-sentence (`{nutrient}`). Check that "शर्करा (चीनी)", "ऊर्जा (कैलोरी)", "फॅट (स्निग्ध पदार्थ)" and similar read well inside `nutrient_missing`, `reason_variant.nutrient_missing_low_confidence` and `claim_reason.nutrient_missing`.
- [ ] **`{high_in}` in `cardio_risk_high_in`**: this renders a joined list of `nutrient.*` labels ("संतृप्त वसा और नमक"). Check the sentence with one item and with two.
- [ ] **"100 ग्राम/मि.ली." and "100 ग्रॅम/मि.ली."**: check that the abbreviation is readable. Also check word order around it in `sugar_*`, `salt_*`, `energy_dense`, `child_salt_high`, `infant_*_high` and `claim_reason.exceeds_limit`.
- [ ] **`infant_honey`**: the hi "इससे बड़े छोटे बच्चों" and mr "त्याहून मोठ्या लहान मुलांसाठी" stand in for "toddlers". The phrasing is clumsy. Keep the meaning: honey is not advised under 1 year, and parents should ask a doctor for children aged 1 to 2.
- [ ] **hi `cardio_risk_high_in` "ब्लड शुगर पर ध्यान रखने वाले लोगों"**: check the register. It must not imply the app manages a condition.
- [ ] **`child_sugar_*`**: in hi and mr, the `{basis, select}` phrase starts the sentence ("एक सर्विंग में …", "एका सर्व्हिंगमध्ये …"). Check the sentence with both branches.

## Changed in the review-fix commit (all need review)

The following were rewritten or added: all of `reason.*` that mention amounts, the infant band ("under 2" / "2 साल से छोटे" / "2 वर्षांखालील"), `misleading_sugar_claim`, `nutrient_missing`, `cardio_risk_high_in`, `age_unknown`, every `reason_variant.*` and `nutrient.*` key, and `claim_reason.exceeds_limit`, `below_minimum`, `nutrient_missing` and `no_standard`.

## Added in Plan 2 Tasks 12 and 14 (sign-in)

- [ ] **hi/mr `auth.phoneLabel`, `auth.error`**: machine drafts. Need native review; check the error's tone (no blame).
- [ ] **hi/mr `auth.change`**: machine draft ("बदलें" / "बदला"). Needs native review.
