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

## Plan 5 Task 5 (members API)
- [ ] **hi/mr `error.{consent_required,member_limit,primary_member}`**: machine drafts. `consent_required` must read as a calm request to agree to health data processing before saving allergies, conditions, a goal, height or weight (no blame, no implication that the app treats anything). Check "स्वास्थ्य डेटा" / "आरोग्य डेटा" and the health-field words (लंबाई/उंची, वज़न/वजन, लक्ष्य/उद्दिष्ट). `primary_member` means "your own (account holder) profile can't be removed"; check that "प्रोफ़ाइल" / "प्रोफाइल" is natural.

## Plan 5 Wave A safety fixes (Ruling P7: custom ingredient alerts)
- [ ] **hi/mr `reason.custom_alert`, `reason.custom_alert_unknown`, `reason_variant.custom_alert_flag_only`**: machine drafts. Each must read as a calm note that the member asked to be told about these ingredients, never as a warning that the food is harmful. `custom_alert_unknown` must make clear that the ingredients could not be read, so the check could not be done; it is NOT a statement that the ingredient is absent. Check "अलर्ट चुना था" (hi) and "अलर्ट निवडला होता" (mr); a plainer phrase may read better. `{alerts}` is a joined list of `alert.*` labels: check the sentence with one item and with five.
- [ ] **hi/mr `alert.*`** (`palm_oil`, `maida`, `added_sugar`, `artificial_sweetener`, `msg`): machine drafts, interpolated mid-sentence. Check "कृत्रिम स्वीटनर" (hi) and "कृत्रिम स्वीटनर (गोडवा)" (mr), "एमएसजी" for MSG, and keep `added_sugar` consistent with the open "अतिरिक्त चीनी" / "शर्करा" item above.

## Plan 5 Task 8 (members, consent, explanation screens; alert copy rewrite)
- [ ] **hi/mr `reason.custom_alert`, `reason.custom_alert_unknown`, `reason_variant.custom_alert_flag_only` (rewritten)**: machine drafts. `custom_alert` now names the alert through its `alert.*` label, then the matched ingredients ("इसमें {alert} है: {ingredients}।" / "यात {alert} आहे: {ingredients}."). None of the three says "you asked": a family manager may have set the alert for someone else. `custom_alert_unknown` must cover both "no ingredient list at all" and "a list that could not be read reliably", and must not imply the ingredient is absent. `custom_alert_flag_only` says "sweeteners" (स्वीटनर / स्वीटनर (गोडवा)), not "artificial sweeteners": the product-data flag also covers stevia and polyols.
- [ ] **hi/mr `verdict.for_member`, `verdict.for_you`**: machine drafts for the card headline ("{name} के लिए {status}" / "{name} साठी {status}"). `{status}` is a `verdict.status.*` label (for example "लेबल साफ़ नहीं"). Check the word order with each status, and that "आपके लिए" / "तुमच्यासाठी" reads naturally.
- [ ] **hi/mr `members.*`** (`title`, `add`, `edit`, `remove`, `remove_confirm`, `you_badge`, `saved`, `consent_withdrawn_notice`, `form.*`, `relation.*`, `sex.*`, `goal.*`): machine drafts. Height is "ऊँचाई" (hi) and "उंची" (mr). `consent_withdrawn_notice` must say plainly that saved allergies and conditions are still used for checks. `form.clear_allergies_confirm` gates removing every allergy for a member: it must read as a deliberate confirmation, not a routine prompt. Check `relation.parent` ("माता-पिता" / "आई-वडील") as a single-person label, and `goal.healthy_eating` ("बेहतर खाना" / "चांगला आहार"): it must not sound like a medical goal. mr `remove_confirm` uses the respectful "यांना".
- [ ] **hi/mr `consent.*`** (`health_data`, `ai_processing`, `terms` `title`/`body`; `agree`, `decline`, `withdraw`, `granted`, `not_granted`): machine drafts, and legal text. `health_data.body` must keep "information, not medical advice" (यह जानकारी है, चिकित्सा सलाह नहीं / ही माहिती आहे, वैद्यकीय सल्ला नाही). `ai_processing.body` must keep all three facts: no names are sent, the AI service is processed in India, and the AI never decides a result. Legal or product sign-off on the English body text is also needed before release.
- [ ] **hi/mr `explanation.*`** (`title`, `ai_note`, `tips_title`): machine drafts. `ai_note` must say that AI wrote it and that it never changes a result.
- [ ] **hi `error.consent_required`**: height changed from "लंबाई" to "ऊँचाई" (Ruling P8.5). Review it with the rest of the file.

## Plan 5 safety should-fixes (allergen and alert copy)
- [ ] **hi/mr `reason.allergen_unrecognised` (rewritten)**: machine drafts. Meaning: "We can only search the label for the exact word "{allergen}". Check the ingredients yourself." It must read as a calm limit of the search, not an error, so a parent does not delete the allergy to make it go away. hi: "हम लेबल पर केवल "{allergen}" शब्द ही खोज सकते हैं। सामग्री खुद भी जाँच लें।" mr: "आम्ही लेबलवर फक्त "{allergen}" हा नेमका शब्द शोधू शकतो. घटक स्वतः तपासा." Check "सामग्री" (hi) vs "घटक" (mr) for ingredients, matching the rest of the file.
- [ ] **hi/mr `members.form.custom_alerts_help` (rewritten)**: machine drafts. Meaning: "We point these out when we find them on the label." hi: "लेबल पर ये मिलने पर हम इन्हें बताएँगे।" mr: "लेबलवर हे आढळल्यास आम्ही ते दाखवू."


