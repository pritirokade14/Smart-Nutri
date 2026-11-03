// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Marathi (`mr`).
class AppLocalizationsMr extends AppLocalizations {
  AppLocalizationsMr([String locale = 'mr']) : super(locale);

  @override
  String get alertAddedSugar => 'वरून घातलेली साखर';

  @override
  String get alertArtificialSweetener => 'कृत्रिम स्वीटनर (गोडवा)';

  @override
  String get alertMaida => 'मैदा';

  @override
  String get alertMsg => 'एमएसजी (मोनोसोडियम ग्लूटामेट)';

  @override
  String get alertPalmOil => 'पाम तेल';

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
  String get authOr => 'किंवा';

  @override
  String get authPhone => 'फोनसह पुढे जा';

  @override
  String get authPhoneLabel => 'फोन नंबर (देश कोडसह)';

  @override
  String get authSendCode => 'कोड पाठवा';

  @override
  String get authSignOut => 'साइन आउट करा';

  @override
  String get authSubtitle =>
      'तुमच्या कुटुंबासाठी पॅकबंद अन्न तपासण्यासाठी साइन इन करा.';

  @override
  String get authTagline =>
      'पॅकबंद अन्न तुमच्या कुटुंबातील प्रत्येकासाठी योग्य आहे का ते जाणून घ्या.';

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
  String get commonComingSoon => 'लवकरच येत आहे';

  @override
  String get commonDisclaimer => 'ही माहिती आहे, वैद्यकीय सल्ला नाही.';

  @override
  String get commonErrorTitle => 'काहीतरी चुकले';

  @override
  String get commonGoHome => 'मुख्य पानावर जा';

  @override
  String get commonLoading => 'लोड होत आहे…';

  @override
  String get commonNotFoundBody =>
      'तुम्ही शोधत असलेले पान अस्तित्वात नाही किंवा दुसरीकडे हलवले आहे.';

  @override
  String get commonRetry => 'पुन्हा प्रयत्न करा';

  @override
  String get commonSkipToContent => 'थेट मुख्य मजकुराकडे जा';

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
  String get confirmAddIngredient => 'घटक जोडा';

  @override
  String get confirmAllergenStatement => 'ॲलर्जीविषयक विधान';

  @override
  String get confirmBasis => 'पॅकवरील मूल्ये आहेत';

  @override
  String get confirmBasisOptionPer100g => 'प्रति 100 g';

  @override
  String get confirmBasisOptionPerServing => 'प्रति सर्व्हिंग';

  @override
  String get confirmBrand => 'ब्रँड';

  @override
  String get confirmCategory => 'उत्पादनाचा प्रकार';

  @override
  String get confirmCategoryOptionBeverage => 'पेय';

  @override
  String get confirmCategoryOptionCheese => 'चीज';

  @override
  String get confirmCategoryOptionFat => 'तेल किंवा चरबी';

  @override
  String get confirmCategoryOptionGeneral => 'खाद्यपदार्थ';

  @override
  String get confirmCategoryOptionWater => 'पॅक्ड पाणी';

  @override
  String get confirmChooseRequired => 'पुढे जाण्यासाठी एक निवडा';

  @override
  String get confirmClaims => 'पॅकवरील दावे';

  @override
  String get confirmClearStatementConfirm =>
      'मी पॅक तपासला आहे: हे विधान त्यावर छापलेले नाही';

  @override
  String get confirmConfirmValue => 'पॅकशी जुळते';

  @override
  String confirmDerivedPerServing(String serving) {
    return '$serving g च्या सर्व्हिंगवरून काढले';
  }

  @override
  String get confirmFieldAddedSugarsG => 'वरून घातलेली साखर (g)';

  @override
  String get confirmFieldCarbsG => 'कार्बोहायड्रेट्स (g)';

  @override
  String get confirmFieldEnergyKcal => 'ऊर्जा (kcal)';

