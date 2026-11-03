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

  /// No description provided for @alertAddedSugar.
  ///
  /// In en, this message translates to:
  /// **'added sugar'**
  String get alertAddedSugar;

  /// No description provided for @alertArtificialSweetener.
  ///
  /// In en, this message translates to:
  /// **'artificial sweeteners'**
  String get alertArtificialSweetener;

  /// No description provided for @alertMaida.
  ///
  /// In en, this message translates to:
  /// **'maida (refined wheat flour)'**
  String get alertMaida;

  /// No description provided for @alertMsg.
  ///
  /// In en, this message translates to:
  /// **'MSG (monosodium glutamate)'**
  String get alertMsg;

  /// No description provided for @alertPalmOil.
  ///
  /// In en, this message translates to:
  /// **'palm oil'**
  String get alertPalmOil;

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

  /// No description provided for @alternativesCompare.
  ///
  /// In en, this message translates to:
  /// **'Compare'**
  String get alternativesCompare;

  /// No description provided for @alternativesForMember.
  ///
  /// In en, this message translates to:
  /// **'For {name}'**
  String alternativesForMember(String name);

  /// No description provided for @alternativesReasonNoBetterFound.
  ///
  /// In en, this message translates to:
  /// **'We did not find a product with a better Nutri-Score of this kind.'**
  String get alternativesReasonNoBetterFound;

  /// No description provided for @alternativesReasonNoCategory.
  ///
  /// In en, this message translates to:
  /// **'We cannot suggest options for this product yet.'**
  String get alternativesReasonNoCategory;

  /// No description provided for @alternativesReasonSourceUngraded.
  ///
  /// In en, this message translates to:
  /// **'This product does not have enough label data to compare.'**
  String get alternativesReasonSourceUngraded;

  /// No description provided for @alternativesSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Same kind of product with a better Nutri-Score (calculated by SmartNutri)'**
  String get alternativesSubtitle;

  /// No description provided for @alternativesSugars.
  ///
  /// In en, this message translates to:
  /// **'Sugars: {value} g per 100 g/ml'**
  String alternativesSugars(String value);

  /// No description provided for @alternativesTitle.
  ///
  /// In en, this message translates to:
  /// **'Healthier options'**
  String get alternativesTitle;

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

  /// No description provided for @authOr.
  ///
  /// In en, this message translates to:
  /// **'or'**
  String get authOr;

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

  /// No description provided for @authSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Sign in to check packaged foods for your family.'**
  String get authSubtitle;

  /// No description provided for @authTagline.
  ///
  /// In en, this message translates to:
  /// **'Know if a packaged food suits each person in your family.'**
  String get authTagline;

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

  /// No description provided for @commonCancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get commonCancel;

  /// No description provided for @commonClose.
  ///
  /// In en, this message translates to:
  /// **'Close'**
  String get commonClose;

  /// No description provided for @commonComingSoon.
  ///
  /// In en, this message translates to:
  /// **'Coming soon'**
  String get commonComingSoon;

  /// No description provided for @commonDisclaimer.
  ///
  /// In en, this message translates to:
  /// **'Information, not medical advice.'**
  String get commonDisclaimer;

  /// No description provided for @commonErrorTitle.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong'**
  String get commonErrorTitle;

  /// No description provided for @commonGoHome.
  ///
  /// In en, this message translates to:
  /// **'Go to the home page'**
  String get commonGoHome;

  /// No description provided for @commonLoading.
  ///
  /// In en, this message translates to:
  /// **'Loading…'**
  String get commonLoading;

  /// No description provided for @commonNotFoundBody.
  ///
  /// In en, this message translates to:
  /// **'The page you\'re looking for doesn\'t exist or has moved.'**
  String get commonNotFoundBody;

  /// No description provided for @commonRetry.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get commonRetry;

  /// No description provided for @commonSkipToContent.
  ///
  /// In en, this message translates to:
  /// **'Skip to content'**
  String get commonSkipToContent;

  /// No description provided for @compareBetterA.
  ///
  /// In en, this message translates to:
  /// **'The first product is better here'**
  String get compareBetterA;

  /// No description provided for @compareBetterB.
  ///
  /// In en, this message translates to:
  /// **'The second product is better here'**
  String get compareBetterB;

  /// No description provided for @compareBetterChip.
  ///
  /// In en, this message translates to:
  /// **'Better'**
  String get compareBetterChip;

  /// No description provided for @compareBetterSame.
  ///
  /// In en, this message translates to:
  /// **'About the same'**
  String get compareBetterSame;

  /// No description provided for @compareBetterUnknown.
  ///
  /// In en, this message translates to:
  /// **'Cannot compare: missing on a label'**
  String get compareBetterUnknown;

  /// No description provided for @comparePickSecond.
  ///
  /// In en, this message translates to:
  /// **'Choose a product to compare with'**
  String get comparePickSecond;

  /// No description provided for @compareRowEnergyKcal.
  ///
  /// In en, this message translates to:
  /// **'Calories (per 100 g/ml)'**
  String get compareRowEnergyKcal;

  /// No description provided for @compareRowFiberG.
  ///
  /// In en, this message translates to:
  /// **'Fibre (per 100 g/ml)'**
  String get compareRowFiberG;

  /// No description provided for @compareRowGrade.
  ///
  /// In en, this message translates to:
  /// **'Nutri-Score (calculated by SmartNutri)'**
  String get compareRowGrade;

  /// No description provided for @compareRowProteinG.
  ///
  /// In en, this message translates to:
  /// **'Protein (per 100 g/ml)'**
  String get compareRowProteinG;

  /// No description provided for @compareRowSaltG.
  ///
  /// In en, this message translates to:
  /// **'Salt (per 100 g/ml)'**
  String get compareRowSaltG;

  /// No description provided for @compareRowSatFatG.
  ///
  /// In en, this message translates to:
  /// **'Saturated fat (per 100 g/ml)'**
  String get compareRowSatFatG;

  /// No description provided for @compareRowSugarsG.
  ///
  /// In en, this message translates to:
  /// **'Sugars (per 100 g/ml)'**
  String get compareRowSugarsG;

  /// No description provided for @compareTitle.
  ///
  /// In en, this message translates to:
  /// **'Compare'**
  String get compareTitle;

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

  /// No description provided for @confirmSectionAllergens.
  ///
  /// In en, this message translates to:
  /// **'Allergens'**
  String get confirmSectionAllergens;

  /// No description provided for @confirmSectionNutrition.
  ///
  /// In en, this message translates to:
  /// **'Nutrition table'**
  String get confirmSectionNutrition;

  /// No description provided for @confirmSectionPack.
  ///
  /// In en, this message translates to:
  /// **'Claims and marks on the pack'**
  String get confirmSectionPack;

  /// No description provided for @confirmSectionProduct.
  ///
  /// In en, this message translates to:
  /// **'Product'**
  String get confirmSectionProduct;

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

  /// No description provided for @consentAgree.
  ///
  /// In en, this message translates to:
  /// **'I agree'**
  String get consentAgree;

  /// No description provided for @consentAiOptional.
  ///
  /// In en, this message translates to:
  /// **'Optional. Without it you still get every result, just no AI explanation.'**
  String get consentAiOptional;

  /// No description provided for @consentAiProcessingBody.
  ///
  /// In en, this message translates to:
  /// **'Allow SmartNutri to send a summary of each result, without names, to an AI service processed in India, to write a short explanation. The AI never decides a result.'**
  String get consentAiProcessingBody;

  /// No description provided for @consentAiProcessingTitle.
  ///
  /// In en, this message translates to:
  /// **'AI explanations'**
  String get consentAiProcessingTitle;

  /// No description provided for @consentDecline.
  ///
  /// In en, this message translates to:
  /// **'Not now'**
  String get consentDecline;

  /// No description provided for @consentGranted.
  ///
  /// In en, this message translates to:
  /// **'Agreed'**
  String get consentGranted;

  /// No description provided for @consentHealthDataBody.
  ///
  /// In en, this message translates to:
  /// **'SmartNutri uses the allergies, health conditions, goal, height and weight you enter to check products for each family member. This is information, not medical advice. You can withdraw this consent at any time.'**
  String get consentHealthDataBody;

  /// No description provided for @consentHealthDataTitle.
  ///
  /// In en, this message translates to:
  /// **'Health data'**
  String get consentHealthDataTitle;

  /// No description provided for @consentNotGranted.
  ///
  /// In en, this message translates to:
  /// **'Not agreed'**
  String get consentNotGranted;

  /// No description provided for @consentRequiredNote.
  ///
  /// In en, this message translates to:
  /// **'Needed to save allergies, health conditions, a goal, height or weight.'**
  String get consentRequiredNote;

  /// No description provided for @consentTermsBody.
  ///
  /// In en, this message translates to:
  /// **'I agree to the SmartNutri terms of use and privacy policy.'**
  String get consentTermsBody;

  /// No description provided for @consentTermsTitle.
  ///
  /// In en, this message translates to:
  /// **'Terms of use'**
  String get consentTermsTitle;

  /// No description provided for @consentWithdraw.
  ///
  /// In en, this message translates to:
  /// **'Withdraw consent'**
  String get consentWithdraw;

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

  /// No description provided for @errorAiUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Voice answers are unavailable right now. Please try again later.'**
  String get errorAiUnavailable;

  /// No description provided for @errorAudioTooLarge.
  ///
  /// In en, this message translates to:
  /// **'That recording is too large. Please ask a shorter question.'**
  String get errorAudioTooLarge;

  /// No description provided for @errorAudioTooLong.
  ///
  /// In en, this message translates to:
  /// **'That recording is longer than 30 seconds. Please ask a shorter question.'**
  String get errorAudioTooLong;

  /// No description provided for @errorAudioUnsupported.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t play that recording. Please try again.'**
  String get errorAudioUnsupported;

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

  /// No description provided for @errorConsentRequired.
  ///
  /// In en, this message translates to:
  /// **'To save allergies, health conditions, a goal, height or weight, please agree to health data processing first.'**
  String get errorConsentRequired;

  /// No description provided for @errorConsentVersionMismatch.
  ///
  /// In en, this message translates to:
  /// **'This consent text has been updated. Please reload and review it again.'**
  String get errorConsentVersionMismatch;

  /// No description provided for @errorDeletionIncomplete.
  ///
  /// In en, this message translates to:
  /// **'We could not finish deleting your account. Please try again; nothing you deleted will come back.'**
  String get errorDeletionIncomplete;

  /// No description provided for @errorEatenAtOutOfRange.
  ///
  /// In en, this message translates to:
  /// **'Choose a time within the last 30 days.'**
  String get errorEatenAtOutOfRange;

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

  /// No description provided for @errorMealNotFound.
  ///
  /// In en, this message translates to:
  /// **'That food log wasn\'t found.'**
  String get errorMealNotFound;

  /// No description provided for @errorMemberLimit.
  ///
  /// In en, this message translates to:
  /// **'You can add up to 10 family members.'**
  String get errorMemberLimit;

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

  /// No description provided for @errorPhoneOtpDisabled.
  ///
  /// In en, this message translates to:
  /// **'Phone sign-in is not available yet. Please sign in with email or Google.'**
  String get errorPhoneOtpDisabled;

  /// No description provided for @errorPortionRequired.
  ///
  /// In en, this message translates to:
  /// **'Choose how much was eaten: servings or grams.'**
  String get errorPortionRequired;

  /// No description provided for @errorPrimaryMember.
  ///
  /// In en, this message translates to:
  /// **'Your own profile can\'t be removed.'**
  String get errorPrimaryMember;

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

  /// No description provided for @errorServingSizeUnknown.
  ///
  /// In en, this message translates to:
  /// **'This pack doesn\'t show a serving size. Enter the amount in grams.'**
  String get errorServingSizeUnknown;

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

  /// No description provided for @errorVoiceNotUnderstood.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t hear a question. Please hold the button and speak clearly.'**
  String get errorVoiceNotUnderstood;

  /// No description provided for @explanationAiNote.
  ///
  /// In en, this message translates to:
  /// **'Written by AI from the results above. It never changes a result.'**
  String get explanationAiNote;

  /// No description provided for @explanationFallbackTip1.
  ///
  /// In en, this message translates to:
  /// **'Compare the labels of similar products and choose the one with less sugar and salt.'**
  String get explanationFallbackTip1;

  /// No description provided for @explanationFallbackTip2.
  ///
  /// In en, this message translates to:
  /// **'Check the serving size on the pack: the label values are per 100 g or 100 ml.'**
  String get explanationFallbackTip2;

  /// No description provided for @explanationFallbackTip3.
  ///
  /// In en, this message translates to:
  /// **'If you have a health condition, ask your doctor or a dietitian before making changes.'**
  String get explanationFallbackTip3;

  /// No description provided for @explanationSourceFallbackNote.
  ///
  /// In en, this message translates to:
  /// **'The AI explanation isn\'t available right now, so this summary comes from our rules.'**
  String get explanationSourceFallbackNote;

  /// No description provided for @explanationTipsTitle.
  ///
  /// In en, this message translates to:
  /// **'Tips'**
  String get explanationTipsTitle;

  /// No description provided for @explanationTitle.
  ///
  /// In en, this message translates to:
  /// **'Why this result'**
  String get explanationTitle;

  /// No description provided for @familyBody.
  ///
  /// In en, this message translates to:
  /// **'Add each family member with their age, allergies and diet, so every result is about them.'**
  String get familyBody;

  /// No description provided for @familyComingSoonBody.
  ///
  /// In en, this message translates to:
  /// **'Add each person\'s age, allergies and diet to get a result for each of them.'**
  String get familyComingSoonBody;

  /// No description provided for @familyComingSoonTitle.
  ///
  /// In en, this message translates to:
  /// **'Family profiles are coming soon'**
  String get familyComingSoonTitle;

  /// No description provided for @familyTitle.
  ///
  /// In en, this message translates to:
  /// **'Family'**
  String get familyTitle;

  /// No description provided for @footerTagline.
  ///
  /// In en, this message translates to:
  /// **'Packaged-food information for Indian families.'**
  String get footerTagline;

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

  /// No description provided for @historyBody.
  ///
  /// In en, this message translates to:
  /// **'Products you check will be listed here, so you can find them again.'**
  String get historyBody;

  /// No description provided for @historyComingSoonBody.
  ///
  /// In en, this message translates to:
  /// **'You\'ll see every product you\'ve checked here.'**
  String get historyComingSoonBody;

  /// No description provided for @historyComingSoonTitle.
  ///
  /// In en, this message translates to:
  /// **'Your history is coming soon'**
  String get historyComingSoonTitle;

  /// No description provided for @historyEmpty.
  ///
  /// In en, this message translates to:
  /// **'Nothing logged yet.'**
  String get historyEmpty;

  /// No description provided for @historyItemAmount.
  ///
  /// In en, this message translates to:
  /// **'{grams} g'**
  String historyItemAmount(String grams);

  /// No description provided for @historyLoggedTitle.
  ///
  /// In en, this message translates to:
  /// **'What was eaten'**
  String get historyLoggedTitle;

  /// No description provided for @historyMember.
  ///
  /// In en, this message translates to:
  /// **'Family member'**
  String get historyMember;

  /// No description provided for @historyNextDay.
  ///
  /// In en, this message translates to:
  /// **'Next day'**
  String get historyNextDay;

  /// No description provided for @historyPreviousDay.
  ///
  /// In en, this message translates to:
  /// **'Previous day'**
  String get historyPreviousDay;

  /// No description provided for @historyRemove.
  ///
  /// In en, this message translates to:
  /// **'Remove'**
  String get historyRemove;

  /// No description provided for @historyRemoveConfirm.
  ///
  /// In en, this message translates to:
  /// **'Remove this item from the log?'**
  String get historyRemoveConfirm;

  /// No description provided for @historyThisWeek.
  ///
  /// In en, this message translates to:
  /// **'This week'**
  String get historyThisWeek;

  /// No description provided for @historyTitle.
  ///
  /// In en, this message translates to:
  /// **'History'**
  String get historyTitle;

  /// No description provided for @historyToday.
  ///
  /// In en, this message translates to:
  /// **'Today'**
  String get historyToday;

  /// No description provided for @homeLabelBody.
  ///
  /// In en, this message translates to:
  /// **'No barcode, or a product we don\'t know yet? Photograph the label.'**
  String get homeLabelBody;

  /// No description provided for @homeLabelTitle.
  ///
  /// In en, this message translates to:
  /// **'Photograph a label'**
  String get homeLabelTitle;

  /// No description provided for @homeManualBody.
  ///
  /// In en, this message translates to:
  /// **'Type the nutrition facts from the pack yourself.'**
  String get homeManualBody;

  /// No description provided for @homeRecentEmptyBody.
  ///
  /// In en, this message translates to:
  /// **'Products you check will show up here.'**
  String get homeRecentEmptyBody;

  /// No description provided for @homeRecentEmptyTitle.
  ///
  /// In en, this message translates to:
  /// **'No scans yet'**
  String get homeRecentEmptyTitle;

  /// No description provided for @homeRecentTitle.
  ///
  /// In en, this message translates to:
  /// **'Recent scans'**
  String get homeRecentTitle;

  /// No description provided for @homeScanBody.
  ///
  /// In en, this message translates to:
  /// **'Use your camera, or type the number under the barcode.'**
  String get homeScanBody;

  /// No description provided for @homeScanCta.
  ///
  /// In en, this message translates to:
  /// **'Scan a product'**
  String get homeScanCta;

  /// No description provided for @homeSubtitle.
  ///
  /// In en, this message translates to:
  /// **'What would you like to check today?'**
  String get homeSubtitle;

  /// No description provided for @homeWelcome.
  ///
  /// In en, this message translates to:
  /// **'Hello, {name}'**
  String homeWelcome(String name);

  /// No description provided for @homeWelcomeNoName.
  ///
  /// In en, this message translates to:
  /// **'Hello'**
  String get homeWelcomeNoName;

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

  /// No description provided for @landingCtaStart.
  ///
  /// In en, this message translates to:
  /// **'Get started'**
  String get landingCtaStart;

  /// No description provided for @landingEyebrow.
  ///
  /// In en, this message translates to:
  /// **'For Indian families'**
  String get landingEyebrow;

  /// No description provided for @landingHeroBody.
  ///
  /// In en, this message translates to:
  /// **'Scan a barcode or photograph the label. SmartNutri reads it, checks it against each person\'s age, allergies and diet, and tells you why.'**
  String get landingHeroBody;

  /// No description provided for @landingHeroTitle.
  ///
  /// In en, this message translates to:
  /// **'Know if a packaged food is right for each member of your family'**
  String get landingHeroTitle;

  /// No description provided for @landingHowTitle.
  ///
  /// In en, this message translates to:
  /// **'How it works'**
  String get landingHowTitle;

  /// No description provided for @landingMetaDescription.
  ///
  /// In en, this message translates to:
  /// **'Scan a packaged food and see whether it suits each member of your family, with the reasons. Information, not medical advice.'**
  String get landingMetaDescription;

  /// No description provided for @landingMetaTitle.
  ///
  /// In en, this message translates to:
  /// **'SmartNutri AI – is this packaged food right for your family?'**
  String get landingMetaTitle;

  /// No description provided for @landingStep1Body.
  ///
  /// In en, this message translates to:
  /// **'Scan the barcode, or take a photo of the nutrition label on the pack.'**
  String get landingStep1Body;

  /// No description provided for @landingStep1Title.
  ///
  /// In en, this message translates to:
  /// **'Scan or snap'**
  String get landingStep1Title;

  /// No description provided for @landingStep2Body.
  ///
  /// In en, this message translates to:
  /// **'You confirm the label details before anything is saved.'**
  String get landingStep2Body;

  /// No description provided for @landingStep2Title.
  ///
  /// In en, this message translates to:
  /// **'Check what we read'**
  String get landingStep2Title;

  /// No description provided for @landingStep3Body.
  ///
  /// In en, this message translates to:
  /// **'Get a simple result for each family member, with the reasons in plain words.'**
  String get landingStep3Body;

  /// No description provided for @landingStep3Title.
  ///
  /// In en, this message translates to:
  /// **'See who it suits'**
  String get landingStep3Title;

  /// No description provided for @languageEn.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get languageEn;

  /// No description provided for @languageHi.
  ///
  /// In en, this message translates to:
  /// **'हिन्दी'**
  String get languageHi;

  /// No description provided for @languageLabel.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get languageLabel;

  /// No description provided for @languageMr.
  ///
  /// In en, this message translates to:
  /// **'मराठी'**
  String get languageMr;

  /// No description provided for @mealsLogAmountGrams.
  ///
  /// In en, this message translates to:
  /// **'Amount in grams'**
  String get mealsLogAmountGrams;

  /// No description provided for @mealsLogAmountInvalid.
  ///
  /// In en, this message translates to:
  /// **'Enter an amount more than 0 and up to {max}.'**
  String mealsLogAmountInvalid(String max);

  /// No description provided for @mealsLogAmountServings.
  ///
  /// In en, this message translates to:
  /// **'Number of servings'**
  String get mealsLogAmountServings;

  /// No description provided for @mealsLogCta.
  ///
  /// In en, this message translates to:
  /// **'I ate this'**
  String get mealsLogCta;

  /// No description provided for @mealsLogEatenAt.
  ///
  /// In en, this message translates to:
  /// **'When'**
  String get mealsLogEatenAt;

  /// No description provided for @mealsLogGrams.
  ///
  /// In en, this message translates to:
  /// **'Grams'**
  String get mealsLogGrams;

  /// No description provided for @mealsLogMember.
  ///
  /// In en, this message translates to:
  /// **'Who ate it?'**
  String get mealsLogMember;

  /// No description provided for @mealsLogNow.
  ///
  /// In en, this message translates to:
  /// **'Now'**
  String get mealsLogNow;

  /// No description provided for @mealsLogPortion.
  ///
  /// In en, this message translates to:
  /// **'How much was eaten?'**
  String get mealsLogPortion;

  /// No description provided for @mealsLogSave.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get mealsLogSave;

  /// No description provided for @mealsLogSaved.
  ///
  /// In en, this message translates to:
  /// **'Logged for {who}'**
  String mealsLogSaved(String who);

  /// No description provided for @mealsLogSavedYou.
  ///
  /// In en, this message translates to:
  /// **'Logged for you'**
  String get mealsLogSavedYou;

  /// No description provided for @mealsLogServingSize.
  ///
  /// In en, this message translates to:
  /// **'1 serving = {grams} g'**
  String mealsLogServingSize(String grams);

  /// No description provided for @mealsLogServings.
  ///
  /// In en, this message translates to:
  /// **'Servings'**
  String get mealsLogServings;

  /// No description provided for @mealsLogTitle.
  ///
  /// In en, this message translates to:
  /// **'Log what was eaten'**
  String get mealsLogTitle;

  /// No description provided for @mealsLogUndo.
  ///
  /// In en, this message translates to:
  /// **'Undo'**
  String get mealsLogUndo;

  /// No description provided for @mealsLogUndone.
  ///
  /// In en, this message translates to:
  /// **'Removed from the log'**
  String get mealsLogUndone;

  /// No description provided for @mealsOnlineOnly.
  ///
  /// In en, this message translates to:
  /// **'On the web, logging needs an internet connection. Items are not saved offline.'**
  String get mealsOnlineOnly;

  /// No description provided for @mealsQueuedOffline.
  ///
  /// In en, this message translates to:
  /// **'Saved on this phone. It will be added to the log when you are back online.'**
  String get mealsQueuedOffline;

  /// No description provided for @mealsSyncFailed.
  ///
  /// In en, this message translates to:
  /// **'Some items could not be added to the log. Please log them again.'**
  String get mealsSyncFailed;

  /// No description provided for @mealsSyncing.
  ///
  /// In en, this message translates to:
  /// **'Syncing logged items…'**
  String get mealsSyncing;

  /// No description provided for @membersAdd.
  ///
  /// In en, this message translates to:
  /// **'Add a family member'**
  String get membersAdd;

  /// No description provided for @membersBorn.
  ///
  /// In en, this message translates to:
  /// **'Born {year}'**
  String membersBorn(String year);

  /// No description provided for @membersConsentWithdrawnNotice.
  ///
  /// In en, this message translates to:
  /// **'Health data consent is off. Saved allergies and conditions are still used to check products, but new ones can\'t be saved until you agree again.'**
  String get membersConsentWithdrawnNotice;

  /// No description provided for @membersEdit.
  ///
  /// In en, this message translates to:
  /// **'Edit'**
  String get membersEdit;

  /// No description provided for @membersFormAllergenAdd.
  ///
  /// In en, this message translates to:
  /// **'Add'**
  String get membersFormAllergenAdd;

  /// No description provided for @membersFormAllergenInvalid.
  ///
  /// In en, this message translates to:
  /// **'An allergy must be 2 to 40 characters.'**
  String get membersFormAllergenInvalid;

  /// No description provided for @membersFormAllergenLength.
  ///
  /// In en, this message translates to:
  /// **'Type 2 to 40 characters.'**
  String get membersFormAllergenLength;

  /// No description provided for @membersFormAllergenLimit.
  ///
  /// In en, this message translates to:
  /// **'You can add up to 20 allergies.'**
  String get membersFormAllergenLimit;

  /// No description provided for @membersFormAllergenOther.
  ///
  /// In en, this message translates to:
  /// **'Other allergy'**
  String get membersFormAllergenOther;

  /// No description provided for @membersFormAllergens.
  ///
  /// In en, this message translates to:
  /// **'Allergies'**
  String get membersFormAllergens;

  /// No description provided for @membersFormAllergensHelp.
  ///
  /// In en, this message translates to:
  /// **'Pick from the list, or type your own.'**
  String get membersFormAllergensHelp;

  /// No description provided for @membersFormBirthYear.
  ///
  /// In en, this message translates to:
  /// **'Year of birth'**
  String get membersFormBirthYear;

  /// No description provided for @membersFormBirthYearHelp.
  ///
  /// In en, this message translates to:
  /// **'Used for the checks for children and babies under 2.'**
  String get membersFormBirthYearHelp;

  /// No description provided for @membersFormBirthYearInvalid.
  ///
  /// In en, this message translates to:
  /// **'Enter a year from 1900 to {year}.'**
  String membersFormBirthYearInvalid(String year);

  /// No description provided for @membersFormCancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get membersFormCancel;

  /// No description provided for @membersFormClearAllergiesConfirm.
  ///
  /// In en, this message translates to:
  /// **'Remove every allergy for {name}? Products with these allergens will no longer be flagged for them.'**
  String membersFormClearAllergiesConfirm(String name);

  /// No description provided for @membersFormConditions.
  ///
  /// In en, this message translates to:
  /// **'Health conditions'**
  String get membersFormConditions;

  /// No description provided for @membersFormCustomAlerts.
  ///
  /// In en, this message translates to:
  /// **'Ingredient alerts'**
  String get membersFormCustomAlerts;

  /// No description provided for @membersFormCustomAlertsHelp.
  ///
  /// In en, this message translates to:
  /// **'We point these out when we find them on the label.'**
  String get membersFormCustomAlertsHelp;

  /// No description provided for @membersFormDiet.
  ///
  /// In en, this message translates to:
  /// **'Diet'**
  String get membersFormDiet;

  /// No description provided for @membersFormGoal.
  ///
  /// In en, this message translates to:
  /// **'Goal (optional)'**
  String get membersFormGoal;

  /// No description provided for @membersFormHealthFieldsNote.
  ///
  /// In en, this message translates to:
  /// **'Allergies, health conditions, goal, height and weight are saved only with your consent to health data processing.'**
  String get membersFormHealthFieldsNote;

  /// No description provided for @membersFormHeightCm.
  ///
  /// In en, this message translates to:
  /// **'Height (cm, optional)'**
  String get membersFormHeightCm;

  /// No description provided for @membersFormHeightInvalid.
  ///
  /// In en, this message translates to:
  /// **'Enter a height between 30 and 250 cm, or leave it blank.'**
  String get membersFormHeightInvalid;

  /// No description provided for @membersFormName.
  ///
  /// In en, this message translates to:
  /// **'Name'**
  String get membersFormName;

  /// No description provided for @membersFormNameInvalid.
  ///
  /// In en, this message translates to:
  /// **'Enter a name of up to 40 characters.'**
  String get membersFormNameInvalid;

  /// No description provided for @membersFormNameRequired.
  ///
  /// In en, this message translates to:
  /// **'Enter a name.'**
  String get membersFormNameRequired;

  /// No description provided for @membersFormNotSet.
  ///
  /// In en, this message translates to:
  /// **'Not set'**
  String get membersFormNotSet;

  /// No description provided for @membersFormNumberRange.
  ///
  /// In en, this message translates to:
  /// **'Enter a number from {min} to {max}.'**
  String membersFormNumberRange(String max, String min);

  /// No description provided for @membersFormRelation.
  ///
  /// In en, this message translates to:
  /// **'Relation'**
  String get membersFormRelation;

  /// No description provided for @membersFormRelationRequired.
  ///
  /// In en, this message translates to:
  /// **'Choose a relation.'**
  String get membersFormRelationRequired;

  /// No description provided for @membersFormRemoveAllergy.
  ///
  /// In en, this message translates to:
  /// **'Remove {allergen}'**
  String membersFormRemoveAllergy(String allergen);

  /// No description provided for @membersFormRemoveAllergyConfirm.
  ///
  /// In en, this message translates to:
  /// **'Remove {allergen} from the allergies for {name}? Products with it will no longer be flagged for them.'**
  String membersFormRemoveAllergyConfirm(String allergen, String name);

  /// No description provided for @membersFormSave.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get membersFormSave;

  /// No description provided for @membersFormSex.
  ///
  /// In en, this message translates to:
  /// **'Sex (optional)'**
  String get membersFormSex;

  /// No description provided for @membersFormWeightInvalid.
  ///
  /// In en, this message translates to:
  /// **'Enter a weight between 2 and 300 kg, or leave it blank.'**
  String get membersFormWeightInvalid;

  /// No description provided for @membersFormWeightKg.
  ///
  /// In en, this message translates to:
  /// **'Weight (kg, optional)'**
  String get membersFormWeightKg;

  /// No description provided for @membersGoalHealthyEating.
  ///
  /// In en, this message translates to:
  /// **'Eat better'**
  String get membersGoalHealthyEating;

  /// No description provided for @membersGoalWeightGain.
  ///
  /// In en, this message translates to:
  /// **'Gain weight'**
  String get membersGoalWeightGain;

  /// No description provided for @membersGoalWeightLoss.
  ///
  /// In en, this message translates to:
  /// **'Lose weight'**
  String get membersGoalWeightLoss;

  /// No description provided for @membersLimitReached.
  ///
  /// In en, this message translates to:
  /// **'You have 10 family members, the most you can add.'**
  String get membersLimitReached;

  /// No description provided for @membersRelationChild.
  ///
  /// In en, this message translates to:
  /// **'Child'**
  String get membersRelationChild;

  /// No description provided for @membersRelationOther.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get membersRelationOther;

  /// No description provided for @membersRelationParent.
  ///
  /// In en, this message translates to:
  /// **'Parent'**
  String get membersRelationParent;

  /// No description provided for @membersRelationSelf.
  ///
  /// In en, this message translates to:
  /// **'You'**
  String get membersRelationSelf;

  /// No description provided for @membersRelationSpouse.
  ///
  /// In en, this message translates to:
  /// **'Spouse'**
  String get membersRelationSpouse;

  /// No description provided for @membersRemove.
  ///
  /// In en, this message translates to:
  /// **'Remove'**
  String get membersRemove;

  /// No description provided for @membersRemoveConfirm.
  ///
  /// In en, this message translates to:
  /// **'Remove {name} from your family?'**
  String membersRemoveConfirm(String name);

  /// No description provided for @membersSaved.
  ///
  /// In en, this message translates to:
  /// **'Saved'**
  String get membersSaved;

  /// No description provided for @membersSexFemale.
  ///
  /// In en, this message translates to:
  /// **'Female'**
  String get membersSexFemale;

  /// No description provided for @membersSexMale.
  ///
  /// In en, this message translates to:
  /// **'Male'**
  String get membersSexMale;

  /// No description provided for @membersSexOther.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get membersSexOther;

  /// No description provided for @membersTitle.
  ///
  /// In en, this message translates to:
  /// **'Family'**
  String get membersTitle;

  /// No description provided for @membersYouBadge.
  ///
  /// In en, this message translates to:
  /// **'You'**
  String get membersYouBadge;

  /// No description provided for @methodologyIntro.
  ///
  /// In en, this message translates to:
  /// **'SmartNutri checks each packaged food against its label and each family member\'s profile using fixed rules. An AI only explains the result; it never decides it. This is information, not medical advice.'**
  String get methodologyIntro;

  /// No description provided for @methodologyPendingReview.
  ///
  /// In en, this message translates to:
  /// **'These thresholds are working values, pending review by a clinician.'**
  String get methodologyPendingReview;

  /// No description provided for @methodologySectionAllergensDescription.
  ///
  /// In en, this message translates to:
  /// **'We look for each allergen\'s ingredient names and for the pack\'s allergen statements. If the ingredients can\'t be read, we say the label is unclear, never OK.'**
  String get methodologySectionAllergensDescription;

  /// No description provided for @methodologySectionAllergensTitle.
  ///
  /// In en, this message translates to:
  /// **'Allergens'**
  String get methodologySectionAllergensTitle;

  /// No description provided for @methodologySectionBloodSugarDescription.
  ///
  /// In en, this message translates to:
  /// **'For members managing blood sugar (diabetes, prediabetes or PCOS), we flag products with a lot of sugar, or a lot of carbohydrate per serving, and high salt or saturated fat.'**
  String get methodologySectionBloodSugarDescription;

  /// No description provided for @methodologySectionBloodSugarTitle.
  ///
  /// In en, this message translates to:
  /// **'Blood sugar'**
  String get methodologySectionBloodSugarTitle;

  /// No description provided for @methodologySectionChildDescription.
  ///
  /// In en, this message translates to:
  /// **'For children, we compare the sugar in 100 g or one serving with a daily sugar limit for their age.'**
  String get methodologySectionChildDescription;

  /// No description provided for @methodologySectionChildTitle.
  ///
  /// In en, this message translates to:
  /// **'Children'**
  String get methodologySectionChildTitle;

  /// No description provided for @methodologySectionClaimsDescription.
  ///
  /// In en, this message translates to:
  /// **'We check claims such as \"sugar free\" or \"high protein\" against the label values and the FSSAI limits.'**
  String get methodologySectionClaimsDescription;

  /// No description provided for @methodologySectionClaimsTitle.
  ///
  /// In en, this message translates to:
  /// **'Front-of-pack claims'**
  String get methodologySectionClaimsTitle;

  /// No description provided for @methodologySectionCustomAlertsDescription.
  ///
  /// In en, this message translates to:
  /// **'Ingredients a member asked to be told about, such as palm oil or maida. These are preferences, so there is no source to cite.'**
  String get methodologySectionCustomAlertsDescription;

  /// No description provided for @methodologySectionCustomAlertsTitle.
  ///
  /// In en, this message translates to:
  /// **'Your ingredient alerts'**
  String get methodologySectionCustomAlertsTitle;

  /// No description provided for @methodologySectionDailyLimitsDescription.
  ///
  /// In en, this message translates to:
  /// **'In the food log, we add up the sugar and salt logged for each member in a day and compare the totals with a daily limit for their age. Protein is shown as progress towards a daily target. Labels give total sugar, not only added sugar, so this can warn more than needed.'**
  String get methodologySectionDailyLimitsDescription;

  /// No description provided for @methodologySectionDailyLimitsTitle.
  ///
  /// In en, this message translates to:
  /// **'Daily limits'**
  String get methodologySectionDailyLimitsTitle;

  /// No description provided for @methodologySectionDietDescription.
  ///
  /// In en, this message translates to:
  /// **'We look for ingredients that don\'t fit a member\'s diet (vegetarian, eggetarian, vegan or Jain) and check the green or brown mark on the pack.'**
  String get methodologySectionDietDescription;

  /// No description provided for @methodologySectionDietTitle.
  ///
  /// In en, this message translates to:
  /// **'Diet'**
  String get methodologySectionDietTitle;

  /// No description provided for @methodologySectionHighInDescription.
  ///
  /// In en, this message translates to:
  /// **'A product is marked high in a nutrient when its amount per 100 g or 100 ml is at or above these limits.'**
  String get methodologySectionHighInDescription;

  /// No description provided for @methodologySectionHighInTitle.
  ///
  /// In en, this message translates to:
  /// **'High in sugar, fat, saturated fat or salt'**
  String get methodologySectionHighInTitle;

  /// No description provided for @methodologySectionHypertensionDescription.
  ///
  /// In en, this message translates to:
  /// **'For members with high blood pressure, we flag products with a lot of salt.'**
  String get methodologySectionHypertensionDescription;

  /// No description provided for @methodologySectionHypertensionTitle.
  ///
  /// In en, this message translates to:
  /// **'Blood pressure'**
  String get methodologySectionHypertensionTitle;

  /// No description provided for @methodologySectionInfantDescription.
  ///
  /// In en, this message translates to:
  /// **'For babies and toddlers, we flag added sugar, added salt, honey and caffeine, and high sugar or salt.'**
  String get methodologySectionInfantDescription;

  /// No description provided for @methodologySectionInfantTitle.
  ///
  /// In en, this message translates to:
  /// **'Babies and toddlers'**
  String get methodologySectionInfantTitle;

  /// No description provided for @methodologySectionNutriscore2023Description.
  ///
  /// In en, this message translates to:
  /// **'We calculate a Nutri-Score grade from the label, using the 2023 update of the method. It is calculated by SmartNutri; it is not an FSSAI rating.'**
  String get methodologySectionNutriscore2023Description;

  /// No description provided for @methodologySectionNutriscore2023Title.
  ///
  /// In en, this message translates to:
  /// **'Nutri-Score (calculated by SmartNutri)'**
  String get methodologySectionNutriscore2023Title;

  /// No description provided for @methodologySectionWeightLossDescription.
  ///
  /// In en, this message translates to:
  /// **'For members losing weight, we flag energy-dense products and low Nutri-Score grades, and note products with good protein for their calories.'**
  String get methodologySectionWeightLossDescription;

  /// No description provided for @methodologySectionWeightLossTitle.
  ///
  /// In en, this message translates to:
  /// **'Weight loss'**
  String get methodologySectionWeightLossTitle;

  /// No description provided for @methodologySourcesTitle.
  ///
  /// In en, this message translates to:
  /// **'Sources'**
  String get methodologySourcesTitle;

  /// No description provided for @methodologyTitle.
  ///
  /// In en, this message translates to:
  /// **'How we score'**
  String get methodologyTitle;

  /// No description provided for @methodologyUrlUnverified.
  ///
  /// In en, this message translates to:
  /// **'Link not yet checked'**
  String get methodologyUrlUnverified;

  /// No description provided for @methodologyVersion.
  ///
  /// In en, this message translates to:
  /// **'Rules version {version}'**
  String methodologyVersion(String version);

  /// No description provided for @navFamily.
  ///
  /// In en, this message translates to:
  /// **'Family'**
  String get navFamily;

  /// No description provided for @navHistory.
  ///
  /// In en, this message translates to:
  /// **'History'**
  String get navHistory;

  /// No description provided for @navHome.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get navHome;

  /// No description provided for @navLabel.
  ///
  /// In en, this message translates to:
  /// **'Main navigation'**
  String get navLabel;

  /// No description provided for @navProfile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get navProfile;

  /// No description provided for @navScan.
  ///
  /// In en, this message translates to:
  /// **'Scan'**
  String get navScan;

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

  /// No description provided for @productNotFoundBody.
  ///
  /// In en, this message translates to:
  /// **'Check the barcode number. You can also sign in and photograph the label to add this product.'**
  String get productNotFoundBody;

  /// No description provided for @productPublicCta.
  ///
  /// In en, this message translates to:
  /// **'Check it for your family'**
  String get productPublicCta;

  /// No description provided for @profileBody.
  ///
  /// In en, this message translates to:
  /// **'Your account, language and privacy settings will be here.'**
  String get profileBody;

  /// No description provided for @profileComingSoonBody.
  ///
  /// In en, this message translates to:
  /// **'Language, privacy and account settings will appear here.'**
  String get profileComingSoonBody;

  /// No description provided for @profileComingSoonTitle.
  ///
  /// In en, this message translates to:
  /// **'Settings are coming soon'**
  String get profileComingSoonTitle;

  /// No description provided for @profileGiveConsent.
  ///
  /// In en, this message translates to:
  /// **'Agree'**
  String get profileGiveConsent;

  /// No description provided for @profilePrivacyTitle.
  ///
  /// In en, this message translates to:
  /// **'Privacy and consent'**
  String get profilePrivacyTitle;

  /// No description provided for @profileTitle.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profileTitle;

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
  /// **'We can only search the label for the exact word \"{allergen}\". Check the ingredients yourself.'**
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

  /// No description provided for @reasonCustomAlert.
  ///
  /// In en, this message translates to:
  /// **'Contains {alert}: {ingredients}.'**
  String reasonCustomAlert(String alert, String ingredients);

  /// No description provided for @reasonCustomAlertUnknown.
  ///
  /// In en, this message translates to:
  /// **'These alerts couldn\'t be checked: {alerts}.'**
  String reasonCustomAlertUnknown(String alerts);

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

  /// No description provided for @reasonVariantCustomAlertFlagOnly.
  ///
  /// In en, this message translates to:
  /// **'The product data says it contains sweeteners.'**
  String get reasonVariantCustomAlertFlagOnly;

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

  /// No description provided for @reportButton.
  ///
  /// In en, this message translates to:
  /// **'Report a problem'**
  String get reportButton;

  /// No description provided for @reportNoteLabel.
  ///
  /// In en, this message translates to:
  /// **'Tell us more (optional)'**
  String get reportNoteLabel;

  /// No description provided for @reportReasonOther.
  ///
  /// In en, this message translates to:
  /// **'Something else'**
  String get reportReasonOther;

  /// No description provided for @reportReasonWrongIngredients.
  ///
  /// In en, this message translates to:
  /// **'The ingredients are wrong'**
  String get reportReasonWrongIngredients;

  /// No description provided for @reportReasonWrongProduct.
  ///
  /// In en, this message translates to:
  /// **'This is a different product'**
  String get reportReasonWrongProduct;

  /// No description provided for @reportReasonWrongValues.
  ///
  /// In en, this message translates to:
  /// **'The nutrition values are wrong'**
  String get reportReasonWrongValues;

  /// No description provided for @reportSubmit.
  ///
  /// In en, this message translates to:
  /// **'Send report'**
  String get reportSubmit;

  /// No description provided for @reportThanks.
  ///
  /// In en, this message translates to:
  /// **'Thanks. We\'ll review this product\'s data.'**
  String get reportThanks;

  /// No description provided for @reportTitle.
  ///
  /// In en, this message translates to:
  /// **'What\'s wrong with this product\'s data?'**
  String get reportTitle;

  /// No description provided for @resultFamilyTitle.
  ///
  /// In en, this message translates to:
  /// **'For your family'**
  String get resultFamilyTitle;

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

  /// No description provided for @resultMembersTitle.
  ///
  /// In en, this message translates to:
  /// **'For your family'**
  String get resultMembersTitle;

  /// No description provided for @resultNoIngredients.
  ///
  /// In en, this message translates to:
  /// **'Ingredients not available'**
  String get resultNoIngredients;

  /// No description provided for @resultNotOnLabel.
  ///
  /// In en, this message translates to:
  /// **'Not on the label'**
  String get resultNotOnLabel;

  /// No description provided for @resultNutritionTitle.
  ///
  /// In en, this message translates to:
  /// **'Nutrition per 100 g/ml'**
  String get resultNutritionTitle;

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

  /// No description provided for @scanLabelHint.
  ///
  /// In en, this message translates to:
  /// **'No barcode? Photograph the label instead.'**
  String get scanLabelHint;

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

  /// No description provided for @scanSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Point your camera at the barcode, or type the number below.'**
  String get scanSubtitle;

  /// No description provided for @scanTitle.
  ///
  /// In en, this message translates to:
  /// **'Scan a barcode'**
  String get scanTitle;

  /// No description provided for @searchNoResults.
  ///
  /// In en, this message translates to:
  /// **'No products found.'**
  String get searchNoResults;

  /// No description provided for @searchPlaceholder.
  ///
  /// In en, this message translates to:
  /// **'Search by name or brand'**
  String get searchPlaceholder;

  /// No description provided for @searchSourceOff.
  ///
  /// In en, this message translates to:
  /// **'Open Food Facts'**
  String get searchSourceOff;

  /// No description provided for @searchSourceOurs.
  ///
  /// In en, this message translates to:
  /// **'SmartNutri'**
  String get searchSourceOurs;

  /// No description provided for @searchTitle.
  ///
  /// In en, this message translates to:
  /// **'Search products'**
  String get searchTitle;

  /// No description provided for @searchTooShort.
  ///
  /// In en, this message translates to:
  /// **'Type at least 2 letters.'**
  String get searchTooShort;

  /// No description provided for @shareButton.
  ///
  /// In en, this message translates to:
  /// **'Share'**
  String get shareButton;

  /// No description provided for @shareCopied.
  ///
  /// In en, this message translates to:
  /// **'Link copied'**
  String get shareCopied;

  /// No description provided for @shareCopyLink.
  ///
  /// In en, this message translates to:
  /// **'Copy link'**
  String get shareCopyLink;

  /// No description provided for @sharePrivacyNote.
  ///
  /// In en, this message translates to:
  /// **'Only the product, its grade and each person\'s result are shared. Health details stay private.'**
  String get sharePrivacyNote;

  /// No description provided for @shareRelationChild.
  ///
  /// In en, this message translates to:
  /// **'Child'**
  String get shareRelationChild;

  /// No description provided for @shareRelationOther.
  ///
  /// In en, this message translates to:
  /// **'Family member'**
  String get shareRelationOther;

  /// No description provided for @shareRelationParent.
  ///
  /// In en, this message translates to:
  /// **'Parent'**
  String get shareRelationParent;

  /// No description provided for @shareRelationSelf.
  ///
  /// In en, this message translates to:
  /// **'Me'**
  String get shareRelationSelf;

  /// No description provided for @shareRelationSpouse.
  ///
  /// In en, this message translates to:
  /// **'Spouse'**
  String get shareRelationSpouse;

  /// No description provided for @shareResultMember.
  ///
  /// In en, this message translates to:
  /// **'{who}: {status}'**
  String shareResultMember(String status, String who);

  /// No description provided for @shareResultText.
  ///
  /// In en, this message translates to:
  /// **'{product} — Nutri-Score {grade} (calculated by SmartNutri). {members}. Checked with SmartNutri: {url}'**
  String shareResultText(
    String grade,
    String members,
    String product,
    String url,
  );

  /// No description provided for @shareResultUngraded.
  ///
  /// In en, this message translates to:
  /// **'{product} — not enough label data for a Nutri-Score. {members}. Checked with SmartNutri: {url}'**
  String shareResultUngraded(String members, String product, String url);

  /// No description provided for @shareWeekly.
  ///
  /// In en, this message translates to:
  /// **'Our week on SmartNutri — products checked: {scans}, items logged: {logged}. {url}'**
  String shareWeekly(String logged, String scans, String url);

  /// No description provided for @shareWeeklyButton.
  ///
  /// In en, this message translates to:
  /// **'Share our week'**
  String get shareWeeklyButton;

  /// No description provided for @shareWhatsapp.
  ///
  /// In en, this message translates to:
  /// **'Share on WhatsApp'**
  String get shareWhatsapp;

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

  /// No description provided for @summaryBandNear.
  ///
  /// In en, this message translates to:
  /// **'Close to limit'**
  String get summaryBandNear;

  /// No description provided for @summaryBandOk.
  ///
  /// In en, this message translates to:
  /// **'Within limit'**
  String get summaryBandOk;

  /// No description provided for @summaryBandOver.
  ///
  /// In en, this message translates to:
  /// **'Over limit'**
  String get summaryBandOver;

  /// No description provided for @summaryBandUnknown.
  ///
  /// In en, this message translates to:
  /// **'Not enough data'**
  String get summaryBandUnknown;

  /// No description provided for @summaryIncomplete.
  ///
  /// In en, this message translates to:
  /// **'Some logged items do not show this value on the label, so the real total may be higher.'**
  String get summaryIncomplete;

  /// No description provided for @summaryKcalInfo.
  ///
  /// In en, this message translates to:
  /// **'Calories are shown for information. There is no personal calorie target yet.'**
  String get summaryKcalInfo;

  /// No description provided for @summaryKcalTotal.
  ///
  /// In en, this message translates to:
  /// **'{total} kcal'**
  String summaryKcalTotal(String total);

  /// No description provided for @summaryLimitsNote.
  ///
  /// In en, this message translates to:
  /// **'Limits pending clinician review.'**
  String get summaryLimitsNote;

  /// No description provided for @summaryNoProteinTarget.
  ///
  /// In en, this message translates to:
  /// **'Add weight to the profile to see a protein target.'**
  String get summaryNoProteinTarget;

  /// No description provided for @summaryNothingLogged.
  ///
  /// In en, this message translates to:
  /// **'Nothing logged on this day.'**
  String get summaryNothingLogged;

  /// No description provided for @summaryNutrientEnergyKcal.
  ///
  /// In en, this message translates to:
  /// **'Calories'**
  String get summaryNutrientEnergyKcal;

  /// No description provided for @summaryNutrientProteinG.
  ///
  /// In en, this message translates to:
  /// **'Protein'**
  String get summaryNutrientProteinG;

  /// No description provided for @summaryNutrientSaltG.
  ///
  /// In en, this message translates to:
  /// **'Salt'**
  String get summaryNutrientSaltG;

  /// No description provided for @summaryNutrientSugarsG.
  ///
  /// In en, this message translates to:
  /// **'Sugars'**
  String get summaryNutrientSugarsG;

  /// No description provided for @summaryProteinOfTarget.
  ///
  /// In en, this message translates to:
  /// **'{total} g of a {target} g target'**
  String summaryProteinOfTarget(String target, String total);

  /// No description provided for @summarySugarNote.
  ///
  /// In en, this message translates to:
  /// **'Labels show total sugars, including natural sugars, so this total may be higher than added sugar alone.'**
  String get summarySugarNote;

  /// No description provided for @summaryTitleDay.
  ///
  /// In en, this message translates to:
  /// **'Today'**
  String get summaryTitleDay;

  /// No description provided for @summaryTitleWeek.
  ///
  /// In en, this message translates to:
  /// **'Last 7 days'**
  String get summaryTitleWeek;

  /// No description provided for @summaryTotalG.
  ///
  /// In en, this message translates to:
  /// **'{total} g'**
  String summaryTotalG(String total);

  /// No description provided for @summaryTotalOfLimit.
  ///
  /// In en, this message translates to:
  /// **'{total} g of {limit} g'**
  String summaryTotalOfLimit(String limit, String total);

  /// No description provided for @summaryWeekNote.
  ///
  /// In en, this message translates to:
  /// **'The week is compared with the daily limit for each day something was logged.'**
  String get summaryWeekNote;

  /// No description provided for @verdictConfidenceNote.
  ///
  /// In en, this message translates to:
  /// **'{reason, select, low_confidence {The label was hard to read, so this result is less certain.} other {Some data is uncertain.}}'**
  String verdictConfidenceNote(String reason);

  /// No description provided for @verdictForMember.
  ///
  /// In en, this message translates to:
  /// **'{status} for {name}'**
  String verdictForMember(String name, String status);

  /// No description provided for @verdictForYou.
  ///
  /// In en, this message translates to:
  /// **'{status} for you'**
  String verdictForYou(String status);

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

  /// No description provided for @verdictSpokenAvoid.
  ///
  /// In en, this message translates to:
  /// **'For this member, avoid this product.'**
  String get verdictSpokenAvoid;

  /// No description provided for @verdictSpokenCaution.
  ///
  /// In en, this message translates to:
  /// **'For this member, take care with this product.'**
  String get verdictSpokenCaution;

  /// No description provided for @verdictSpokenOk.
  ///
  /// In en, this message translates to:
  /// **'For this member, this product looks OK.'**
  String get verdictSpokenOk;

  /// No description provided for @verdictSpokenUnknown.
  ///
  /// In en, this message translates to:
  /// **'For this member, the label is unclear, so we can\'t say.'**
  String get verdictSpokenUnknown;

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

  /// No description provided for @voiceAiUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Voice answers are unavailable right now. Please try again later.'**
  String get voiceAiUnavailable;

  /// No description provided for @voiceButtonHold.
  ///
  /// In en, this message translates to:
  /// **'Hold to ask'**
  String get voiceButtonHold;

  /// No description provided for @voiceMicDenied.
  ///
  /// In en, this message translates to:
  /// **'Microphone access is off. Allow it in your settings to ask by voice.'**
  String get voiceMicDenied;

  /// No description provided for @voiceNotUnderstood.
  ///
  /// In en, this message translates to:
  /// **'We couldn\'t hear a question. Hold the button and speak clearly.'**
  String get voiceNotUnderstood;

  /// No description provided for @voicePlaying.
  ///
  /// In en, this message translates to:
  /// **'Playing the answer'**
  String get voicePlaying;

  /// No description provided for @voiceRateLimited.
  ///
  /// In en, this message translates to:
  /// **'You\'ve reached today\'s voice-question limit.'**
  String get voiceRateLimited;

  /// No description provided for @voiceRecording.
  ///
  /// In en, this message translates to:
  /// **'Listening… release to send'**
  String get voiceRecording;

  /// No description provided for @voiceThinking.
  ///
  /// In en, this message translates to:
  /// **'Getting your answer…'**
  String get voiceThinking;

  /// No description provided for @voiceTooLong.
  ///
  /// In en, this message translates to:
  /// **'Please keep your question under 30 seconds.'**
  String get voiceTooLong;

  /// No description provided for @voiceUnsupportedBrowser.
  ///
  /// In en, this message translates to:
  /// **'Voice questions don\'t work in this browser. Try the latest Chrome, Edge or Firefox.'**
  String get voiceUnsupportedBrowser;

  /// No description provided for @voiceWordSafe.
  ///
  /// In en, this message translates to:
  /// **'safe'**
  String get voiceWordSafe;

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