## Web design pass (app shell, landing, placeholders)
- [ ] **hi/mr `landing.*`** (`eyebrow`, `hero_title`, `hero_body`, `cta_start`, `how_title`, `step1_*`, `step2_*`, `step3_*`, `meta_title`, `meta_description`): machine drafts. The hero is the public value proposition and the page title in search results: check that it reads naturally and stays informational ("सही है या नहीं" / "योग्य आहे का"), never a promise about health. `meta_description` must keep the "information, not medical advice" wording. Check "पैकेटबंद खाना" (hi) and "पॅकबंद अन्न" (mr) for "packaged food".
- [ ] **hi/mr `nav.*`, `history.*`, `family.*`, `profile.*`, `footer.tagline`**: machine drafts. Tab labels must be short (they sit under icons in a bottom bar). Check "होम" vs "मुख्य पृष्ठ", and "परिवार" / "कुटुंब".
- [ ] **hi/mr `common.{go_home,coming_soon,skip_to_content}`, `auth.{subtitle,or}`, `home.{subtitle,scan_body,label_body,manual_body}`, `scan.{subtitle,label_hint}`, `result.members_title`, `product.not_found_body`, `common.not_found_body`**: machine drafts. Check the tone (calm, no blame).
- `language.{en,hi,mr}` are endonyms ("English", "हिन्दी", "मराठी") and are deliberately the same in all three files.
- [ ] **hi/mr `alert.*`** (`palm_oil`, `maida`, `added_sugar`, `artificial_sweetener`, `msg`): machine drafts, interpolated mid-sentence.

## Android design pass (app shell and restyled screens)
- [ ] **hi/mr `nav.*`** (`home`, `scan`, `history`, `family`, `profile`): machine drafts for the bottom navigation labels. They must be short (one word fits under an icon). Check "होम" (a loanword) against "मुखपृष्ठ", and "प्रोफ़ाइल" / "प्रोफाइल".
- [ ] **hi/mr `common.coming_soon`, `common.error_title`**: machine drafts. "जल्द आ रहा है" / "लवकरच येत आहे" should read as a friendly label, not a promise with a date.
- [ ] **hi/mr `auth.tagline`, `auth.or`**: machine drafts. The tagline must stay informational ("know if it suits"), never a health promise. Check "पैकेज्ड खाना" (hi) and "पॅकबंद अन्न" (mr).
- [ ] **hi/mr `home.{welcome_no_name,subtitle,scan_body,label_title,label_body,recent_title,recent_empty_title,recent_empty_body}`**: machine drafts. `label_title` repeats `label.title` on purpose (same action). Check that "पोषण लेबल" / "पोषण लेबल" is what users call the nutrition table on the pack.
- [ ] **hi/mr `history.*`, `family.*`, `profile.*`** (`title`, `coming_soon_title`, `coming_soon_body`): machine drafts. `family.coming_soon_body` mentions age, allergies and diet: keep it informational, no claim that the app manages a condition.
- [ ] **hi/mr `result.{family_title,nutrition_title,not_on_label}`**: machine drafts. `not_on_label` must read as "the pack does not print this value", not "zero". Keep "100 ग्राम/मि.ली." / "100 ग्रॅम/मि.ली." consistent with the reason strings.
- [ ] **hi/mr `confirm.{section_product,section_nutrition,section_allergens,section_pack}`**: machine drafts for the confirm-screen group titles. Check "एलर्जी कारक" (hi) and "ॲलर्जी घटक" (mr) for "Allergens", and "तालिका" / "तक्ता" for the nutrition table. Check "कृत्रिम स्वीटनर" (hi) and "कृत्रिम स्वीटनर (गोडवा)" (mr), "एमएसजी" for MSG, and keep `added_sugar` consistent with the open "अतिरिक्त चीनी" / "शर्करा" item above.

## Android family members and consent (Plan 5 Task 9)
- [ ] **hi/mr `members.form.remove_allergy_confirm`**: machine draft. It warns that a removed allergy is no longer flagged on products, so it must read as a clear, calm warning. Integration (wave 2): both clients now share one string; see the integration section below.
- [ ] **hi/mr `members.born_in`, `members.form.{name_required,birth_year_invalid,number_range,allergen_length,allergen_limit}`**: machine drafts for form labels and validation. Numbers stay in Latin digits.
- [ ] **hi/mr `consent.optional_ai_note`**: machine draft. It must say the AI consent is optional and that results are the same without it (the AI never decides).
- [ ] **hi/mr `profile.consents_title`**: machine draft ("गोपनीयता और सहमति" / "गोपनीयता आणि संमती").

## Plan 5 Task 11 (web members form, consent dialog, profile consent)
- [ ] **hi/mr `members.form.{not_set,name_invalid,relation_required,birth_year_invalid,height_invalid,weight_invalid,allergen_invalid,allergen_limit,remove_allergy}`, `members.{born,limit_reached}`**: machine drafts for form errors and list lines. Check that the error lines read as a calm instruction, not blame.
- [ ] **hi/mr `members.form.remove_allergy_confirm`**: machine draft, allergy safety copy. It must say plainly that products with this allergen will no longer be flagged for this person. `{allergen}` comes after a colon so the sentence does not agree with the interpolated noun's gender.
- [ ] **hi/mr `consent.{ai_optional,required_note}`, `profile.{privacy_title,give_consent}`**: machine drafts. `ai_optional` must make clear that every result still appears without AI; only the explanation is missing.

