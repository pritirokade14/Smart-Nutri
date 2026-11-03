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
  String get allergenTreeNut => 'ट्री नट्स (बदाम, काजू, अक्रोड इ.)';

  @override
  String get appName => 'SmartNutri AI';

  @override
  String get attributionOff => 'डेटा: Open Food Facts (ODbL)';

  @override
  String get authChange => 'बदला';

  @override
  String get authCodeLabel => '6 अंकी कोड';

  @override
  String get authEmail => 'ईमेलसह पुढे जा';

  @override
  String get authEmailLabel => 'ईमेल पत्ता';

  @override
  String get authError => 'साइन इन करता आले नाही. कृपया पुन्हा प्रयत्न करा.';

  @override
  String get authGoogle => 'Google सह पुढे जा';

  @override
  String get authPhone => 'फोनसह पुढे जा';

  @override
  String get authPhoneLabel => 'फोन नंबर (देश कोडसह)';

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
    return 'प्रथिनांमधून $value% ऊर्जा मिळते, जी या दाव्यासाठी आवश्यक $limit% पेक्षा कमी आहे.';
  }

  @override
  String claimReasonExceedsLimit(String limit, String value) {
    return 'लेबलवर प्रति 100 ग्रॅम/मि.ली. $value आहे, जे या दाव्याच्या $limit मर्यादेपेक्षा जास्त आहे.';
  }

  @override
  String get claimReasonIngredientsUnknown =>
      'घटकांची यादी उपलब्ध नाही, त्यामुळे हा दावा तपासता येत नाही.';

  @override
  String get claimReasonNoStandard =>
      'हा दावा तपासण्यासाठी आमच्याकडे कोणतेही मानक नाही.';

  @override
  String claimReasonNutrientMissing(String nutrient) {
    return 'लेबलवर $nutrient ची माहिती नाही, त्यामुळे हा दावा तपासता येत नाही.';
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
  String get errorExtractionFailed =>
      'आम्हाला हे लेबल वाचता आले नाही. दुसरा फोटो वापरून पाहा किंवा माहिती स्वतः भरा.';

  @override
  String get errorExtractionUnavailable =>
      'लेबल वाचण्याची सुविधा सध्या उपलब्ध नाही. नंतर पुन्हा प्रयत्न करा किंवा माहिती स्वतः भरा.';

  @override
  String get errorForbidden => 'तुम्हाला याचा प्रवेश नाही.';

  @override
  String get errorHttpError => 'काहीतरी चुकले. कृपया पुन्हा प्रयत्न करा.';

  @override
  String get errorImageTooLarge =>
      'हा फोटो खूप मोठा आहे. कृपया 8 MB पेक्षा लहान फोटो वापरा.';

  @override
  String get errorImplausibleValue =>
      'काही मूल्ये बरोबर वाटत नाहीत. कृपया चिन्हांकित फील्ड तपासा, किंवा ती रिकामी सोडा.';

  @override
  String get errorInternalError => 'काहीतरी चुकले. कृपया पुन्हा प्रयत्न करा.';

  @override
  String get errorInvalidBarcode => 'हा योग्य बारकोड वाटत नाही.';

  @override
  String get errorInvalidProductRef => 'तपासण्यासाठी एक उत्पादन निवडा.';

  @override
  String get errorMemberNotFound => 'कुटुंबातील हा सदस्य सापडला नाही.';

  @override
  String get errorMethodNotAllowed =>
      'ही क्रिया समर्थित नाही. कृपया ॲप अपडेट करा.';

  @override
  String get errorNetwork => 'इंटरनेट कनेक्शन नाही.';

  @override
  String get errorNotFound => 'सापडले नाही.';

  @override
  String get errorOffUnavailable =>
      'उत्पादन डेटाबेस सध्या व्यस्त आहे. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.';

  @override
  String get errorProductExists => 'हे उत्पादन आधीच जतन केले आहे.';

  @override
  String get errorProductNotFound => 'हे उत्पादन आम्हाला अजून सापडले नाही.';

  @override
  String get errorRateLimited => 'खूप जास्त विनंत्या. कृपया थोडा वेळ थांबा.';

  @override
  String get errorRateLimitedScans =>
      'तुम्ही आजच्या लेबल-स्कॅन मर्यादेपर्यंत पोहोचला आहात.';

  @override
  String get errorRateLimitedVoice =>
      'तुम्ही आजच्या आवाजाद्वारे प्रश्न विचारण्याच्या मर्यादेपर्यंत पोहोचला आहात.';

  @override
  String get errorScanImageNotFound =>
      'तो फोटो आम्हाला सापडला नाही. कृपया फोटो पुन्हा काढा किंवा अपलोड करा.';

  @override
  String get errorScanNotFound =>
      'हा लेबल स्कॅन सापडला नाही. कृपया लेबल पुन्हा स्कॅन करा.';

  @override
  String get errorStorageUnavailable =>
      'आम्ही सध्या फोटो हाताळू शकलो नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.';

  @override
  String get errorUnauthorized => 'कृपया साइन इन करा.';

  @override
  String get errorUnsupportedImage => 'कृपया JPEG, PNG किंवा WebP फोटो वापरा.';

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
  String get homeScanCta => 'उत्पादन स्कॅन करा';

  @override
  String homeWelcome(String name) {
    return 'नमस्कार, $name';
  }

  @override
  String get nutrientCarbsG => 'कार्बोहायड्रेट';

  @override
  String get nutrientEnergyKcal => 'ऊर्जा (कॅलरी)';

  @override
  String get nutrientFatG => 'फॅट (स्निग्ध पदार्थ)';

  @override
  String get nutrientProteinG => 'प्रथिने';

  @override
  String get nutrientSalt => 'मीठ';

  @override
  String get nutrientSatFat => 'संतृप्त फॅट';

  @override
  String get nutrientSodiumMg => 'सोडियम';

  @override
  String get nutrientSugarsG => 'शर्करा (साखर)';

  @override
  String get nutriscoreCalculatedBy =>
      'Nutri-Score ची गणना SmartNutri ने केली आहे';

  @override
  String get nutriscoreInsufficientData =>
      'Nutri-Score काढण्यासाठी लेबलवर पुरेशी माहिती नाही.';

  @override
  String get productClaimsHeading => 'लेबलवरील दावे, SmartNutri ने तपासलेले';

  @override
  String productLabelSays(String claim) {
    return 'लेबलवर लिहिले आहे: $claim';
  }

  @override
  String get productMetaDescription =>
      'या पॅकेटबंद अन्नपदार्थाची पोषण माहिती, SmartNutri ने मोजलेला Nutri-Score आणि घटक. माहिती, वैद्यकीय सल्ला नाही.';

  @override
  String productMetaTitle(String name) {
    return '$name – पोषण माहिती | SmartNutri';
  }

  @override
  String get productPublicCta => 'तुमच्या कुटुंबासाठी तपासा';

  @override
  String reasonAddedSugars(String ingredients) {
    return 'यात वरून घातलेली साखर आहे: $ingredients.';
  }

  @override
  String get reasonAgeUnknown =>
      'या सदस्याचे जन्मवर्ष जोडा: हा पदार्थ कदाचित लहान मुलांना किंवा बाळांना योग्य नसेल.';

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
  String reasonCarbsPerServingHigh(String basis, String carbs_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्व्हिंग',
      'other': 'प्रति 100 ग्रॅम/मि.ली.',
    });
    return '$_temp0 $carbs_g ग्रॅम कार्बोहायड्रेट. हे तुमच्या स्थितीला कदाचित योग्य नसेल; तुमच्या डॉक्टरांना विचारा.';
  }

  @override
  String reasonCardioRiskHighIn(String high_in) {
    return 'यात $high_in जास्त आहे. रक्तातील साखरेकडे लक्ष देणाऱ्या लोकांना हे मर्यादित ठेवण्याचा सल्ला अनेकदा दिला जातो; तुमच्या डॉक्टरांना विचारा.';
  }

  @override
  String get reasonChildCaffeine =>
      'यात कॅफिन आहे, जे मुलांसाठी शिफारस केलेले नाही.';

  @override
  String reasonChildSaltHigh(String salt_g) {
    return 'प्रति 100 ग्रॅम/मि.ली. $salt_g ग्रॅम मीठ मुलासाठी जास्त आहे.';
  }

  @override
  String reasonChildSugarHigh(String basis, String limit_g, String pct) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'एका सर्व्हिंगमध्ये',
      'other': '100 ग्रॅम/मि.ली. मध्ये',
    });
    return '$_temp0 मुलाच्या दैनिक साखर मर्यादेच्या (दिवसाला सुमारे $limit_g ग्रॅम) $pct% साखर आहे. हे मुलासाठी जास्त आहे.';
  }

  @override
  String reasonChildSugarModerate(String basis, String limit_g, String pct) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'एका सर्व्हिंगमध्ये',
      'other': '100 ग्रॅम/मि.ली. मध्ये',
    });
    return '$_temp0 मुलाच्या दैनिक साखर मर्यादेच्या (दिवसाला सुमारे $limit_g ग्रॅम) $pct% साखर आहे. हे मुलासाठी थोडे जास्त आहे.';
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
    return 'हे कदाचित $diet आहाराशी जुळणार नाही: $ingredients.';
  }

  @override
  String reasonEnergyDense(String energy_kcal) {
    return 'हा ऊर्जेने भरपूर (जास्त कॅलरीचा) पदार्थ आहे (प्रति 100 ग्रॅम/मि.ली. $energy_kcal किलोकॅलरी). कमी प्रमाणात घेण्याचा विचार करा.';
  }

  @override
  String get reasonGoodProteinDensity =>
      'कॅलरींच्या तुलनेत प्रथिने चांगल्या प्रमाणात आहेत.';

  @override
  String reasonHiddenSugars(String ingredients) {
    return 'यात इतर नावांनी लिहिलेल्या शर्करा आहेत: $ingredients.';
  }

  @override
  String get reasonInfantAddedSalt =>
      'यात वरून घातलेले मीठ आहे, जे 2 वर्षांखालील मुलांसाठी शिफारस केलेले नाही.';

  @override
  String get reasonInfantAddedSugar =>
      'यात वरून घातलेली साखर आहे, जी 2 वर्षांखालील मुलांसाठी शिफारस केलेली नाही.';

  @override
  String get reasonInfantCaffeine =>
      'यात कॅफिन आहे, जे 2 वर्षांखालील मुलांसाठी शिफारस केलेले नाही.';

  @override
  String get reasonInfantHoney =>
      'यात मध आहे, जो 1 वर्षाखालील बाळांना देऊ नये. त्याहून मोठ्या लहान मुलांसाठी तुमच्या डॉक्टरांना विचारा.';

  @override
  String reasonInfantSaltHigh(String salt_g) {
    return 'प्रति 100 ग्रॅम/मि.ली. $salt_g ग्रॅम मीठ 2 वर्षांखालील मुलासाठी जास्त आहे.';
  }

  @override
  String reasonInfantSugarHigh(String sugars_g) {
    return 'प्रति 100 ग्रॅम/मि.ली. $sugars_g ग्रॅम साखर 2 वर्षांखालील मुलासाठी जास्त आहे.';
  }

  @override
  String get reasonIngredientsMissing =>
      'घटकांची यादी वाचता आली नाही, त्यामुळे काही तपासण्या करता आल्या नाहीत.';

  @override
  String reasonMisleadingSugarClaim(String claim) {
    return 'पॅकवर \"$claim\" असे लिहिले आहे, पण लेबलवरील माहिती या दाव्याला पुष्टी देत नाही.';
  }

  @override
  String reasonNutrientMissing(String nutrient) {
    return 'लेबलवर $nutrient ची माहिती नाही, त्यामुळे ही तपासणी करता आली नाही.';
  }

  @override
  String reasonNutriscoreLow(String grade) {
    return 'Nutri-Score $grade एकूण पोषण दर्जा कमी असल्याचे सूचित करतो.';
  }

  @override
  String reasonSaltHigh(String salt_g) {
    return 'मीठ जास्त आहे: प्रति 100 ग्रॅम/मि.ली. $salt_g ग्रॅम.';
  }

  @override
  String reasonSaltModerate(String salt_g) {
    return 'मीठ मध्यम आहे: प्रति 100 ग्रॅम/मि.ली. $salt_g ग्रॅम.';
  }

  @override
  String reasonSodiumAdditives(String ingredients) {
    return 'यात सोडियमयुक्त पदार्थ (ॲडिटिव्ह) आहेत: $ingredients.';
  }

  @override
  String reasonSugarHigh(String sugars_g) {
    return 'साखर जास्त आहे: प्रति 100 ग्रॅम/मि.ली. $sugars_g ग्रॅम.';
  }

  @override
  String reasonSugarModerate(String sugars_g) {
    return 'साखर मध्यम आहे: प्रति 100 ग्रॅम/मि.ली. $sugars_g ग्रॅम.';
  }

  @override
  String reasonVariantDietViolationMarkOnly(String diet) {
    return 'पॅकवर तपकिरी रंगाची मांसाहारी खूण आहे, त्यामुळे हे कदाचित $diet आहाराशी जुळणार नाही.';
  }

  @override
  String reasonVariantNutrientMissingLowConfidence(String nutrient) {
    return 'लेबलवरील $nutrient स्पष्टपणे वाचता आले नाही, त्यामुळे ही तपासणी करता आली नाही.';
  }

  @override
  String resultForMember(String name) {
    return '$name साठी';
  }

  @override
  String resultGrade(String grade) {
    return 'न्यूट्री-स्कोअर $grade';
  }

  @override
  String get resultHighInTitle => 'यामध्ये जास्त';

  @override
  String get resultIngredients => 'घटक';

  @override
  String get resultNoIngredients => 'घटक उपलब्ध नाहीत';

  @override
  String get resultScanAnother => 'दुसरे उत्पादन स्कॅन करा';

  @override
  String get resultTitle => 'निकाल';

  @override
  String get resultYou => 'तुम्ही';

  @override
  String get scanCameraDenied =>
      'कॅमेरा परवानगी बंद आहे. तुम्ही बारकोड टाइप करू शकता.';

  @override
  String get scanCameraUnavailable =>
      'कॅमेरा सापडला नाही. तुम्ही बारकोड टाइप करू शकता.';

  @override
  String get scanInvalid => 'बारकोडखालील 8, 12, 13 किंवा 14 अंक टाका.';

  @override
  String get scanManualEntry => 'किंवा बारकोड टाइप करा';

  @override
  String get scanManualPlaceholder => 'उदा. 8901063201089';

  @override
  String get scanNotFound => 'हे उत्पादन आम्हाला अजून सापडले नाही.';

  @override
  String get scanOffUnavailable =>
      'उत्पादन डेटाबेस सध्या व्यस्त आहे. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.';

  @override
  String get scanRetry => 'पुन्हा प्रयत्न करा';

  @override
  String get scanScanning => 'कॅमेरा बारकोडकडे धरा';

  @override
  String get scanSubmit => 'हे उत्पादन तपासा';

  @override
  String get scanTitle => 'बारकोड स्कॅन करा';

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
  String get verdictHideReasons => 'कारणे लपवा';

  @override
  String get verdictProfileNotSetUp =>
      'प्रोफाइल सेट केलेले नाही: वय, ॲलर्जी आणि आहार यांची अजून तपासणी झालेली नाही.';

  @override
  String get verdictReasonUnavailable =>
      'या निकालाचे तपशील या आवृत्तीत उपलब्ध नाहीत.';

  @override
  String verdictRuleApplied(String rule) {
    return 'लागू केलेला नियम: $rule';
  }

  @override
  String get verdictShowAllReasons => 'सर्व कारणे दाखवा';

  @override
  String get verdictStatusAvoid => 'टाळा';

  @override
  String get verdictStatusCaution => 'सावधगिरी';

  @override
  String get verdictStatusOk => 'ठीक आहे';

  @override
  String get verdictStatusUnknown => 'लेबल स्पष्ट नाही';
}
