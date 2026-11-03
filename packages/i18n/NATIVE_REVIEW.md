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

## Added in the Plan 2 final-review fixes (R36)
- [ ] **hi/mr `error.{unauthorized,forbidden,method_not_allowed,http_error}`**: machine drafts for generic HTTP errors. Check the tone (no blame) and "समर्थित" (hi/mr) for "supported"; a plainer word may read better.

## Added for Plan 3 (M1 scan and result screens)
- [ ] **hi/mr `scan.*`, `result.*` (use the existing `nutriscore.calculated_by` for the score label), `attribution.off`, `error.{invalid_barcode,product_not_found,off_unavailable,member_not_found,invalid_product_ref}`, `home.scan_cta`, `result.you`**: machine drafts. Check "न्यूट्री-स्कोर"/"न्यूट्री-स्कोअर" transliteration and the tone of the "busy" message.

### Public product page (Plan 3 Task 9)
- [ ] **hi/mr `product.public_cta`, `product.meta_title`, `product.meta_description`**: machine drafts. Check that the page title reads naturally in search results and that the description keeps the "information, not medical advice" wording.
- [ ] **hi/mr `product.claims_heading`, `product.label_says`**: machine drafts. The framing must read as "the pack claims this", never as SmartNutri endorsing the claim.

### Verdict fallback and profile notes (R20/R21)
- [ ] **hi/mr `verdict.reason_unavailable`, `verdict.profile_not_set_up`, `verdict.show_all_reasons`, `verdict.hide_reasons`**: machine drafts. Check tone (informational, tentative) and that "profile not set up" reads naturally.

## Added for Plan 4 (M2 label scan, Task 5: saving a product)
- [ ] **hi/mr `error.{scan_not_found,implausible_value,product_exists}`**: machine drafts. Check that `implausible_value` reads as "please check these numbers", not as blaming the user, and that "सहेजा गया" (hi) and "जतन केले" (mr) are natural for "saved".

## Added for Plan 4 Task 4 (label photo upload and extraction)
- [ ] **hi/mr `error.{scan_image_not_found,image_too_large,unsupported_image,extraction_failed,extraction_unavailable,storage_unavailable}`**: machine drafts. Check the tone (no blame), that "जानकारी खुद भरें" / "माहिती स्वतः भरा" reads as the "enter manually" path, and that "8 MB" and the format names (JPEG, PNG, WebP) stay as written.

## Plan 4 Task 7 (label capture and confirm screen)
- [ ] **hi/mr `label.*`, `notfound.go_to_label`**: machine drafts. Check "जानकारी खुद भरें" / "माहिती स्वतः भरा" (enter manually) and that the photo wording reads naturally.
- [ ] **hi/mr `confirm.*`** (`title`, `subtitle`, `field.*`, `serving_size`, `ingredients`, `add_ingredient`, `claims`, `veg_mark.*`, `save`, `category`, `category_option.*`, `sodium_unit`, `sodium_unit_option.*`, `basis`, `basis_option.*`, `choose_required`, `withheld_hint`, `confirm_value`, `derived_per_serving`, `leave_blank_hint`, `allergen_statement`, `may_contain_statement`, `not_medical_advice`): machine drafts. Units (g, mg, kcal, kJ) and "100 g" stay as written. Check the nutrient names (added sugars, "तंतू" for fibre in mr) and that the may-contain statement reads as the pack's own wording.
- [ ] **hi/mr `warning.*`** (`implausible_value`, `per_100g_missing`, `basis_mismatch`, `per_serving_ignored`, `energy_mismatch`, `kcal_kj_mismatch`, `salt_sodium_mismatch`, `unit_unconfirmed`, `low_confidence`, `category_unknown`, `category_check`, `unreadable_field`, `upper_bound`, `derived_from_serving`): machine drafts. **Check the tone**: each must be calm, non-blaming and say what to check on the pack. Check that "कम" / "कमी" in `upper_bound` clearly means "less than".

## Plan 4 Task 9 (web confirm screen)
- [ ] **hi/mr `confirm.{name,brand,sodium,veg_mark_title,remove_ingredient,clear_statement_confirm,open_existing}`**: machine drafts. Check that `clear_statement_confirm` reads as a deliberate "the pack has no such statement" confirmation (it gates removing the allergen or may-contain text), and that `sodium` works as a field label next to the separate mg/g picker.

## Plan 4 round B (Android label capture)
- [ ] **hi/mr `label.camera_permission_denied`**: machine drafts. Check that "सेटिंग्स" / "सेटिंग्ज" is the word users see on their phone, that the sentence reads as a calm "turn on camera access" instruction (no blame), and that the two fallbacks (choose a photo, enter manually) match the `label.choose_file` and `label.enter_manually` wording.

## Plan 5 Task 4 (consents API)
- [ ] **hi/mr `error.consent_version_mismatch`**: machine drafts. Check that it reads as "the consent text changed, please review it again" (calm, no blame) and that the word for "consent" (सहमति in hi, संमती in mr) is the one users know.