## Integration wave 2 (Plan 5 Android and web merge)
- [ ] **hi/mr `members.form.remove_allergy_confirm`**: one string for both clients, with `{name}` and `{allergen}`. Integration machine draft. `{allergen}` follows a colon so the sentence does not agree with the noun's gender. It must say plainly that products with this allergen will no longer be flagged for this person.
- [ ] **Deduped keys**: `members.born_in` became `members.born`, `consent.optional_ai_note` became `consent.ai_optional`, `profile.consents_title` became `profile.privacy_title`. The web texts were kept; the Android drafts above for the removed keys no longer apply.
- [ ] **hi/mr `reason.custom_alert_unknown`**: integration machine draft for "These alerts couldn't be checked: {alerts}." It no longer blames the ingredient list (the alert can be unchecked for other reasons). `{alerts}` follows a colon so the sentence does not agree with the list.

## Plan 6 Task 3 (meal logging API)
- [ ] **hi/mr `error.{portion_required,serving_size_unknown,eaten_at_out_of_range,meal_not_found}`**: machine drafts. Check "सर्विंग" / "सर्व्हिंग" and "ग्राम" / "ग्रॅम", and that "खाने की एंट्री" / "खाण्याची नोंद" reads naturally for "food log".

## Plan 6 Task 7 (log, history, summaries, alternatives, search, compare, share)
- [ ] **hi/mr `meals.*`, `history.*`**: machine drafts. Check "दर्ज करें" / "नोंदवा" for "log", that `meals.online_only` clearly says web logging needs the internet and nothing is saved offline, and that `meals.queued_offline` reads as reassurance, not an error.
- [ ] **hi/mr `summary.*`**: machine drafts. `summary.incomplete` must say the real total may be HIGHER (some labels lack the value), never that the total is fine. `summary.limits_note` must read as "pending a clinician's review" ("चिकित्सक की समीक्षा" / "डॉक्टरांच्या पुनरावलोकनात"). `summary.sugar_note` must explain that label sugars include natural sugars. Check "शर्करा" vs "चीनी" (hi) and "साखर" (mr) against the open added-sugar item above.
- [ ] **hi/mr `alternatives.*`, `search.*`, `compare.*`**: machine drafts. "न्यूट्री-स्कोर" / "न्यूट्री-स्कोअर" must stay consistent with `result.grade`; "calculated by SmartNutri" must never read as an official or FSSAI rating. Check "संतृप्त वसा" / "संपृक्त चरबी" and "फ़ाइबर" / "तंतू".
- [ ] **hi/mr `share.*`**: machine drafts, and the exact strings in `packages/test-fixtures/share/` are generated from them (regenerate with `scripts/export_meal_fixtures.py --write` after any change). Check that `share.result.text` and `share.weekly` read naturally as a WhatsApp message, the end punctuation ("।" in hi, "." in mr) after `{members}`, and the relation labels used when a member has no name (`मैं`/`मी`, `माता/पिता`/`आई/वडील`, `जीवनसाथी`/`जोडीदार`). They must never mention health.

## Plan 7 Task 3 (voice answers and the rule-based fallback)
- [ ] **hi/mr `verdict.spoken.*` (spoken verdict sentences; kept in the server-only `verdict` namespace on web)** (`ok`, `caution`, `unknown`, `avoid`): machine drafts. These are spoken first in every voice answer, so they are health wording: each must state the engine status plainly and never soften it. `unknown` must make clear the label could not be read, so nothing can be said (never "probably fine"). Check "इस सदस्य के लिए" / "या सदस्यासाठी" sounds natural when spoken, and that `caution` ("सावधानी रखें" / "काळजी घ्या") is not read as "avoid".
- [ ] **hi/mr `voice.word_safe`**: "सुरक्षित" in both. This is the word the verdict lock rejects in LLM answers. Add any other common spoken word for "safe" (for example a Hinglish "सेफ") if users would say it.
- [ ] **hi/mr `error.{audio_too_long,audio_too_large,audio_unsupported,voice_not_understood,ai_unavailable}`** (Plan 7 Task 4): machine drafts. Calm, no blame. `voice_not_understood` must read as "we could not hear a question; hold the button and speak clearly". `ai_unavailable` is shown for every voice outage (speech, AI or storage).
- [ ] **hi/mr `voice.*` UI strings** (Plan 7 Task 7: `button_hold`, `recording`, `thinking`, `playing`, `mic_denied`, `unsupported_browser`, `too_long`, `not_understood`, `rate_limited`, `ai_unavailable`): machine drafts. Short button and status labels; check they fit a button and sound natural.
- [ ] **hi/mr `explanation.{title,source_fallback_note}`**: machine drafts. The fallback note must not suggest the result is less reliable: the verdict always comes from the rules; only the AI wording is missing.
- [ ] **hi/mr `methodology.*`** (intro, pending_review, sources_title, url_unverified, version, and `section.<id>.{title,description}` for all 11 sections): machine drafts and **health wording**. Check that nothing reads as a medical claim, that `nutriscore_2023` keeps "calculated by SmartNutri, not an FSSAI rating", that `allergens` keeps "unclear, never OK", and that `pending_review` clearly says a clinician has not reviewed the values yet. "हम कैसे जाँचते हैं" / "आम्ही कसे तपासतो" render "How we score"; check whether "स्कोर" wording is better.
- [ ] **hi/mr `report.*`**: machine drafts. Calm, no blame; `thanks` must not promise a fix or a date.
- [ ] **hi/mr `explanation.fallback_tip.{1,2,3}`**: machine drafts. General tips shown or spoken when the AI explanation is unavailable. Tip 3 must stay a suggestion to ask a doctor or dietitian, never an instruction that implies a diagnosis.
- [ ] **hi/mr `methodology.section.daily_limits.{title,description}`**: integration machine draft (Plan 6 added the `daily_limits` methodology section; Plan 7 requires client strings for every section). Health wording: it must say the comparison can over-warn because labels give total sugar, and must not read as advice to eat more protein.

