// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Marathi (`mr`).
class AppLocalizationsMr extends AppLocalizations {
  AppLocalizationsMr([String locale = 'mr']) : super(locale);

  @override
  String get allergenCrustacean => 'शेलफिश (कोळंबी, खेकडा इ.)';

  @override
  String get allergenEgg => 'अंडे';

  @override
  String get allergenFish => 'मासे';

  @override
  String get allergenGluten => 'ग्लूटेन';

  @override
  String get allergenMilk => 'दूध';

  @override
  String get allergenMustard => 'मोहरी';

  @override
  String get allergenPeanut => 'शेंगदाणे';

  @override
  String get allergenSesame => 'तीळ';

  @override
  String get allergenSoy => 'सोया';

  @override
  String get allergenSulphite => 'सल्फाइट';

  @override
  String get allergenTreeNut => 'सुकामेवा (ट्री नट्स)';

  @override
  String get appName => 'SmartNutri AI';

  @override
  String get authCodeLabel => '6 अंकी कोड';

  @override
  String get authEmail => 'ईमेलसह पुढे जा';

  @override
  String get authEmailLabel => 'ईमेल पत्ता';

  @override
  String get authGoogle => 'Google सह पुढे जा';

  @override
  String get authPhone => 'फोनसह पुढे जा';

  @override
  String get authSendCode => 'कोड पाठवा';

  @override
  String get authSignOut => 'साइन आउट करा';

  @override
  String get authTitle => 'साइन इन करा';

  @override
  String get authVerify => 'पडताळा';

  @override
  String get claimDiabeticFriendly => 'डायबेटिसला अनुकूल';

  @override
  String get claimHighProtein => 'जास्त प्रथिने';

  @override
  String get claimLowFat => 'कमी फॅट';

  @override
  String get claimLowSodium => 'कमी सोडियम';

  @override
  String get claimLowSugar => 'कमी साखर';

  @override
  String get claimNoAddedSugar => 'वरून साखर घातलेली नाही';

  @override
  String get claimNoRefinedSugar => 'रिफाइंड साखर नाही';

  @override
  String claimReasonAddedSugarIngredient(String ingredients) {
    return 'घटकांमध्ये वरून घातलेली साखर आहे: $ingredients.';
  }

  @override
  String claimReasonBelowMinimum(String limit, String value) {
    return '$value हे या दाव्याच्या किमान $limit पेक्षा कमी आहे.';
  }

  @override
  String claimReasonExceedsLimit(String limit, String value) {
    return '$value हे या दाव्याच्या $limit मर्यादेपेक्षा जास्त आहे.';
  }

  @override
  String get claimReasonIngredientsUnknown =>
      'घटकांची यादी उपलब्ध नाही, त्यामुळे हा दावा तपासता येत नाही.';

  @override
  String claimReasonNoStandard(String claim) {
    return '\"$claim\" तपासण्यासाठी आमच्याकडे कोणतेही मानक नाही.';
  }

  @override
  String claimReasonNutrientMissing(String nutrient) {
    return 'लेबलवर $nutrient दिलेले नाही, त्यामुळे हा दावा तपासता येत नाही.';
  }

  @override
  String get claimReasonOk => 'लेबलवरील माहिती या दाव्याशी जुळते.';

  @override
  String claimReasonRefinedSugarIngredient(String ingredients) {
    return 'घटकांमध्ये रिफाइंड साखर आहे: $ingredients.';
  }

  @override
  String get claimSourceOfProtein => 'प्रथिनांचा स्रोत';

  @override
  String get claimSugarFree => 'साखरमुक्त';

  @override
  String get claimVerdictContradicted =>
      'लेबलवरील माहिती या दाव्याशी जुळत नाही';

  @override
  String get claimVerdictSupported => 'लेबलवरील माहिती या दाव्याला पुष्टी देते';

  @override
  String get claimVerdictUnverifiable => 'लेबलवरून तपासता येत नाही';

  @override
  String get commonDisclaimer => 'ही माहिती आहे, वैद्यकीय सल्ला नाही.';

  @override
  String get commonLoading => 'लोड होत आहे…';

  @override
  String get commonRetry => 'पुन्हा प्रयत्न करा';

  @override
  String get conditionDiabetes => 'मधुमेह (डायबेटिस)';

  @override
  String get conditionHypertension => 'उच्च रक्तदाब';

  @override
  String get conditionPcos => 'पीसीओएस';

  @override
  String get conditionPrediabetes => 'प्रीडायबेटिस';

  @override
  String get conditionWeightLoss => 'वजन कमी करणे';

  @override
  String get dietEggetarian => 'अंडाहारी (अंडे खाणारा शाकाहारी)';

