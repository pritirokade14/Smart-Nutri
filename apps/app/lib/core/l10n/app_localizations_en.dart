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
  String get alternativesCompare => 'Compare';

  @override
  String alternativesForMember(String name) {
    return 'For $name';
  }

  @override
  String get alternativesReasonNoBetterFound =>
      'We did not find a product with a better Nutri-Score of this kind.';

  @override
  String get alternativesReasonNoCategory =>
      'We cannot suggest options for this product yet.';

  @override
  String get alternativesReasonSourceProteinUnknown =>
      'This product\'s label does not show enough protein and energy data to compare protein.';

  @override
  String get alternativesReasonSourceSupplement =>
      'We do not suggest other products for supplements.';

  @override
  String get alternativesReasonSourceUngraded =>
      'This product does not have enough label data to compare.';

  @override
  String get alternativesSubtitle =>
      'Same kind of product with a better Nutri-Score (calculated by SmartNutri)';

  @override
  String alternativesSugars(String value) {
    return 'Sugars: $value g per 100 g/ml';
  }

  @override
  String get alternativesTitle => 'Healthier options';

  @override
  String get appName => 'SmartNutri AI';

  @override
  String get attributionOff => 'Data from Open Food Facts (ODbL)';

  @override
  String get attributionSmartnutriRecipe =>
      'Recipe by SmartNutri from USDA FoodData Central ingredients. Pending dietitian review.';

  @override
  String get attributionUsdaFdc =>
      'Nutrition data: USDA FoodData Central (public domain)';

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
  String get authOr => 'or';

  @override
  String get authPhone => 'Continue with phone';

  @override
  String get authPhoneLabel => 'Phone number (with country code)';

  @override
  String get authSendCode => 'Send code';

  @override
  String get authSignOut => 'Sign out';

  @override
  String get authSubtitle => 'Sign in to check packaged foods for your family.';

  @override
  String get authTagline =>
      'Know if a packaged food suits each person in your family.';

  @override
  String get authTitle => 'Sign in';

  @override
  String get authVerify => 'Verify';

  @override
  String get categorySupplement => 'Supplement';

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
  String get claimProteinAmount => 'Protein amount';

  @override
  String claimReasonAddedSugarIngredient(String ingredients) {
    return 'The ingredients include added sugar: $ingredients.';
  }

  @override
  String get claimReasonBasisUnknown =>
      'The claim doesn\'t clearly say per 100 g or per serving, so it can\'t be checked against the table.';

  @override
  String claimReasonBelowClaimed(String basis, String claimed, String value) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'per serving',
      'other': 'per 100 g',
    });
    return 'The nutrition table shows $value g protein $_temp0, below the $claimed g claimed.';
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
  String claimReasonOtherProteinSource(String ingredients) {
    return 'The ingredients include another protein source: $ingredients.';
  }

  @override
  String claimReasonRefinedSugarIngredient(String ingredients) {
    return 'The ingredients include refined sugar: $ingredients.';
  }

  @override
  String get claimReasonWheyNotListed =>
      'Whey is not listed in the ingredients.';

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
  String get claimWheyOnly => '100% whey';

  @override
  String get claimWheyProtein => 'Whey protein';

  @override
  String get commonCancel => 'Cancel';

  @override
  String get commonClose => 'Close';

  @override
  String get commonComingSoon => 'Coming soon';

  @override
  String get commonDisclaimer => 'Information, not medical advice.';

  @override
  String get commonErrorTitle => 'Something went wrong';

  @override
  String get commonGoHome => 'Go to the home page';

  @override
  String get commonLoading => 'Loading…';

  @override
  String get commonNotFoundBody =>
      'The page you\'re looking for doesn\'t exist or has moved.';

  @override
  String get commonOpenSettings => 'Open settings';

  @override
  String get commonRetry => 'Try again';

  @override
  String get commonSkipToContent => 'Skip to content';

  @override
  String get compareBetterA => 'The first product is better here';

  @override
  String get compareBetterB => 'The second product is better here';

  @override
  String get compareBetterChip => 'Better';

  @override
  String get compareBetterSame => 'About the same';

  @override
  String get compareBetterUnknown => 'Cannot compare: missing on a label';

  @override
  String get comparePickSecond => 'Choose a product to compare with';

  @override
  String get compareRowEnergyKcal => 'Calories (per 100 g/ml)';

  @override
  String get compareRowFiberG => 'Fibre (per 100 g/ml)';

  @override
  String get compareRowGrade => 'Nutri-Score (calculated by SmartNutri)';

  @override
  String get compareRowProteinG => 'Protein (per 100 g/ml)';

  @override
  String get compareRowSaltG => 'Salt (per 100 g/ml)';

  @override
  String get compareRowSatFatG => 'Saturated fat (per 100 g/ml)';

  @override
  String get compareRowSugarsG => 'Sugars (per 100 g/ml)';

  @override
  String get compareTitle => 'Compare';

  @override
  String get conditionBuildMuscle => 'Build muscle';

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
  String get confirmCategoryOptionFat => 'Oil, fat, nuts or seeds';

  @override
  String get confirmCategoryOptionGeneral => 'Food';

  @override
  String get confirmCategoryOptionSupplement =>
      'Supplement (protein powder, whey, health supplement)';

  @override
  String get confirmCategoryOptionWater => 'Packaged water';

  @override
  String get confirmCategorySuggestionSupplement =>
      'The ingredients or the protein amount suggest this may be a supplement (protein powder or whey). If it is, pick Supplement as the type.';

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
  String get confirmSectionAllergens => 'Allergens';

  @override
  String get confirmSectionNutrition => 'Nutrition table';

  @override
  String get confirmSectionPack => 'Claims and marks on the pack';

  @override
  String get confirmSectionProduct => 'Product';

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
  String get consentAgree => 'I agree';

  @override
  String get consentAiOptional =>
      'Optional. Without it you still get every result, just no AI explanation.';

  @override
  String get consentAiProcessingBody =>
      'Allow SmartNutri to send a summary of each result, without names, to an AI service processed in India, to write a short explanation. The AI never decides a result.';

  @override
  String get consentAiProcessingTitle => 'AI explanations';

  @override
  String get consentDecline => 'Not now';

  @override
  String get consentGranted => 'Agreed';

  @override
  String get consentHealthDataBody =>
      'SmartNutri uses the allergies, health conditions, goal, height and weight you enter to check products for each family member. This is information, not medical advice. You can withdraw this consent at any time.';

  @override
  String get consentHealthDataTitle => 'Health data';

  @override
  String get consentNeedsUpdate => 'Updated, please review';

  @override
  String get consentNotGranted => 'Not agreed';

  @override
  String get consentPromptBody =>
      'To continue, please agree to the following. You can withdraw at any time from your profile.';

  @override
  String get consentPromptTitle => 'Your agreement is needed';

  @override
  String get consentRequiredNote =>
      'Needed to save allergies, health conditions, a goal, height or weight.';

  @override
  String get consentRequiredToContinue =>
      'Please review and agree to continue.';

  @override
  String get consentReviewAgree => 'Review and agree';

  @override
  String get consentTermsBody =>
      'I agree to the SmartNutri terms of use and privacy policy.';

  @override
  String get consentTermsStepBody =>
      'Please read our terms of use and privacy notice. You need to agree to them to check and scan products.';

  @override
  String get consentTermsStepLeaveNote =>
      'Don\'t want to agree? You can sign out, or delete your account from your profile.';

  @override
  String get consentTermsStepReadPrivacy => 'Privacy notice';

  @override
  String get consentTermsStepReadTerms => 'Terms of use';

  @override
  String get consentTermsStepTitle => 'Before you start';

  @override
  String get consentTermsStepUpdatedBody =>
      'Our terms of use or privacy notice have changed. Please read them and agree again to keep checking and scanning products.';

  @override
  String get consentTermsStepUpdatedTitle => 'We\'ve updated our terms';

  @override
  String get consentTermsTitle => 'Terms of use';

  @override
  String get consentTermsWithdrawConfirm =>
      'If you withdraw, you can\'t check or scan products until you agree again. Your saved data stays until you delete your account.';

  @override
  String get consentUpdateNote =>
      'We\'ve updated this text. Please read it and agree again.';

  @override
  String get consentUpdatesBanner =>
      'We\'ve updated some consent texts. Please review them.';

  @override
  String get consentWithdraw => 'Withdraw consent';

  @override
  String get customFoodBarcode => 'Barcode (optional)';

  @override
  String get customFoodBasisG => 'Measured in grams';

  @override
  String get customFoodBasisMl => 'Measured in millilitres';

  @override
  String get customFoodBrand => 'Brand (optional)';

  @override
  String get customFoodDelete => 'Delete food';

  @override
  String get customFoodDeleteConfirm =>
      'Delete this food? Meals you already logged keep their values.';

  @override
  String get customFoodDensity => 'Grams in 1 ml (optional)';

  @override
  String get customFoodDensityHint =>
      'Needed to turn a katori, cup or glass into grams. Leave blank if you don\'t know it.';

  @override
  String get customFoodFieldSalt => 'Salt (g)';

  @override
  String get customFoodFieldSatFat => 'Saturated fat (g)';

  @override
  String get customFoodFieldSodium => 'Sodium (mg)';

  @override
  String get customFoodFieldSugars => 'Sugars (g)';

  @override
  String get customFoodHistoryKept => 'Meals you already logged are unchanged.';

  @override
  String get customFoodName => 'Name';

  @override
  String get customFoodPortions => 'Your own measures';

  @override
  String get customFoodSave => 'Save food';

  @override
  String get customFoodSaved => 'Food saved';

  @override
  String get customFoodServingSize => 'Serving size';

  @override
  String get customFoodTitle => 'My food';

  @override
  String get diaryAdd => 'Add food';

  @override
  String diaryAddToSlot(String slot) {
    return 'Add to $slot';
  }

  @override
  String get diaryConsumed => 'Eaten';

  @override
  String diaryCopied(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '# items copied',
      one: '# item copied',
    );
    return '$_temp0';
  }

  @override
  String get diaryCopyDay => 'Copy a day';

  @override
  String get diaryCopyMeal => 'Copy this meal';

  @override
  String get diaryCopyPickDay => 'Pick a day';

  @override
  String get diaryCopyPickMeal => 'Pick a meal';

  @override
  String get diaryCopyTo => 'Copy to…';

  @override
  String get diaryCopyYesterday => 'Copy yesterday';

  @override
  String get diaryDelete => 'Remove';

  @override
  String get diaryDeleteConfirm => 'Remove this item from your diary?';

  @override
  String get diaryDisclaimer =>
      'Information, not medical advice. Daily guides are estimates and are pending clinician review.';

  @override
  String get diaryEdit => 'Edit';

  @override
  String get diaryEmptyDay => 'Nothing logged yet.';

  @override
  String get diaryEyeHide => 'Hide numbers';

  @override
  String get diaryEyeShow => 'Show numbers';

  @override
  String diaryGramsLine(String grams) {
    return '$grams g';
  }

  @override
  String get diaryHiddenNumbers =>
      'Numbers are hidden. You can change this in settings.';

  @override
  String get diaryIncomplete =>
      'Some items don\'t show this value, so the real total may be higher.';

  @override
  String diaryLeft(String value) {
    return '$value left';
  }

  @override
  String get diaryMarkPartial => 'Mark as partly logged';

  @override
  String get diaryMove => 'Move to another meal';

  @override
  String get diaryNextDay => 'Next day';

  @override
  String get diaryNoGuide => 'Set up your daily guide, or just log food.';

  @override
  String diaryOfTarget(String eaten, String target) {
    return '$eaten of $target';
  }

  @override
  String diaryOver(String value) {
    return '$value over';
  }

  @override
  String get diaryPartialBadge => 'Partly logged';

  @override
  String get diaryPartialNote =>
      'Partly logged days are left out of weekly averages.';

  @override
  String get diaryPickDate => 'Pick a date';

  @override
  String diaryPortionLine(String grams, String quantity, String unit) {
    return '$quantity $unit · $grams g';
  }

  @override
  String diaryPortionLineMl(String amount, String quantity, String unit) {
    return '$quantity $unit · $amount ml';
  }

  @override
  String get diaryPrevDay => 'Previous day';

  @override
  String get diaryQuickAddCarbs => 'Carbs (g)';

  @override
  String get diaryQuickAddEnergy => 'Calories';

  @override
  String get diaryQuickAddFat => 'Fat (g)';

  @override
  String get diaryQuickAddFibre => 'Fibre (g)';

  @override
  String get diaryQuickAddName => 'Quick add';

  @override
  String get diaryQuickAddNameLabel => 'Name (optional)';

  @override
  String get diaryQuickAddProtein => 'Protein (g)';

  @override
  String get diaryQuickAddTitle => 'Quick add';

  @override
  String get diaryQuickBadge => 'Entered by you';

  @override
  String get diaryRemaining => 'Remaining';

  @override
  String diaryServingsLine(String grams, num servings) {
    String _temp0 = intl.Intl.pluralLogic(
      servings,
      locale: localeName,
      other: '# servings',
      one: '# serving',
    );
    return '$_temp0 · $grams g';
  }

  @override
  String get diaryShareWeek => 'Share this week';

  @override
  String get diarySlotBreakfast => 'Breakfast';

  @override
  String get diarySlotDinner => 'Dinner';

  @override
  String get diarySlotLunch => 'Lunch';

  @override
  String get diarySlotSnack => 'Snacks';

  @override
  String get diarySlotsAdd => 'Add a meal';

  @override
  String get diarySlotsDuplicate => 'You already have a meal with this name.';

  @override
  String get diarySlotsLastActive => 'Keep at least one meal.';

  @override
  String diarySlotsLimit(String max) {
    return 'You can have up to $max meals.';
  }

  @override
  String get diarySlotsManage => 'Edit meals';

  @override
  String diarySlotsMoveDown(String title) {
    return 'Move $title down';
  }

  @override
  String diarySlotsMoveUp(String title) {
    return 'Move $title up';
  }

  @override
  String get diarySlotsNameHint =>
      'Names you type are kept exactly as you type them.';

  @override
  String get diarySlotsPickAgain =>
      'That meal was removed. Please pick another meal for this item.';

  @override
  String get diarySlotsRemove => 'Remove this meal';

  @override
  String get diarySlotsRemoveNote =>
      'Food you already logged here stays in your diary.';

  @override
  String get diarySlotsRemoved => 'Removed meal';

  @override
  String get diarySlotsRemovedBadge => 'Removed meal';

  @override
  String get diarySlotsRename => 'Rename';

  @override
  String get diarySlotsReorder => 'Change order';

  @override
  String get diarySlotsResetName => 'Use the original name';

  @override
  String get diarySlotsTimeEnd => 'End time';

  @override
  String get diarySlotsTimeStart => 'Start time';

  @override
  String get diarySlotsTimeWindow => 'Usual time (optional)';

  @override
  String get diarySlotsTimeWindowHint =>
      'We use this to suggest a meal when you add food.';

  @override
  String get diaryTargetsConsent =>
      'To see your daily guide, allow SmartNutri to use your health details.';

  @override
  String get diaryTitle => 'Diary';

  @override
  String get diaryToday => 'Today';

  @override
  String get diaryViewDay => 'Day';

  @override
  String get diaryViewProgress => 'Progress';

  @override
  String get diaryWaitingSync => 'Waiting to sync';

  @override
  String diaryWeekAtLeast(String value) {
    return 'At least $value';
  }

  @override
  String diaryWeekAverage(num days) {
    String _temp0 = intl.Intl.pluralLogic(
      days,
      locale: localeName,
      other: '# logged days',
      one: '# logged day',
    );
    return 'Average over $_temp0';
  }

  @override
  String diaryWeekProteinDays(String days, String met) {
    return 'Protein guide reached on $met of $days logged days';
  }

  @override
  String get diaryWeekTitle => 'This week';

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
  String get errorAdaptiveNotEnabled => 'This option isn\'t available yet.';

  @override
  String get errorAiUnavailable =>
      'Voice answers are unavailable right now. Please try again later.';

  @override
  String get errorAudioTooLarge =>
      'That recording is too large. Please ask a shorter question.';

  @override
  String get errorAudioTooLong =>
      'That recording is longer than 30 seconds. Please ask a shorter question.';

  @override
  String get errorAudioUnsupported =>
      'We couldn\'t play that recording. Please try again.';

  @override
  String get errorAuthInvalid => 'Your session expired. Please sign in again.';

  @override
  String get errorAuthRequired => 'Please sign in.';

  @override
  String get errorBarcodeAlreadyUsed =>
      'You already have a food with this barcode.';

  @override
  String get errorBodyFatOutOfRange =>
      'Please enter a body fat percentage between 3 and 70.';

  @override
  String get errorConsentRequired =>
      'To save allergies, health conditions, a goal, height or weight, please agree to health data processing first.';

  @override
  String get errorConsentVersionMismatch =>
      'This consent text has been updated. Please reload and review it again.';

  @override
  String get errorCopySourceEmpty => 'There is nothing to copy there.';

  @override
  String get errorCopyTooMany =>
      'That is too many items to copy at once. Copy one meal at a time.';

  @override
  String get errorCustomFoodNotFound => 'We couldn\'t find that food of yours.';

  @override
  String get errorCustomFoodNutrientsEmpty =>
      'Add the energy, or at least one of protein, carbs or fat.';

  @override
  String get errorDateInFuture => 'That date hasn\'t happened yet.';

  @override
  String get errorDateRangeTooLong =>
      'Please choose a range of up to 400 days.';

  @override
  String get errorDateTooOld => 'You can only add to the last 30 days.';

  @override
  String get errorDeletionIncomplete =>
      'We could not finish deleting your account. Please try again; nothing you deleted will come back.';

  @override
  String get errorDiaryMemberNotEnabled =>
      'Daily guides are only available for your own profile for now.';

  @override
  String get errorEatenAtOutOfRange => 'Choose a time within the last 30 days.';

  @override
  String get errorExtractionFailed =>
      'We couldn\'t read this label. Try another photo or enter the details manually.';

  @override
  String get errorExtractionUnavailable =>
      'Label reading is unavailable right now. Try again later or enter the details manually.';

  @override
  String get errorFatPctOutOfRange =>
      'Please choose a share of calories from fat between 20% and 30%.';

  @override
  String get errorFavouriteLimit =>
      'You can keep up to 200 favourites. Remove one to add another.';

  @override
  String get errorFavouriteNotFound => 'We couldn\'t find that favourite.';

  @override
  String get errorFollowUpWithoutType =>
      'Please check your answers and try again.';

  @override
  String get errorFoodNotFound => 'We couldn\'t find that food.';

  @override
  String get errorFoodRetired =>
      'We no longer offer this dish, so it can\'t be added again. Your earlier entries are unchanged.';

  @override
  String get errorForbidden => 'You don\'t have access to this.';

  @override
  String get errorGoalNotAllowedMinor =>
      'Daily guides are for adults. You can still log food.';

  @override
  String get errorGoalNotAllowedUnderweight =>
      'We can help you keep a steady weight instead.';

  @override
  String get errorGoalSettingsNotFound => 'Set up your daily guide first.';

  @override
  String get errorHttpError => 'Something went wrong. Please try again.';

  @override
  String get errorImageQualityLow =>
      'This photo is hard to read. Please take it again.';

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
  String get errorMealNotFound => 'That food log wasn\'t found.';

  @override
  String get errorMealSlotArchived =>
      'That meal has been removed. Pick another meal.';

  @override
  String get errorMealSlotLabelDuplicate =>
      'You already have a meal with this name.';

  @override
  String get errorMealSlotLastActive => 'You need at least one meal.';

  @override
  String get errorMealSlotLimitReached =>
      'You can have at most 6 active meals. Remove one first.';

  @override
  String get errorMealSlotNotFound => 'We couldn\'t find that meal.';

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
  String get errorPayloadTooLarge =>
      'That request is too large. Please try again with less.';

  @override
  String get errorPhoneOtpDisabled =>
      'Phone sign-in is not available yet. Please sign in with email or Google.';

  @override
  String get errorPortionRequired =>
      'Choose how much was eaten: servings or grams.';

  @override
  String get errorPrimaryMember => 'Your own profile can\'t be removed.';

  @override
  String get errorProductExists => 'This product is already saved.';

  @override
  String get errorProductNotFound => 'We couldn\'t find this product yet.';

  @override
  String get errorQuantityOutOfRange =>
      'That amount is too large or too small. Check the number and try again.';

  @override
  String get errorQuickAddEnergyRequired => 'Enter the calories to add this.';

  @override
  String get errorRateLimited => 'Too many requests. Please wait a moment.';

  @override
  String get errorRateLimitedScans =>
      'You\'ve reached today\'s label-scan limit.';

  @override
  String get errorRateLimitedVoice =>
      'You\'ve reached today\'s voice-question limit.';

  @override
  String get errorRateNotAllowed =>
      'That pace isn\'t available. Please pick one of the options shown.';

  @override
  String get errorRecipeIngredientLimit =>
      'A recipe can have 1 to 50 ingredients.';

  @override
  String get errorRecipeNotFound => 'We couldn\'t find that recipe.';

  @override
  String get errorRecipeWeightInvalid =>
      'The recipe weight doesn\'t look right. Check the cooked weight.';

  @override
  String get errorScanImageNotFound =>
      'We couldn\'t find that photo. Please take or upload it again.';

  @override
  String get errorScanNotFound =>
      'We couldn\'t find that label scan. Please scan the label again.';

  @override
  String get errorSearchQueryTooShort => 'Type at least 3 letters to search.';

  @override
  String get errorServingSizeUnknown =>
      'This pack doesn\'t show a serving size. Enter the amount in grams.';

  @override
  String get errorStorageUnavailable =>
      'We couldn\'t handle the photo right now. Please try again in a moment.';

  @override
  String get errorTargetWeightTooLow => 'Please choose a higher target weight.';

  @override
  String get errorTimezoneInvalid => 'That time zone isn\'t recognised.';

  @override
  String get errorUnauthorized => 'Please sign in.';

  @override
  String get errorUnitGramsUnknown =>
      'We don\'t know the grams for this measure yet. Enter grams, or set your own value.';

  @override
  String get errorUnitNotSupported =>
      'That measure isn\'t available here. Choose another.';

  @override
  String get errorUnsupportedImage => 'Please use a JPEG, PNG or WebP photo.';

  @override
  String get errorUserTypeNotSelected =>
      'Pick one of the options you chose for yourself.';

  @override
  String get errorUserTypesNotFound =>
      'Tell us what brings you to SmartNutri first.';

  @override
  String get errorValidationError => 'Please check the highlighted fields.';

  @override
  String get errorVoiceNotUnderstood =>
      'We couldn\'t hear a question. Please hold the button and speak clearly.';

  @override
  String get errorWeightNeedsConfirm =>
      'This weight is quite different from your last one. Please confirm it.';

  @override
  String get errorWeightNotFound => 'We couldn\'t find that weigh-in.';

  @override
  String get errorWeightOutOfRange => 'Enter a weight between 2 and 300 kg.';

  @override
  String get explanationAiNote =>
      'Written by AI from the results above. It never changes a result.';

  @override
  String get explanationFallbackTip1 =>
      'Compare the labels of similar products and choose the one with less sugar and salt.';

  @override
  String get explanationFallbackTip2 =>
      'Check the serving size on the pack: the label values are per 100 g or 100 ml.';

  @override
  String get explanationFallbackTip3 =>
      'If you have a health condition, ask your doctor or a dietitian before making changes.';

  @override
  String get explanationSourceFallbackNote =>
      'The AI explanation isn\'t available right now, so this summary comes from our rules.';

  @override
  String get explanationTipsTitle => 'Tips';

  @override
  String get explanationTitle => 'Why this result';

  @override
  String get familyBody =>
      'Add each family member with their age, allergies and diet, so every result is about them.';

  @override
  String get familyComingSoonBody =>
      'Add each person\'s age, allergies and diet to get a result for each of them.';

  @override
  String get familyComingSoonTitle => 'Family profiles are coming soon';

  @override
  String get familyTitle => 'Family';

  @override
  String get favouritesAdd => 'Add to favourites';

  @override
  String get favouritesAdded => 'Added to favourites';

  @override
  String get favouritesEmpty => 'No favourites yet';

  @override
  String get favouritesLimit => 'You can keep up to 200 favourites.';

  @override
  String get favouritesLogAgain => 'Log again';

  @override
  String favouritesMealItems(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '# items',
      one: '# item',
    );
    return '$_temp0';
  }

  @override
  String get favouritesMealName => 'Meal name';

  @override
  String get favouritesMealNameHint =>
      'Names you type are kept exactly as you type them.';

  @override
  String get favouritesRemove => 'Remove from favourites';

  @override
  String get favouritesSaveMeal => 'Save as favourite meal';

  @override
  String get foodsBlankIsUnknown =>
      'Leave blank if you don\'t know. Blank is never counted as 0.';

  @override
  String get foodsDishIngredients => 'Made with';

  @override
  String get foodsFavourites => 'Favourites';

  @override
  String get foodsGroupIndian => 'Indian foods';

  @override
  String get foodsGroupMine => 'My foods and recipes';

  @override
  String get foodsGroupPackaged => 'Packaged products';

  @override
  String get foodsKindCustomFood => 'My food';

  @override
  String get foodsKindDish => 'Dish';

  @override
  String get foodsKindFood => 'Food';

  @override
  String get foodsKindProduct => 'Product';

  @override
  String get foodsKindRecipe => 'Recipe';

  @override
  String get foodsLoadMore => 'Load more';

  @override
  String get foodsMyFoods => 'My foods and recipes';

  @override
  String get foodsNewFood => 'New food';

  @override
  String get foodsNewRecipe => 'New recipe';

  @override
  String get foodsNoResults =>
      'No foods found. Try another word, or use quick add.';

  @override
  String get foodsNotKnown => 'Not known';

  @override
  String get foodsPartialResults => 'Some results couldn\'t load. Try again.';

  @override
  String get foodsPortionQuantity => 'Amount';

  @override
  String get foodsPortionSave => 'Add';

  @override
  String get foodsPortionTitle => 'How much?';

  @override
  String get foodsPreviewNote =>
      'Estimate. The saved values come from SmartNutri.';

  @override
  String get foodsQuickAdd => 'Quick add';

  @override
  String get foodsRecent => 'Recent';

  @override
  String get foodsReviewPending =>
      'Household measures and Indian dishes are pending dietitian review.';

  @override
  String get foodsSearchPlaceholder => 'Search foods, dishes or brands';

  @override
  String get foodsValuesPer100g => 'Values per 100 g';

  @override
  String get foodsValuesPer100ml => 'Values per 100 ml';

  @override
  String get foodsValuesPerServing => 'Values per serving';

  @override
  String get footerLinksLabel => 'About SmartNutri';

  @override
  String get footerTagline => 'Packaged-food information for Indian families.';

  @override
  String get goalBuildMuscle => 'Build muscle';

  @override
  String get goalHealthyEating => 'Eat healthier';

  @override
  String get goalWeightGain => 'Gain weight';

  @override
  String get goalWeightLoss => 'Lose weight';

  @override
  String get goodbyeAction => 'Back to sign in';

  @override
  String get goodbyeBody =>
      'Your account and its data have been deleted, and you have been signed out. Thank you for trying SmartNutri.';

  @override
  String get goodbyeMetaTitle => 'Account deleted';

  @override
  String get goodbyeTitle => 'Your account has been deleted';

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
  String get historyBody =>
      'Products you check will be listed here, so you can find them again.';

  @override
  String get historyComingSoonBody =>
      'You\'ll see every product you\'ve checked here.';

  @override
  String get historyComingSoonTitle => 'Your history is coming soon';

  @override
  String get historyEmpty => 'Nothing logged yet.';

  @override
  String historyItemAmount(String grams) {
    return '$grams g';
  }

  @override
  String get historyLoggedTitle => 'What was eaten';

  @override
  String get historyMember => 'Family member';

  @override
  String get historyNextDay => 'Next day';

  @override
  String get historyPreviousDay => 'Previous day';

  @override
  String get historyRemove => 'Remove';

  @override
  String get historyRemoveConfirm => 'Remove this item from the log?';

  @override
  String get historyThisWeek => 'This week';

  @override
  String get historyTitle => 'History';

  @override
  String get historyToday => 'Today';

  @override
  String get homeCardsAllergyCheckAddCta => 'Add allergies';

  @override
  String homeCardsAllergyCheckMemberLine(String allergens, String name) {
    return '$name: $allergens';
  }

  @override
  String get homeCardsAllergyCheckNone => 'No allergies added yet.';

  @override
  String get homeCardsAllergyCheckTitle => 'Allergy check';

  @override
  String get homeCardsAllergyCheckUnknownNote =>
      'Unknown means we couldn\'t check, so it is never marked safe.';

  @override
  String get homeCardsClaimsTipBody =>
      'Sugar-free? We check claims against the label.';

  @override
  String get homeCardsClaimsTipTitle => 'Claims on the pack';

  @override
  String get homeCardsCustomAlertsSetupBody =>
      'Choose ingredients you want us to point out on labels.';

  @override
  String get homeCardsCustomAlertsSetupCta => 'Set up alerts';

  @override
  String get homeCardsCustomAlertsSetupTitle => 'Ingredient alerts';

  @override
  String get homeCardsFamilyStripAdd => 'Add member';

  @override
  String get homeCardsFamilyStripTitle => 'Your family';

  @override
  String get homeCardsNotCoveredBody =>
      'Not covered yet: thyroid, cholesterol, kidney disease, pregnancy.';

  @override
  String get homeCardsNotCoveredTitle => 'Not covered yet';

  @override
  String get homeCardsProteinClaimsTipBody =>
      'We check protein claims against the nutrition table.';

  @override
  String get homeCardsProteinClaimsTipTitle => 'Protein claims';

  @override
  String get homeCardsProteinSwapsCta => 'Find higher-protein options';

  @override
  String get homeCardsProteinSwapsTitle => 'Higher-protein options';

  @override
  String get homeCardsRecentScansTitle => 'Recent scans';

  @override
  String get homeCardsTodayProteinTitle => 'Today: protein';

  @override
  String get homeCardsTodaySugarSaltTitle => 'Today: sugar and salt';

  @override
  String get homeCardsTodayTargetsTitle => 'Today';

  @override
  String get homeCardsUnknownExplainerBody =>
      'When a label is missing ingredients or is hard to read, we can\'t check it. We never show that as safe.';

  @override
  String get homeCardsUnknownExplainerTitle => 'Why \"unknown\" is not safe';

  @override
  String homeCardsWeeklyFamilyBody(String count) {
    return '$count items logged for your family in the last 7 days';
  }

  @override
  String get homeCardsWeeklyFamilyTitle => 'This week';

  @override
  String get homeLabelBody =>
      'No barcode, or a product we don\'t know yet? Photograph the label.';

  @override
  String get homeLabelTitle => 'Photograph a label';

  @override
  String get homeManualBody =>
      'Type the nutrition facts from the pack yourself.';

  @override
  String get homeRecentEmptyBody => 'Products you check will show up here.';

  @override
  String get homeRecentEmptyTitle => 'No scans yet';

  @override
  String get homeRecentTitle => 'Recent scans';

  @override
  String get homeScanBody =>
      'Use your camera, or type the number under the barcode.';

  @override
  String get homeScanCta => 'Scan a product';

  @override
  String get homeSubtitle => 'What would you like to check today?';

  @override
  String homeWelcome(String name) {
    return 'Hello, $name';
  }

  @override
  String get homeWelcomeNoName => 'Hello';

  @override
  String get imageQualityBlur =>
      'The photo is blurred. Hold the phone steady and tap the label to focus.';

  @override
  String get imageQualityGlare =>
      'The photo is washed out by light. Turn off the flash or tilt the pack away from the light.';

  @override
  String get imageQualityHintGeneric =>
      'Take the photo in good light with the whole label in the frame.';

  @override
  String get imageQualityTitle => 'Please retake the photo';

  @override
  String get imageQualityTooSmall =>
      'The photo is too small. Take it closer, with the label filling the frame.';

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
  String get landingCtaStart => 'Get started';

  @override
  String get landingEyebrow => 'For Indian families';

  @override
  String get landingHeroBody =>
      'Scan a barcode or photograph the label. SmartNutri reads it, checks it against each person\'s age, allergies and diet, and tells you why.';

  @override
  String get landingHeroTitle =>
      'Know if a packaged food is right for each member of your family';

  @override
  String get landingHowTitle => 'How it works';

  @override
  String get landingMetaDescription =>
      'Scan a packaged food and see whether it suits each member of your family, with the reasons. Information, not medical advice.';

  @override
  String get landingMetaTitle =>
      'SmartNutri AI – is this packaged food right for your family?';

  @override
  String get landingStep1Body =>
      'Scan the barcode, or take a photo of the nutrition label on the pack.';

  @override
  String get landingStep1Title => 'Scan or snap';

  @override
  String get landingStep2Body =>
      'You confirm the label details before anything is saved.';

  @override
  String get landingStep2Title => 'Check what we read';

  @override
  String get landingStep3Body =>
      'Get a simple result for each family member, with the reasons in plain words.';

  @override
  String get landingStep3Title => 'See who it suits';

  @override
  String get languageEn => 'English';

  @override
  String get languageHi => 'हिन्दी';

  @override
  String get languageLabel => 'Language';

  @override
  String get languageMr => 'मराठी';

  @override
  String get legalDraftNotice =>
      'Draft: this document is being reviewed by a lawyer before launch.';

  @override
  String get legalEnglishOnly =>
      'This document is available in English only for now.';

  @override
  String get legalPrivacyDescription =>
      'How SmartNutri AI collects, uses and protects your family\'s data under India\'s DPDP Act, 2023.';

  @override
  String get legalPrivacyTitle => 'Privacy notice';

  @override
  String get legalTermsDescription =>
      'The terms for using SmartNutri AI. Information, not medical advice.';

  @override
  String get legalTermsTitle => 'Terms of use';

  @override
  String legalVersion(String version) {
    return 'Version $version';
  }

  @override
  String get mealsLogAmountGrams => 'Amount in grams';

  @override
  String mealsLogAmountInvalid(String max) {
    return 'Enter an amount more than 0 and up to $max.';
  }

  @override
  String get mealsLogAmountServings => 'Number of servings';

  @override
  String get mealsLogCta => 'I ate this';

  @override
  String mealsLogCtaFor(String name) {
    return 'I ate this, $name';
  }

  @override
  String get mealsLogEatenAt => 'When';

  @override
  String get mealsLogGrams => 'Grams';

  @override
  String get mealsLogMember => 'Who ate it?';

  @override
  String get mealsLogNow => 'Now';

  @override
  String get mealsLogPortion => 'How much was eaten?';

  @override
  String get mealsLogSave => 'Save';

  @override
  String mealsLogSaved(String who) {
    return 'Logged for $who';
  }

  @override
  String get mealsLogSavedYou => 'Logged for you';

  @override
  String mealsLogServingSize(String grams) {
    return '1 serving = $grams g';
  }

  @override
  String get mealsLogServings => 'Servings';

  @override
  String get mealsLogTitle => 'Log what was eaten';

  @override
  String get mealsLogUndo => 'Undo';

  @override
  String get mealsLogUndone => 'Removed from the log';

  @override
  String get mealsOnlineOnly =>
      'On the web, logging needs an internet connection. Items are not saved offline.';

  @override
  String get mealsQueuedOffline =>
      'Saved on this phone. It will be added to the log when you are back online.';

  @override
  String get mealsSyncFailed =>
      'Some items could not be added to the log. Please log them again.';

  @override
  String get mealsSyncing => 'Syncing logged items…';

  @override
  String get membersAdd => 'Add a family member';

  @override
  String membersBorn(String year) {
    return 'Born $year';
  }

  @override
  String get membersConsentWithdrawnNotice =>
      'Health data consent is off. Saved allergies and conditions are still used to check products, but new ones can\'t be saved until you agree again.';

  @override
  String get membersEdit => 'Edit';

  @override
  String get membersFormAllergenAdd => 'Add';

  @override
  String get membersFormAllergenInvalid =>
      'An allergy must be 2 to 40 characters.';

  @override
  String get membersFormAllergenLength => 'Type 2 to 40 characters.';

  @override
  String get membersFormAllergenLimit => 'You can add up to 20 allergies.';

  @override
  String get membersFormAllergenOther => 'Other allergy';

  @override
  String get membersFormAllergens => 'Allergies';

  @override
  String get membersFormAllergensHelp =>
      'Pick from the list, or type your own.';

  @override
  String get membersFormBirthYear => 'Year of birth';

  @override
  String get membersFormBirthYearHelp =>
      'Used for the checks for children and babies under 2.';

  @override
  String membersFormBirthYearInvalid(String year) {
    return 'Enter a year from 1900 to $year.';
  }

  @override
  String get membersFormCancel => 'Cancel';

  @override
  String membersFormClearAllergiesConfirm(String name) {
    return 'Remove every allergy for $name? Products with these allergens will no longer be flagged for them.';
  }

  @override
  String get membersFormConditions => 'Health conditions';

  @override
  String get membersFormCustomAlerts => 'Ingredient alerts';

  @override
  String get membersFormCustomAlertsHelp =>
      'We point these out when we find them on the label.';

  @override
  String get membersFormDiet => 'Diet';

  @override
  String get membersFormGoal => 'Goal (optional)';

  @override
  String get membersFormHealthFieldsNote =>
      'Allergies, health conditions, goal, height and weight are saved only with your consent to health data processing.';

  @override
  String get membersFormHeightCm => 'Height (cm, optional)';

  @override
  String get membersFormHeightInvalid =>
      'Enter a height between 30 and 250 cm, or leave it blank.';

  @override
  String get membersFormName => 'Name';

  @override
  String get membersFormNameInvalid => 'Enter a name of up to 40 characters.';

  @override
  String get membersFormNameRequired => 'Enter a name.';

  @override
  String get membersFormNotSet => 'Not set';

  @override
  String membersFormNumberRange(String max, String min) {
    return 'Enter a number from $min to $max.';
  }

  @override
  String get membersFormRelation => 'Relation';

  @override
  String get membersFormRelationRequired => 'Choose a relation.';

  @override
  String membersFormRemoveAllergy(String allergen) {
    return 'Remove $allergen';
  }

  @override
  String membersFormRemoveAllergyConfirm(String allergen, String name) {
    return 'Remove $allergen from the allergies for $name? Products with it will no longer be flagged for them.';
  }

  @override
  String get membersFormSave => 'Save';

  @override
  String get membersFormSex => 'Sex (optional)';

  @override
  String get membersFormWeightInvalid =>
      'Enter a weight between 2 and 300 kg, or leave it blank.';

  @override
  String get membersFormWeightKg => 'Weight (kg, optional)';

  @override
  String get membersGoalBuildMuscle => 'Build muscle';

  @override
  String get membersGoalBuildMuscleAdultsOnly =>
      'Build muscle is a goal for adults (18 and over). Pick another goal for this member.';

  @override
  String get membersGoalHealthyEating => 'Eat better';

  @override
  String get membersGoalWeightGain => 'Gain weight';

  @override
  String get membersGoalWeightLoss => 'Lose weight';

  @override
  String get membersLimitReached =>
      'You have 10 family members, the most you can add.';

  @override
  String get membersRelationChild => 'Child';

  @override
  String get membersRelationOther => 'Other';

  @override
  String get membersRelationParent => 'Parent';

  @override
  String get membersRelationSelf => 'You';

  @override
  String get membersRelationSpouse => 'Spouse';

  @override
  String get membersRemove => 'Remove';

  @override
  String membersRemoveConfirm(String name) {
    return 'Remove $name from your family?';
  }

  @override
  String get membersSaved => 'Saved';

  @override
  String get membersSexFemale => 'Female';

  @override
  String get membersSexMale => 'Male';

  @override
  String get membersSexOther => 'Other';

  @override
  String get membersTitle => 'Family';

  @override
  String get membersYouBadge => 'You';

  @override
  String get methodologyBasedOn => 'Based on:';

  @override
  String get methodologyFoodDataBody =>
      'Packaged-food values come from the label. Generic foods come from USDA FoodData Central (U.S. Department of Agriculture, Agricultural Research Service. FoodData Central. fdc.nal.usda.gov), which is in the public domain. Katori sizes follow the ICMR-NIN Dietary Guidelines for Indians 2024 (Annexure I). Some cup-based conversions are derived from USDA cup weights and are marked approximate. Glass and other values are our own reference set, pending dietitian review. Where a value is not known, we leave it unknown and never guess. Indian dishes are calculated by SmartNutri from their ingredients and are pending dietitian review. Information, not medical advice.';

  @override
  String get methodologyFoodDataTitle => 'Food data and household measures';

  @override
  String get methodologyIntro =>
      'SmartNutri checks each packaged food against its label and each family member\'s profile using fixed rules. An AI only explains the result; it never decides it. This is information, not medical advice.';

  @override
  String get methodologyMetaDescription =>
      'How SmartNutri checks packaged food for each family member: the fixed rules, their thresholds and sources. Information, not medical advice.';

  @override
  String get methodologyPendingReview =>
      'These thresholds are working values, pending review by a clinician.';

  @override
  String get methodologySectionAllergensDescription =>
      'We look for each allergen\'s ingredient names and for the pack\'s allergen statements. If the ingredients can\'t be read, we say the label is unclear, never OK.';

  @override
  String get methodologySectionAllergensTitle => 'Allergens';

  @override
  String get methodologySectionBloodSugarDescription =>
      'For members managing blood sugar (diabetes, prediabetes or PCOS), we flag products with a lot of sugar, or a lot of carbohydrate per serving, and high salt or saturated fat.';

  @override
  String get methodologySectionBloodSugarTitle => 'Blood sugar';

  @override
  String get methodologySectionBuildMuscleDescription =>
      'For adult members (18 and over) who want to build muscle, we note products with good protein for their calories. This goal never adds a caution or an avoid, and it can\'t be set for members under 18. In the food log, adults with a weight see a daily protein guide based on body weight. If you have kidney disease, ask your doctor before eating more protein.';

  @override
  String get methodologySectionBuildMuscleTitle => 'Build muscle';

  @override
  String get methodologySectionChildDescription =>
      'For children, we compare the sugar in 100 g or one serving with a daily sugar limit for their age.';

  @override
  String get methodologySectionChildTitle => 'Children';

  @override
  String get methodologySectionClaimsDescription =>
      'We check claims such as \"sugar free\" or \"high protein\" against the label values and the FSSAI limits.';

  @override
  String get methodologySectionClaimsTitle => 'Front-of-pack claims';

  @override
  String get methodologySectionCustomAlertsDescription =>
      'Ingredients a member asked to be told about, such as palm oil or maida. These are preferences, so there is no source to cite.';

  @override
  String get methodologySectionCustomAlertsTitle => 'Your ingredient alerts';

  @override
  String get methodologySectionDailyLimitsDescription =>
      'In the food log, we add up the sugar and salt logged for each member in a day and compare the totals with a daily limit for their age. Protein is shown as progress towards a daily target. Labels give total sugar, not only added sugar, so this can warn more than needed.';

  @override
  String get methodologySectionDailyLimitsTitle => 'Daily limits';

  @override
  String get methodologySectionDietDescription =>
      'We look for ingredients that don\'t fit a member\'s diet (vegetarian, eggetarian, vegan or Jain) and check the green or brown mark on the pack.';

  @override
  String get methodologySectionDietTitle => 'Diet';

  @override
  String get methodologySectionEnergyTargetsDescription =>
      'Your daily guide is an estimate. We start from the Mifflin-St Jeor equation using age, sex, height and weight, multiply by an activity level, adjust gently for the chosen goal, and set protein, fat and carbs from the result. Safe minimums and pace limits always apply. Every value is pending clinician review. Information, not medical advice.';

  @override
  String get methodologySectionEnergyTargetsTitle => 'How we set daily guides';

  @override
  String get methodologySectionHighInDescription =>
      'A product is marked high in a nutrient when its amount per 100 g or 100 ml is at or above these limits.';

  @override
  String get methodologySectionHighInTitle =>
      'High in sugar, fat, saturated fat or salt';

  @override
  String get methodologySectionHypertensionDescription =>
      'For members with high blood pressure, we flag products with a lot of salt.';

  @override
  String get methodologySectionHypertensionTitle => 'Blood pressure';

  @override
  String get methodologySectionInfantDescription =>
      'For babies and toddlers, we flag added sugar, added salt, honey and caffeine, and high sugar or salt.';

  @override
  String get methodologySectionInfantTitle => 'Babies and toddlers';

  @override
  String get methodologySectionNutriscore2023Description =>
      'We calculate a Nutri-Score grade from the label, using the 2023 update of the method. It is calculated by SmartNutri; it is not an FSSAI rating.';

  @override
  String get methodologySectionNutriscore2023Title =>
      'Nutri-Score (calculated by SmartNutri)';

  @override
  String get methodologySectionSupplementsDescription =>
      'Protein powders, whey and other supplements get no Nutri-Score grade and are never suggested as alternatives. We still check allergens, diet, claims and each member\'s rules, and add a caution for children and teenagers (an avoid under 2). When a label lists whey or a protein isolate, or has 50 g or more protein per 100 g, the confirm screen asks whether it is a supplement, and such products are left out of protein-sorted results for members under 18.';

  @override
  String get methodologySectionSupplementsTitle => 'Supplements';

  @override
  String get methodologySectionWeightLossDescription =>
      'For members losing weight, we flag energy-dense products and low Nutri-Score grades, and for adults (18 and over) note products with good protein for their calories.';

  @override
  String get methodologySectionWeightLossTitle => 'Weight loss';

  @override
  String get methodologySourcesTitle => 'Sources';

  @override
  String get methodologyTitle => 'How we score';

  @override
  String get methodologyUnavailable =>
      'We couldn\'t load the scoring rules right now. Please try again in a moment.';

  @override
  String get methodologyUrlUnverified => 'Link not yet checked';

  @override
  String get methodologyValues => 'Rule values';

  @override
  String methodologyVersion(String version) {
    return 'Rules version $version';
  }

  @override
  String modesCurrent(String mode) {
    return 'Current mode: $mode';
  }

  @override
  String get modesMore => 'More';

  @override
  String get modesMoreTitle => 'More';

  @override
  String get modesNameAllergyDiet => 'Allergy or diet';

  @override
  String get modesNameEatBetter => 'Eating better';

  @override
  String get modesNameFamily => 'Family';

  @override
  String get modesNameGym => 'Gym and fitness';

  @override
  String get modesNameHealthCondition => 'Health condition';

  @override
  String get modesNameWeightLoss => 'Weight loss';

  @override
  String get modesSameChecks =>
      'Scanning, results and allergy checks are the same in every mode.';

  @override
  String modesSwitchTo(String mode) {
    return 'Switch to $mode';
  }

  @override
  String get modesSwitcherLabel => 'Mode';

  @override
  String get navCompare => 'Compare';

  @override
  String get navDiary => 'Diary';

  @override
  String get navFamily => 'Family';

  @override
  String get navHistory => 'History';

  @override
  String get navHome => 'Home';

  @override
  String get navHowWeScore => 'How we score';

  @override
  String get navLabel => 'Main navigation';

  @override
  String get navMore => 'More';

  @override
  String get navProfile => 'Profile';

  @override
  String get navProtein => 'Protein';

  @override
  String get navScan => 'Scan';

  @override
  String get navSearch => 'Search';

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
  String get nutrientServingSizeG => 'serving size';

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
  String get nutriscoreNotScoredSupplement =>
      'Nutri-Score is not calculated for supplements.';

  @override
  String get policyOpenFailed => 'Couldn\'t open the page. Please try again.';

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
  String get productNotFoundBody =>
      'Check the barcode number. You can also sign in and photograph the label to add this product.';

  @override
  String get productPublicCta => 'Check it for your family';

  @override
  String get profileBody =>
      'Your account, language and privacy settings will be here.';

  @override
  String get profileComingSoonBody =>
      'Language, privacy and account settings will appear here.';

  @override
  String get profileComingSoonTitle => 'Settings are coming soon';

  @override
  String get profileGiveConsent => 'Agree';

  @override
  String get profilePrivacyTitle => 'Privacy and consent';

  @override
  String get profileTitle => 'Profile';

  @override
  String get proteinComparePriceScoop => 'Price per scoop';

  @override
  String get proteinCompareProtein100kcal => 'Protein per 100 kcal';

  @override
  String get proteinCompareProteinServing => 'Protein per serving';

  @override
  String get proteinCompareSugar => 'Sugars';

  @override
  String proteinGuide(String per_kg, String target) {
    return 'Daily protein guide: $target g, based on $per_kg g per kg. Information, not medical advice.';
  }

  @override
  String proteinGuideAdjusted(String per_kg, String target) {
    return 'Daily protein guide: $target g, based on $per_kg g per kg of an adjusted weight. Information, not medical advice.';
  }

  @override
  String proteinGuideLean(String per_kg, String target) {
    return 'Daily protein guide: $target g, based on $per_kg g per kg of lean mass. Information, not medical advice.';
  }

  @override
  String get proteinKidneyNote =>
      'If you have kidney disease, ask your doctor before eating more protein.';

  @override
  String proteinLeftToday(String left) {
    return '$left g left today';
  }

  @override
  String get proteinNoTarget =>
      'No daily protein guide yet. Add weight and year of birth for an adult to see one.';

  @override
  String get proteinNotOnLabel => 'Not on the label';

  @override
  String get proteinPackSizeLabel => 'Pack size (g)';

  @override
  String get proteinPer100g => 'Protein per 100 g';

  @override
  String get proteinPer100kcal => 'Protein per 100 kcal';

  @override
  String get proteinPerServing => 'Protein per serving';

  @override
  String get proteinPriceLabel => 'Price of the pack';

  @override
  String get proteinPriceNote =>
      'The price you type is used on this screen only and is never saved.';

  @override
  String get proteinPricePerScoop => 'Price per scoop';

  @override
  String proteinProgress(String target, String total) {
    return '$total g of $target g';
  }

  @override
  String get proteinSortHigher => 'Higher protein';

  @override
  String get proteinSwapsEmpty =>
      'We did not find a higher-protein option of this kind.';

  @override
  String get proteinSwapsTitle => 'Higher-protein options';

  @override
  String get proteinTitle => 'Protein';

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
    return 'We can only search the label for the exact word \"$allergen\". Check the ingredients yourself.';
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
  String reasonCustomAlert(String alert, String ingredients) {
    return 'Contains $alert: $ingredients.';
  }

  @override
  String reasonCustomAlertUnknown(String alerts) {
    return 'These alerts couldn\'t be checked: $alerts.';
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
  String get reasonSupplementChild =>
      'This is a supplement, which is not recommended for children and teenagers. Check with your doctor first.';

  @override
  String get reasonSupplementInfant =>
      'This is a supplement, which is not recommended for children under 2.';

  @override
  String get reasonVariantCustomAlertFlagOnly =>
      'The product data says it contains sweeteners.';

  @override
  String reasonVariantDietViolationMarkOnly(String diet) {
    return 'The pack has the brown non-vegetarian mark, so this may not match the $diet diet.';
  }

  @override
  String reasonVariantNutrientMissingLowConfidence(String nutrient) {
    return 'We couldn\'t read $nutrient clearly on the label, so this check could not be done.';
  }

  @override
  String get recipesAddIngredient => 'Add ingredient';

  @override
  String get recipesCookedWeight => 'Cooked weight (g)';

  @override
  String get recipesCookedWeightTip =>
      'Weigh the pot after cooking for the best accuracy.';

  @override
  String get recipesDelete => 'Delete recipe';

  @override
  String get recipesDeleteConfirm =>
      'Delete this recipe? Meals you already logged keep their values.';

  @override
  String get recipesEmpty => 'No recipes yet';

  @override
  String get recipesIncomplete =>
      'Some ingredients don\'t show this value, so the real amount may be higher.';

  @override
  String get recipesIngredientUnavailable =>
      'This ingredient was deleted. Replace it to save the recipe.';

  @override
  String get recipesIngredients => 'Ingredients';

  @override
  String get recipesLogServing => 'Log a serving';

  @override
  String get recipesName => 'Recipe name';

  @override
  String get recipesPer100g => 'Per 100 g';

  @override
  String get recipesPerServing => 'Per serving';

  @override
  String get recipesSave => 'Save recipe';

  @override
  String get recipesSaved => 'Recipe saved';

  @override
  String get recipesServings => 'Number of servings';

  @override
  String get recipesTitle => 'Recipe';

  @override
  String get reportButton => 'Report a problem';

  @override
  String get reportCaffeine => 'Contains caffeine';

  @override
  String get reportNoteHint =>
      'Please don\'t include personal or health details.';

  @override
  String get reportNoteLabel => 'Tell us more (optional)';

  @override
  String get reportReasonLabel => 'What\'s wrong?';

  @override
  String get reportReasonOther => 'Something else';

  @override
  String get reportReasonWrongIngredients => 'The ingredients are wrong';

  @override
  String get reportReasonWrongProduct => 'This is a different product';

  @override
  String get reportReasonWrongValues => 'The nutrition values are wrong';

  @override
  String get reportSubmit => 'Send report';

  @override
  String get reportSweeteners => 'Contains sweeteners';

  @override
  String get reportThanks => 'Thanks. We\'ll review this product\'s data.';

  @override
  String get reportTitle => 'What\'s wrong with this product\'s data?';

  @override
  String get resultFamilyTitle => 'For your family';

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
  String get resultMembersTitle => 'For your family';

  @override
  String get resultNoIngredients => 'Ingredients not available';

  @override
  String get resultNotOnLabel => 'Not on the label';

  @override
  String get resultNutritionTitle => 'Nutrition per 100 g/ml';

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
  String get scanLabelHint => 'No barcode? Photograph the label instead.';

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
  String get scanSubtitle =>
      'Point your camera at the barcode, or type the number below.';

  @override
  String get scanTitle => 'Scan a barcode';

  @override
  String get searchHint =>
      'Find a product by name or brand, then open it or compare it.';

  @override
  String get searchNoResults => 'No products found.';

  @override
  String get searchOffDegraded => 'More results will be added later.';

  @override
  String get searchPlaceholder => 'Search by name or brand';

  @override
  String get searchSortLabel => 'Sort';

  @override
  String get searchSortRelevance => 'Best match';

  @override
  String get searchSourceOff => 'Open Food Facts';

  @override
  String get searchSourceOurs => 'SmartNutri';

  @override
  String get searchTitle => 'Search products';

  @override
  String get searchTooShort => 'Type at least 3 letters.';

  @override
  String get settingsAboutTitle => 'About SmartNutri';

  @override
  String get settingsAccountTitle => 'Account';

  @override
  String get settingsDeleteBody =>
      'This permanently deletes your account, your family profiles and health data, scans, food logs and label photos. Products you added stay in the shared catalogue without your name. This can\'t be undone.';

  @override
  String get settingsDeleteButton => 'Delete account';

  @override
  String get settingsDeleteConfirm => 'Delete permanently';

  @override
  String settingsDeleteConfirmLabel(String word) {
    return 'Type $word to confirm';
  }

  @override
  String get settingsDeleteConfirmWord => 'DELETE';

  @override
  String get settingsDeleteDialogTitle => 'Delete your account permanently?';

  @override
  String get settingsDeleteRetrying => 'Still deleting. Trying again…';

  @override
  String get settingsDeleteTitle => 'Delete account';

  @override
  String get settingsDeleting => 'Deleting your account…';

  @override
  String get settingsDiaryBodyFat => 'Body fat %';

  @override
  String get settingsDiaryMeals => 'Meals';

  @override
  String get settingsDiaryNumbersHideAll => 'Hide all numbers';

  @override
  String get settingsDiaryNumbersHideEnergy => 'Hide calories';

  @override
  String get settingsDiaryNumbersHideNote =>
      'You can still log food. Your guide keeps working in the background.';

  @override
  String get settingsDiaryNumbersShow => 'Show numbers';

  @override
  String get settingsDiaryNumbersTitle => 'Numbers';

  @override
  String get settingsDiaryReset => 'Reset daily guide';

  @override
  String get settingsDiaryResetConfirm =>
      'Reset your daily guide? Your food log stays.';

  @override
  String get settingsDiaryTitle => 'Diary and daily guide';

  @override
  String get settingsLanguageBody =>
      'Choose the language for SmartNutri on this device.';

  @override
  String get settingsLanguageSystem => 'Device language';

  @override
  String get shareButton => 'Share';

  @override
  String get shareCopied => 'Link copied';

  @override
  String get shareCopyLink => 'Copy link';

  @override
  String get shareInclude => 'Add a person\'s result (optional)';

  @override
  String shareLink(String url) {
    return 'Checked with SmartNutri: $url';
  }

  @override
  String get sharePreview => 'Message preview';

  @override
  String get sharePrivacyNote =>
      'Only the product and its grade are shared, plus the result of anyone you tick. Health details stay private.';

  @override
  String get shareRelationChild => 'Child';

  @override
  String get shareRelationOther => 'Family member';

  @override
  String get shareRelationParent => 'Parent';

  @override
  String get shareRelationSelf => 'Me';

  @override
  String get shareRelationSpouse => 'Spouse';

  @override
  String shareResultMember(String status, String who) {
    return '$who: $status';
  }

  @override
  String shareResultProductOnly(String grade, String product) {
    return '$product — Nutri-Score $grade (calculated by SmartNutri).';
  }

  @override
  String shareResultProductOnlyUngraded(String product) {
    return '$product — not enough label data for a Nutri-Score.';
  }

  @override
  String shareResultText(String grade, String members, String product) {
    return '$product — Nutri-Score $grade (calculated by SmartNutri). $members.';
  }

  @override
  String shareResultUngraded(String members, String product) {
    return '$product — not enough label data for a Nutri-Score. $members.';
  }

  @override
  String shareWeekly(String logged, String scans) {
    return 'Our week on SmartNutri — products checked: $scans, items logged: $logged.';
  }

  @override
  String get shareWeeklyButton => 'Share our week';

  @override
  String get shareWhatsapp => 'Share on WhatsApp';

  @override
  String get statusAvoid => 'Avoid';

  @override
  String get statusCaution => 'Caution';

  @override
  String get statusOk => 'OK';

  @override
  String get statusUnknown => 'Label unclear';

  @override
  String get summaryBandNear => 'Close to limit';

  @override
  String get summaryBandOk => 'Within limit';

  @override
  String get summaryBandOver => 'Over limit';

  @override
  String get summaryBandUnknown => 'Not enough data';

  @override
  String get summaryIncomplete =>
      'Some logged items do not show this value on the label, so the real total may be higher.';

  @override
  String get summaryKcalInfo =>
      'Calories are shown for information. There is no personal calorie target yet.';

  @override
  String summaryKcalTotal(String total) {
    return '$total kcal';
  }

  @override
  String get summaryLimitsNote => 'Limits pending clinician review.';

  @override
  String get summaryNoProteinTarget => 'No protein target for this member';

  @override
  String get summaryNothingLogged => 'Nothing logged on this day.';

  @override
  String get summaryNutrientEnergyKcal => 'Calories';

  @override
  String get summaryNutrientProteinG => 'Protein';

  @override
  String get summaryNutrientSaltG => 'Salt';

  @override
  String get summaryNutrientSugarsG => 'Sugars';

  @override
  String summaryProteinOfTarget(String target, String total) {
    return '$total g of a $target g target';
  }

  @override
  String get summarySugarNote =>
      'Labels show total sugars, including natural sugars, so this total may be higher than added sugar alone.';

  @override
  String get summaryTitleDay => 'Today';

  @override
  String get summaryTitleWeek => 'Last 7 days';

  @override
  String summaryTotalG(String total) {
    return '$total g';
  }

  @override
  String summaryTotalOfLimit(String limit, String total) {
    return '$total g of $limit g';
  }

  @override
  String get summaryWeekNote =>
      'The week is compared with the daily limit for each day something was logged.';

  @override
  String get targetsActivityLight => 'Lightly active';

  @override
  String get targetsActivityLightHint =>
      'On your feet part of the day, or light exercise 1 to 3 days a week';

  @override
  String get targetsActivityModerate => 'Active';

  @override
  String get targetsActivityModerateHint =>
      'An active job, or exercise 3 to 5 days a week';

  @override
  String get targetsActivitySedentary => 'Mostly sitting';

  @override
  String get targetsActivitySedentaryHint => 'Desk work and little walking';

  @override
  String get targetsActivityVery => 'Very active';

  @override
  String get targetsActivityVeryHint =>
      'Hard physical work, or hard training 6 to 7 days a week';

  @override
  String get targetsBodyFatHint =>
      'If you know it, for example from a body-composition scale, we base your protein guide on lean mass. If you leave it blank, we use your weight.';

  @override
  String get targetsBodyFatLabel => 'Body fat % (optional)';

  @override
  String targetsBodyFatOutOfRange(String max, String min) {
    return 'Please enter a number between $min and $max.';
  }

  @override
  String get targetsCarbs => 'Carbs';

  @override
  String get targetsDirectionGain => 'Gain slowly';

  @override
  String get targetsDirectionLose => 'Lose weight slowly';

  @override
  String get targetsDirectionMaintain => 'Stay the same';

  @override
  String get targetsEnergy => 'Calories';

  @override
  String get targetsFat => 'Fat';

  @override
  String get targetsFieldActivity => 'Activity level';

  @override
  String get targetsFieldBirthYear => 'Birth year';

  @override
  String get targetsFieldBodyFat => 'Body fat';

  @override
  String get targetsFieldHeight => 'Height';

  @override
  String get targetsFieldSex => 'Sex';

  @override
  String get targetsFieldWeight => 'Weight';

  @override
  String get targetsFlagAverageSexReference =>
      'This guide uses an in-between estimate.';

  @override
  String get targetsFlagCarbsBelowReference =>
      'Carbs are below the usual minimum of 130 g a day. A dietitian can help you adjust.';

  @override
  String get targetsFlagCarbsBelowReferenceHidden =>
      'Carbs are below the usual minimum. A dietitian can help you adjust.';

  @override
  String get targetsFlagDeficitCapped =>
      'We\'ve kept the daily change to a gentle amount.';

  @override
  String targetsFlagFloorApplied(String value) {
    return 'We don\'t suggest going below $value kcal a day. A doctor or dietitian can advise you.';
  }

  @override
  String get targetsFlagFloorAppliedHidden =>
      'We don\'t suggest going lower than this. A doctor or dietitian can advise you.';

  @override
  String get targetsFlagFloorLimitsDeficit =>
      'Your chosen pace isn\'t possible within a safe minimum, so this guide is for staying the same.';

  @override
  String get targetsFlagGoalWeightReached =>
      'You\'re at your target weight. The guide is now for staying the same.';

  @override
  String get targetsFlagOutsideEquationAgeRange =>
      'This estimate is less certain at your age.';

  @override
  String get targetsFlagProteinCapped =>
      'We\'ve kept protein to a moderate share of your calories.';

  @override
  String get targetsFlagRateCapped =>
      'We\'ve set the pace to the nearest available option.';

  @override
  String get targetsFlagTaperActive =>
      'You\'re close to your target, so the pace is easing off.';

  @override
  String get targetsFlagUnderweightMaintenance =>
      'We can help you keep a steady weight instead.';

  @override
  String targetsGValue(String value) {
    return '$value g';
  }

  @override
  String targetsHowActivity(String value) {
    return 'Activity factor: $value';
  }

  @override
  String targetsHowAdjustment(String value) {
    return 'Change for your goal: $value kcal a day';
  }

  @override
  String targetsHowBmr(String value) {
    return 'Estimated energy at rest: $value kcal';
  }

  @override
  String targetsHowFloor(String value) {
    return 'Lowest we suggest: $value kcal a day';
  }

  @override
  String targetsHowMaintenance(String value) {
    return 'Estimated energy to stay the same: $value kcal';
  }

  @override
  String targetsHowProtein(String per_kg, String weight) {
    return 'Protein: $per_kg g per kg of your weight ($weight kg)';
  }

  @override
  String targetsHowProteinAdjusted(String per_kg, String weight) {
    return 'Protein: $per_kg g per kg of an adjusted weight ($weight kg)';
  }

  @override
  String targetsHowProteinLean(String per_kg, String weight) {
    return 'Protein: $per_kg g per kg of lean mass ($weight kg)';
  }

  @override
  String get targetsHowSources => 'Sources and method';

  @override
  String get targetsHowTitle => 'How we got this';

  @override
  String targetsHowWeightLatest(String value) {
    return 'Weight used: $value kg (your latest weigh-in)';
  }

  @override
  String targetsHowWeightTrend(String value) {
    return 'Weight used: $value kg (your trend)';
  }

  @override
  String get targetsIntroBody =>
      'An estimate to guide you, based on your details. Information, not medical advice.';

  @override
  String get targetsIntroTitle => 'Your daily guide';

  @override
  String targetsKcalValue(String value) {
    return '$value kcal';
  }

  @override
  String get targetsMinor =>
      'Daily guides are for adults. You can still log food.';

  @override
  String targetsNeedsBodyData(String fields) {
    return 'Add $fields to see a daily guide.';
  }

  @override
  String get targetsPendingReview => 'Pending clinician review';

  @override
  String get targetsPregnancyNo => 'No';

  @override
  String get targetsPregnancyPaused =>
      'Daily guides are paused during pregnancy and breastfeeding. Please ask your doctor about your needs. You can still log food.';

  @override
  String get targetsPregnancyPreferNot => 'Prefer not to say';

  @override
  String get targetsPregnancyQuestion => 'Are you pregnant or breastfeeding?';

  @override
  String get targetsPregnancyYes => 'Yes';

  @override
  String get targetsProtein => 'Protein';

  @override
  String targetsRateOption(String kg, String pct) {
    return 'About $kg kg a week ($pct% of body weight)';
  }

  @override
  String targetsRateOptionPct(String pct) {
    return 'About $pct% of body weight a week';
  }

  @override
  String get targetsRateTitle => 'Pace';

  @override
  String get targetsSave => 'Save my daily guide';

  @override
  String get targetsSetupCta => 'Set up your daily guide';

  @override
  String get targetsSexReferenceAverage => 'In between';

  @override
  String get targetsSexReferenceFemale => 'Female estimate';

  @override
  String get targetsSexReferenceMale => 'Male estimate';

  @override
  String get targetsSexReferenceTitle => 'Which estimate should we use?';

  @override
  String get targetsSkip => 'Skip, just log food';

  @override
  String get targetsStepAbout => 'About you';

  @override
  String get targetsStepActivity => 'Activity';

  @override
  String get targetsStepGoal => 'Your goal';

  @override
  String get targetsStepGuide => 'Your guide';

  @override
  String get targetsTargetWeight => 'Target weight (optional)';

  @override
  String targetsTargetWeightTooLow(String min) {
    return 'Please choose $min kg or more.';
  }

  @override
  String get targetsTitle => 'Your daily guide';

  @override
  String get targetsUnderweight =>
      'We can help you keep a steady weight instead.';

  @override
  String targetsUnusualConfirm(String fields) {
    return 'Please check $fields. Is this right?';
  }

  @override
  String unitAmountHintMl(String amount, String unit) {
    return '1 $unit ≈ $amount ml';
  }

  @override
  String unitCup(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'cups',
      one: 'cup',
    );
    return '$_temp0';
  }

  @override
  String get unitEditGrams => 'Edit grams for this measure';

  @override
  String unitG(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'g',
      one: 'g',
    );
    return '$_temp0';
  }

  @override
  String unitGlass(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'glasses',
      one: 'glass',
    );
    return '$_temp0';
  }

  @override
  String unitGramsHint(String grams, String unit) {
    return '1 $unit ≈ $grams g';
  }

  @override
  String unitKatori(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'katoris',
      one: 'katori',
    );
    return '$_temp0';
  }

  @override
  String unitKatoriLarge(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'large katoris',
      one: 'large katori',
    );
    return '$_temp0';
  }

  @override
  String unitKatoriMedium(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'medium katoris',
      one: 'medium katori',
    );
    return '$_temp0';
  }

  @override
  String unitKatoriSmall(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'small katoris',
      one: 'small katori',
    );
    return '$_temp0';
  }

  @override
  String unitMl(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'ml',
      one: 'ml',
    );
    return '$_temp0';
  }

  @override
  String unitMlHint(String ml) {
    return '$ml ml';
  }

  @override
  String unitPiece(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'pieces',
      one: 'piece',
    );
    return '$_temp0';
  }

  @override
  String unitPieceLarge(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'large pieces',
      one: 'large piece',
    );
    return '$_temp0';
  }

  @override
  String unitPieceMedium(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'medium pieces',
      one: 'medium piece',
    );
    return '$_temp0';
  }

  @override
  String unitPieceSmall(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'small pieces',
      one: 'small piece',
    );
    return '$_temp0';
  }

  @override
  String get unitResetGrams => 'Use the standard value';

  @override
  String unitRoti(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'rotis',
      one: 'roti',
    );
    return '$_temp0';
  }

  @override
  String unitServing(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'servings',
      one: 'serving',
    );
    return '$_temp0';
  }

  @override
  String unitSetGrams(String unit) {
    return 'Set grams for $unit';
  }

  @override
  String unitSlice(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'slices',
      one: 'slice',
    );
    return '$_temp0';
  }

  @override
  String unitTbsp(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'tbsp',
      one: 'tbsp',
    );
    return '$_temp0';
  }

  @override
  String unitTsp(num count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'tsp',
      one: 'tsp',
    );
    return '$_temp0';
  }

  @override
  String get unitUnknown =>
      'We don\'t know the grams for this measure yet. Enter grams, or set your own value.';

  @override
  String get unitYourValue => 'Your value';

  @override
  String get userTypesChangeLater => 'You can change this in Profile';

  @override
  String get userTypesConsentNeeded =>
      'Saving health details needs your consent to health data processing.';

  @override
  String get userTypesConsentNote =>
      'Choosing some of these may offer to add details to your profile. This is saved only if you confirm, and only with your consent to health data processing.';

  @override
  String get userTypesContinue => 'Continue';

  @override
  String get userTypesEdit => 'Change your focus';

  @override
  String get userTypesFollowUpAllergyDietAllergensQuestion =>
      'Which allergies should we check for?';

  @override
  String get userTypesFollowUpAllergyDietDietQuestion =>
      'Which diet do you follow?';

  @override
  String get userTypesFollowUpEatBetterHint =>
      'For example palm oil or artificial sweeteners. You can add these now or later.';

  @override
  String get userTypesFollowUpEatBetterQuestion =>
      'Ingredients you would like us to point out';

  @override
  String get userTypesFollowUpFamilyChildren => 'Children';

  @override
  String get userTypesFollowUpFamilyOthers => 'Others';

  @override
  String get userTypesFollowUpFamilyParents => 'Parents';

  @override
  String get userTypesFollowUpFamilyPartner => 'Partner';

  @override
  String get userTypesFollowUpFamilyQuestion =>
      'Who are you checking food for?';

  @override
  String get userTypesFollowUpGymBuildMuscle => 'Build muscle';

  @override
  String get userTypesFollowUpGymLoseFat => 'Lose fat';

  @override
  String get userTypesFollowUpGymQuestion => 'What is your main goal?';

  @override
  String get userTypesFollowUpGymStayFit => 'Stay fit';

  @override
  String get userTypesFollowUpHealthConditionQuestion =>
      'Which of these apply?';

  @override
  String get userTypesMaxReached => 'You can pick up to 3.';

  @override
  String get userTypesNotCoveredBody =>
      'Thyroid, cholesterol, kidney disease and pregnancy are not covered yet, so results do not take them into account.';

  @override
  String get userTypesNotCoveredTitle => 'Not covered yet';

  @override
  String get userTypesPickUpTo => 'Pick up to 3';

  @override
  String get userTypesPrefillApply => 'Add to profile';

  @override
  String get userTypesPrefillBody =>
      'Nothing is added unless you confirm. Information, not medical advice.';

  @override
  String get userTypesPrefillGoalConflict =>
      'You picked weight loss and gym. Choose one goal for your profile.';

  @override
  String get userTypesPrefillGoalNeither => 'Neither (keep my current goal)';

  @override
  String userTypesPrefillLineAllergens(String values) {
    return 'Allergies: $values';
  }

  @override
  String userTypesPrefillLineConditions(String values) {
    return 'Health conditions: $values';
  }

  @override
  String userTypesPrefillLineCustomAlerts(String values) {
    return 'Ingredient alerts: $values';
  }

  @override
  String userTypesPrefillLineDiet(String value) {
    return 'Diet: $value';
  }

  @override
  String userTypesPrefillLineGoal(String value) {
    return 'Goal: $value';
  }

  @override
  String get userTypesPrefillNotNow => 'Not now';

  @override
  String get userTypesPrefillNothing => 'Nothing to add.';

  @override
  String get userTypesPrefillTitle => 'Add these to your profile?';

  @override
  String get userTypesSaved => 'Saved';

  @override
  String get userTypesSkip => 'Skip for now';

  @override
  String get userTypesSubtitle =>
      'We arrange the app around what matters to you. Scanning and results stay the same.';

  @override
  String get userTypesTileAllergyDietSubtitle =>
      'Check labels for allergens, vegetarian, vegan or Jain';

  @override
  String get userTypesTileAllergyDietTitle => 'A food allergy or special diet';

  @override
  String get userTypesTileEatBetterSubtitle =>
      'Compare products and understand labels';

  @override
  String get userTypesTileEatBetterTitle => 'Just eating better';

  @override
  String get userTypesTileFamilySubtitle =>
      'Check food for children, parents or everyone at home';

  @override
  String get userTypesTileFamilyTitle => 'My family';

  @override
  String get userTypesTileGymSubtitle =>
      'Track protein and compare protein products';

  @override
  String get userTypesTileGymTitle => 'Gym and fitness';

  @override
  String get userTypesTileHealthConditionSubtitle =>
      'Diabetes, prediabetes, PCOS or high blood pressure';

  @override
  String get userTypesTileHealthConditionTitle => 'A health condition';

  @override
  String get userTypesTileWeightLossSubtitle =>
      'See sugar, salt, calories and protein for what you eat';

  @override
  String get userTypesTileWeightLossTitle => 'Losing weight';

  @override
  String get userTypesTitle => 'What brings you to SmartNutri?';

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
  String verdictForMember(String name, String status) {
    return '$status for $name';
  }

  @override
  String verdictForYou(String status) {
    return '$status for you';
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
  String get verdictSpokenAvoid => 'For this member, avoid this product.';

  @override
  String get verdictSpokenCaution =>
      'For this member, take care with this product.';

  @override
  String get verdictSpokenOk => 'For this member, this product looks OK.';

  @override
  String get verdictSpokenUnknown =>
      'For this member, the label is unclear, so we can\'t say.';

  @override
  String get verdictStatusAvoid => 'Avoid';

  @override
  String get verdictStatusCaution => 'Caution';

  @override
  String get verdictStatusOk => 'OK';

  @override
  String get verdictStatusUnknown => 'Label unclear';

  @override
  String get voiceAiUnavailable =>
      'Voice answers are unavailable right now. Please try again later.';

  @override
  String get voiceAnswerTitle => 'Answer';

  @override
  String get voiceButtonHold => 'Hold to ask';

  @override
  String voiceButtonHoldFor(String name) {
    return 'Hold to ask, $name';
  }

  @override
  String voiceElapsed(String seconds) {
    return '$seconds s of 30 s';
  }

  @override
  String get voiceHint =>
      'Hold the button, ask about this product, then let go. Press Space to start and again to send.';

  @override
  String get voiceMicDenied =>
      'Microphone access is off. Allow it in your settings to ask by voice.';

  @override
  String get voiceNoMic => 'We couldn\'t find a microphone on this device.';

  @override
  String get voiceNotUnderstood =>
      'We couldn\'t hear a question. Hold the button and speak clearly.';

  @override
  String get voicePlaying => 'Playing the answer';

  @override
  String get voiceRateLimited =>
      'You\'ve reached today\'s voice-question limit.';

  @override
  String get voiceRecording => 'Listening… release to send';

  @override
  String get voiceReplay => 'Play again';

  @override
  String get voiceThinking => 'Getting your answer…';

  @override
  String get voiceTitle => 'Ask a question';

  @override
  String get voiceTooLong => 'Please keep your question under 30 seconds.';

  @override
  String get voiceUnsupportedBrowser =>
      'Voice questions don\'t work in this browser. Try the latest Chrome, Edge or Firefox.';

  @override
  String get voiceWordSafe => 'safe';

  @override
  String voiceYouAsked(String question) {
    return 'You asked: $question';
  }

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
  String get warningColumnMismatch =>
      'The per 100 g and per-serving values for this nutrient don\'t match the serving size. Check both on the pack.';

  @override
  String get warningDecimalShift =>
      'The decimal point in this value may have been misread. Check it on the pack.';

  @override
  String get warningDerivedFromServing =>
      'This value was worked out from the per-serving amount. Check it against the pack.';

  @override
  String get warningEnergyMismatch =>
      'The energy doesn\'t match the other values. Check it on the pack.';

  @override
  String get warningFatPartsMismatch =>
      'Saturated and trans fat add up to more than the total fat. Check these values on the pack.';

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
  String get warningSodiumUnitSuspect =>
      'The sodium looks too low for this product. Check whether the pack prints it in mg or g, and choose that unit.';

  @override
  String get warningUnitUnconfirmed =>
      'The unit for this value wasn\'t clear. Choose mg or g as printed.';

  @override
  String get warningUnreadableField =>
      'We couldn\'t read this value. Enter it from the pack, or leave it blank.';

  @override
  String get warningUpperBound =>
      'The pack says \'less than\' this amount. Confirm it if that\'s right.';

  @override
  String get weightAdd => 'Add a weigh-in';

  @override
  String get weightCheckEntry => 'Check this weigh-in';

  @override
  String weightConfirmUnusual(String previous) {
    return 'This is quite different from your last weigh-in ($previous kg). Save anyway?';
  }

  @override
  String get weightConfirmUnusualHidden =>
      'This is quite different from your last weigh-in. Save anyway?';

  @override
  String get weightConsent =>
      'To keep a weight log, allow SmartNutri to use your health details.';

  @override
  String get weightDate => 'Date';

  @override
  String get weightDelete => 'Delete weigh-in';

  @override
  String get weightDeleteAll => 'Delete all weigh-ins';

  @override
  String get weightDeleteAllConfirm =>
      'Delete all your weigh-ins? This can\'t be undone. The weight in your profile stays as it is.';

  @override
  String get weightDeleteAllDone => 'All weigh-ins deleted';

  @override
  String get weightDeleteConfirm => 'Delete this weigh-in?';

  @override
  String get weightEdit => 'Edit weigh-in';

  @override
  String get weightEmpty => 'No weigh-ins yet';

  @override
  String weightKgValue(String value) {
    return '$value kg';
  }

  @override
  String get weightNoProjectionMovingAway =>
      'Your trend isn\'t heading toward your target right now.';

  @override
  String get weightNoProjectionNoTarget =>
      'Set a target weight to see a projection.';

  @override
  String get weightNoProjectionReached => 'You\'re at your target weight.';

  @override
  String get weightNoProjectionTooFar =>
      'At this pace the target is more than a year away.';

  @override
  String get weightNoProjectionTooFewWeighIns =>
      'Add a few more weigh-ins over a couple of weeks to see a projection.';

  @override
  String get weightOutlier => 'Left out of the trend';

  @override
  String weightProjection(String date, String target) {
    return 'At this pace you\'d reach $target kg around $date.';
  }

  @override
  String get weightRange30 => '30 days';

  @override
  String get weightRange365 => '1 year';

  @override
  String get weightRange90 => '90 days';

  @override
  String weightRapidLoss(String pct) {
    return 'Your weight is going down faster than $pct% a week. A slower pace is usually easier to keep up.';
  }

  @override
  String get weightRapidLossHidden =>
      'Your weight is going down quickly. A slower pace is usually easier to keep up.';

  @override
  String get weightSaveAnyway => 'Save anyway';

  @override
  String get weightTipSameTime => 'Same time of day, for example after waking.';

  @override
  String get weightTitle => 'Weight';

  @override
  String get weightTrend => 'Trend';

  @override
  String weightWeeklyRate(String kg, String pct) {
    return 'About $kg kg a week ($pct% of body weight)';
  }
}