## Plan 8 Task 2 (account deletion)
- [ ] **hi/mr `error.deletion_incomplete`**: machine drafts. It must read as a calm "deletion did not finish, please try again" and make clear that what was already deleted stays deleted (no hint that data was restored). Check "खाता" (hi) / "खाते" (mr) for account.

## Plan 8 Task 5 (phone OTP hook)
- [ ] **hi/mr `error.phone_otp_disabled`**: machine drafts. Calm "phone sign-in is not available yet, use email or Google"; keep "Google" in Latin script.

## Plan 6 Task 10 (web: log and history)
- [ ] **hi/mr `common.{cancel,close}`, `history.{previous_day,next_day,logged_title}`, `meals.log.{portion,saved_you}`**: machine drafts. Short button and heading labels; check `meals.log.saved_you` ("आपके लिए दर्ज किया गया" / "तुमच्यासाठी नोंदवले") matches `meals.log.saved`.
- [ ] **hi/mr `meals.log.amount_invalid`**: machine draft; `{max}` is 200 (servings) or 5000 (grams), passed in Latin numerals.
- [ ] **hi/mr `summary.total_g`, `summary.week_note`**: machine drafts. Health wording: `week_note` must say the week is compared with the DAILY limit for each day that has something logged (empty days are not counted), and must not read as a weekly allowance.

## Plan 6 Task 11 (web: alternatives, search, compare, share)
- [ ] **hi/mr `share.result.product_only`, `share.result.product_only_ungraded`**: machine drafts, used when the user leaves every member out of a share. They must match `share.result.text` / `share.result.ungraded` exactly, minus the `{members}` sentence (same "calculated by SmartNutri" wording and end punctuation).
- [ ] **hi/mr `share.include`, `share.preview`, `search.hint`**: machine drafts; short labels.

## Plan 8 Task 1 (Android: terms screen and consent routing)
- [ ] **hi/mr `consent.{update_note,needs_update,required_to_continue,updates_banner}`, `common.cancel`, `policy.open_failed`**: machine drafts. `required_to_continue` replaces the health-data text when a scan or check is refused for a missing consent; it must stay neutral ("please review and agree"). (Android now uses the web keys `consent.terms_step.*`, `consent.prompt.*`, `consent.review_agree` and `consent.terms.withdraw_confirm`; see the integration wave 3 note.)

## Plan 8 Task 2 (Android: profile tab and account deletion)
- [ ] **hi/mr `settings.*`** (`language_system`, `about_title`, `account_title`, `delete_button`, `delete_title`, `delete_body`, `delete_confirm_label`, `delete_confirm`) and `goodbye.action`: machine drafts. `delete_body` must list plainly what is erased and say it cannot be undone. **`settings.delete_confirm_word` is "DELETE" in all three languages on purpose** (easy to type on any keyboard); the app compares it ignoring case and spaces. If a reviewer localizes it, keep it a single word that is easy to type.

## Plan 7 Task 9 (Android: how we score)
- [ ] **hi/mr `methodology.{values,based_on}`** (now shared by both clients): machine drafts. `based_on` introduces source document titles (kept in their original language); it must read as "based on", not as an endorsement.

## Plan 7 Task 8 (Android: push-to-talk voice)
- [ ] **hi/mr `voice.replay`**: machine drafts. Short button labels.

## Plan 8 Task 1 (web: terms acceptance and consent routing)
- [ ] **hi/mr `consent.terms_step.*`, `consent.needs_update`, `consent.review_agree`, `consent.prompt.*`, `consent.terms.withdraw_confirm`**: machine drafts. The terms step must read as a clear, voluntary agreement (no pressure). `withdraw_confirm` must say plainly that checking and scanning stop until the user agrees again, and that saved data stays until the account is deleted (it is not erased by withdrawal). Keep "गोपनीयता सूचना" consistent with the privacy page title.

## Plan 8 Task 1 (web: privacy and terms pages, footer)
- [ ] **hi/mr `legal.*`, `footer.links_label`**: machine drafts. `english_only` must say plainly that the policy text is in English only for now (no promise of a date). `draft_notice` must say a lawyer is reviewing the text before launch. "गोपनीयता सूचना" / "उपयोग की शर्तें" (hi) and "गोपनीयता सूचना" / "वापराच्या अटी" (mr) must match `consent.terms_step.read_*`.

## Plan 8 Task 2 (web: profile language and Delete account)
- [ ] **hi/mr `settings.*`, `goodbye.*`**: machine drafts. `delete_body` must list plainly what is erased and say it cannot be undone; `goodbye.body` must not suggest anything was kept. `settings.delete_confirm_word` is "DELETE" in every language for now (typed in Latin script); decide with Android whether hi/mr should use a Devanagari word instead (the web compares case-insensitively).

## Plan 7 Task 11 (web: How we score page)
- [ ] **hi/mr `methodology.{meta_description,values,based_on,unavailable}`**: machine drafts. `meta_description` is the search-result snippet: it must keep "information, not medical advice" and make no health claim.

## Plan 7 Task 11 (web: Report a problem)
- [ ] **hi/mr `report.{reason_label,note_hint}`**: machine drafts. `note_hint` must clearly ask people not to type personal or health details into the free-text note.

## Plan 7 Task 10 (web: push-to-talk voice)
- [ ] **hi/mr `voice.{title,hint,elapsed,no_mic,you_asked,answer_title}`**: machine drafts. `hint` names the Space key (keep "Space" in Latin script). `you_asked` shows the transcript back; check it reads naturally with a quoted question.

