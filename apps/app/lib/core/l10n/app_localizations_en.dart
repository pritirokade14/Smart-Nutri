// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

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
  String get errorInternalError => 'Something went wrong. Please try again.';

  @override
  String get errorInvalidBarcode => 'That doesn\'t look like a valid barcode.';

  @override
  String get errorInvalidProductRef => 'Choose a product to check.';

  @override
  String get errorMemberNotFound => 'That family member wasn\'t found.';

  @override
  String get errorNetwork => 'No internet connection.';

  @override
  String get errorNotFound => 'Not found.';

  @override
  String get errorOffUnavailable =>
      'The product database is busy right now. Please try again in a moment.';

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
  String verdictRuleApplied(String rule) {
    return 'Rule applied: $rule';
  }

  @override
  String get verdictStatusAvoid => 'Avoid';

  @override
  String get verdictStatusCaution => 'Caution';

  @override
  String get verdictStatusOk => 'OK';

  @override
  String get verdictStatusUnknown => 'Label unclear';
}