  @override
  String get dietJain => 'जैन';

  @override
  String get dietNonVeg => 'मांसाहारी';

  @override
  String get dietVeg => 'शाकाहारी';

  @override
  String get dietVegan => 'व्हेगन';

  @override
  String get errorAuthInvalid =>
      'तुमचे सत्र संपले आहे. कृपया पुन्हा साइन इन करा.';

  @override
  String get errorAuthRequired => 'कृपया साइन इन करा.';

  @override
  String get errorInternalError => 'काहीतरी चुकले. कृपया पुन्हा प्रयत्न करा.';

  @override
  String get errorNetwork => 'इंटरनेट कनेक्शन नाही.';

  @override
  String get errorNotFound => 'सापडले नाही.';

  @override
  String get errorRateLimited => 'खूप जास्त विनंत्या. कृपया थोडा वेळ थांबा.';

  @override
  String get errorRateLimitedScans =>
      'तुम्ही आजच्या लेबल-स्कॅन मर्यादेपर्यंत पोहोचला आहात.';

  @override
  String get errorRateLimitedVoice =>
      'तुम्ही आजच्या आवाजाद्वारे प्रश्न विचारण्याच्या मर्यादेपर्यंत पोहोचला आहात.';

  @override
  String get errorValidationError => 'कृपया अधोरेखित केलेली फील्ड तपासा.';

  @override
  String get highInFat => 'फॅट जास्त';

  @override
  String highInPercentOfLimit(String pct) {
    return 'मर्यादेच्या $pct%';
  }

  @override
  String get highInSalt => 'मीठ जास्त';

  @override
  String get highInSatFat => 'संतृप्त फॅट जास्त';

  @override
  String get highInSugar => 'साखर जास्त';

  @override
  String homeWelcome(String name) {
    return 'नमस्कार, $name';
  }

  @override
  String get nutriscoreCalculatedBy =>
      'Nutri-Score ची गणना SmartNutri ने केली आहे';

  @override
  String get nutriscoreInsufficientData =>
      'Nutri-Score काढण्यासाठी लेबलवर पुरेशी माहिती नाही.';

  @override
  String reasonAddedSugars(String ingredients) {
    return 'यात वरून घातलेली साखर आहे: $ingredients.';
  }

  @override
  String reasonAllergenContains(String allergen) {
    return 'यात $allergen आहे, जे तुमच्या टाळण्याच्या यादीत आहे.';
  }

  @override
  String reasonAllergenMayContain(String allergen) {
    return 'यात $allergen असू शकते, जे तुमच्या टाळण्याच्या यादीत आहे.';
  }

  @override
  String reasonAllergenUnknown(String allergen) {
    return 'यात $allergen आहे की नाही हे आम्ही सांगू शकत नाही.';
  }

  @override
  String reasonAllergenUnrecognised(String allergen) {
    return 'तुमच्या प्रोफाइलमधील ॲलर्जन \"$allergen\" आम्हाला ओळखता आला नाही.';
  }

  @override
  String reasonCarbsPerServingHigh(String carbs_g) {
    return 'प्रति सर्व्हिंग $carbs_g ग्रॅम कार्बोहायड्रेट. हे तुमच्या स्थितीला योग्य नसू शकते; तुमच्या डॉक्टरांना विचारा.';
  }

  @override
  String get reasonChildCaffeine =>
      'यात कॅफिन आहे, जे मुलांसाठी शिफारस केलेले नाही.';

  @override
  String reasonChildSaltHigh(String limit_g, String salt_g) {
    return 'मुलासाठी $salt_g ग्रॅम मीठ जास्त आहे (मार्गदर्शक मर्यादा: सुमारे $limit_g ग्रॅम).';
  }

  @override
  String reasonChildSugarHigh(String limit_g, String sugars_g) {
    return 'मुलासाठी $sugars_g ग्रॅम साखर जास्त आहे (मार्गदर्शक मर्यादा: सुमारे $limit_g ग्रॅम).';
  }

  @override
  String reasonChildSugarModerate(String limit_g, String sugars_g) {
    return 'मुलासाठी $sugars_g ग्रॅम साखर थोडी जास्त आहे (मार्गदर्शक मर्यादा: सुमारे $limit_g ग्रॅम).';
  }

  @override
  String reasonConditionUnrecognised(String condition) {
    return '\"$condition\" साठी आमच्याकडे अद्याप मार्गदर्शन उपलब्ध नाही.';
  }

  @override
  String reasonDietUnknown(String diet) {
    return 'हे $diet आहाराला अनुकूल आहे की नाही हे आम्ही सांगू शकत नाही.';
  }