## Integration wave 3 (Plans 6–8 clients merged)
- [ ] **hi/mr `consent.needs_update`**: Android and web drafted different hi/mr text for the same key; the web drafts were kept ("अपडेट हुआ है, कृपया देखें" / "अपडेट झाले आहे, कृपया पाहा").
- [ ] **hi/mr `settings.delete_title`, `settings.delete_body`, mr `settings.delete_confirm_label`**: both clients drafted these; the web drafts were kept. `delete_title` is now the section heading ("Delete account"); the Android dialog uses `settings.delete_dialog_title`.
- Keys removed as duplicates (callers moved): `consent.{screen_title,screen_intro,review,withdraw_terms_confirm}`, `settings.{goodbye_title,goodbye_body,delete_cancel}`, `methodology.{values_title,section_sources}`, `policy.{privacy,terms}`, `report.{cancel,close}`, `voice.close`. `settings.goodbye_action` moved to `goodbye.action` (text unchanged).

## Integration wave 3: SH1 (share defaults to product and grade)
- [ ] **hi/mr `share.privacy_note`, `share.include`**: new machine drafts. `privacy_note` must say only the product and its grade are shared, plus the result of anyone the user ticks; `include` must read as optional ("add a person's result").
- [ ] **hi/mr `share.result.*`, `share.weekly`, `share.link`**: the old texts with the trailing "Checked with SmartNutri: {url}" sentence moved into the new `share.link` key (text unchanged), and a full stop (। in hi) added where the sentence now ends. Check the punctuation reads naturally.

## Final fix batch (API errors)
- [ ] **hi/mr `error.payload_too_large`**: machine drafts. Shown when a request body is over the server cap (I2); generic, no blame.
- [ ] **hi/mr `error.search_query_too_short`**: machine drafts (I4, server minimum 3 letters). Keep the wording close to `search.too_short`.
- [ ] **hi/mr `summary.no_protein_target`**: machine drafts of the new neutral copy (F4). The old text asked for a weight, but children and members of unknown age get no target even with one; it must not hint that something is missing or wrong.

## Final fix batch (I4 search, m7 permissions)
- [ ] **hi/mr `search.too_short`**: the minimum went from 2 to 3 letters (I4); only the number changed in the drafts.
- [ ] **hi/mr `common.open_settings`**: machine drafts for the "Open settings" action shown when the microphone or camera permission is permanently denied (m7). "सेटिंग्स" (hi) and "सेटिंग्ज" (mr) match the existing permission messages.

## Search degraded note (follow-up a)
- [ ] **hi/mr `search.off_degraded`**: machine drafts. A small note under search results when the product-database search budget is spent and only SmartNutri products are shown ("more results will be added later"). Neutral, no blame.

## Plan 9 Tasks 1-2 (API errors: user types)
- [ ] **hi/mr `error.user_type_not_selected`, `error.follow_up_without_type`, `error.user_types_not_found`**: machine drafts. Neutral, no blame; they must not name a health type or condition.

## Plan 9 Task 3 (build muscle goal)
- [ ] **hi/mr `condition.build_muscle`, `members.goal.build_muscle`, `methodology.section.build_muscle.*`**: machine drafts ("मांसपेशियाँ बनाना" / "स्नायू बळकट करणे"). The description must stay informational: the daily protein figure is a guide, never "you need", and the kidney sentence must read as "ask your doctor", not as advice.

## Plan 9 Task 4 (protein and whey claims)
- [ ] **hi/mr `claim.protein_amount`, `claim.whey_only`, `claim.whey_protein`, `claim_reason.below_claimed`, `claim_reason.other_protein_source`, `claim_reason.whey_not_listed`, `nutrient.serving_size_g`**: machine drafts. "व्हे" is a transliteration of whey; check it is understood (or whether "व्हे (दूध से बना प्रोटीन)" is clearer). `below_claimed` starts with a `{basis, select}` phrase in hi/mr: check both branches. The tone must be factual (the table shows less than the claim), never "fake" or "cheating".

## Plan 9 Tasks 6 and 7 (protein sort, supplements)
- [ ] **hi/mr `reason.supplement_child`, `reason.supplement_infant`, `nutriscore.not_scored_supplement`, `confirm.category_option.supplement`, `alternatives.reason.source_supplement`, `alternatives.reason.source_protein_unknown`, `methodology.section.supplements.*`**: machine drafts. "सप्लीमेंट" / "सप्लिमेंट" are transliterations; check they are understood. The supplement reasons must stay "not recommended … check with your doctor", never a diagnosis or a dose. The confirm option must read as the user describing the pack (protein powder, whey, health supplement), not as a recommendation.

## Label accuracy v2
- [ ] **hi/mr `warning.fat_parts_mismatch`**: machine drafts. Shown when saturated plus trans fat is more than total fat; the user must tick the fat values. "संतृप्त"/"संपृक्त" should match `nutrient.sat_fat`.
- [ ] **hi/mr `warning.decimal_shift`**: machine drafts. "The decimal point may have been misread" (for example 50 instead of 5.0). Check that "दशमलव बिंदु" (hi) and "दशांश चिन्ह" (mr) are understood.
- [ ] **hi/mr `warning.column_mismatch`**: machine drafts. Shown next to one nutrient when its per 100 g and per-serving values disagree once the serving size is applied. Check "सर्विंग साइज़" (hi) and "सर्व्हिंग आकार" (mr) against `confirm.serving_size`.
- [ ] **hi/mr `error.image_quality_low`, `image_quality.{blur,glare,too_small}`**: machine drafts. Shown when a label photo is clearly unreadable and no extraction was tried (a retake prompt with a concrete fix). Keep it blame-free; check "धुंधली"/"धूसर" for blurred and "फ़्लैश"/"फ्लॅश" spellings.