  @override
  String get confirmFieldFatG => 'एकूण चरबी (g)';

  @override
  String get confirmFieldFiberG => 'तंतू (g)';

  @override
  String get confirmFieldProteinG => 'प्रथिने (g)';

  @override
  String get confirmFieldSaltG => 'मीठ (g)';

  @override
  String get confirmFieldSatFatG => 'संतृप्त चरबी (g)';

  @override
  String get confirmFieldSodiumMg => 'सोडियम (mg)';

  @override
  String get confirmFieldSugarsG => 'एकूण साखर (g)';

  @override
  String get confirmFieldTransFatG => 'ट्रान्स फॅट (g)';

  @override
  String get confirmIngredients => 'घटक';

  @override
  String get confirmLeaveBlankHint => 'छापलेले नसेल तर रिकामे ठेवा';

  @override
  String get confirmMayContainStatement => '\"असू शकते\" हे विधान';

  @override
  String get confirmName => 'उत्पादनाचे नाव';

  @override
  String get confirmNotMedicalAdvice => 'ही माहिती आहे, वैद्यकीय सल्ला नाही.';

  @override
  String get confirmOpenExisting => 'जतन केलेले उत्पादन उघडा';

  @override
  String get confirmRemoveIngredient => 'हा घटक काढा';

  @override
  String get confirmSave => 'खात्री करा आणि जतन करा';

  @override
  String get confirmSectionAllergens => 'ॲलर्जी घटक';

  @override
  String get confirmSectionNutrition => 'पोषण तक्ता';

  @override
  String get confirmSectionPack => 'पॅकवरील दावे आणि खुणा';

  @override
  String get confirmSectionProduct => 'उत्पादन';

  @override
  String get confirmServingSize => 'सर्व्हिंग साइज (g)';

  @override
  String get confirmSodium => 'सोडियम';

  @override
  String get confirmSodiumUnit => 'पॅकवरील सोडियमचे एकक';

  @override
  String get confirmSodiumUnitOptionG => 'g';

  @override
  String get confirmSodiumUnitOptionMg => 'mg';

  @override
  String get confirmSubtitle =>
      'प्रत्येक मूल्य पॅकशी जुळवून तपासा. जे छापलेले नसेल ते रिकामे ठेवा.';

  @override
  String get confirmTitle => 'लेबलवरील मूल्ये तपासा';

  @override
  String get confirmVegMarkNonVeg => 'मांसाहारी (तपकिरी खूण)';

  @override
  String get confirmVegMarkNone => 'पॅकवर कोणतीही खूण नाही';

  @override
  String get confirmVegMarkTitle => 'शाकाहारी किंवा मांसाहारी खूण';

  @override
  String get confirmVegMarkVeg => 'शाकाहारी (हिरवी खूण)';

  @override
  String get confirmWithheldHint =>
      'पॅकवर हे मूल्य तपासा, मग खात्रीसाठी टिक करा.';

  @override
  String get consentAgree => 'मी सहमत आहे';

  @override
  String get consentAiOptional =>
      'ऐच्छिक. याशिवायही तुम्हाला प्रत्येक निकाल मिळेल, फक्त AI स्पष्टीकरण मिळणार नाही.';

  @override
  String get consentAiProcessingBody =>
      'प्रत्येक निकालाचा सारांश, नावांशिवाय, भारतात प्रक्रिया होणाऱ्या AI सेवेला पाठवण्याची SmartNutri ला परवानगी द्या, म्हणजे छोटे स्पष्टीकरण लिहिता येईल. निकाल कधीही AI ठरवत नाही.';

  @override
  String get consentAiProcessingTitle => 'AI स्पष्टीकरण';

  @override
  String get consentDecline => 'आत्ता नाही';

  @override
  String get consentGranted => 'संमती दिली';

