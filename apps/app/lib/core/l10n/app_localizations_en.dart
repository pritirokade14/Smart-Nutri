// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get alertAddedSugar => 'added sugar';

  @override
  String get alertArtificialSweetener => 'artificial sweeteners';

  @override
  String get alertMaida => 'maida (refined wheat flour)';

  @override
  String get alertMsg => 'MSG (monosodium glutamate)';

  @override
  String get alertPalmOil => 'palm oil';

  @override
  String get allergenCrustacean => 'Shellfish (crustaceans)';

  @override
  String get allergenEgg => 'Egg';

  @override
  String get allergenFish => 'Fish';

  @override
  String get allergenGluten => 'Gluten';

  @override
  String get allergenMilk => 'Milk';

  @override
  String get allergenMustard => 'Mustard';

  @override
  String get allergenPeanut => 'Peanut';

  @override
  String get allergenSesame => 'Sesame';

  @override
  String get allergenSoy => 'Soy';

  @override
  String get allergenSulphite => 'Sulphites';

  @override
  String get allergenTreeNut => 'Tree nuts';

  @override
  String get appName => 'SmartNutri AI';

  @override
  String get attributionOff => 'Data from Open Food Facts (ODbL)';

  @override
  String get authChange => 'Change';

  @override
  String get authCodeLabel => '6-digit code';

  @override
  String get authEmail => 'Continue with email';

  @override
  String get authEmailLabel => 'Email address';

  @override
  String get authError => 'Could not sign in. Please try again.';

  @override
  String get authGoogle => 'Continue with Google';

  @override
  String get authPhone => 'Continue with phone';

  @override
  String get authPhoneLabel => 'Phone number (with country code)';

  @override
  String get authSendCode => 'Send code';

  @override
  String get authSignOut => 'Sign out';

  @override
  String get authTitle => 'Sign in';

  @override
  String get authVerify => 'Verify';

  @override
  String get claimDiabeticFriendly => 'Diabetic friendly';

  @override
  String get claimHighProtein => 'High protein';

  @override
  String get claimLowFat => 'Low fat';

  @override
  String get claimLowSodium => 'Low sodium';

  @override
  String get claimLowSugar => 'Low sugar';

  @override
  String get claimNoAddedSugar => 'No added sugar';

  @override
  String get claimNoRefinedSugar => 'No refined sugar';

  @override
  String claimReasonAddedSugarIngredient(String ingredients) {
    return 'The ingredients include added sugar: $ingredients.';
  }

  @override
  String claimReasonBelowMinimum(String limit, String value) {
    return 'Protein gives $value% of the energy, below the $limit% this claim needs.';
  }

  @override
  String claimReasonExceedsLimit(String limit, String value) {
    return 'The label shows $value per 100 g/ml, above this claim\'s limit of $limit.';
  }

  @override
  String get claimReasonIngredientsUnknown =>
      'The ingredients list is not available, so this claim can\'t be checked.';

  @override
  String get claimReasonNoStandard =>
      'There is no standard to check this claim against.';

  @override
  String claimReasonNutrientMissing(String nutrient) {
    return 'The label does not show $nutrient, so this claim can\'t be checked.';
  }

  @override
  String get claimReasonOk => 'The label data is consistent with this claim.';

  @override
  String claimReasonRefinedSugarIngredient(String ingredients) {
    return 'The ingredients include refined sugar: $ingredients.';
  }

  @override
  String get claimSourceOfProtein => 'Source of protein';

  @override
  String get claimSugarFree => 'Sugar free';

  @override
  String get claimVerdictContradicted => 'Label data contradicts this claim';

  @override
  String get claimVerdictSupported => 'Label data supports this claim';

  @override
  String get claimVerdictUnverifiable => 'Can\'t be checked from the label';

  @override
  String get commonDisclaimer => 'Information, not medical advice.';

  @override
  String get commonLoading => 'Loading…';

  @override
  String get commonRetry => 'Try again';

  @override
  String get conditionDiabetes => 'Diabetes';

  @override
  String get conditionHypertension => 'High blood pressure';

  @override
  String get conditionPcos => 'PCOS';

  @override
  String get conditionPrediabetes => 'Prediabetes';

  @override
  String get conditionWeightLoss => 'Weight loss';

  @override
  String get confirmAddIngredient => 'Add an ingredient';

  @override
  String get confirmAllergenStatement => 'Allergen statement';

  @override
  String get confirmBasis => 'Values on the pack are';

  @override
  String get confirmBasisOptionPer100g => 'Per 100 g';

  @override
  String get confirmBasisOptionPerServing => 'Per serving';

  @override
  String get confirmBrand => 'Brand';

  @override
  String get confirmCategory => 'Product type';

  @override
  String get confirmCategoryOptionBeverage => 'Drink';

  @override
  String get confirmCategoryOptionCheese => 'Cheese';

  @override
  String get confirmCategoryOptionFat => 'Oil or fat';

  @override
  String get confirmCategoryOptionGeneral => 'Food';

  @override
  String get confirmCategoryOptionWater => 'Packaged water';

  @override
  String get confirmChooseRequired => 'Choose one to continue';

  @override
  String get confirmClaims => 'Claims on the pack';

  @override
  String get confirmClearStatementConfirm =>
      'I checked the pack: this statement isn\'t printed';

  @override
  String get confirmConfirmValue => 'Matches the pack';

  @override
  String confirmDerivedPerServing(String serving) {
    return 'Worked out from a $serving g serving';
  }

  @override
  String get confirmFieldAddedSugarsG => 'Added sugars (g)';

  @override
  String get confirmFieldCarbsG => 'Carbohydrates (g)';

  @override
  String get confirmFieldEnergyKcal => 'Energy (kcal)';

  @override
  String get confirmFieldFatG => 'Total fat (g)';

  @override
  String get confirmFieldFiberG => 'Fibre (g)';

  @override
  String get confirmFieldProteinG => 'Protein (g)';

  @override
  String get confirmFieldSaltG => 'Salt (g)';

  @override
  String get confirmFieldSatFatG => 'Saturated fat (g)';

  @override
  String get confirmFieldSodiumMg => 'Sodium (mg)';

  @override
  String get confirmFieldSugarsG => 'Total sugars (g)';

  @override
  String get confirmFieldTransFatG => 'Trans fat (g)';

  @override
  String get confirmIngredients => 'Ingredients';

  @override
  String get confirmLeaveBlankHint => 'Leave blank if it isn\'t printed';

  @override
  String get confirmMayContainStatement => 'May-contain statement';

  @override
  String get confirmName => 'Product name';

  @override
  String get confirmNotMedicalAdvice => 'Information, not medical advice.';

  @override
  String get confirmOpenExisting => 'Open the saved product';

  @override
  String get confirmRemoveIngredient => 'Remove this ingredient';

  @override
  String get confirmSave => 'Confirm and save';

  @override
  String get confirmServingSize => 'Serving size (g)';

  @override
  String get confirmSodium => 'Sodium';

  @override
  String get confirmSodiumUnit => 'Sodium unit on the pack';

  @override
  String get confirmSodiumUnitOptionG => 'g';

  @override
  String get confirmSodiumUnitOptionMg => 'mg';

  @override
  String get confirmSubtitle =>
      'Check every value against the pack. Leave blank if not printed.';

  @override
  String get confirmTitle => 'Check the label values';

  @override
  String get confirmVegMarkNonVeg => 'Non-vegetarian (brown mark)';

  @override
  String get confirmVegMarkNone => 'No mark on the pack';

  @override
  String get confirmVegMarkTitle => 'Veg or non-veg mark';

  @override
  String get confirmVegMarkVeg => 'Vegetarian (green mark)';

  @override
  String get confirmWithheldHint =>
      'Check this value on the pack, then tick to confirm it.';

  @override
  String get dietEggetarian => 'Eggetarian';

  @override
  String get dietJain => 'Jain';

  @override
  String get dietNonVeg => 'Non-vegetarian';

  @override
  String get dietVeg => 'Vegetarian';

  @override
  String get dietVegan => 'Vegan';

  @override
  String get errorAuthInvalid => 'Your session expired. Please sign in again.';

  @override
  String get errorAuthRequired => 'Please sign in.';

  @override
  String get errorConsentRequired =>
      'To save allergies, health conditions, a goal, height or weight, please agree to health data processing first.';

  @override
  String get errorConsentVersionMismatch =>
      'This consent text has been updated. Please reload and review it again.';

  @override
  String get errorExtractionFailed =>
      'We couldn\'t read this label. Try another photo or enter the details manually.';

  @override
  String get errorExtractionUnavailable =>
      'Label reading is unavailable right now. Try again later or enter the details manually.';

  @override
  String get errorForbidden => 'You don\'t have access to this.';

  @override
  String get errorHttpError => 'Something went wrong. Please try again.';

  @override
  String get errorImageTooLarge =>
      'This photo is too large. Please use a photo under 8 MB.';

  @override
  String get errorImplausibleValue =>
      'Some values don\'t look right. Please check the highlighted fields, or leave them blank.';

  @override
  String get errorInternalError => 'Something went wrong. Please try again.';

  @override
  String get errorInvalidBarcode => 'That doesn\'t look like a valid barcode.';

  @override
  String get errorInvalidProductRef => 'Choose a product to check.';

  @override
  String get errorMemberLimit => 'You can add up to 10 family members.';

  @override
  String get errorMemberNotFound => 'That family member wasn\'t found.';

  @override
  String get errorMethodNotAllowed =>
      'This action isn\'t supported. Please update the app.';

  @override
  String get errorNetwork => 'No internet connection.';

  @override
  String get errorNotFound => 'Not found.';

  @override
  String get errorOffUnavailable =>
      'The product database is busy right now. Please try again in a moment.';

  @override
  String get errorPrimaryMember => 'Your own profile can\'t be removed.';

  @override
  String get errorProductExists => 'This product is already saved.';

  @override
  String get errorProductNotFound => 'We couldn\'t find this product yet.';

  @override
  String get errorRateLimited => 'Too many requests. Please wait a moment.';

  @override
  String get errorRateLimitedScans =>
      'You\'ve reached today\'s label-scan limit.';

  @override
  String get errorRateLimitedVoice =>
      'You\'ve reached today\'s voice-question limit.';

  @override
  String get errorScanImageNotFound =>
      'We couldn\'t find that photo. Please take or upload it again.';

  @override
  String get errorScanNotFound =>
      'We couldn\'t find that label scan. Please scan the label again.';

  @override
  String get errorStorageUnavailable =>
      'We couldn\'t handle the photo right now. Please try again in a moment.';

  @override
  String get errorUnauthorized => 'Please sign in.';

  @override
  String get errorUnsupportedImage => 'Please use a JPEG, PNG or WebP photo.';

  @override
  String get errorValidationError => 'Please check the highlighted fields.';

  @override
  String get highInFat => 'High in fat';

  @override
  String highInPercentOfLimit(String pct) {
    return '$pct% of the limit';
  }

  @override
  String get highInSalt => 'High in salt';

  @override
  String get highInSatFat => 'High in saturated fat';

  @override
  String get highInSugar => 'High in sugar';

  @override
  String get homeScanCta => 'Scan a product';

  @override
  String homeWelcome(String name) {
    return 'Hello, $name';
  }

  @override
  String get labelCameraPermissionDenied =>
      'Camera access is off. Allow it in Settings to photograph the label, or choose a photo or enter the details manually.';

  @override
  String get labelChooseFile => 'Choose a file';

  @override
  String get labelDropHere => 'Drop a photo here';

  @override
  String get labelEnterManually => 'Enter the details manually';

  @override
  String get labelReading => 'Reading the label…';

  @override
  String get labelRetake => 'Retake';

  @override
  String get labelTakePhoto => 'Take a photo';

  @override
  String get labelTitle => 'Photograph the label';

  @override
  String get labelUploading => 'Uploading the photo…';

  @override
  String get notfoundGoToLabel =>
      'We don\'t know this product yet — photograph its label';

  @override
  String get nutrientCarbsG => 'carbohydrate';

  @override
  String get nutrientEnergyKcal => 'energy (calories)';

  @override
  String get nutrientFatG => 'fat';

  @override
  String get nutrientProteinG => 'protein';

  @override
  String get nutrientSalt => 'salt';

  @override
  String get nutrientSatFat => 'saturated fat';

  @override
  String get nutrientSodiumMg => 'sodium';

  @override
  String get nutrientSugarsG => 'sugars';

  @override
  String get nutriscoreCalculatedBy => 'Nutri-Score calculated by SmartNutri';

  @override
  String get nutriscoreInsufficientData =>
      'Not enough label data to calculate a Nutri-Score.';

  @override
  String get productClaimsHeading =>
      'Claims on the label, checked by SmartNutri';

  @override
  String productLabelSays(String claim) {
    return 'Label says: $claim';
  }

  @override
  String get productMetaDescription =>
      'Nutrition facts, Nutri-Score calculated by SmartNutri, and ingredients for this packaged food. Information, not medical advice.';

  @override
  String productMetaTitle(String name) {
    return '$name – nutrition facts | SmartNutri';
  }

  @override
  String get productPublicCta => 'Check it for your family';

  @override
  String reasonAddedSugars(String ingredients) {
    return 'Contains added sugars: $ingredients.';
  }

  @override
  String get reasonAgeUnknown =>
      'Add this member\'s birth year: this food may not suit young children or babies.';

  @override
  String reasonAllergenContains(String allergen) {
    return 'Contains $allergen, which is on your avoid list.';
  }

  @override
  String reasonAllergenMayContain(String allergen) {
    return 'May contain $allergen, which is on your avoid list.';
  }

  @override
  String reasonAllergenUnknown(String allergen) {
    return 'We can\'t tell whether this contains $allergen.';
  }

  @override
  String reasonAllergenUnrecognised(String allergen) {
    return 'We don\'t recognise the allergen \"$allergen\" in your profile.';
  }

  @override
  String reasonCarbsPerServingHigh(String basis, String carbs_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'per serving',
      'other': 'per 100 g/ml',
    });
    return '$carbs_g g carbohydrate $_temp0. This may not suit your condition; check with your doctor.';
  }

  @override
  String reasonCardioRiskHighIn(String high_in) {
    return 'High in $high_in. People managing blood sugar are often advised to limit these; check with your doctor.';
  }

  @override
  String get reasonChildCaffeine =>
      'Contains caffeine, which is not recommended for children.';

  @override
  String reasonChildSaltHigh(String salt_g) {
    return '$salt_g g salt per 100 g/ml is high for a child.';
  }

  @override
  String reasonChildSugarHigh(String basis, String limit_g, String pct) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'One serving',
      'other': '100 g/ml',
    });
    return '$_temp0 gives $pct% of a child\'s daily sugar limit (about $limit_g g a day). That is high for a child.';
  }

  @override
  String reasonChildSugarModerate(String basis, String limit_g, String pct) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'One serving',
      'other': '100 g/ml',
    });
    return '$_temp0 gives $pct% of a child\'s daily sugar limit (about $limit_g g a day). That is on the higher side for a child.';
  }

  @override
  String reasonConditionUnrecognised(String condition) {
    return 'We do not have guidance for \"$condition\" yet.';
  }

  @override
  String reasonCustomAlert(String ingredients) {
    return 'Contains $ingredients, which you asked to be alerted about.';
  }

  @override
  String reasonCustomAlertUnknown(String alerts) {
    return 'We couldn\'t read the ingredients clearly, so we can\'t check for $alerts, which you asked to be alerted about.';
  }

  @override
  String reasonDietUnknown(String diet) {
    return 'We can\'t tell whether this fits the $diet diet.';
  }

  @override
  String reasonDietViolation(String diet, String ingredients) {
    return 'May not match the $diet diet: $ingredients.';
  }

  @override
  String reasonEnergyDense(String energy_kcal) {
    return 'This is an energy-dense food ($energy_kcal kcal per 100 g/ml). Consider a smaller portion.';
  }

  @override
  String get reasonGoodProteinDensity =>
      'A good amount of protein for its calories.';

  @override
  String reasonHiddenSugars(String ingredients) {
    return 'Contains sugars listed under other names: $ingredients.';
  }

  @override
  String get reasonInfantAddedSalt =>
      'Contains added salt, which is not recommended for children under 2.';

  @override
  String get reasonInfantAddedSugar =>
      'Contains added sugar, which is not recommended for children under 2.';

  @override
  String get reasonInfantCaffeine =>
      'Contains caffeine, which is not recommended for children under 2.';

  @override
  String get reasonInfantHoney =>
      'Contains honey, which should not be given to babies under 1 year. For toddlers, check with your doctor.';

  @override
  String reasonInfantSaltHigh(String salt_g) {
    return '$salt_g g salt per 100 g/ml is high for a child under 2.';
  }

  @override
  String reasonInfantSugarHigh(String sugars_g) {
    return '$sugars_g g sugar per 100 g/ml is high for a child under 2.';
  }

  @override
  String get reasonIngredientsMissing =>
      'The ingredients list was not readable, so some checks could not be done.';

  @override
  String reasonMisleadingSugarClaim(String claim) {
    return 'The pack says \"$claim\", but the label data does not support this claim.';
  }

  @override
  String reasonNutrientMissing(String nutrient) {
    return 'The label does not show $nutrient, so this check could not be done.';
  }

  @override
  String reasonNutriscoreLow(String grade) {
    return 'Nutri-Score $grade points to lower overall nutrition quality.';
  }

  @override
  String reasonSaltHigh(String salt_g) {
    return 'High in salt: $salt_g g per 100 g/ml.';
  }

  @override
  String reasonSaltModerate(String salt_g) {
    return 'Moderate salt: $salt_g g per 100 g/ml.';
  }

  @override
  String reasonSodiumAdditives(String ingredients) {
    return 'Contains sodium-based additives: $ingredients.';
  }

  @override
  String reasonSugarHigh(String sugars_g) {
    return 'High in sugar: $sugars_g g per 100 g/ml.';
  }

  @override
  String reasonSugarModerate(String sugars_g) {
    return 'Moderate sugar: $sugars_g g per 100 g/ml.';
  }

  @override
  String reasonVariantCustomAlertFlagOnly(String alert) {
    return 'The product data lists $alert, which you asked to be alerted about.';
  }

  @override
  String reasonVariantDietViolationMarkOnly(String diet) {
    return 'The pack has the brown non-vegetarian mark, so this may not match the $diet diet.';
  }

  @override
  String reasonVariantNutrientMissingLowConfidence(String nutrient) {
    return 'We couldn\'t read $nutrient clearly on the label, so this check could not be done.';
  }

  @override
  String resultForMember(String name) {
    return 'For $name';
  }

  @override
  String resultGrade(String grade) {
    return 'Nutri-Score $grade';
  }

  @override
  String get resultHighInTitle => 'High in';

  @override
  String get resultIngredients => 'Ingredients';

  @override
  String get resultNoIngredients => 'Ingredients not available';

  @override
  String get resultScanAnother => 'Scan another product';

  @override
  String get resultTitle => 'Result';

  @override
  String get resultYou => 'You';

  @override
  String get scanCameraDenied =>
      'Camera access is off. You can type the barcode instead.';

  @override
  String get scanCameraUnavailable =>
      'No camera found. You can type the barcode instead.';

  @override
  String get scanInvalid =>
      'Enter the 8, 12, 13 or 14 digits under the barcode.';

  @override
  String get scanManualEntry => 'Or type the barcode';

  @override
  String get scanManualPlaceholder => 'e.g. 8901063201089';

  @override
  String get scanNotFound => 'We couldn\'t find this product yet.';

  @override
  String get scanOffUnavailable =>
      'The product database is busy right now. Please try again in a moment.';

  @override
  String get scanRetry => 'Try again';

  @override
  String get scanScanning => 'Point the camera at the barcode';

  @override
  String get scanSubmit => 'Check this product';

  @override
  String get scanTitle => 'Scan a barcode';

  @override
  String get statusAvoid => 'Avoid';

  @override
  String get statusCaution => 'Caution';

  @override
  String get statusOk => 'OK';

  @override
  String get statusUnknown => 'Label unclear';

  @override
  String verdictConfidenceNote(String reason) {
    String _temp0 = intl.Intl.selectLogic(reason, {
      'low_confidence':
          'The label was hard to read, so this result is less certain.',
      'other': 'Some data is uncertain.',
    });
    return '$_temp0';
  }

  @override
  String get verdictHideReasons => 'Hide reasons';

  @override
  String get verdictProfileNotSetUp =>
      'Profile not set up: age, allergies and diet aren\'t checked yet.';

  @override
  String get verdictReasonUnavailable =>
      'Details for this result aren\'t available in this version.';

  @override
  String verdictRuleApplied(String rule) {
    return 'Rule applied: $rule';
  }

  @override
  String get verdictShowAllReasons => 'Show all reasons';

  @override
  String get verdictStatusAvoid => 'Avoid';

  @override
  String get verdictStatusCaution => 'Caution';

  @override
  String get verdictStatusOk => 'OK';

  @override
  String get verdictStatusUnknown => 'Label unclear';

  @override
  String get warningBasisMismatch =>
      'We couldn\'t tell whether these values are per 100 g or per serving. Choose which one the pack shows.';

  @override
  String get warningCategoryCheck =>
      'Check that the product type is right, because it changes how the values are read.';

  @override
  String get warningCategoryUnknown =>
      'We couldn\'t tell what type of product this is. Choose one.';

  @override
  String get warningDerivedFromServing =>
      'This value was worked out from the per-serving amount. Check it against the pack.';

  @override
  String get warningEnergyMismatch =>
      'The energy doesn\'t match the other values. Check it on the pack.';

  @override
  String get warningImplausibleValue =>
      'This value looks unusual. Please check it against the pack.';

  @override
  String get warningKcalKjMismatch =>
      'The kcal and kJ values don\'t match each other. Check both on the pack.';

  @override
  String get warningLowConfidence =>
      'The label was hard to read. Please check every value against the pack.';

  @override
  String get warningPer100gMissing =>
      'The pack\'s per 100 g values weren\'t found. Check the numbers or enter them from the pack.';

  @override
  String get warningPerServingIgnored =>
      'The per-serving values on the pack weren\'t used. Check that the per 100 g values are right.';

  @override
  String get warningSaltSodiumMismatch =>
      'The salt and sodium values don\'t match each other. Check both on the pack.';

  @override
  String get warningUnitUnconfirmed =>
      'The unit for this value wasn\'t clear. Choose mg or g as printed.';

  @override
  String get warningUnreadableField =>
      'We couldn\'t read this value. Enter it from the pack, or leave it blank.';

  @override
  String get warningUpperBound =>
      'The pack says \'less than\' this amount. Confirm it if that\'s right.';
}