## Plan 9 Task 8 (user types, focused modes, protein guide)
All hi/mr strings below are machine drafts and need a native reader. Safe words and health wording first.
- [ ] **hi/mr `user_types.*`** (title, 6 tiles, follow-ups, `not_covered`, `consent_note`, `prefill.*`): the health tile names diabetes, prediabetes, PCOS and BP. `consent_note` and `prefill.body` must say plainly that nothing is added unless the user confirms. `not_covered.body` must say results do not take thyroid, cholesterol, kidney disease or pregnancy into account. `prefill.goal_conflict` asks the user to choose ONE goal.
- [ ] **hi/mr `modes.*`, `nav.{protein,compare,search,more,how_we_score}`**: "मोड" / "मोड", "और" / "अधिक" for "More". `modes.same_checks` must say scan, results and allergy checks are identical in every mode.
- [ ] **hi/mr `home.cards.*`**: `allergy_check.unknown_note` and `unknown_explainer.body` must say that unknown means "could not check" and is never shown as safe. `claims_tip` / `protein_claims_tip` must say we CHECK claims, not that they are true. `weekly_family.body` is a count only (`{count}`).
- [ ] **hi/mr `protein.*`**: `guide` ends with "Information, not medical advice". `kidney_note` says to ask a doctor before eating more protein; it must not read as advice to eat more or less. `price_note` must say the price is never saved. Check "प्रोटीन" (hi) vs "प्रथिने" (mr), "स्कूप", and "सर्विंग" / "सर्व्हिंग" against the existing `summary.*` choices.
- [ ] **hi/mr `goal.*`**: `build_muscle` "मांसपेशियाँ बनाना" / "स्नायू वाढवणे". Informational only, no promise of results.
- [ ] **hi/mr `category.supplement`, `report.{sweeteners,caffeine}`, `image_quality.{title,hint_generic}`**: machine drafts. `report.sweeteners` and `report.caffeine` are plain facts from the ingredient list, not a warning level.
- Already present from earlier tasks and NOT re-added here (check they are on the review list above): `reason.supplement_{child,infant}`, `nutriscore.not_scored_supplement`, `claim.{protein_amount,whey_only,whey_protein}`, `claim_reason.{below_claimed,other_protein_source,whey_not_listed}`, `alternatives.reason.source_{supplement,protein_unknown}`, `warning.{fat_parts_mismatch,decimal_shift,column_mismatch}`, `image_quality.{blur,glare,too_small}` (the retake hint per `image_quality_low` `details.reasons`), `error.{user_type_not_selected,follow_up_without_type,user_types_not_found}`, `confirm.category_option.supplement`.
## Engine fixes EF1-EF3 (real-data experiments)
- [ ] **hi/mr `confirm.category_option.fat`**: machine drafts, now "Oil, fat, nuts or seeds" (the Nutri-Score 2023 fats, oils, nuts and seeds group: oils, ghee, butter, cream, nuts, peanut butter, oilseeds). "नट्स" is a transliteration (not "मेवे", which also means dried fruit); check it is understood. "बीज" / "बिया" must read as oilseeds (sunflower, pumpkin, flax), not grains or pulses.
- [ ] **hi/mr `warning.sodium_unit_suspect`**: machine drafts. Shown when a label prints sodium only (no salt) and the value read as mg is implausibly low for the product, most likely a "g" value (0.4 g read as 0.4 mg). The user then picks mg or g. It must read as "check the unit on the pack", never as "this food is low in sodium". Units mg and g stay as written.
## P9 safety review fixes
- [ ] **hi/mr `claim_reason.basis_unknown`**: machine drafts. Shown when a protein-amount claim does not say per 100 g or per serving (or names a bar or pack that may hold more than one serving). Neutral: the claim cannot be checked, never "wrong".
- [ ] **hi/mr `members.goal.build_muscle_adults_only`**: machine drafts. Shown when "build muscle" is picked for a member under 18 (the API answers 422 `body.goal`). Neutral and factual; it must not suggest any protein amount or product for the child.
- [ ] **hi/mr `confirm.category_suggestion.supplement`**: machine drafts. A hint on the confirm screen when the ingredients name whey or a protein isolate/concentrate, or protein is at least 50 g per 100 g. It must read as "may be", never as a recommendation; "सप्लीमेंट"/"सप्लिमेंट" should match `confirm.category_option.supplement`.
- [ ] **hi/mr `methodology.section.{build_muscle,weight_loss,supplements}.description`** (amended): machine drafts of the added sentences (protein notes for adults 18+ only; build muscle can't be set under 18; the supplement question on the confirm screen and the under-18 protein-sort exclusion). Keep "प्रोटीन आइसोलेट"/"प्रोटीन आयसोलेट" understandable.

## Plan 9 web (T12 to T14)
- [ ] **hi/mr `user_types.prefill.goal_neither`**: machine drafts. The third option in the goal-conflict radio list ("Neither (keep my current goal)"); it must read as keeping the goal unchanged, not as removing it.
- [ ] **hi/mr `search.sort_label`, `search.sort_relevance`**: machine drafts. The sort control on search and alternatives ("Sort": "Best match" / "Higher protein").
- Removed at P9 integration: `members.form.build_muscle_adult_only` (both clients use `members.goal.build_muscle_adults_only`).

## Voice audio not stored (ADR 0020)
- [ ] **hi/mr `settings.delete_body`**: machine edit. "Voice answers" was removed from the list of what account deletion erases, because voice answers are no longer stored. mr: the verb now agrees with "फोटो" ("कायमचे हटवले जातील"); check it reads naturally.

## Web QA fixes (2026-11-04)
- [ ] **hi/mr `meals.log.cta_for`, `voice.button_hold_for`**: machine drafts. Screen-reader names only ("I ate this, {name}", "Hold to ask, {name}"), so each member's button is distinct; the visible text stays `meals.log.cta` / `voice.button_hold`.

## Plan 10 (Food Diary slice 1: daily guide, hidden numbers, protein basis)
All of these are machine drafts in hi and mr. They sit beside health numbers, so tone matters most: information, never a judgement, never "you need", and no support contact (Q14).
- [ ] **hi/mr `targets.flag.*`** (tone, never judging): `rate_capped`, `deficit_capped`, `taper_active`, `goal_weight_reached`, `floor_applied`, `floor_applied_hidden`, `floor_limits_deficit`, `protein_capped`, `carbs_below_reference`, `average_sex_reference`, `outside_equation_age_range`, `underweight_maintenance`. They say what the guide did and that a doctor or dietitian can advise. `floor_applied_hidden` must read the same as `floor_applied` without a number.
- [ ] **hi/mr `targets.pregnancy.paused`** (and `targets.pregnancy.{question,yes,no,prefer_not}`): the question asks about pregnancy or breastfeeding; "Prefer not to say" pauses the guide as "yes" does. Hindi uses the feminine forms for the reader; check that is acceptable for a general audience.
- [ ] **hi/mr `targets.rate_option`**: plural and number formatting ("About {kg} kg a week ({pct}% of body weight)"); confirm word order and that `{kg}` and `{pct}` read naturally with the client's number formatting.
- [ ] **hi/mr `targets.how.*`, `targets.how.floor`**: the "how we got this" lines. Check "लीन मास" / "लीन मास" (lean mass), "समायोजित वज़न" / "समायोजित वजन" (adjusted weight) and "किलोकैलोरी" / "किलोकॅलरी" (kcal) are understood.
- [ ] **hi/mr `targets.activity.*` and `*_hint`**, **`targets.direction.*`**, **`targets.sex_reference.*`**, **`targets.step.*`**, **`targets.intro.*`**, **`targets.body_fat.*`**, **`targets.unusual_confirm`**, **`targets.save`**, **`targets.target_weight*`**, **`targets.needs_body_data`**: machine drafts of the guide setup screens. `{fields}` is a list of field names made by the client.
- [ ] **hi/mr `diary.disclaimer`, `diary.targets_consent`, `diary.eye.{hide,show}`, `diary.hidden_numbers`, `diary.of_target`, `diary.incomplete`**: machine drafts. `diary.of_target` ("{eaten} of {target}") needs the word order checked.
- [ ] **hi/mr `settings.diary.*`**, **`home.cards.today_targets.title`**, **`protein.guide_lean`**, **`protein.guide_adjusted`**, **`methodology.section.energy_targets.{title,description}`**: machine drafts. "Information, not medical advice" must stay in the protein guide lines.
- [ ] **hi/mr `error.{goal_not_allowed_minor, goal_not_allowed_underweight, target_weight_too_low, rate_not_allowed, fat_pct_out_of_range, adaptive_not_enabled, body_fat_out_of_range, diary_member_not_enabled, date_in_future, goal_settings_not_found}`**: machine drafts. `goal_not_allowed_underweight` is gentle by design (it offers keeping a steady weight).

### Plan 10 fix round 1 (safety review)
- [ ] **hi/mr `targets.flag.carbs_below_reference_hidden`** (new): the same message as `carbs_below_reference` without the 130 g figure; the client shows it when macros are hidden.
- [ ] **hi/mr `targets.flag.rate_capped`** (reworded): "nearest available option" replaces "safest option" (neutral, no safety claim). Check it reads as neutral.
- [ ] **hi/mr `targets.field.{height,weight,birth_year,sex,activity,body_fat}`** (new): plain field names for the "needs data" and "please check" messages. No units and no "(optional)".

- `targets.rate_option_pct` (hi, mr): pace shown as % only when all numbers are hidden. Machine draft.

## Plan 11 (Food Diary slice 2: the diary day, quick add, copy)
All of these are machine drafts in hi and mr. The diary sits beside health numbers, so the tone is neutral: information, never a judgement ("over" is a plain fact, not a warning), no streaks, no "good day" labels.
- [ ] **hi/mr `diary.copied`, `diary.week.average`** (plural forms): `{count, plural, one {...} other {...}}` and the "average over {days} logged days" sentence. Check the singular and plural wording reads naturally, and that `#` sits where a Hindi or Marathi speaker expects the number.
- [ ] **hi/mr `diary.over`** (tone): "{value} over" is a plain fact about the day's number, not a warning. Check "ज़्यादा" / "जास्त" does not read as scolding. Same for `diary.left`.
- [ ] **hi/mr `diary.servings_line`**: "{servings, plural, one {# serving} other {# servings}} · {grams} g". Hindi and Marathi use one form for both; check "सर्विंग" / "सर्व्हिंग" is the word people use.
- [ ] **hi/mr `diary.slot.{breakfast,lunch,snack,dinner}`**: the default meal names (a user can rename them). Check "दोपहर का खाना" / "दुपारचे जेवण" and "रात का खाना" / "रात्रीचे जेवण" are what families say, and that "स्नैक्स" / "स्नॅक्स" is understood.
- [ ] **hi/mr `diary.week.at_least`, `diary.view.day`, `diary.slots.manage`, `diary.slots.removed`**: "At least {value}" (a lower bound when a logged day is incomplete), the "Day" segment, "Edit meals" (the claims check bans the word "manage"), and the label for an archived meal slot in history ("Removed meal"). Check each reads naturally.
- [ ] **mr `diary.copied`, `diary.week.average`, `diary.servings_line`** now print the number with a plain `{count}` / `{days}` / `{servings}` inside the plural (not `#`) so it stays a Latin digit. Check the wording still reads well.
- [ ] **hi/mr `diary.mark_partial`, `diary.partial_badge`, `diary.partial_note`**: "partly logged" days are left out of weekly averages. Check the phrasing is clear without sounding like a fault.
- [ ] **hi/mr `diary.week.protein_days`**: "Protein guide reached on {met} of {days} logged days". Check the word order with two numbers.
- [ ] **hi/mr `diary.quick_add.*`, `diary.quick_add_name`, `diary.quick_badge`, `foods.blank_is_unknown`, `foods.quick_add`**: quick-add form labels. "Blank is never counted as 0" must stay clear: an empty field means "unknown".
- [ ] **hi/mr `diary.title`, `diary.today`, `diary.add`, `diary.add_to_slot`, `diary.empty_day`, `diary.copy_*`, `diary.move`, `diary.edit`, `diary.delete`, `diary.delete_confirm`, `diary.waiting_sync`, `diary.prev_day`, `diary.next_day`, `diary.pick_date`, `diary.share_week`, `diary.no_guide`, `diary.remaining`, `diary.consumed`, `nav.diary`, `foods.recent`**: everyday UI words. `diary.add_to_slot` puts a meal name in `{slot}`; check the postposition ("में" / "मध्ये") works with a user-typed meal name.
- [ ] **hi/mr `error.{quick_add_energy_required, copy_source_empty, copy_too_many, date_too_old, meal_slot_not_found, meal_slot_archived, meal_slot_limit_reached, timezone_invalid}`**: error messages. `date_too_old` mentions 30 days (Marathi uses ३०).
- Note: `diary.partial_note` is shorter than the spec draft: it drops "and of learning your energy use" because the energy-learning feature does not ship in this slice. `diary.quick_add.name_label` replaces the plan's `diary.quick_add.name`, which flattens to the same ARB key as `diary.quick_add_name`.
- [ ] **hi/mr `diary.slots.{add,rename,reset_name,name_hint,time_window,time_window_hint,reorder,remove,remove_note,removed_badge,limit,last_active,duplicate,pick_again}`, `settings.diary.meals`, `error.{meal_slot_last_active, meal_slot_label_duplicate}`** (Plan 11 Task 14): meal-management screen copy. `diary.slots.limit` uses `{max}`. Check "भोजन"/"जेवण" is what families call a meal slot, and that "हटाएँ"/"काढा" (remove) does not suggest the logged food is deleted (`remove_note` says it stays).

- `diary.slots.move_up`, `diary.slots.move_down` (hi, mr): accessible names for the meal reorder buttons. Machine draft.
- `diary.slots.time_start`, `diary.slots.time_end` (hi, mr): accessible names for the meal time inputs. Machine draft.

## Plan 12 slice 3 (Food Diary: household units and Indian foods)
All of these are machine drafts in hi and mr.
- [ ] **hi/mr `error.{unit_grams_unknown, unit_not_supported, quantity_out_of_range, food_not_found}`**: error messages. `unit_grams_unknown` says we do not know the grams of a household measure (for example a katori of a food with no density) and offers grams or the user's own value; check it does not read as a fault of the user. "Measure" is "माप" (hi, mr).
- [ ] **hi/mr `unit.*`** (the 17 unit names, ICU plurals; the label always shows the ml beside it through `unit.ml_hint`): check the word people use, and the plural forms. Hindi: कटोरी / कटोरियाँ, रोटी / रोटियाँ, चम्मच, गिलास, पीस, स्लाइस, सर्विंग. Marathi: **वाटी / वाट्या** (katori), चपाती / चपात्या (roti; check "पोळी" is not what families say), चमचा / चमचे, ग्लास, नग (piece), स्लाइस, सर्व्हिंग. The size words (छोटी, मध्यम, बड़ी / लहान, मध्यम, मोठी) match the NIN small, medium and large katori (115, 155 and 360 ml), and "medium" is smaller than the default katori (200 ml), so the ml hint matters. Marathi plurals print the word only (no `#`).
- [ ] **hi/mr `unit.{ml_hint, grams_hint, amount_hint_ml, edit_grams, set_grams, your_value, reset_grams, unknown}`**: "1 {unit} ≈ {grams} g" keeps the "≈" sign: check it reads naturally with the Devanagari word order. `unit.unknown` must not read as a fault of the user.
- [ ] **hi/mr `foods.*`** (`search_placeholder`, `group.{indian,packaged}`, `partial_results`, `no_results`, `kind.{food,dish,product}`, `dish_ingredients`, `review_pending`, `preview_note`, `not_known`, `portion.{title,quantity,save}`) and **`diary.portion_line`, `diary.portion_line_ml`**: everyday UI words. "Dish" is "व्यंजन" / "पदार्थ"; check both. `foods.review_pending` must read as a plain status, not a warning.
- [ ] **hi/mr `attribution.{usda_fdc,smartnutri_recipe}`**: credit lines. Keep "USDA FoodData Central" in Latin script (the data source's name), and check "सार्वजनिक डोमेन" / "public domain" is understood.
- [ ] **hi/mr `methodology.food_data.{title,body}`**: the How we score paragraph on food data and household measures. It cites USDA FoodData Central (kept in English, as a citation) and ICMR-NIN 2024 Annexure I, and says dishes are pending dietitian review. Reworded after safety review (the old text overstated the source): katori sizes follow ICMR-NIN 2024; some cup conversions derive from USDA cup weights and are marked approximate; glass and other values are our reference set pending dietitian review; unknown values stay unknown. Check that "approximate" (अनुमानित / अंदाजे) and "unknown" (अज्ञात) read plainly, that it does not read as a medical claim and that "information, not medical advice" stays.