  @override
  String get consentHealthDataBody =>
      'तुम्ही नोंदवलेल्या ॲलर्जी, आरोग्य स्थिती, उद्दिष्ट, उंची आणि वजन वापरून SmartNutri कुटुंबातील प्रत्येक सदस्यासाठी उत्पादने तपासते. ही माहिती आहे, वैद्यकीय सल्ला नाही. तुम्ही ही संमती कधीही मागे घेऊ शकता.';

  @override
  String get consentHealthDataTitle => 'आरोग्य डेटा';

  @override
  String get consentNotGranted => 'संमती दिलेली नाही';

  @override
  String get consentRequiredNote =>
      'ॲलर्जी, आरोग्य स्थिती, उद्दिष्ट, उंची किंवा वजन जतन करण्यासाठी आवश्यक.';

  @override
  String get consentTermsBody =>
      'मी SmartNutri च्या वापराच्या अटी आणि गोपनीयता धोरणाशी सहमत आहे.';

  @override
  String get consentTermsTitle => 'वापराच्या अटी';

  @override
  String get consentWithdraw => 'संमती मागे घ्या';

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
  String get errorConsentRequired =>
      'ॲलर्जी, आरोग्य स्थिती, उद्दिष्ट, उंची किंवा वजन जतन करण्यासाठी, कृपया आधी आरोग्य डेटाच्या वापराला संमती द्या.';

  @override
  String get errorConsentVersionMismatch =>
      'संमतीचा मजकूर अद्ययावत झाला आहे. कृपया पुन्हा लोड करून तो पुन्हा पाहा.';

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
  String get errorMemberLimit =>
      'तुम्ही कुटुंबातील जास्तीत जास्त 10 सदस्य जोडू शकता.';

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
  String get errorPrimaryMember => 'तुमची स्वतःची प्रोफाइल काढता येत नाही.';

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
  String get explanationAiNote =>
      'वरील निकालांवरून AI ने लिहिले आहे. यामुळे कोणताही निकाल बदलत नाही.';

  @override
  String get explanationTipsTitle => 'सूचना';

  @override
  String get explanationTitle => 'हा निकाल का';

  @override
  String get familyBody =>
      'कुटुंबातील प्रत्येक सदस्याला त्यांचे वय, ॲलर्जी आणि आहार यांसह जोडा, म्हणजे प्रत्येक निकाल त्यांच्यानुसार असेल.';

  @override
  String get familyComingSoonBody =>
      'प्रत्येकाचे वय, ॲलर्जी आणि आहार जोडा, म्हणजे प्रत्येकासाठी वेगळा निकाल मिळेल.';

  @override
  String get familyComingSoonTitle => 'कुटुंब प्रोफाइल लवकरच येत आहेत';

  @override
  String get familyTitle => 'कुटुंब';

  @override
  String get footerTagline => 'भारतीय कुटुंबांसाठी पॅकबंद अन्नाची माहिती.';

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
  String get historyBody =>
      'तुम्ही तपासलेली उत्पादने इथे दिसतील, म्हणजे ती पुन्हा शोधता येतील.';

  @override
  String get historyComingSoonBody =>
      'तुम्ही तपासलेली सर्व उत्पादने इथे दिसतील.';

  @override
  String get historyComingSoonTitle => 'तुमचा इतिहास लवकरच येत आहे';

  @override
  String get historyTitle => 'इतिहास';

  @override
  String get homeLabelBody =>
      'बारकोड नाही, किंवा उत्पादन आम्हाला अजून माहीत नाही? लेबलचा फोटो घ्या.';

  @override
  String get homeLabelTitle => 'लेबलचा फोटो घ्या';

  @override
  String get homeManualBody => 'पाकिटावरील पोषण माहिती स्वतः टाइप करा.';

  @override
  String get homeRecentEmptyBody => 'तुम्ही तपासलेली उत्पादने इथे दिसतील.';

  @override
  String get homeRecentEmptyTitle => 'अजून एकही स्कॅन नाही';

