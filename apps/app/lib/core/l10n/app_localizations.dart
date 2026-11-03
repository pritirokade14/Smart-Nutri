import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_hi.dart';
import 'app_localizations_mr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('hi'),
    Locale('mr'),
  ];

  /// No description provided for @allergenCrustacean.
  ///
  /// In en, this message translates to:
  /// **'Shellfish (crustaceans)'**
  String get allergenCrustacean;

  /// No description provided for @allergenEgg.
  ///
  /// In en, this message translates to:
  /// **'Egg'**
  String get allergenEgg;

  /// No description provided for @allergenFish.
  ///
  /// In en, this message translates to:
  /// **'Fish'**
  String get allergenFish;

  /// No description provided for @allergenGluten.
  ///
  /// In en, this message translates to:
  /// **'Gluten'**
  String get allergenGluten;

  /// No description provided for @allergenMilk.
  ///
  /// In en, this message translates to:
  /// **'Milk'**
  String get allergenMilk;

  /// No description provided for @allergenMustard.
  ///
  /// In en, this message translates to:
  /// **'Mustard'**
  String get allergenMustard;

  /// No description provided for @allergenPeanut.
  ///
  /// In en, this message translates to:
  /// **'Peanut'**
  String get allergenPeanut;

  /// No description provided for @allergenSesame.
  ///
  /// In en, this message translates to:
  /// **'Sesame'**
  String get allergenSesame;

  /// No description provided for @allergenSoy.
  ///
  /// In en, this message translates to:
  /// **'Soy'**
  String get allergenSoy;

  /// No description provided for @allergenSulphite.
  ///
  /// In en, this message translates to:
  /// **'Sulphites'**
  String get allergenSulphite;

  /// No description provided for @allergenTreeNut.
  ///
  /// In en, this message translates to:
  /// **'Tree nuts'**
  String get allergenTreeNut;

  /// No description provided for @appName.
  ///
  /// In en, this message translates to:
  /// **'SmartNutri AI'**
  String get appName;

  /// No description provided for @attributionOff.
  ///
  /// In en, this message translates to:
  /// **'Data from Open Food Facts (ODbL)'**
  String get attributionOff;

  /// No description provided for @authChange.
  ///
  /// In en, this message translates to:
  /// **'Change'**
  String get authChange;

  /// No description provided for @authCodeLabel.
  ///
  /// In en, this message translates to:
  /// **'6-digit code'**
  String get authCodeLabel;

  /// No description provided for @authEmail.
  ///
  /// In en, this message translates to:
  /// **'Continue with email'**
  String get authEmail;

  /// No description provided for @authEmailLabel.
  ///
  /// In en, this message translates to:
  /// **'Email address'**
  String get authEmailLabel;

  /// No description provided for @authError.
  ///
  /// In en, this message translates to:
  /// **'Could not sign in. Please try again.'**
  String get authError;

  /// No description provided for @authGoogle.
  ///
  /// In en, this message translates to:
  /// **'Continue with Google'**
  String get authGoogle;

  /// No description provided for @authPhone.
  ///
  /// In en, this message translates to:
  /// **'Continue with phone'**
  String get authPhone;

  /// No description provided for @authPhoneLabel.
  ///
  /// In en, this message translates to:
  /// **'Phone number (with country code)'**
  String get authPhoneLabel;

  /// No description provided for @authSendCode.
  ///
  /// In en, this message translates to:
  /// **'Send code'**
  String get authSendCode;

  /// No description provided for @authSignOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get authSignOut;

  /// No description provided for @authTitle.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get authTitle;

  /// No description provided for @authVerify.
  ///
  /// In en, this message translates to:
  /// **'Verify'**
  String get authVerify;

  /// No description provided for @claimDiabeticFriendly.
  ///
  /// In en, this message translates to:
  /// **'Diabetic friendly'**
  String get claimDiabeticFriendly;

  /// No description provided for @claimHighProtein.
  ///
  /// In en, this message translates to:
  /// **'High protein'**
  String get claimHighProtein;

  /// No description provided for @claimLowFat.
  ///
  /// In en, this message translates to:
  /// **'Low fat'**
  String get claimLowFat;

  /// No description provided for @claimLowSodium.
  ///
  /// In en, this message translates to:
  /// **'Low sodium'**
  String get claimLowSodium;

  /// No description provided for @claimLowSugar.
  ///
  /// In en, this message translates to:
  /// **'Low sugar'**
  String get claimLowSugar;

  /// No description provided for @claimNoAddedSugar.
  ///
  /// In en, this message translates to:
  /// **'No added sugar'**
  String get claimNoAddedSugar;

  /// No description provided for @claimNoRefinedSugar.
  ///
  /// In en, this message translates to:
  /// **'No refined sugar'**
  String get claimNoRefinedSugar;

  /// No description provided for @claimReasonAddedSugarIngredient.
  ///
  /// In en, this message translates to:
  /// **'The ingredients include added sugar: {ingredients}.'**
  String claimReasonAddedSugarIngredient(String ingredients);

  /// No description provided for @claimReasonBelowMinimum.
  ///
  /// In en, this message translates to:
  /// **'Protein gives {value}% of the energy, below the {limit}% this claim needs.'**
  String claimReasonBelowMinimum(String limit, String value);

  /// No description provided for @claimReasonExceedsLimit.
  ///
  /// In en, this message translates to:
  /// **'The label shows {value} per 100 g/ml, above this claim\'s limit of {limit}.'**
  String claimReasonExceedsLimit(String limit, String value);

  /// No description provided for @claimReasonIngredientsUnknown.
  ///
  /// In en, this message translates to:
  /// **'The ingredients list is not available, so this claim can\'t be checked.'**
  String get claimReasonIngredientsUnknown;

  /// No description provided for @claimReasonNoStandard.
  ///
  /// In en, this message translates to:
  /// **'There is no standard to check this claim against.'**
  String get claimReasonNoStandard;

  /// No description provided for @claimReasonNutrientMissing.
  ///
  /// In en, this message translates to:
  /// **'The label does not show {nutrient}, so this claim can\'t be checked.'**
  String claimReasonNutrientMissing(String nutrient);

  /// No description provided for @claimReasonOk.
  ///
  /// In en, this message translates to:
  /// **'The label data is consistent with this claim.'**
  String get claimReasonOk;

  /// No description provided for @claimReasonRefinedSugarIngredient.
  ///
  /// In en, this message translates to:
  /// **'The ingredients include refined sugar: {ingredients}.'**
  String claimReasonRefinedSugarIngredient(String ingredients);

  /// No description provided for @claimSourceOfProtein.
  ///
  /// In en, this message translates to:
  /// **'Source of protein'**
  String get claimSourceOfProtein;

  /// No description provided for @claimSugarFree.
  ///
  /// In en, this message translates to:
  /// **'Sugar free'**
  String get claimSugarFree;

  /// No description provided for @claimVerdictContradicted.
  ///
  /// In en, this message translates to:
  /// **'Label data contradicts this claim'**
  String get claimVerdictContradicted;

  /// No description provided for @claimVerdictSupported.
  ///
  /// In en, this message translates to:
  /// **'Label data supports this claim'**
  String get claimVerdictSupported;

  /// No description provided for @claimVerdictUnverifiable.
  ///
  /// In en, this message translates to:
  /// **'Can\'t be checked from the label'**
  String get claimVerdictUnverifiable;

  /// No description provided for @commonDisclaimer.
  ///
  /// In en, this message translates to:
  /// **'Information, not medical advice.'**
  String get commonDisclaimer;

  /// No description provided for @commonLoading.
  ///
  /// In en, this message translates to:
  /// **'Loading…'**
  String get commonLoading;

  /// No description provided for @commonRetry.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get commonRetry;

  /// No description provided for @conditionDiabetes.
  ///
  /// In en, this message translates to:
  /// **'Diabetes'**
  String get conditionDiabetes;

  /// No description provided for @conditionHypertension.
  ///
  /// In en, this message translates to:
  /// **'High blood pressure'**
  String get conditionHypertension;

  /// No description provided for @conditionPcos.
  ///
  /// In en, this message translates to:
  /// **'PCOS'**
  String get conditionPcos;

  /// No description provided for @conditionPrediabetes.
  ///
  /// In en, this message translates to:
  /// **'Prediabetes'**
  String get conditionPrediabetes;

  /// No description provided for @conditionWeightLoss.
  ///
  /// In en, this message translates to:
  /// **'Weight loss'**
  String get conditionWeightLoss;

  /// No description provided for @confirmAddIngredient.
  ///
  /// In en, this message translates to:
  /// **'Add an ingredient'**
  String get confirmAddIngredient;

  /// No description provided for @confirmAllergenStatement.
  ///
  /// In en, this message translates to:
  /// **'Allergen statement'**
  String get confirmAllergenStatement;

  /// No description provided for @confirmBasis.
  ///
  /// In en, this message translates to:
  /// **'Values on the pack are'**
  String get confirmBasis;

  /// No description provided for @confirmBasisOptionPer100g.
  ///
  /// In en, this message translates to:
  /// **'Per 100 g'**
  String get confirmBasisOptionPer100g;

  /// No description provided for @confirmBasisOptionPerServing.
  ///
  /// In en, this message translates to:
  /// **'Per serving'**
  String get confirmBasisOptionPerServing;

  /// No description provided for @confirmBrand.
  ///
  /// In en, this message translates to:
  /// **'Brand'**
  String get confirmBrand;

  /// No description provided for @confirmCategory.
  ///
  /// In en, this message translates to:
  /// **'Product type'**
  String get confirmCategory;

  /// No description provided for @confirmCategoryOptionBeverage.
  ///
  /// In en, this message translates to:
  /// **'Drink'**
  String get confirmCategoryOptionBeverage;

  /// No description provided for @confirmCategoryOptionCheese.
  ///
  /// In en, this message translates to:
  /// **'Cheese'**
  String get confirmCategoryOptionCheese;

  /// No description provided for @confirmCategoryOptionFat.
  ///
  /// In en, this message translates to:
  /// **'Oil or fat'**
  String get confirmCategoryOptionFat;

  /// No description provided for @confirmCategoryOptionGeneral.
  ///
  /// In en, this message translates to:
  /// **'Food'**
  String get confirmCategoryOptionGeneral;

  /// No description provided for @confirmCategoryOptionWater.
  ///
  /// In en, this message translates to:
  /// **'Packaged water'**
  String get confirmCategoryOptionWater;

  /// No description provided for @confirmChooseRequired.
  ///
  /// In en, this message translates to:
  /// **'Choose one to continue'**
  String get confirmChooseRequired;

  /// No description provided for @confirmClaims.
  ///
  /// In en, this message translates to:
  /// **'Claims on the pack'**
  String get confirmClaims;

  /// No description provided for @confirmClearStatementConfirm.
  ///
  /// In en, this message translates to:
  /// **'I checked the pack: this statement isn\'t printed'**
  String get confirmClearStatementConfirm;

  /// No description provided for @confirmConfirmValue.
  ///
  /// In en, this message translates to:
  /// **'Matches the pack'**
  String get confirmConfirmValue;

  /// No description provided for @confirmDerivedPerServing.
  ///
  /// In en, this message translates to:
  /// **'Worked out from a {serving} g serving'**
  String confirmDerivedPerServing(String serving);

  /// No description provided for @confirmFieldAddedSugarsG.
  ///
  /// In en, this message translates to:
  /// **'Added sugars (g)'**
  String get confirmFieldAddedSugarsG;

  /// No description provided for @confirmFieldCarbsG.
  ///
  /// In en, this message translates to:
  /// **'Carbohydrates (g)'**
  String get confirmFieldCarbsG;

  /// No description provided for @confirmFieldEnergyKcal.
  ///
  /// In en, this message translates to:
  /// **'Energy (kcal)'**
  String get confirmFieldEnergyKcal;

  /// No description provided for @confirmFieldFatG.
  ///
  /// In en, this message translates to:
  /// **'Total fat (g)'**
  String get confirmFieldFatG;

  /// No description provided for @confirmFieldFiberG.
  ///
  /// In en, this message translates to:
  /// **'Fibre (g)'**
  String get confirmFieldFiberG;

  /// No description provided for @confirmFieldProteinG.
  ///
  /// In en, this message translates to:
  /// **'Protein (g)'**
  String get confirmFieldProteinG;

  /// No description provided for @confirmFieldSaltG.
  ///
  /// In en, this message translates to:
  /// **'Salt (g)'**
  String get confirmFieldSaltG;

  /// No description provided for @confirmFieldSatFatG.
  ///
  /// In en, this message translates to:
  /// **'Saturated fat (g)'**
  String get confirmFieldSatFatG;

  /// No description provided for @confirmFieldSodiumMg.
  ///
  /// In en, this message translates to:
  /// **'Sodium (mg)'**
  String get confirmFieldSodiumMg;

  /// No description provided for @confirmFieldSugarsG.
  ///
  /// In en, this message translates to:
  /// **'Total sugars (g)'**
  String get confirmFieldSugarsG;

  /// No description provided for @confirmFieldTransFatG.
  ///
  /// In en, this message translates to:
  /// **'Trans fat (g)'**
  String get confirmFieldTransFatG;

  /// No description provided for @confirmIngredients.
  ///
  /// In en, this message translates to:
  /// **'Ingredients'**
  String get confirmIngredients;

  /// No description provided for @confirmLeaveBlankHint.
  ///
  /// In en, this message translates to:
  /// **'Leave blank if it isn\'t printed'**
  String get confirmLeaveBlankHint;

  /// No description provided for @confirmMayContainStatement.
  ///
  /// In en, this message translates to:
  /// **'May-contain statement'**
  String get confirmMayContainStatement;

  /// No description provided for @confirmName.
  ///
  /// In en, this message translates to:
  /// **'Product name'**
  String get confirmName;

  /// No description provided for @confirmNotMedicalAdvice.
  ///
  /// In en, this message translates to:
  /// **'Information, not medical advice.'**
  String get confirmNotMedicalAdvice;

  /// No description provided for @confirmOpenExisting.
  ///
  /// In en, this message translates to:
  /// **'Open the saved product'**
  String get confirmOpenExisting;

  /// No description provided for @confirmRemoveIngredient.
  ///
  /// In en, this message translates to:
  /// **'Remove this ingredient'**
  String get confirmRemoveIngredient;

  /// No description provided for @confirmSave.
  ///
  /// In en, this message translates to:
  /// **'Confirm and save'**
  String get confirmSave;

  /// No description provided for @confirmServingSize.
  ///
  /// In en, this message translates to:
  /// **'Serving size (g)'**
  String get confirmServingSize;

  /// No description provided for @confirmSodium.
  ///
  /// In en, this message translates to:
  /// **'Sodium'**
  String get confirmSodium;

  /// No description provided for @confirmSodiumUnit.
  ///
  /// In en, this message translates to:
  /// **'Sodium unit on the pack'**
  String get confirmSodiumUnit;

  /// No description provided for @confirmSodiumUnitOptionG.
  ///
  /// In en, this message translates to:
  /// **'g'**
  String get confirmSodiumUnitOptionG;

  /// No description provided for @confirmSodiumUnitOptionMg.
  ///
  /// In en, this message translates to:
  /// **'mg'**
  String get confirmSodiumUnitOptionMg;

  /// No description provided for @confirmSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Check every value against the pack. Leave blank if not printed.'**
  String get confirmSubtitle;

  /// No description provided for @confirmTitle.
  ///
  /// In en, this message translates to:
  /// **'Check the label values'**
  String get confirmTitle;

  /// No description provided for @confirmVegMarkNonVeg.
  ///
  /// In en, this message translates to:
  /// **'Non-vegetarian (brown mark)'**
  String get confirmVegMarkNonVeg;

  /// No description provided for @confirmVegMarkNone.
  ///
  /// In en, this message translates to:
  /// **'No mark on the pack'**
  String get confirmVegMarkNone;

  /// No description provided for @confirmVegMarkTitle.
  ///
  /// In en, this message translates to:
  /// **'Veg or non-veg mark'**
  String get confirmVegMarkTitle;

  /// No description provided for @confirmVegMarkVeg.
  ///
  /// In en, this message translates to:
  /// **'Vegetarian (green mark)'**
  String get confirmVegMarkVeg;

  /// No description provided for @confirmWithheldHint.
  ///
  /// In en, this message translates to:
  /// **'Check this value on the pack, then tick to confirm it.'**
  String get confirmWithheldHint;

  /// No description provided for @dietEggetarian.
  ///
  /// In en, this message translates to:
  /// **'Eggetarian'**
  String get dietEggetarian;

  /// No description provided for @dietJain.
  ///
  /// In en, this message translates to:
  /// **'Jain'**
  String get dietJain;

  /// No description provided for @dietNonVeg.
  ///
  /// In en, this message translates to:
  /// **'Non-vegetarian'**
  String get dietNonVeg;

  /// No description provided for @dietVeg.
  ///
  /// In en, this message translates to:
  /// **'Vegetarian'**
  String get dietVeg;

  /// No description provided for @dietVegan.
  ///
  /// In en, this message translates to:
  /// **'Vegan'**
  String get dietVegan;

  /// No description provided for @errorAuthInvalid.
  ///
  /// In en, this message translates to:
  /// **'Your session expired. Please sign in again.'**
  String get errorAuthInvalid;

  /// No description provided for @errorAuthRequired.
  ///
  /// In en, this message translates to:
  /// **'Please sign in.'**
  String get errorAuthRequired;

  /// No description provided for @errorExtractionFailed.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t read this label. Try another photo or enter the details manually.'**
  String get errorExtractionFailed;

  /// No description provided for @errorExtractionUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Label reading is unavailable right now. Try again later or enter the details manually.'**
  String get errorExtractionUnavailable;

  /// No description provided for @errorForbidden.
  ///
  /// In en, this message translates to:
  /// **'You don\'t have access to this.'**
  String get errorForbidden;

  /// No description provided for @errorHttpError.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Please try again.'**
  String get errorHttpError;

  /// No description provided for @errorImageTooLarge.
  ///
  /// In en, this message translates to:
  /// **'This photo is too large. Please use a photo under 8 MB.'**
  String get errorImageTooLarge;

  /// No description provided for @errorImplausibleValue.
  ///
  /// In en, this message translates to:
  /// **'Some values don\'t look right. Please check the highlighted fields, or leave them blank.'**
  String get errorImplausibleValue;

  /// No description provided for @errorInternalError.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Please try again.'**
  String get errorInternalError;

  /// No description provided for @errorInvalidBarcode.
  ///
  /// In en, this message translates to:
  /// **'That doesn\'t look like a valid barcode.'**
  String get errorInvalidBarcode;

  /// No description provided for @errorInvalidProductRef.
  ///
  /// In en, this message translates to:
  /// **'Choose a product to check.'**
  String get errorInvalidProductRef;

  /// No description provided for @errorMemberNotFound.
  ///
  /// In en, this message translates to:
  /// **'That family member wasn\'t found.'**
  String get errorMemberNotFound;

  /// No description provided for @errorMethodNotAllowed.
  ///
  /// In en, this message translates to:
  /// **'This action isn\'t supported. Please update the app.'**
  String get errorMethodNotAllowed;

  /// No description provided for @errorNetwork.
  ///
  /// In en, this message translates to:
  /// **'No internet connection.'**
  String get errorNetwork;

  /// No description provided for @errorNotFound.
  ///
  /// In en, this message translates to:
  /// **'Not found.'**
  String get errorNotFound;

  /// No description provided for @errorOffUnavailable.
  ///
  /// In en, this message translates to:
  /// **'The product database is busy right now. Please try again in a moment.'**
  String get errorOffUnavailable;

  /// No description provided for @errorProductExists.
  ///
  /// In en, this message translates to:
  /// **'This product is already saved.'**
  String get errorProductExists;

  /// No description provided for @errorProductNotFound.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t find this product yet.'**
  String get errorProductNotFound;

  /// No description provided for @errorRateLimited.
  ///
  /// In en, this message translates to:
  /// **'Too many requests. Please wait a moment.'**
  String get errorRateLimited;

  /// No description provided for @errorRateLimitedScans.
  ///
  /// In en, this message translates to:
  /// **'You\'ve reached today\'s label-scan limit.'**
  String get errorRateLimitedScans;

  /// No description provided for @errorRateLimitedVoice.
  ///
  /// In en, this message translates to:
  /// **'You\'ve reached today\'s voice-question limit.'**
  String get errorRateLimitedVoice;

  /// No description provided for @errorScanImageNotFound.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t find that photo. Please take or upload it again.'**
  String get errorScanImageNotFound;

  /// No description provided for @errorScanNotFound.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t find that label scan. Please scan the label again.'**
  String get errorScanNotFound;

  /// No description provided for @errorStorageUnavailable.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t handle the photo right now. Please try again in a moment.'**
  String get errorStorageUnavailable;

  /// No description provided for @errorUnauthorized.
  ///
  /// In en, this message translates to:
  /// **'Please sign in.'**
  String get errorUnauthorized;

  /// No description provided for @errorUnsupportedImage.
  ///
  /// In en, this message translates to:
  /// **'Please use a JPEG, PNG or WebP photo.'**
  String get errorUnsupportedImage;

  /// No description provided for @errorValidationError.
  ///
  /// In en, this message translates to:
  /// **'Please check the highlighted fields.'**
  String get errorValidationError;

  /// No description provided for @highInFat.
  ///
  /// In en, this message translates to:
  /// **'High in fat'**
  String get highInFat;

  /// No description provided for @highInPercentOfLimit.
  ///
  /// In en, this message translates to:
  /// **'{pct}% of the limit'**
  String highInPercentOfLimit(String pct);

  /// No description provided for @highInSalt.
  ///
  /// In en, this message translates to:
  /// **'High in salt'**
  String get highInSalt;

  /// No description provided for @highInSatFat.
  ///
  /// In en, this message translates to:
  /// **'High in saturated fat'**
  String get highInSatFat;

  /// No description provided for @highInSugar.
  ///
  /// In en, this message translates to:
  /// **'High in sugar'**
  String get highInSugar;

  /// No description provided for @homeScanCta.
  ///
  /// In en, this message translates to:
  /// **'Scan a product'**
  String get homeScanCta;

  /// No description provided for @homeWelcome.
  ///
  /// In en, this message translates to:
  /// **'Hello, {name}'**
  String homeWelcome(String name);

  /// No description provided for @labelCameraPermissionDenied.
  ///
  /// In en, this message translates to:
  /// **'Camera access is off. Allow it in Settings to photograph the label, or choose a photo or enter the details manually.'**
  String get labelCameraPermissionDenied;

  /// No description provided for @labelChooseFile.
  ///
  /// In en, this message translates to:
  /// **'Choose a file'**
  String get labelChooseFile;

  /// No description provided for @labelDropHere.
  ///
  /// In en, this message translates to:
  /// **'Drop a photo here'**
  String get labelDropHere;

  /// No description provided for @labelEnterManually.
  ///
  /// In en, this message translates to:
  /// **'Enter the details manually'**
  String get labelEnterManually;

  /// No description provided for @labelReading.
  ///
  /// In en, this message translates to:
  /// **'Reading the label…'**
  String get labelReading;

  /// No description provided for @labelRetake.
  ///
  /// In en, this message translates to:
  /// **'Retake'**
  String get labelRetake;

  /// No description provided for @labelTakePhoto.
  ///
  /// In en, this message translates to:
  /// **'Take a photo'**
  String get labelTakePhoto;

  /// No description provided for @labelTitle.
  ///
  /// In en, this message translates to:
  /// **'Photograph the label'**
  String get labelTitle;

  /// No description provided for @labelUploading.
  ///
  /// In en, this message translates to:
  /// **'Uploading the photo…'**
  String get labelUploading;

  /// No description provided for @notfoundGoToLabel.
  ///
  /// In en, this message translates to:
  /// **'We don\'t know this product yet — photograph its label'**
  String get notfoundGoToLabel;

  /// No description provided for @nutrientCarbsG.
  ///
  /// In en, this message translates to:
  /// **'carbohydrate'**
  String get nutrientCarbsG;

  /// No description provided for @nutrientEnergyKcal.
  ///
  /// In en, this message translates to:
  /// **'energy (calories)'**
  String get nutrientEnergyKcal;

  /// No description provided for @nutrientFatG.
  ///
  /// In en, this message translates to:
  /// **'fat'**
  String get nutrientFatG;

  /// No description provided for @nutrientProteinG.
  ///
  /// In en, this message translates to:
  /// **'protein'**
  String get nutrientProteinG;

  /// No description provided for @nutrientSalt.
  ///
  /// In en, this message translates to:
  /// **'salt'**
  String get nutrientSalt;

  /// No description provided for @nutrientSatFat.
  ///
  /// In en, this message translates to:
  /// **'saturated fat'**
  String get nutrientSatFat;

  /// No description provided for @nutrientSodiumMg.
  ///
  /// In en, this message translates to:
  /// **'sodium'**
  String get nutrientSodiumMg;

  /// No description provided for @nutrientSugarsG.
  ///
  /// In en, this message translates to:
  /// **'sugars'**
  String get nutrientSugarsG;

  /// No description provided for @nutriscoreCalculatedBy.
  ///
  /// In en, this message translates to:
  /// **'Nutri-Score calculated by SmartNutri'**
  String get nutriscoreCalculatedBy;

  /// No description provided for @nutriscoreInsufficientData.
  ///
  /// In en, this message translates to:
  /// **'Not enough label data to calculate a Nutri-Score.'**
  String get nutriscoreInsufficientData;

  /// No description provided for @productClaimsHeading.
  ///
  /// In en, this message translates to:
  /// **'Claims on the label, checked by SmartNutri'**
  String get productClaimsHeading;

  /// No description provided for @productLabelSays.
  ///
  /// In en, this message translates to:
  /// **'Label says: {claim}'**
  String productLabelSays(String claim);

  /// No description provided for @productMetaDescription.
  ///
  /// In en, this message translates to:
  /// **'Nutrition facts, Nutri-Score calculated by SmartNutri, and ingredients for this packaged food. Information, not medical advice.'**
  String get productMetaDescription;

  /// No description provided for @productMetaTitle.
  ///
  /// In en, this message translates to:
  /// **'{name} – nutrition facts | SmartNutri'**
  String productMetaTitle(String name);

  /// No description provided for @productPublicCta.
  ///
  /// In en, this message translates to:
  /// **'Check it for your family'**
  String get productPublicCta;

  /// No description provided for @reasonAddedSugars.
  ///
  /// In en, this message translates to:
  /// **'Contains added sugars: {ingredients}.'**
  String reasonAddedSugars(String ingredients);

  /// No description provided for @reasonAgeUnknown.
  ///
  /// In en, this message translates to:
  /// **'Add this member\'s birth year: this food may not suit young children or babies.'**
  String get reasonAgeUnknown;

  /// No description provided for @reasonAllergenContains.
  ///
  /// In en, this message translates to:
  /// **'Contains {allergen}, which is on your avoid list.'**
  String reasonAllergenContains(String allergen);

  /// No description provided for @reasonAllergenMayContain.
  ///
  /// In en, this message translates to:
  /// **'May contain {allergen}, which is on your avoid list.'**
  String reasonAllergenMayContain(String allergen);

  /// No description provided for @reasonAllergenUnknown.
  ///
  /// In en, this message translates to:
  /// **'We can\'t tell whether this contains {allergen}.'**
  String reasonAllergenUnknown(String allergen);

  /// No description provided for @reasonAllergenUnrecognised.
  ///
  /// In en, this message translates to:
  /// **'We don\'t recognise the allergen \"{allergen}\" in your profile.'**
  String reasonAllergenUnrecognised(String allergen);

  /// No description provided for @reasonCarbsPerServingHigh.
  ///
  /// In en, this message translates to:
  /// **'{carbs_g} g carbohydrate {basis, select, per_serving {per serving} other {per 100 g/ml}}. This may not suit your condition; check with your doctor.'**
  String reasonCarbsPerServingHigh(String basis, String carbs_g);

  /// No description provided for @reasonCardioRiskHighIn.
  ///
  /// In en, this message translates to:
  /// **'High in {high_in}. People managing blood sugar are often advised to limit these; check with your doctor.'**
  String reasonCardioRiskHighIn(String high_in);

  /// No description provided for @reasonChildCaffeine.
  ///
  /// In en, this message translates to:
  /// **'Contains caffeine, which is not recommended for children.'**
  String get reasonChildCaffeine;

  /// No description provided for @reasonChildSaltHigh.
  ///
  /// In en, this message translates to:
  /// **'{salt_g} g salt per 100 g/ml is high for a child.'**
  String reasonChildSaltHigh(String salt_g);

  /// No description provided for @reasonChildSugarHigh.
  ///
  /// In en, this message translates to:
  /// **'{basis, select, per_serving {One serving} other {100 g/ml}} gives {pct}% of a child\'s daily sugar limit (about {limit_g} g a day). That is high for a child.'**
  String reasonChildSugarHigh(String basis, String limit_g, String pct);

  /// No description provided for @reasonChildSugarModerate.
  ///
  /// In en, this message translates to:
  /// **'{basis, select, per_serving {One serving} other {100 g/ml}} gives {pct}% of a child\'s daily sugar limit (about {limit_g} g a day). That is on the higher side for a child.'**
  String reasonChildSugarModerate(String basis, String limit_g, String pct);

  /// No description provided for @reasonConditionUnrecognised.
  ///
  /// In en, this message translates to:
  /// **'We do not have guidance for \"{condition}\" yet.'**
  String reasonConditionUnrecognised(String condition);

  /// No description provided for @reasonDietUnknown.
  ///
  /// In en, this message translates to:
  /// **'We can\'t tell whether this fits the {diet} diet.'**
  String reasonDietUnknown(String diet);

  /// No description provided for @reasonDietViolation.
  ///
  /// In en, this message translates to:
  /// **'May not match the {diet} diet: {ingredients}.'**
  String reasonDietViolation(String diet, String ingredients);

  /// No description provided for @reasonEnergyDense.
  ///
  /// In en, this message translates to:
  /// **'This is an energy-dense food ({energy_kcal} kcal per 100 g/ml). Consider a smaller portion.'**
  String reasonEnergyDense(String energy_kcal);

  /// No description provided for @reasonGoodProteinDensity.
  ///
  /// In en, this message translates to:
  /// **'A good amount of protein for its calories.'**
  String get reasonGoodProteinDensity;

  /// No description provided for @reasonHiddenSugars.
  ///
  /// In en, this message translates to:
  /// **'Contains sugars listed under other names: {ingredients}.'**
  String reasonHiddenSugars(String ingredients);

  /// No description provided for @reasonInfantAddedSalt.
  ///
  /// In en, this message translates to:
  /// **'Contains added salt, which is not recommended for children under 2.'**
  String get reasonInfantAddedSalt;

  /// No description provided for @reasonInfantAddedSugar.
  ///
  /// In en, this message translates to:
  /// **'Contains added sugar, which is not recommended for children under 2.'**
  String get reasonInfantAddedSugar;

  /// No description provided for @reasonInfantCaffeine.
  ///
  /// In en, this message translates to:
  /// **'Contains caffeine, which is not recommended for children under 2.'**
  String get reasonInfantCaffeine;

  /// No description provided for @reasonInfantHoney.
  ///
  /// In en, this message translates to:
  /// **'Contains honey, which should not be given to babies under 1 year. For toddlers, check with your doctor.'**
  String get reasonInfantHoney;

  /// No description provided for @reasonInfantSaltHigh.
  ///
  /// In en, this message translates to:
  /// **'{salt_g} g salt per 100 g/ml is high for a child under 2.'**
  String reasonInfantSaltHigh(String salt_g);

  /// No description provided for @reasonInfantSugarHigh.
  ///
  /// In en, this message translates to:
  /// **'{sugars_g} g sugar per 100 g/ml is high for a child under 2.'**
  String reasonInfantSugarHigh(String sugars_g);

  /// No description provided for @reasonIngredientsMissing.
  ///
  /// In en, this message translates to:
  /// **'The ingredients list was not readable, so some checks could not be done.'**
  String get reasonIngredientsMissing;

  /// No description provided for @reasonMisleadingSugarClaim.
  ///
  /// In en, this message translates to:
  /// **'The pack says \"{claim}\", but the label data does not support this claim.'**
  String reasonMisleadingSugarClaim(String claim);

  /// No description provided for @reasonNutrientMissing.
  ///
  /// In en, this message translates to:
  /// **'The label does not show {nutrient}, so this check could not be done.'**
  String reasonNutrientMissing(String nutrient);

  /// No description provided for @reasonNutriscoreLow.
  ///
  /// In en, this message translates to:
  /// **'Nutri-Score {grade} points to lower overall nutrition quality.'**
  String reasonNutriscoreLow(String grade);

  /// No description provided for @reasonSaltHigh.
  ///
  /// In en, this message translates to:
  /// **'High in salt: {salt_g} g per 100 g/ml.'**
  String reasonSaltHigh(String salt_g);

  /// No description provided for @reasonSaltModerate.
  ///
  /// In en, this message translates to:
  /// **'Moderate salt: {salt_g} g per 100 g/ml.'**
  String reasonSaltModerate(String salt_g);

  /// No description provided for @reasonSodiumAdditives.
  ///
  /// In en, this message translates to:
  /// **'Contains sodium-based additives: {ingredients}.'**
  String reasonSodiumAdditives(String ingredients);

  /// No description provided for @reasonSugarHigh.
  ///
  /// In en, this message translates to:
  /// **'High in sugar: {sugars_g} g per 100 g/ml.'**
  String reasonSugarHigh(String sugars_g);

  /// No description provided for @reasonSugarModerate.
  ///
  /// In en, this message translates to:
  /// **'Moderate sugar: {sugars_g} g per 100 g/ml.'**
  String reasonSugarModerate(String sugars_g);

  /// No description provided for @reasonVariantDietViolationMarkOnly.
  ///
  /// In en, this message translates to:
  /// **'The pack has the brown non-vegetarian mark, so this may not match the {diet} diet.'**
  String reasonVariantDietViolationMarkOnly(String diet);

  /// No description provided for @reasonVariantNutrientMissingLowConfidence.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t read {nutrient} clearly on the label, so this check could not be done.'**
  String reasonVariantNutrientMissingLowConfidence(String nutrient);

  /// No description provided for @resultForMember.
  ///
  /// In en, this message translates to:
  /// **'For {name}'**
  String resultForMember(String name);

  /// No description provided for @resultGrade.
  ///
  /// In en, this message translates to:
  /// **'Nutri-Score {grade}'**
  String resultGrade(String grade);

  /// No description provided for @resultHighInTitle.
  ///
  /// In en, this message translates to:
  /// **'High in'**
  String get resultHighInTitle;

  /// No description provided for @resultIngredients.
  ///
  /// In en, this message translates to:
  /// **'Ingredients'**
  String get resultIngredients;

  /// No description provided for @resultNoIngredients.
  ///
  /// In en, this message translates to:
  /// **'Ingredients not available'**
  String get resultNoIngredients;

  /// No description provided for @resultScanAnother.
  ///
  /// In en, this message translates to:
  /// **'Scan another product'**
  String get resultScanAnother;

  /// No description provided for @resultTitle.
  ///
  /// In en, this message translates to:
  /// **'Result'**
  String get resultTitle;

  /// No description provided for @resultYou.
  ///
  /// In en, this message translates to:
  /// **'You'**
  String get resultYou;

  /// No description provided for @scanCameraDenied.
  ///
  /// In en, this message translates to:
  /// **'Camera access is off. You can type the barcode instead.'**
  String get scanCameraDenied;

  /// No description provided for @scanCameraUnavailable.
  ///
  /// In en, this message translates to:
  /// **'No camera found. You can type the barcode instead.'**
  String get scanCameraUnavailable;

  /// No description provided for @scanInvalid.
  ///
  /// In en, this message translates to:
  /// **'Enter the 8, 12, 13 or 14 digits under the barcode.'**
  String get scanInvalid;

  /// No description provided for @scanManualEntry.
  ///
  /// In en, this message translates to:
  /// **'Or type the barcode'**
  String get scanManualEntry;

  /// No description provided for @scanManualPlaceholder.
  ///
  /// In en, this message translates to:
  /// **'e.g. 8901063201089'**
  String get scanManualPlaceholder;

  /// No description provided for @scanNotFound.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t find this product yet.'**
  String get scanNotFound;

  /// No description provided for @scanOffUnavailable.
  ///
  /// In en, this message translates to:
  /// **'The product database is busy right now. Please try again in a moment.'**
  String get scanOffUnavailable;

  /// No description provided for @scanRetry.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get scanRetry;

  /// No description provided for @scanScanning.
  ///
  /// In en, this message translates to:
  /// **'Point the camera at the barcode'**
  String get scanScanning;

  /// No description provided for @scanSubmit.
  ///
  /// In en, this message translates to:
  /// **'Check this product'**
  String get scanSubmit;

  /// No description provided for @scanTitle.
  ///
  /// In en, this message translates to:
  /// **'Scan a barcode'**
  String get scanTitle;

  /// No description provided for @statusAvoid.
  ///
  /// In en, this message translates to:
  /// **'Avoid'**
  String get statusAvoid;

  /// No description provided for @statusCaution.
  ///
  /// In en, this message translates to:
  /// **'Caution'**
  String get statusCaution;

  /// No description provided for @statusOk.
  ///
  /// In en, this message translates to:
  /// **'OK'**
  String get statusOk;

  /// No description provided for @statusUnknown.
  ///
  /// In en, this message translates to:
  /// **'Label unclear'**
  String get statusUnknown;

  /// No description provided for @verdictConfidenceNote.
  ///
  /// In en, this message translates to:
  /// **'{reason, select, low_confidence {The label was hard to read, so this result is less certain.} other {Some data is uncertain.}}'**
  String verdictConfidenceNote(String reason);

  /// No description provided for @verdictHideReasons.
  ///
  /// In en, this message translates to:
  /// **'Hide reasons'**
  String get verdictHideReasons;

  /// No description provided for @verdictProfileNotSetUp.
  ///
  /// In en, this message translates to:
  /// **'Profile not set up: age, allergies and diet aren\'t checked yet.'**
  String get verdictProfileNotSetUp;

  /// No description provided for @verdictReasonUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Details for this result aren\'t available in this version.'**
  String get verdictReasonUnavailable;

  /// No description provided for @verdictRuleApplied.
  ///
  /// In en, this message translates to:
  /// **'Rule applied: {rule}'**
  String verdictRuleApplied(String rule);

  /// No description provided for @verdictShowAllReasons.
  ///
  /// In en, this message translates to:
  /// **'Show all reasons'**
  String get verdictShowAllReasons;

  /// No description provided for @verdictStatusAvoid.
  ///
  /// In en, this message translates to:
  /// **'Avoid'**
  String get verdictStatusAvoid;

  /// No description provided for @verdictStatusCaution.
  ///
  /// In en, this message translates to:
  /// **'Caution'**
  String get verdictStatusCaution;

  /// No description provided for @verdictStatusOk.
  ///
  /// In en, this message translates to:
  /// **'OK'**
  String get verdictStatusOk;

  /// No description provided for @verdictStatusUnknown.
  ///
  /// In en, this message translates to:
  /// **'Label unclear'**
  String get verdictStatusUnknown;

  /// No description provided for @warningBasisMismatch.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t tell whether these values are per 100 g or per serving. Choose which one the pack shows.'**
  String get warningBasisMismatch;

  /// No description provided for @warningCategoryCheck.
  ///
  /// In en, this message translates to:
  /// **'Check that the product type is right, because it changes how the values are read.'**
  String get warningCategoryCheck;

  /// No description provided for @warningCategoryUnknown.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t tell what type of product this is. Choose one.'**
  String get warningCategoryUnknown;

  /// No description provided for @warningDerivedFromServing.
  ///
  /// In en, this message translates to:
  /// **'This value was worked out from the per-serving amount. Check it against the pack.'**
  String get warningDerivedFromServing;

  /// No description provided for @warningEnergyMismatch.
  ///
  /// In en, this message translates to:
  /// **'The energy doesn\'t match the other values. Check it on the pack.'**
  String get warningEnergyMismatch;

  /// No description provided for @warningImplausibleValue.
  ///
  /// In en, this message translates to:
  /// **'This value looks unusual. Please check it against the pack.'**
  String get warningImplausibleValue;

  /// No description provided for @warningKcalKjMismatch.
  ///
  /// In en, this message translates to:
  /// **'The kcal and kJ values don\'t match each other. Check both on the pack.'**
  String get warningKcalKjMismatch;

  /// No description provided for @warningLowConfidence.
  ///
  /// In en, this message translates to:
  /// **'The label was hard to read. Please check every value against the pack.'**
  String get warningLowConfidence;

  /// No description provided for @warningPer100gMissing.
  ///
  /// In en, this message translates to:
  /// **'The pack\'s per 100 g values weren\'t found. Check the numbers or enter them from the pack.'**
  String get warningPer100gMissing;

  /// No description provided for @warningPerServingIgnored.
  ///
  /// In en, this message translates to:
  /// **'The per-serving values on the pack weren\'t used. Check that the per 100 g values are right.'**
  String get warningPerServingIgnored;

  /// No description provided for @warningSaltSodiumMismatch.
  ///
  /// In en, this message translates to:
  /// **'The salt and sodium values don\'t match each other. Check both on the pack.'**
  String get warningSaltSodiumMismatch;

  /// No description provided for @warningUnitUnconfirmed.
  ///
  /// In en, this message translates to:
  /// **'The unit for this value wasn\'t clear. Choose mg or g as printed.'**
  String get warningUnitUnconfirmed;

  /// No description provided for @warningUnreadableField.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t read this value. Enter it from the pack, or leave it blank.'**
  String get warningUnreadableField;

  /// No description provided for @warningUpperBound.
  ///
  /// In en, this message translates to:
  /// **'The pack says \'less than\' this amount. Confirm it if that\'s right.'**
  String get warningUpperBound;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'hi', 'mr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'hi':
      return AppLocalizationsHi();
    case 'mr':
      return AppLocalizationsMr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