  @override
  String reasonDietViolation(String diet, String ingredients) {
    return 'हे $diet आहाराशी जुळणार नाही असे असू शकते: $ingredients.';
  }

  @override
  String get reasonEnergyDense =>
      'हा ऊर्जेने भरपूर (जास्त कॅलरीचा) पदार्थ आहे. कमी प्रमाणात घेणे चांगले.';

  @override
  String get reasonGoodProteinDensity =>
      'कॅलरींच्या तुलनेत प्रथिने चांगल्या प्रमाणात आहेत.';

  @override
  String reasonHiddenSugars(String ingredients) {
    return 'यात इतर नावांनी लिहिलेल्या शर्करा आहेत: $ingredients.';
  }

  @override
  String get reasonInfantAddedSalt =>
      'यात वरून घातलेले मीठ आहे, जे लहान बाळांसाठी शिफारस केलेले नाही.';

  @override
  String get reasonInfantAddedSugar =>
      'यात वरून घातलेली साखर आहे, जी लहान बाळांसाठी शिफारस केलेली नाही.';

  @override
  String get reasonInfantCaffeine =>
      'यात कॅफिन आहे, जे लहान बाळांसाठी शिफारस केलेले नाही.';

  @override
  String get reasonInfantHoney =>
      'यात मध आहे, जो 12 महिन्यांपेक्षा लहान बाळांना देऊ नये.';

  @override
  String reasonInfantSaltHigh(String salt_g) {
    return 'लहान बाळासाठी $salt_g ग्रॅम मीठ जास्त आहे.';
  }

  @override
  String reasonInfantSugarHigh(String sugars_g) {
    return 'लहान बाळासाठी $sugars_g ग्रॅम साखर जास्त आहे.';
  }

  @override
  String get reasonIngredientsMissing =>
      'घटकांची यादी वाचता आली नाही, त्यामुळे काही तपासण्या करता आल्या नाहीत.';

  @override
  String reasonMisleadingSugarClaim(String ingredients, String mark) {
    return 'पॅकवर \"$mark\" असे लिहिले आहे, पण घटकांमध्ये साखर आहे: $ingredients.';
  }

  @override
  String reasonNutrientMissing(String nutrient) {
    return 'लेबलवर $nutrient दिलेले नाही, त्यामुळे ही तपासणी करता आली नाही.';
  }

  @override
  String reasonNutriscoreLow(String grade) {
    return 'Nutri-Score $grade एकूण पोषण दर्जा कमी असल्याचे सूचित करतो.';
  }

  @override
  String reasonSaltHigh(String basis, String salt_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्व्हिंग',
      'other': 'प्रति 100 ग्रॅम',
    });
    return 'मीठ जास्त आहे: $salt_g ग्रॅम $_temp0.';
  }

  @override
  String reasonSaltModerate(String basis, String salt_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्व्हिंग',
      'other': 'प्रति 100 ग्रॅम',
    });
    return 'मीठ मध्यम आहे: $salt_g ग्रॅम $_temp0.';
  }

  @override
  String reasonSodiumAdditives(String ingredients) {
    return 'यात सोडियमयुक्त पदार्थ (ॲडिटिव्ह) आहेत: $ingredients.';
  }

  @override
  String reasonSugarHigh(String basis, String sugars_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्व्हिंग',
      'other': 'प्रति 100 ग्रॅम',
    });
    return 'साखर जास्त आहे: $sugars_g ग्रॅम $_temp0.';
  }

  @override
  String reasonSugarModerate(String basis, String sugars_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्व्हिंग',
      'other': 'प्रति 100 ग्रॅम',
    });
    return 'साखर मध्यम आहे: $sugars_g ग्रॅम $_temp0.';
  }

  @override
  String get statusAvoid => 'टाळा';

  @override
  String get statusCaution => 'सावधगिरी';

  @override
  String get statusOk => 'ठीक आहे';

  @override
  String get statusUnknown => 'लेबल स्पष्ट नाही';

  @override
  String verdictConfidenceNote(String reason) {
    String _temp0 = intl.Intl.selectLogic(reason, {
      'low_confidence':
          'लेबल वाचणे कठीण होते, त्यामुळे हा निकाल कमी निश्चित आहे.',
      'other': 'काही माहिती अनिश्चित आहे.',
    });
    return '$_temp0';
  }

  @override
  String verdictRuleApplied(String rule) {
    return 'लागू केलेला नियम: $rule';
  }

  @override
  String get verdictStatusAvoid => 'टाळा';

  @override
  String get verdictStatusCaution => 'सावधगिरी';

  @override
  String get verdictStatusOk => 'ठीक आहे';

  @override
  String get verdictStatusUnknown => 'लेबल स्पष्ट नाही';
}