  @override
  String get homeRecentTitle => 'अलीकडील स्कॅन';

  @override
  String get homeScanBody =>
      'कॅमेरा वापरा, किंवा बारकोडखालील क्रमांक टाइप करा.';

  @override
  String get homeScanCta => 'उत्पादन स्कॅन करा';

  @override
  String get homeSubtitle => 'आज तुम्हाला काय तपासायचे आहे?';

  @override
  String homeWelcome(String name) {
    return 'नमस्कार, $name';
  }

  @override
  String get homeWelcomeNoName => 'नमस्कार';

  @override
  String get labelCameraPermissionDenied =>
      'कॅमेऱ्याची परवानगी बंद आहे. लेबलचा फोटो घेण्यासाठी सेटिंग्जमध्ये ती सुरू करा, किंवा फोटो निवडा किंवा माहिती स्वतः भरा.';

  @override
  String get labelChooseFile => 'फाइल निवडा';

  @override
  String get labelDropHere => 'फोटो इथे टाका';

  @override
  String get labelEnterManually => 'माहिती स्वतः भरा';

  @override
  String get labelReading => 'लेबल वाचले जात आहे…';

  @override
  String get labelRetake => 'पुन्हा घ्या';

  @override
  String get labelTakePhoto => 'फोटो घ्या';

  @override
  String get labelTitle => 'लेबलचा फोटो घ्या';

  @override
  String get labelUploading => 'फोटो अपलोड होत आहे…';

  @override
  String get landingCtaStart => 'सुरुवात करा';

  @override
  String get landingEyebrow => 'भारतीय कुटुंबांसाठी';

  @override
  String get landingHeroBody =>
      'बारकोड स्कॅन करा किंवा लेबलचा फोटो घ्या. SmartNutri ते वाचून प्रत्येक व्यक्तीचे वय, ॲलर्जी आणि आहार यांनुसार तपासते आणि कारणही सांगते.';

  @override
  String get landingHeroTitle =>
      'पॅकबंद अन्न तुमच्या कुटुंबातील प्रत्येक सदस्यासाठी योग्य आहे का, ते जाणून घ्या';

  @override
  String get landingHowTitle => 'हे कसे काम करते';

  @override
  String get landingMetaDescription =>
      'पॅकबंद अन्न स्कॅन करा आणि ते तुमच्या कुटुंबातील प्रत्येक सदस्यासाठी योग्य आहे का ते कारणांसह पाहा. ही माहिती आहे, वैद्यकीय सल्ला नाही.';

  @override
  String get landingMetaTitle =>
      'SmartNutri AI – हे पॅकबंद अन्न तुमच्या कुटुंबासाठी योग्य आहे का?';

  @override
  String get landingStep1Body =>
      'बारकोड स्कॅन करा, किंवा पाकिटावरील पोषण लेबलचा फोटो घ्या.';

  @override
  String get landingStep1Title => 'स्कॅन करा किंवा फोटो घ्या';

  @override
  String get landingStep2Body =>
      'काहीही जतन करण्यापूर्वी तुम्ही लेबलवरील माहितीची खात्री करता.';

  @override
  String get landingStep2Title => 'आम्ही काय वाचले ते तपासा';

  @override
  String get landingStep3Body =>
      'कुटुंबातील प्रत्येक सदस्यासाठी सोपा निकाल मिळवा, सोप्या शब्दांतील कारणांसह.';

  @override
  String get landingStep3Title => 'हे कोणासाठी योग्य आहे ते पाहा';

  @override
  String get languageEn => 'English';

  @override
  String get languageHi => 'हिन्दी';

  @override
  String get languageLabel => 'भाषा';

  @override
  String get languageMr => 'मराठी';

  @override
  String get membersAdd => 'कुटुंबातील सदस्य जोडा';

  @override
  String membersBorn(String year) {
    return 'जन्म वर्ष $year';
  }

