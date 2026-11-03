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

## Final fix batch (I4 search, m7 permissions)
- [ ] **hi/mr `search.too_short`**: the minimum went from 2 to 3 letters (I4); only the number changed in the drafts.
- [ ] **hi/mr `common.open_settings`**: machine drafts for the "Open settings" action shown when the microphone or camera permission is permanently denied (m7). "सेटिंग्स" (hi) and "सेटिंग्ज" (mr) match the existing permission messages.