  @override
  String get membersConsentWithdrawnNotice =>
      'आरोग्य डेटाची संमती बंद आहे. जतन केलेल्या ॲलर्जी आणि आरोग्य स्थिती अजूनही उत्पादनांच्या तपासणीसाठी वापरल्या जातात, पण पुन्हा संमती देईपर्यंत नवीन जतन करता येणार नाहीत.';

  @override
  String get membersEdit => 'बदला';

  @override
  String get membersFormAllergenAdd => 'जोडा';

  @override
  String get membersFormAllergenInvalid =>
      'ॲलर्जीचे नाव 2 ते 40 अक्षरांचे असावे.';

  @override
  String get membersFormAllergenLength => '2 ते 40 अक्षरे लिहा.';

  @override
  String get membersFormAllergenLimit =>
      'तुम्ही जास्तीत जास्त 20 ॲलर्जी जोडू शकता.';

  @override
  String get membersFormAllergenOther => 'इतर ॲलर्जी';

  @override
  String get membersFormAllergens => 'ॲलर्जी';

  @override
  String get membersFormAllergensHelp => 'यादीतून निवडा, किंवा स्वतः लिहा.';

  @override
  String get membersFormBirthYear => 'जन्म वर्ष';

  @override
  String get membersFormBirthYearHelp =>
      'मुलांच्या आणि 2 वर्षांखालील बाळांच्या तपासणीसाठी वापरले जाते.';

  @override
  String membersFormBirthYearInvalid(String year) {
    return '1900 ते $year मधील वर्ष लिहा.';
  }

  @override
  String get membersFormCancel => 'रद्द करा';

  @override
  String membersFormClearAllergiesConfirm(String name) {
    return '$name यांच्या सर्व ॲलर्जी काढायच्या? या ॲलर्जी असलेल्या उत्पादनांवर त्यांच्यासाठी इशारा दिसणार नाही.';
  }

  @override
  String get membersFormConditions => 'आरोग्य स्थिती';

  @override
  String get membersFormCustomAlerts => 'घटक अलर्ट';

  @override
  String get membersFormCustomAlertsHelp =>
      'लेबलवर हे आढळल्यास आम्ही ते दाखवू.';

  @override
  String get membersFormDiet => 'आहार';

  @override
  String get membersFormGoal => 'उद्दिष्ट (ऐच्छिक)';

  @override
  String get membersFormHealthFieldsNote =>
      'ॲलर्जी, आरोग्य स्थिती, उद्दिष्ट, उंची आणि वजन फक्त आरोग्य डेटाच्या वापराला तुमची संमती असल्यासच जतन केले जातात.';

  @override
  String get membersFormHeightCm => 'उंची (सेमी, ऐच्छिक)';

  @override
  String get membersFormHeightInvalid =>
      '30 ते 250 सेमी दरम्यान उंची लिहा, किंवा रिकामे ठेवा.';

  @override
  String get membersFormName => 'नाव';

  @override
  String get membersFormNameInvalid => '40 अक्षरांपर्यंतचे नाव लिहा.';

  @override
  String get membersFormNameRequired => 'नाव लिहा.';

  @override
  String get membersFormNotSet => 'ठरवलेले नाही';

  @override
  String membersFormNumberRange(String max, String min) {
    return '$min ते $max मधील संख्या लिहा.';
  }

  @override
  String get membersFormRelation => 'नाते';

  @override
  String get membersFormRelationRequired => 'नाते निवडा.';

  @override
  String membersFormRemoveAllergy(String allergen) {
    return '$allergen काढा';
  }

  @override
  String membersFormRemoveAllergyConfirm(String allergen, String name) {
    return '$name यांच्या ॲलर्जी यादीतून हे काढायचे: $allergen? त्यानंतर ते असलेल्या उत्पादनांवर त्यांच्यासाठी इशारा दिसणार नाही.';
  }

  @override
  String get membersFormSave => 'जतन करा';

  @override
  String get membersFormSex => 'लिंग (ऐच्छिक)';

  @override
  String get membersFormWeightInvalid =>
      '2 ते 300 किलो दरम्यान वजन लिहा, किंवा रिकामे ठेवा.';

  @override
  String get membersFormWeightKg => 'वजन (किलो, ऐच्छिक)';

  @override
  String get membersGoalHealthyEating => 'चांगला आहार';

  @override
  String get membersGoalWeightGain => 'वजन वाढवणे';

  @override
  String get membersGoalWeightLoss => 'वजन कमी करणे';

  @override
  String get membersLimitReached =>
      'तुमच्या कुटुंबात 10 सदस्य आहेत, यापेक्षा जास्त जोडता येणार नाहीत.';

  @override
  String get membersRelationChild => 'मूल';

  @override
  String get membersRelationOther => 'इतर';

  @override
  String get membersRelationParent => 'आई-वडील';

  @override
  String get membersRelationSelf => 'तुम्ही';

  @override
  String get membersRelationSpouse => 'जोडीदार';

  @override
  String get membersRemove => 'काढा';

  @override
  String membersRemoveConfirm(String name) {
    return '$name यांना कुटुंबातून काढायचे?';
  }

  @override
  String get membersSaved => 'जतन केले';

  @override
  String get membersSexFemale => 'स्त्री';

  @override
  String get membersSexMale => 'पुरुष';

  @override
  String get membersSexOther => 'इतर';

  @override
  String get membersTitle => 'कुटुंब';

  @override
  String get membersYouBadge => 'तुम्ही';

  @override
  String get navFamily => 'कुटुंब';

  @override
  String get navHistory => 'इतिहास';

  @override
  String get navHome => 'होम';

  @override
  String get navLabel => 'मुख्य मेनू';

  @override
  String get navProfile => 'प्रोफाइल';

  @override
  String get navScan => 'स्कॅन';

  @override
  String get notfoundGoToLabel =>
      'हे उत्पादन आम्हाला अजून माहीत नाही — त्याच्या लेबलचा फोटो घ्या';

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
  String get productNotFoundBody =>
      'बारकोड क्रमांक तपासा. तुम्ही साइन इन करून लेबलचा फोटो घेऊन हे उत्पादन जोडू शकता.';

  @override
  String get productPublicCta => 'तुमच्या कुटुंबासाठी तपासा';

  @override
  String get profileBody => 'तुमचे खाते, भाषा आणि गोपनीयता सेटिंग्ज इथे असतील.';

  @override
  String get profileComingSoonBody =>
      'भाषा, गोपनीयता आणि खात्याची सेटिंग्ज इथे दिसतील.';

  @override
  String get profileComingSoonTitle => 'सेटिंग्ज लवकरच येत आहेत';

  @override
  String get profileGiveConsent => 'संमती द्या';

  @override
  String get profilePrivacyTitle => 'गोपनीयता आणि संमती';

  @override
  String get profileTitle => 'प्रोफाइल';

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
    return 'आम्ही लेबलवर फक्त \"$allergen\" हा नेमका शब्द शोधू शकतो. घटक स्वतः तपासा.';
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
  String reasonCustomAlert(String alert, String ingredients) {
    return 'यात $alert आहे: $ingredients.';
  }

  @override
  String reasonCustomAlertUnknown(String alerts) {
    return 'घटकांची यादी उपलब्ध नाही किंवा पुरेशी स्पष्ट नाही, त्यामुळे $alerts तपासता आले नाही.';
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
  String get reasonVariantCustomAlertFlagOnly =>
      'उत्पादनाच्या माहितीनुसार यात स्वीटनर (गोडवा) आहेत.';

  @override
  String reasonVariantDietViolationMarkOnly(String diet) {
    return 'पॅकवर तपकिरी रंगाची मांसाहारी खूण आहे, त्यामुळे हे कदाचित $diet आहाराशी जुळणार नाही.';
  }

  @override
  String reasonVariantNutrientMissingLowConfidence(String nutrient) {
    return 'लेबलवरील $nutrient स्पष्टपणे वाचता आले नाही, त्यामुळे ही तपासणी करता आली नाही.';
  }

  @override
  String get resultFamilyTitle => 'तुमच्या कुटुंबासाठी';

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
  String get resultMembersTitle => 'तुमच्या कुटुंबासाठी';

  @override
  String get resultNoIngredients => 'घटक उपलब्ध नाहीत';

  @override
  String get resultNotOnLabel => 'लेबलवर नाही';

  @override
  String get resultNutritionTitle => 'प्रति 100 ग्रॅम/मि.ली. पोषण';

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
  String get scanLabelHint => 'बारकोड नाही? त्याऐवजी लेबलचा फोटो घ्या.';

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
  String get scanSubtitle =>
      'कॅमेरा बारकोडकडे धरा, किंवा खाली क्रमांक टाइप करा.';

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
  String verdictForMember(String name, String status) {
    return '$name साठी $status';
  }

  @override
  String verdictForYou(String status) {
    return 'तुमच्यासाठी $status';
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

  @override
  String get warningBasisMismatch =>
      'ही मूल्ये प्रति 100 g आहेत की प्रति सर्व्हिंग हे आम्हाला समजले नाही. पॅकवर जे दिसते ते निवडा.';

  @override
  String get warningCategoryCheck =>
      'उत्पादनाचा प्रकार बरोबर आहे का ते तपासा, कारण त्यामुळे मूल्ये वाचण्याची पद्धत बदलते.';

  @override
  String get warningCategoryUnknown =>
      'हे कोणत्या प्रकारचे उत्पादन आहे हे आम्हाला समजले नाही. एक निवडा.';

  @override
  String get warningDerivedFromServing =>
      'हे मूल्य प्रति सर्व्हिंगच्या प्रमाणावरून काढले आहे. ते पॅकशी जुळवून पाहा.';

  @override
  String get warningEnergyMismatch =>
      'ऊर्जेचे मूल्य इतर मूल्यांशी जुळत नाही. ते पॅकवर तपासा.';

  @override
  String get warningImplausibleValue =>
      'हे मूल्य असामान्य वाटते. कृपया पॅकशी जुळवून पाहा.';

  @override
  String get warningKcalKjMismatch =>
      'kcal आणि kJ ची मूल्ये एकमेकांशी जुळत नाहीत. दोन्ही पॅकवर तपासा.';

  @override
  String get warningLowConfidence =>
      'लेबल वाचणे कठीण होते. कृपया प्रत्येक मूल्य पॅकशी जुळवून तपासा.';

  @override
  String get warningPer100gMissing =>
      'पॅकवरील प्रति 100 g ची मूल्ये सापडली नाहीत. आकडे तपासा किंवा पॅकवरून भरा.';

  @override
  String get warningPerServingIgnored =>
      'पॅकवरील प्रति सर्व्हिंग मूल्ये वापरली गेली नाहीत. प्रति 100 g ची मूल्ये बरोबर आहेत का ते तपासा.';

  @override
  String get warningSaltSodiumMismatch =>
      'मीठ आणि सोडियमची मूल्ये एकमेकांशी जुळत नाहीत. दोन्ही पॅकवर तपासा.';

  @override
  String get warningUnitUnconfirmed =>
      'या मूल्याचे एकक स्पष्ट नव्हते. जसे छापले आहे तसे mg किंवा g निवडा.';

  @override
  String get warningUnreadableField =>
      'आम्हाला हे मूल्य वाचता आले नाही. ते पॅकवरून भरा किंवा रिकामे ठेवा.';

  @override
  String get warningUpperBound =>
      'पॅकवर या प्रमाणापेक्षा \"कमी\" असे लिहिले आहे. हे बरोबर असेल तर खात्री करा.';
}
