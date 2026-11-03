// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppLocalizationsHi extends AppLocalizations {
  AppLocalizationsHi([String locale = 'hi']) : super(locale);

  @override
  String get alertAddedSugar => 'अतिरिक्त चीनी';

  @override
  String get alertArtificialSweetener => 'कृत्रिम स्वीटनर';

  @override
  String get alertMaida => 'मैदा';

  @override
  String get alertMsg => 'एमएसजी (मोनोसोडियम ग्लूटामेट)';

  @override
  String get alertPalmOil => 'पाम तेल';

  @override
  String get allergenCrustacean => 'शेलफ़िश (झींगा, केकड़ा आदि)';

  @override
  String get allergenEgg => 'अंडा';

  @override
  String get allergenFish => 'मछली';

  @override
  String get allergenGluten => 'ग्लूटेन';

  @override
  String get allergenMilk => 'दूध';

  @override
  String get allergenMustard => 'सरसों';

  @override
  String get allergenPeanut => 'मूँगफली';

  @override
  String get allergenSesame => 'तिल';

  @override
  String get allergenSoy => 'सोया';

  @override
  String get allergenSulphite => 'सल्फ़ाइट';

  @override
  String get allergenTreeNut => 'ट्री नट्स (बादाम, काजू, अखरोट आदि)';

  @override
  String get alternativesCompare => 'तुलना करें';

  @override
  String alternativesForMember(String name) {
    return '$name के लिए';
  }

  @override
  String get alternativesReasonNoBetterFound =>
      'इस तरह का बेहतर न्यूट्री-स्कोर वाला कोई उत्पाद नहीं मिला।';

  @override
  String get alternativesReasonNoCategory =>
      'इस उत्पाद के लिए अभी हम विकल्प नहीं सुझा सकते।';

  @override
  String get alternativesReasonSourceUngraded =>
      'तुलना के लिए इस उत्पाद के लेबल पर पर्याप्त जानकारी नहीं है।';

  @override
  String get alternativesSubtitle =>
      'उसी तरह का उत्पाद, बेहतर न्यूट्री-स्कोर के साथ (गणना SmartNutri ने की है)';

  @override
  String alternativesSugars(String value) {
    return 'शर्करा: $value ग्राम प्रति 100 ग्राम/मि.ली.';
  }

  @override
  String get alternativesTitle => 'बेहतर विकल्प';

  @override
  String get appName => 'SmartNutri AI';

  @override
  String get attributionOff => 'डेटा: Open Food Facts (ODbL)';

  @override
  String get authChange => 'बदलें';

  @override
  String get authCodeLabel => '6 अंकों का कोड';

  @override
  String get authEmail => 'ईमेल से जारी रखें';

  @override
  String get authEmailLabel => 'ईमेल पता';

  @override
  String get authError => 'साइन इन नहीं हो सका। कृपया दोबारा कोशिश करें।';

  @override
  String get authGoogle => 'Google से जारी रखें';

  @override
  String get authOr => 'या';

  @override
  String get authPhone => 'फ़ोन से जारी रखें';

  @override
  String get authPhoneLabel => 'फ़ोन नंबर (देश कोड सहित)';

  @override
  String get authSendCode => 'कोड भेजें';

  @override
  String get authSignOut => 'साइन आउट करें';

  @override
  String get authSubtitle =>
      'अपने परिवार के लिए पैकेटबंद खाना जाँचने हेतु साइन इन करें।';

  @override
  String get authTagline =>
      'जानिए कि कोई पैकेज्ड खाना आपके परिवार के हर सदस्य के लिए सही है या नहीं।';

  @override
  String get authTitle => 'साइन इन करें';

  @override
  String get authVerify => 'सत्यापित करें';

  @override
  String get claimDiabeticFriendly => 'डायबिटीज़ के अनुकूल';

  @override
  String get claimHighProtein => 'उच्च प्रोटीन';

  @override
  String get claimLowFat => 'कम वसा';

  @override
  String get claimLowSodium => 'कम सोडियम';

  @override
  String get claimLowSugar => 'कम चीनी';

  @override
  String get claimNoAddedSugar => 'अतिरिक्त चीनी नहीं';

  @override
  String get claimNoRefinedSugar => 'रिफ़ाइंड चीनी नहीं';

  @override
  String claimReasonAddedSugarIngredient(String ingredients) {
    return 'सामग्री में अतिरिक्त चीनी शामिल है: $ingredients।';
  }

  @override
  String claimReasonBelowMinimum(String limit, String value) {
    return 'प्रोटीन से $value% ऊर्जा मिलती है, जो इस दावे के लिए ज़रूरी $limit% से कम है।';
  }

  @override
  String claimReasonExceedsLimit(String limit, String value) {
    return 'लेबल पर प्रति 100 ग्राम/मि.ली. $value है, जो इस दावे की सीमा $limit से अधिक है।';
  }

  @override
  String get claimReasonIngredientsUnknown =>
      'सामग्री की सूची उपलब्ध नहीं है, इसलिए इस दावे की जाँच नहीं हो सकती।';

  @override
  String get claimReasonNoStandard =>
      'इस दावे की जाँच के लिए हमारे पास कोई मानक नहीं है।';

  @override
  String claimReasonNutrientMissing(String nutrient) {
    return 'लेबल पर $nutrient की जानकारी नहीं है, इसलिए इस दावे की जाँच नहीं हो सकती।';
  }

  @override
  String get claimReasonOk => 'लेबल की जानकारी इस दावे से मेल खाती है।';

  @override
  String claimReasonRefinedSugarIngredient(String ingredients) {
    return 'सामग्री में रिफ़ाइंड चीनी शामिल है: $ingredients।';
  }

  @override
  String get claimSourceOfProtein => 'प्रोटीन का स्रोत';

  @override
  String get claimSugarFree => 'चीनी रहित';

  @override
  String get claimVerdictContradicted =>
      'लेबल की जानकारी इस दावे से मेल नहीं खाती';

  @override
  String get claimVerdictSupported =>
      'लेबल की जानकारी इस दावे का समर्थन करती है';

  @override
  String get claimVerdictUnverifiable => 'लेबल से इसकी जाँच नहीं हो सकती';

  @override
  String get commonCancel => 'रद्द करें';

  @override
  String get commonClose => 'बंद करें';

  @override
  String get commonComingSoon => 'जल्द आ रहा है';

  @override
  String get commonDisclaimer => 'यह जानकारी है, चिकित्सकीय सलाह नहीं।';

  @override
  String get commonErrorTitle => 'कुछ गड़बड़ हो गई';

  @override
  String get commonGoHome => 'होम पेज पर जाएँ';

  @override
  String get commonLoading => 'लोड हो रहा है…';

  @override
  String get commonNotFoundBody =>
      'आप जो पेज ढूँढ रहे हैं, वह मौजूद नहीं है या कहीं और चला गया है।';

  @override
  String get commonOpenSettings => 'सेटिंग्स खोलें';

  @override
  String get commonRetry => 'फिर से कोशिश करें';

  @override
  String get commonSkipToContent => 'सीधे मुख्य सामग्री पर जाएँ';

  @override
  String get compareBetterA => 'यहाँ पहला उत्पाद बेहतर है';

  @override
  String get compareBetterB => 'यहाँ दूसरा उत्पाद बेहतर है';

  @override
  String get compareBetterChip => 'बेहतर';

  @override
  String get compareBetterSame => 'लगभग बराबर';

  @override
  String get compareBetterUnknown =>
      'तुलना नहीं हो सकती: किसी लेबल पर यह मान नहीं है';

  @override
  String get comparePickSecond => 'तुलना के लिए एक उत्पाद चुनें';

  @override
  String get compareRowEnergyKcal => 'कैलोरी (प्रति 100 ग्राम/मि.ली.)';

  @override
  String get compareRowFiberG => 'फ़ाइबर (प्रति 100 ग्राम/मि.ली.)';

  @override
  String get compareRowGrade => 'न्यूट्री-स्कोर (गणना SmartNutri ने की है)';

  @override
  String get compareRowProteinG => 'प्रोटीन (प्रति 100 ग्राम/मि.ली.)';

  @override
  String get compareRowSaltG => 'नमक (प्रति 100 ग्राम/मि.ली.)';

  @override
  String get compareRowSatFatG => 'संतृप्त वसा (प्रति 100 ग्राम/मि.ली.)';

  @override
  String get compareRowSugarsG => 'शर्करा (प्रति 100 ग्राम/मि.ली.)';

  @override
  String get compareTitle => 'तुलना करें';

  @override
  String get conditionBuildMuscle => 'मांसपेशियाँ बनाना';

  @override
  String get conditionDiabetes => 'मधुमेह (डायबिटीज़)';

  @override
  String get conditionHypertension => 'उच्च रक्तचाप';

  @override
  String get conditionPcos => 'पीसीओएस';

  @override
  String get conditionPrediabetes => 'प्रीडायबिटीज़';

  @override
  String get conditionWeightLoss => 'वज़न घटाना';

  @override
  String get confirmAddIngredient => 'सामग्री जोड़ें';

  @override
  String get confirmAllergenStatement => 'एलर्जी संबंधी कथन';

  @override
  String get confirmBasis => 'पैक पर मान हैं';

  @override
  String get confirmBasisOptionPer100g => 'प्रति 100 g';

  @override
  String get confirmBasisOptionPerServing => 'प्रति सर्विंग';

  @override
  String get confirmBrand => 'ब्रांड';

  @override
  String get confirmCategory => 'उत्पाद का प्रकार';

  @override
  String get confirmCategoryOptionBeverage => 'पेय';

  @override
  String get confirmCategoryOptionCheese => 'चीज़';

  @override
  String get confirmCategoryOptionFat => 'तेल या वसा';

  @override
  String get confirmCategoryOptionGeneral => 'खाद्य पदार्थ';

  @override
  String get confirmCategoryOptionWater => 'पैक्ड पानी';

  @override
  String get confirmChooseRequired => 'आगे बढ़ने के लिए एक चुनें';

  @override
  String get confirmClaims => 'पैक पर किए गए दावे';

  @override
  String get confirmClearStatementConfirm =>
      'मैंने पैक देख लिया है: यह कथन उस पर छपा नहीं है';

  @override
  String get confirmConfirmValue => 'पैक से मेल खाता है';

  @override
  String confirmDerivedPerServing(String serving) {
    return '$serving g की सर्विंग से निकाला गया';
  }

  @override
  String get confirmFieldAddedSugarsG => 'अतिरिक्त शर्करा (g)';

  @override
  String get confirmFieldCarbsG => 'कार्बोहाइड्रेट (g)';

  @override
  String get confirmFieldEnergyKcal => 'ऊर्जा (kcal)';

  @override
  String get confirmFieldFatG => 'कुल वसा (g)';

  @override
  String get confirmFieldFiberG => 'फाइबर (g)';

  @override
  String get confirmFieldProteinG => 'प्रोटीन (g)';

  @override
  String get confirmFieldSaltG => 'नमक (g)';

  @override
  String get confirmFieldSatFatG => 'संतृप्त वसा (g)';

  @override
  String get confirmFieldSodiumMg => 'सोडियम (mg)';

  @override
  String get confirmFieldSugarsG => 'कुल शर्करा (g)';

  @override
  String get confirmFieldTransFatG => 'ट्रांस वसा (g)';

  @override
  String get confirmIngredients => 'सामग्री';

  @override
  String get confirmLeaveBlankHint => 'अगर छपा न हो तो खाली छोड़ें';

  @override
  String get confirmMayContainStatement => '\"हो सकता है\" वाला कथन';

  @override
  String get confirmName => 'उत्पाद का नाम';

  @override
  String get confirmNotMedicalAdvice => 'यह जानकारी है, चिकित्सकीय सलाह नहीं।';

  @override
  String get confirmOpenExisting => 'सहेजा गया उत्पाद खोलें';

  @override
  String get confirmRemoveIngredient => 'यह सामग्री हटाएँ';

  @override
  String get confirmSave => 'पुष्टि करें और सहेजें';

  @override
  String get confirmSectionAllergens => 'एलर्जी कारक';

  @override
  String get confirmSectionNutrition => 'पोषण तालिका';

  @override
  String get confirmSectionPack => 'पैक पर दावे और निशान';

  @override
  String get confirmSectionProduct => 'उत्पाद';

  @override
  String get confirmServingSize => 'सर्विंग साइज़ (g)';

  @override
  String get confirmSodium => 'सोडियम';

  @override
  String get confirmSodiumUnit => 'पैक पर सोडियम की इकाई';

  @override
  String get confirmSodiumUnitOptionG => 'g';

  @override
  String get confirmSodiumUnitOptionMg => 'mg';

  @override
  String get confirmSubtitle =>
      'हर मान को पैक से मिलाकर जाँचें। जो छपा न हो उसे खाली छोड़ें।';

  @override
  String get confirmTitle => 'लेबल के मान जाँचें';

  @override
  String get confirmVegMarkNonVeg => 'मांसाहारी (भूरा निशान)';

  @override
  String get confirmVegMarkNone => 'पैक पर कोई निशान नहीं';

  @override
  String get confirmVegMarkTitle => 'शाकाहारी या मांसाहारी निशान';

  @override
  String get confirmVegMarkVeg => 'शाकाहारी (हरा निशान)';

  @override
  String get confirmWithheldHint =>
      'पैक पर यह मान जाँचें, फिर पुष्टि के लिए टिक करें।';

  @override
  String get consentAgree => 'मैं सहमत हूँ';

  @override
  String get consentAiOptional =>
      'वैकल्पिक। इसके बिना भी आपको हर नतीजा मिलेगा, बस AI की व्याख्या नहीं मिलेगी।';

  @override
  String get consentAiProcessingBody =>
      'SmartNutri को हर नतीजे का सारांश, बिना नामों के, भारत में प्रोसेस होने वाली AI सेवा को भेजने दें, ताकि एक छोटी व्याख्या लिखी जा सके। नतीजा कभी AI तय नहीं करता।';

  @override
  String get consentAiProcessingTitle => 'AI से व्याख्या';

  @override
  String get consentDecline => 'अभी नहीं';

  @override
  String get consentGranted => 'सहमति दी गई';

  @override
  String get consentHealthDataBody =>
      'आप जो एलर्जी, स्वास्थ्य स्थितियाँ, लक्ष्य, ऊँचाई और वज़न दर्ज करते हैं, SmartNutri उनसे परिवार के हर सदस्य के लिए उत्पादों की जाँच करता है। यह जानकारी है, चिकित्सा सलाह नहीं। आप यह सहमति कभी भी वापस ले सकते हैं।';

  @override
  String get consentHealthDataTitle => 'स्वास्थ्य डेटा';

  @override
  String get consentNeedsUpdate => 'अपडेट हुआ है, कृपया देखें';

  @override
  String get consentNotGranted => 'सहमति नहीं दी गई';

  @override
  String get consentPromptBody =>
      'जारी रखने के लिए कृपया इनसे सहमति दें। आप अपनी प्रोफ़ाइल से कभी भी सहमति वापस ले सकते हैं।';

  @override
  String get consentPromptTitle => 'आपकी सहमति चाहिए';

  @override
  String get consentRequiredNote =>
      'एलर्जी, स्वास्थ्य स्थितियाँ, लक्ष्य, ऊँचाई या वज़न सहेजने के लिए ज़रूरी है।';

  @override
  String get consentRequiredToContinue =>
      'आगे बढ़ने के लिए कृपया देखें और सहमति दें।';

  @override
  String get consentReviewAgree => 'पढ़ें और सहमति दें';

  @override
  String get consentTermsBody =>
      'मैं SmartNutri की उपयोग की शर्तों और गोपनीयता नीति से सहमत हूँ।';

  @override
  String get consentTermsStepBody =>
      'कृपया हमारी उपयोग की शर्तें और गोपनीयता सूचना पढ़ें। उत्पादों की जाँच और स्कैन करने के लिए आपको इनसे सहमत होना होगा।';

  @override
  String get consentTermsStepLeaveNote =>
      'सहमत नहीं होना चाहते? आप साइन आउट कर सकते हैं, या अपनी प्रोफ़ाइल से अपना खाता हटा सकते हैं।';

  @override
  String get consentTermsStepReadPrivacy => 'गोपनीयता सूचना';

  @override
  String get consentTermsStepReadTerms => 'उपयोग की शर्तें';

  @override
  String get consentTermsStepTitle => 'शुरू करने से पहले';

  @override
  String get consentTermsStepUpdatedBody =>
      'हमारी उपयोग की शर्तें या गोपनीयता सूचना बदल गई है। उत्पादों की जाँच और स्कैन जारी रखने के लिए कृपया इन्हें पढ़ें और फिर से सहमति दें।';

  @override
  String get consentTermsStepUpdatedTitle => 'हमने अपनी शर्तें अपडेट की हैं';

  @override
  String get consentTermsTitle => 'उपयोग की शर्तें';

  @override
  String get consentTermsWithdrawConfirm =>
      'सहमति वापस लेने पर, जब तक आप फिर से सहमति नहीं देते, आप उत्पादों की जाँच या स्कैन नहीं कर पाएँगे। आपका सहेजा गया डेटा तब तक रहेगा जब तक आप अपना खाता नहीं हटाते।';

  @override
  String get consentUpdateNote =>
      'हमने यह जानकारी अपडेट की है। कृपया इसे पढ़ें और फिर से सहमति दें।';

  @override
  String get consentUpdatesBanner =>
      'हमने कुछ सहमति की जानकारी अपडेट की है। कृपया उन्हें देखें।';

  @override
  String get consentWithdraw => 'सहमति वापस लें';

  @override
  String get dietEggetarian => 'अंडाहारी (अंडा खाने वाला शाकाहारी)';

  @override
  String get dietJain => 'जैन';

  @override
  String get dietNonVeg => 'मांसाहारी';

  @override
  String get dietVeg => 'शाकाहारी';

  @override
  String get dietVegan => 'वीगन';

  @override
  String get errorAiUnavailable =>
      'आवाज़ वाले जवाब अभी उपलब्ध नहीं हैं। कृपया बाद में फिर कोशिश करें।';

  @override
  String get errorAudioTooLarge =>
      'यह रिकॉर्डिंग बहुत बड़ी है। कृपया छोटा सवाल पूछें।';

  @override
  String get errorAudioTooLong =>
      'यह रिकॉर्डिंग 30 सेकंड से लंबी है। कृपया छोटा सवाल पूछें।';

  @override
  String get errorAudioUnsupported =>
      'हम यह रिकॉर्डिंग चला नहीं पाए। कृपया फिर कोशिश करें।';

  @override
  String get errorAuthInvalid =>
      'आपका सत्र समाप्त हो गया है। कृपया फिर से साइन इन करें।';

  @override
  String get errorAuthRequired => 'कृपया साइन इन करें।';

  @override
  String get errorConsentRequired =>
      'एलर्जी, स्वास्थ्य स्थितियाँ, लक्ष्य, ऊँचाई या वज़न सहेजने के लिए, कृपया पहले स्वास्थ्य डेटा के उपयोग के लिए सहमति दें।';

  @override
  String get errorConsentVersionMismatch =>
      'सहमति का पाठ अपडेट हो गया है। कृपया पेज फिर से लोड करके उसे दोबारा देखें।';

  @override
  String get errorDeletionIncomplete =>
      'हम आपका खाता पूरी तरह हटा नहीं सके। कृपया फिर से कोशिश करें; जो हट चुका है वह वापस नहीं आएगा।';

  @override
  String get errorEatenAtOutOfRange => 'पिछले 30 दिनों के भीतर का समय चुनें।';

  @override
  String get errorExtractionFailed =>
      'हम यह लेबल नहीं पढ़ पाए। दूसरी फ़ोटो आज़माएँ या जानकारी खुद भरें।';

  @override
  String get errorExtractionUnavailable =>
      'लेबल पढ़ने की सुविधा अभी उपलब्ध नहीं है। बाद में फिर कोशिश करें या जानकारी खुद भरें।';

  @override
  String get errorFollowUpWithoutType =>
      'कृपया अपने जवाब जाँचें और फिर से कोशिश करें।';

  @override
  String get errorForbidden => 'आपके पास इसकी पहुँच नहीं है।';

  @override
  String get errorHttpError => 'कुछ गड़बड़ हो गई। कृपया फिर से कोशिश करें।';

  @override
  String get errorImageTooLarge =>
      'यह फ़ोटो बहुत बड़ी है। कृपया 8 MB से छोटी फ़ोटो इस्तेमाल करें।';

  @override
  String get errorImplausibleValue =>
      'कुछ मान सही नहीं लगते। कृपया चिह्नित फ़ील्ड जाँचें, या उन्हें खाली छोड़ दें।';

  @override
  String get errorInternalError => 'कुछ गड़बड़ हो गई। कृपया फिर से कोशिश करें।';

  @override
  String get errorInvalidBarcode => 'यह सही बारकोड नहीं लगता।';

  @override
  String get errorInvalidProductRef => 'जाँचने के लिए एक उत्पाद चुनें।';

  @override
  String get errorMealNotFound => 'यह खाने की एंट्री नहीं मिली।';

  @override
  String get errorMemberLimit => 'आप परिवार के अधिकतम 10 सदस्य जोड़ सकते हैं।';

  @override
  String get errorMemberNotFound => 'परिवार का यह सदस्य नहीं मिला।';

  @override
  String get errorMethodNotAllowed =>
      'यह कार्य समर्थित नहीं है। कृपया ऐप अपडेट करें।';

  @override
  String get errorNetwork => 'इंटरनेट कनेक्शन नहीं है।';

  @override
  String get errorNotFound => 'नहीं मिला।';

  @override
  String get errorOffUnavailable =>
      'उत्पाद डेटाबेस अभी व्यस्त है। कृपया थोड़ी देर बाद फिर कोशिश करें।';

  @override
  String get errorPayloadTooLarge =>
      'यह अनुरोध बहुत बड़ा है। कृपया कम डेटा के साथ फिर से कोशिश करें।';

  @override
  String get errorPhoneOtpDisabled =>
      'फ़ोन से साइन-इन अभी उपलब्ध नहीं है। कृपया ईमेल या Google से साइन इन करें।';

  @override
  String get errorPortionRequired => 'कितना खाया, चुनें: सर्विंग या ग्राम।';

  @override
  String get errorPrimaryMember => 'आपकी अपनी प्रोफ़ाइल हटाई नहीं जा सकती।';

  @override
  String get errorProductExists => 'यह उत्पाद पहले से सहेजा गया है।';

  @override
  String get errorProductNotFound => 'यह उत्पाद अभी हमें नहीं मिला।';

  @override
  String get errorRateLimited => 'बहुत अधिक अनुरोध। कृपया थोड़ी देर रुकें।';

  @override
  String get errorRateLimitedScans =>
      'आप आज की लेबल-स्कैन सीमा तक पहुँच गए हैं।';

  @override
  String get errorRateLimitedVoice =>
      'आप आज की आवाज़ से प्रश्न पूछने की सीमा तक पहुँच गए हैं।';

  @override
  String get errorScanImageNotFound =>
      'वह फ़ोटो हमें नहीं मिली। कृपया फ़ोटो फिर से लें या अपलोड करें।';

  @override
  String get errorScanNotFound =>
      'यह लेबल स्कैन नहीं मिला। कृपया लेबल फिर से स्कैन करें।';

  @override
  String get errorSearchQueryTooShort => 'खोजने के लिए कम से कम 3 अक्षर लिखें।';

  @override
  String get errorServingSizeUnknown =>
      'इस पैक पर सर्विंग का आकार नहीं लिखा है। मात्रा ग्राम में भरें।';

  @override
  String get errorStorageUnavailable =>
      'हम अभी फ़ोटो संभाल नहीं पाए। कृपया थोड़ी देर बाद फिर कोशिश करें।';

  @override
  String get errorUnauthorized => 'कृपया साइन इन करें।';

  @override
  String get errorUnsupportedImage =>
      'कृपया JPEG, PNG या WebP फ़ोटो इस्तेमाल करें।';

  @override
  String get errorUserTypeNotSelected =>
      'अपने लिए चुने गए विकल्पों में से एक चुनें।';

  @override
  String get errorUserTypesNotFound =>
      'पहले बताइए कि आप SmartNutri क्यों इस्तेमाल कर रहे हैं।';

  @override
  String get errorValidationError => 'कृपया चिह्नित फ़ील्ड जाँचें।';

  @override
  String get errorVoiceNotUnderstood =>
      'हमें कोई सवाल सुनाई नहीं दिया। कृपया बटन दबाए रखें और साफ़ बोलें।';

  @override
  String get explanationAiNote =>
      'ऊपर के नतीजों से AI ने लिखा है। यह कभी कोई नतीजा नहीं बदलता।';

  @override
  String get explanationFallbackTip1 =>
      'मिलते-जुलते उत्पादों के लेबल की तुलना करें और कम चीनी व कम नमक वाला चुनें।';

  @override
  String get explanationFallbackTip2 =>
      'पैक पर सर्विंग का आकार देखें: लेबल के मान प्रति 100 ग्राम या 100 मि.ली. होते हैं।';

  @override
  String get explanationFallbackTip3 =>
      'अगर आपको कोई स्वास्थ्य समस्या है, तो बदलाव से पहले अपने डॉक्टर या डाइटीशियन से पूछें।';

  @override
  String get explanationSourceFallbackNote =>
      'AI से समझाने की सुविधा अभी उपलब्ध नहीं है, इसलिए यह सारांश हमारे नियमों से बना है।';

  @override
  String get explanationTipsTitle => 'सुझाव';

  @override
  String get explanationTitle => 'यह नतीजा क्यों';

  @override
  String get familyBody =>
      'परिवार के हर सदस्य को उनकी उम्र, एलर्जी और खान-पान के साथ जोड़ें, ताकि हर नतीजा उनके हिसाब से हो।';

  @override
  String get familyComingSoonBody =>
      'हर सदस्य की उम्र, एलर्जी और आहार जोड़ें, ताकि हर किसी के लिए अलग नतीजा मिले।';

  @override
  String get familyComingSoonTitle => 'परिवार प्रोफ़ाइल जल्द आ रही हैं';

  @override
  String get familyTitle => 'परिवार';

  @override
  String get footerLinksLabel => 'SmartNutri के बारे में';

  @override
  String get footerTagline =>
      'भारतीय परिवारों के लिए पैकेटबंद खाने की जानकारी।';

  @override
  String get goodbyeAction => 'साइन इन पर वापस जाएँ';

  @override
  String get goodbyeBody =>
      'आपका खाता और उसका डेटा हटा दिया गया है, और आप साइन आउट हो गए हैं। SmartNutri आज़माने के लिए धन्यवाद।';

  @override
  String get goodbyeMetaTitle => 'खाता हटाया गया';

  @override
  String get goodbyeTitle => 'आपका खाता हटा दिया गया है';

  @override
  String get highInFat => 'वसा अधिक';

  @override
  String highInPercentOfLimit(String pct) {
    return 'सीमा का $pct%';
  }

  @override
  String get highInSalt => 'नमक अधिक';

  @override
  String get highInSatFat => 'संतृप्त वसा अधिक';

  @override
  String get highInSugar => 'चीनी अधिक';

  @override
  String get historyBody =>
      'आप जो उत्पाद जाँचेंगे, वे यहाँ दिखेंगे, ताकि आप उन्हें फिर से ढूँढ सकें।';

  @override
  String get historyComingSoonBody =>
      'आपने जो भी उत्पाद जाँचे हैं, वे सब यहाँ दिखेंगे।';

  @override
  String get historyComingSoonTitle => 'आपका इतिहास जल्द आ रहा है';

  @override
  String get historyEmpty => 'अभी तक कुछ दर्ज नहीं किया गया।';

  @override
  String historyItemAmount(String grams) {
    return '$grams ग्राम';
  }

  @override
  String get historyLoggedTitle => 'क्या खाया गया';

  @override
  String get historyMember => 'परिवार का सदस्य';

  @override
  String get historyNextDay => 'अगला दिन';

  @override
  String get historyPreviousDay => 'पिछला दिन';

  @override
  String get historyRemove => 'हटाएँ';

  @override
  String get historyRemoveConfirm => 'इसे लॉग से हटाएँ?';

  @override
  String get historyThisWeek => 'इस हफ़्ते';

  @override
  String get historyTitle => 'इतिहास';

  @override
  String get historyToday => 'आज';

  @override
  String get homeLabelBody =>
      'बारकोड नहीं है, या उत्पाद हमें अभी पता नहीं? लेबल की फ़ोटो लें।';

  @override
  String get homeLabelTitle => 'लेबल की फ़ोटो लें';

  @override
  String get homeManualBody => 'पैक पर लिखी पोषण जानकारी खुद टाइप करें।';

  @override
  String get homeRecentEmptyBody => 'आप जो उत्पाद जाँचेंगे, वे यहाँ दिखेंगे।';

  @override
  String get homeRecentEmptyTitle => 'अभी कोई स्कैन नहीं';

  @override
  String get homeRecentTitle => 'हाल के स्कैन';

  @override
  String get homeScanBody =>
      'कैमरे का इस्तेमाल करें, या बारकोड के नीचे लिखा नंबर टाइप करें।';

  @override
  String get homeScanCta => 'उत्पाद स्कैन करें';

  @override
  String get homeSubtitle => 'आज आप क्या जाँचना चाहेंगे?';

  @override
  String homeWelcome(String name) {
    return 'नमस्ते, $name';
  }

  @override
  String get homeWelcomeNoName => 'नमस्ते';

  @override
  String get labelCameraPermissionDenied =>
      'कैमरा की अनुमति बंद है। लेबल की फ़ोटो लेने के लिए सेटिंग्स में इसे चालू करें, या कोई फ़ोटो चुनें या जानकारी खुद भरें।';

  @override
  String get labelChooseFile => 'फ़ाइल चुनें';

  @override
  String get labelDropHere => 'फ़ोटो यहाँ छोड़ें';

  @override
  String get labelEnterManually => 'जानकारी खुद भरें';

  @override
  String get labelReading => 'लेबल पढ़ा जा रहा है…';

  @override
  String get labelRetake => 'दोबारा लें';

  @override
  String get labelTakePhoto => 'फ़ोटो लें';

  @override
  String get labelTitle => 'लेबल की फ़ोटो लें';

  @override
  String get labelUploading => 'फ़ोटो अपलोड हो रही है…';

  @override
  String get landingCtaStart => 'शुरू करें';

  @override
  String get landingEyebrow => 'भारतीय परिवारों के लिए';

  @override
  String get landingHeroBody =>
      'बारकोड स्कैन करें या लेबल की फ़ोटो लें। SmartNutri उसे पढ़कर हर व्यक्ति की उम्र, एलर्जी और खान-पान के हिसाब से जाँचता है, और कारण भी बताता है।';

  @override
  String get landingHeroTitle =>
      'जानिए कि कोई पैकेटबंद खाना आपके परिवार के हर सदस्य के लिए सही है या नहीं';

  @override
  String get landingHowTitle => 'यह कैसे काम करता है';

  @override
  String get landingMetaDescription =>
      'पैकेटबंद खाना स्कैन करें और देखें कि यह आपके परिवार के हर सदस्य के लिए ठीक है या नहीं, कारणों के साथ। यह जानकारी है, चिकित्सकीय सलाह नहीं।';

  @override
  String get landingMetaTitle =>
      'SmartNutri AI – क्या यह पैकेटबंद खाना आपके परिवार के लिए सही है?';

  @override
  String get landingStep1Body =>
      'बारकोड स्कैन करें, या पैक पर छपे पोषण लेबल की फ़ोटो लें।';

  @override
  String get landingStep1Title => 'स्कैन करें या फ़ोटो लें';

  @override
  String get landingStep2Body =>
      'कुछ भी सहेजने से पहले आप लेबल की जानकारी की पुष्टि करते हैं।';

  @override
  String get landingStep2Title => 'हमने जो पढ़ा, उसे जाँचें';

  @override
  String get landingStep3Body =>
      'परिवार के हर सदस्य के लिए आसान नतीजा पाएँ, साथ में सरल शब्दों में कारण।';

  @override
  String get landingStep3Title => 'देखें कि यह किसके लिए ठीक है';

  @override
  String get languageEn => 'English';

  @override
  String get languageHi => 'हिन्दी';

  @override
  String get languageLabel => 'भाषा';

  @override
  String get languageMr => 'मराठी';

  @override
  String get legalDraftNotice =>
      'मसौदा: लॉन्च से पहले एक वकील इस दस्तावेज़ की समीक्षा कर रहे हैं।';

  @override
  String get legalEnglishOnly =>
      'यह दस्तावेज़ अभी केवल अंग्रेज़ी में उपलब्ध है।';

  @override
  String get legalPrivacyDescription =>
      'SmartNutri AI भारत के DPDP अधिनियम, 2023 के तहत आपके परिवार का डेटा कैसे इकट्ठा, इस्तेमाल और सुरक्षित करता है।';

  @override
  String get legalPrivacyTitle => 'गोपनीयता सूचना';

  @override
  String get legalTermsDescription =>
      'SmartNutri AI के उपयोग की शर्तें। यह जानकारी है, चिकित्सकीय सलाह नहीं।';

  @override
  String get legalTermsTitle => 'उपयोग की शर्तें';

  @override
  String legalVersion(String version) {
    return 'संस्करण $version';
  }

  @override
  String get mealsLogAmountGrams => 'मात्रा ग्राम में';

  @override
  String mealsLogAmountInvalid(String max) {
    return '0 से ज़्यादा और $max तक की मात्रा डालें।';
  }

  @override
  String get mealsLogAmountServings => 'सर्विंग की संख्या';

  @override
  String get mealsLogCta => 'मैंने यह खाया';

  @override
  String get mealsLogEatenAt => 'कब';

  @override
  String get mealsLogGrams => 'ग्राम';

  @override
  String get mealsLogMember => 'किसने खाया?';

  @override
  String get mealsLogNow => 'अभी';

  @override
  String get mealsLogPortion => 'कितना खाया?';

  @override
  String get mealsLogSave => 'सहेजें';

  @override
  String mealsLogSaved(String who) {
    return '$who के लिए दर्ज किया गया';
  }

  @override
  String get mealsLogSavedYou => 'आपके लिए दर्ज किया गया';

  @override
  String mealsLogServingSize(String grams) {
    return '1 सर्विंग = $grams ग्राम';
  }

  @override
  String get mealsLogServings => 'सर्विंग';

  @override
  String get mealsLogTitle => 'क्या खाया, दर्ज करें';

  @override
  String get mealsLogUndo => 'वापस लें';

  @override
  String get mealsLogUndone => 'लॉग से हटाया गया';

  @override
  String get mealsOnlineOnly =>
      'वेब पर दर्ज करने के लिए इंटरनेट चाहिए। ऑफ़लाइन कुछ भी सहेजा नहीं जाता।';

  @override
  String get mealsQueuedOffline =>
      'इस फ़ोन पर सहेजा गया। ऑनलाइन होते ही यह लॉग में जुड़ जाएगा।';

  @override
  String get mealsSyncFailed =>
      'कुछ चीज़ें लॉग में नहीं जुड़ पाईं। कृपया उन्हें फिर से दर्ज करें।';

  @override
  String get mealsSyncing => 'दर्ज की गई चीज़ें सिंक हो रही हैं…';

  @override
  String get membersAdd => 'परिवार का सदस्य जोड़ें';

  @override
  String membersBorn(String year) {
    return 'जन्म वर्ष $year';
  }

  @override
  String get membersConsentWithdrawnNotice =>
      'स्वास्थ्य डेटा की सहमति बंद है। सहेजी गई एलर्जी और स्वास्थ्य स्थितियाँ अब भी उत्पादों की जाँच में इस्तेमाल होती हैं, लेकिन दोबारा सहमति देने तक नई नहीं सहेजी जा सकतीं।';

  @override
  String get membersEdit => 'बदलें';

  @override
  String get membersFormAllergenAdd => 'जोड़ें';

  @override
  String get membersFormAllergenInvalid =>
      'एलर्जी का नाम 2 से 40 अक्षरों का होना चाहिए।';

  @override
  String get membersFormAllergenLength => '2 से 40 अक्षर लिखें।';

  @override
  String get membersFormAllergenLimit =>
      'आप ज़्यादा से ज़्यादा 20 एलर्जी जोड़ सकते हैं।';

  @override
  String get membersFormAllergenOther => 'दूसरी एलर्जी';

  @override
  String get membersFormAllergens => 'एलर्जी';

  @override
  String get membersFormAllergensHelp => 'सूची में से चुनें, या खुद लिखें।';

  @override
  String get membersFormBirthYear => 'जन्म का वर्ष';

  @override
  String get membersFormBirthYearHelp =>
      'बच्चों और 2 साल से छोटे बच्चों की जाँच के लिए इस्तेमाल होता है।';

  @override
  String membersFormBirthYearInvalid(String year) {
    return '1900 से $year के बीच का वर्ष लिखें।';
  }

  @override
  String get membersFormCancel => 'रद्द करें';

  @override
  String membersFormClearAllergiesConfirm(String name) {
    return '$name की सारी एलर्जी हटाएँ? इन एलर्जी वाले उत्पादों पर उनके लिए चेतावनी नहीं दिखेगी।';
  }

  @override
  String get membersFormConditions => 'स्वास्थ्य स्थितियाँ';

  @override
  String get membersFormCustomAlerts => 'सामग्री अलर्ट';

  @override
  String get membersFormCustomAlertsHelp =>
      'लेबल पर ये मिलने पर हम इन्हें बताएँगे।';

  @override
  String get membersFormDiet => 'आहार';

  @override
  String get membersFormGoal => 'लक्ष्य (वैकल्पिक)';

  @override
  String get membersFormHealthFieldsNote =>
      'एलर्जी, स्वास्थ्य स्थितियाँ, लक्ष्य, ऊँचाई और वज़न केवल स्वास्थ्य डेटा के उपयोग की आपकी सहमति से सहेजे जाते हैं।';

  @override
  String get membersFormHeightCm => 'ऊँचाई (सेमी, वैकल्पिक)';

  @override
  String get membersFormHeightInvalid =>
      '30 से 250 सेमी के बीच ऊँचाई लिखें, या खाली छोड़ें।';

  @override
  String get membersFormName => 'नाम';

  @override
  String get membersFormNameInvalid => '40 अक्षरों तक का नाम लिखें।';

  @override
  String get membersFormNameRequired => 'नाम लिखें।';

  @override
  String get membersFormNotSet => 'तय नहीं';

  @override
  String membersFormNumberRange(String max, String min) {
    return '$min से $max के बीच की संख्या लिखें।';
  }

  @override
  String get membersFormRelation => 'रिश्ता';

  @override
  String get membersFormRelationRequired => 'रिश्ता चुनें।';

  @override
  String membersFormRemoveAllergy(String allergen) {
    return '$allergen हटाएँ';
  }

  @override
  String membersFormRemoveAllergyConfirm(String allergen, String name) {
    return '$name की एलर्जी की सूची से यह हटाएँ: $allergen? इसके बाद इसे रखने वाले उत्पादों पर उनके लिए चेतावनी नहीं दिखेगी।';
  }

  @override
  String get membersFormSave => 'सहेजें';

  @override
  String get membersFormSex => 'लिंग (वैकल्पिक)';

  @override
  String get membersFormWeightInvalid =>
      '2 से 300 किग्रा के बीच वज़न लिखें, या खाली छोड़ें।';

  @override
  String get membersFormWeightKg => 'वज़न (किग्रा, वैकल्पिक)';

  @override
  String get membersGoalBuildMuscle => 'मांसपेशियाँ बनाना';

  @override
  String get membersGoalHealthyEating => 'बेहतर खाना';

  @override
  String get membersGoalWeightGain => 'वज़न बढ़ाना';

  @override
  String get membersGoalWeightLoss => 'वज़न घटाना';

  @override
  String get membersLimitReached =>
      'आपके परिवार में 10 सदस्य हैं, इससे ज़्यादा नहीं जोड़ सकते।';

  @override
  String get membersRelationChild => 'बच्चा';

  @override
  String get membersRelationOther => 'अन्य';

  @override
  String get membersRelationParent => 'माता-पिता';

  @override
  String get membersRelationSelf => 'आप';

  @override
  String get membersRelationSpouse => 'जीवनसाथी';

  @override
  String get membersRemove => 'हटाएँ';

  @override
  String membersRemoveConfirm(String name) {
    return '$name को परिवार से हटाएँ?';
  }

  @override
  String get membersSaved => 'सहेजा गया';

  @override
  String get membersSexFemale => 'महिला';

  @override
  String get membersSexMale => 'पुरुष';

  @override
  String get membersSexOther => 'अन्य';

  @override
  String get membersTitle => 'परिवार';

  @override
  String get membersYouBadge => 'आप';

  @override
  String get methodologyBasedOn => 'आधार:';

  @override
  String get methodologyIntro =>
      'SmartNutri हर पैक्ड खाने को उसके लेबल और परिवार के हर सदस्य की प्रोफ़ाइल से तय नियमों के अनुसार जाँचता है। AI सिर्फ़ नतीजा समझाता है, कभी तय नहीं करता। यह जानकारी है, चिकित्सकीय सलाह नहीं।';

  @override
  String get methodologyMetaDescription =>
      'SmartNutri परिवार के हर सदस्य के लिए पैकेटबंद खाने की जाँच कैसे करता है: तय नियम, उनकी सीमाएँ और स्रोत। यह जानकारी है, चिकित्सकीय सलाह नहीं।';

  @override
  String get methodologyPendingReview =>
      'ये सीमाएँ अभी काम चलाने के मान हैं और किसी चिकित्सक की समीक्षा बाकी है।';

  @override
  String get methodologySectionAllergensDescription =>
      'हम हर एलर्जी वाले तत्व के सामग्री-नाम और पैक पर लिखी एलर्जी की जानकारी देखते हैं। अगर सामग्री पढ़ी न जा सके, तो हम कहते हैं कि लेबल स्पष्ट नहीं है, कभी ठीक नहीं कहते।';

  @override
  String get methodologySectionAllergensTitle => 'एलर्जी वाले तत्व';

  @override
  String get methodologySectionBloodSugarDescription =>
      'ब्लड शुगर पर ध्यान रखने वाले सदस्यों (डायबिटीज़, प्रीडायबिटीज़ या PCOS) के लिए हम ज़्यादा चीनी, प्रति सर्विंग ज़्यादा कार्बोहाइड्रेट, और ज़्यादा नमक या संतृप्त वसा वाले उत्पाद बताते हैं।';

  @override
  String get methodologySectionBloodSugarTitle => 'ब्लड शुगर';

  @override
  String get methodologySectionBuildMuscleDescription =>
      'मांसपेशियाँ बनाना चाहने वाले सदस्यों के लिए हम कैलोरी के हिसाब से अच्छे प्रोटीन वाले उत्पाद बताते हैं। यह लक्ष्य कभी सावधानी या बचें नहीं जोड़ता। फ़ूड लॉग में, जिन वयस्कों का वज़न दर्ज है, उन्हें शरीर के वज़न के आधार पर रोज़ के प्रोटीन की एक गाइड दिखती है। अगर आपको किडनी की बीमारी है, तो ज़्यादा प्रोटीन खाने से पहले अपने डॉक्टर से पूछें।';

  @override
  String get methodologySectionBuildMuscleTitle => 'मांसपेशियाँ बनाना';

  @override
  String get methodologySectionChildDescription =>
      'बच्चों के लिए हम 100 ग्राम या एक सर्विंग की चीनी को उनकी उम्र की दैनिक चीनी सीमा से मिलाते हैं।';

  @override
  String get methodologySectionChildTitle => 'बच्चे';

  @override
  String get methodologySectionClaimsDescription =>
      'हम \"शुगर फ्री\" या \"हाई प्रोटीन\" जैसे दावों को लेबल के मानों और FSSAI की सीमाओं से मिलाकर जाँचते हैं।';

  @override
  String get methodologySectionClaimsTitle => 'पैक के आगे लिखे दावे';

  @override
  String get methodologySectionCustomAlertsDescription =>
      'वे सामग्रियाँ जिनके बारे में सदस्य ने बताने को कहा है, जैसे पाम तेल या मैदा। ये पसंद हैं, इसलिए इनका कोई स्रोत नहीं है।';

  @override
  String get methodologySectionCustomAlertsTitle => 'आपके सामग्री अलर्ट';

  @override
  String get methodologySectionDailyLimitsDescription =>
      'फ़ूड लॉग में हम हर सदस्य के लिए एक दिन में दर्ज चीनी और नमक जोड़ते हैं और कुल मात्रा को उनकी उम्र की दैनिक सीमा से मिलाते हैं। प्रोटीन को दैनिक लक्ष्य की ओर प्रगति के रूप में दिखाया जाता है। लेबल पर कुल चीनी लिखी होती है, सिर्फ़ ऊपर से डाली गई चीनी नहीं, इसलिए यह ज़रूरत से ज़्यादा चेतावनी दे सकता है।';

  @override
  String get methodologySectionDailyLimitsTitle => 'दैनिक सीमाएँ';

  @override
  String get methodologySectionDietDescription =>
      'हम ऐसी सामग्री ढूँढ़ते हैं जो सदस्य के आहार (शाकाहारी, अंडाहारी, वीगन या जैन) से मेल न खाए, और पैक पर हरा या भूरा निशान देखते हैं।';

  @override
  String get methodologySectionDietTitle => 'आहार';

  @override
  String get methodologySectionHighInDescription =>
      'जब किसी पोषक तत्व की मात्रा प्रति 100 ग्राम या 100 मि.ली. इन सीमाओं के बराबर या उनसे ज़्यादा हो, तो उत्पाद को उस तत्व में अधिक बताया जाता है।';

  @override
  String get methodologySectionHighInTitle =>
      'चीनी, वसा, संतृप्त वसा या नमक अधिक';

  @override
  String get methodologySectionHypertensionDescription =>
      'हाई ब्लड प्रेशर वाले सदस्यों के लिए हम ज़्यादा नमक वाले उत्पाद बताते हैं।';

  @override
  String get methodologySectionHypertensionTitle => 'ब्लड प्रेशर';

  @override
  String get methodologySectionInfantDescription =>
      'शिशुओं और छोटे बच्चों के लिए हम अतिरिक्त चीनी, अतिरिक्त नमक, शहद और कैफ़ीन, और ज़्यादा चीनी या नमक बताते हैं।';

  @override
  String get methodologySectionInfantTitle => 'शिशु और छोटे बच्चे';

  @override
  String get methodologySectionNutriscore2023Description =>
      'हम लेबल से न्यूट्री-स्कोर ग्रेड निकालते हैं, इस तरीके के 2023 के अपडेट के अनुसार। इसकी गणना SmartNutri करता है; यह FSSAI रेटिंग नहीं है।';

  @override
  String get methodologySectionNutriscore2023Title =>
      'न्यूट्री-स्कोर (SmartNutri द्वारा गणना)';

  @override
  String get methodologySectionWeightLossDescription =>
      'वज़न घटा रहे सदस्यों के लिए हम ज़्यादा कैलोरी वाले उत्पाद और कम न्यूट्री-स्कोर ग्रेड बताते हैं, और कैलोरी के हिसाब से अच्छे प्रोटीन वाले उत्पाद भी बताते हैं।';

  @override
  String get methodologySectionWeightLossTitle => 'वज़न घटाना';

  @override
  String get methodologySourcesTitle => 'स्रोत';

  @override
  String get methodologyTitle => 'हम कैसे जाँचते हैं';

  @override
  String get methodologyUnavailable =>
      'हम अभी जाँच के नियम लोड नहीं कर पाए। कृपया थोड़ी देर बाद फिर से कोशिश करें।';

  @override
  String get methodologyUrlUnverified => 'लिंक की अभी जाँच नहीं हुई है';

  @override
  String get methodologyValues => 'नियम के मान';

  @override
  String methodologyVersion(String version) {
    return 'नियम संस्करण $version';
  }

  @override
  String get navFamily => 'परिवार';

  @override
  String get navHistory => 'इतिहास';

  @override
  String get navHome => 'होम';

  @override
  String get navLabel => 'मुख्य मेनू';

  @override
  String get navProfile => 'प्रोफ़ाइल';

  @override
  String get navScan => 'स्कैन';

  @override
  String get notfoundGoToLabel =>
      'हम इस उत्पाद को अभी नहीं जानते — इसके लेबल की फ़ोटो लें';

  @override
  String get nutrientCarbsG => 'कार्बोहाइड्रेट';

  @override
  String get nutrientEnergyKcal => 'ऊर्जा (कैलोरी)';

  @override
  String get nutrientFatG => 'वसा';

  @override
  String get nutrientProteinG => 'प्रोटीन';

  @override
  String get nutrientSalt => 'नमक';

  @override
  String get nutrientSatFat => 'संतृप्त वसा';

  @override
  String get nutrientSodiumMg => 'सोडियम';

  @override
  String get nutrientSugarsG => 'शर्करा (चीनी)';

  @override
  String get nutriscoreCalculatedBy =>
      'Nutri-Score की गणना SmartNutri ने की है';

  @override
  String get nutriscoreInsufficientData =>
      'Nutri-Score की गणना के लिए लेबल पर पर्याप्त जानकारी नहीं है।';

  @override
  String get policyOpenFailed => 'पेज नहीं खुल सका। कृपया फिर से कोशिश करें।';

  @override
  String get productClaimsHeading =>
      'लेबल पर किए गए दावे, SmartNutri द्वारा जाँचे गए';

  @override
  String productLabelSays(String claim) {
    return 'लेबल पर लिखा है: $claim';
  }

  @override
  String get productMetaDescription =>
      'इस पैकेट वाले खाद्य पदार्थ की पोषण जानकारी, SmartNutri द्वारा गणना किया गया Nutri-Score और सामग्री। जानकारी, चिकित्सकीय सलाह नहीं।';

  @override
  String productMetaTitle(String name) {
    return '$name – पोषण जानकारी | SmartNutri';
  }

  @override
  String get productNotFoundBody =>
      'बारकोड नंबर जाँचें। आप साइन इन करके लेबल की फ़ोटो लेकर यह उत्पाद जोड़ भी सकते हैं।';

  @override
  String get productPublicCta => 'अपने परिवार के लिए जाँचें';

  @override
  String get profileBody =>
      'आपके खाते, भाषा और गोपनीयता की सेटिंग्स यहाँ होंगी।';

  @override
  String get profileComingSoonBody =>
      'भाषा, गोपनीयता और खाते की सेटिंग्स यहाँ दिखेंगी।';

  @override
  String get profileComingSoonTitle => 'सेटिंग्स जल्द आ रही हैं';

  @override
  String get profileGiveConsent => 'सहमति दें';

  @override
  String get profilePrivacyTitle => 'गोपनीयता और सहमति';

  @override
  String get profileTitle => 'प्रोफ़ाइल';

  @override
  String reasonAddedSugars(String ingredients) {
    return 'इसमें अतिरिक्त शर्करा मिलाई गई है: $ingredients।';
  }

  @override
  String get reasonAgeUnknown =>
      'इस सदस्य का जन्म वर्ष जोड़ें: यह भोजन शायद छोटे बच्चों या शिशुओं के लिए उपयुक्त न हो।';

  @override
  String reasonAllergenContains(String allergen) {
    return 'इसमें $allergen है, जो आपकी बचने वाली सूची में है।';
  }

  @override
  String reasonAllergenMayContain(String allergen) {
    return 'इसमें $allergen हो सकता है, जो आपकी बचने वाली सूची में है।';
  }

  @override
  String reasonAllergenUnknown(String allergen) {
    return 'हम यह नहीं बता सकते कि इसमें $allergen है या नहीं।';
  }

  @override
  String reasonAllergenUnrecognised(String allergen) {
    return 'हम लेबल पर केवल \"$allergen\" शब्द ही खोज सकते हैं। सामग्री खुद भी जाँच लें।';
  }

  @override
  String reasonCarbsPerServingHigh(String basis, String carbs_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्विंग',
      'other': 'प्रति 100 ग्राम/मि.ली.',
    });
    return '$_temp0 $carbs_g ग्राम कार्बोहाइड्रेट। यह शायद आपकी स्थिति के लिए उपयुक्त न हो; अपने डॉक्टर से पूछें।';
  }

  @override
  String reasonCardioRiskHighIn(String high_in) {
    return 'इसमें $high_in अधिक है। ब्लड शुगर पर ध्यान रखने वाले लोगों को अक्सर इन्हें सीमित करने की सलाह दी जाती है; अपने डॉक्टर से पूछें।';
  }

  @override
  String get reasonChildCaffeine =>
      'इसमें कैफ़ीन है, जो बच्चों के लिए अनुशंसित नहीं है।';

  @override
  String reasonChildSaltHigh(String salt_g) {
    return 'प्रति 100 ग्राम/मि.ली. $salt_g ग्राम नमक बच्चे के लिए अधिक है।';
  }

  @override
  String reasonChildSugarHigh(String basis, String limit_g, String pct) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'एक सर्विंग में',
      'other': '100 ग्राम/मि.ली. में',
    });
    return '$_temp0 बच्चे की दैनिक चीनी सीमा (लगभग $limit_g ग्राम प्रतिदिन) का $pct% है। यह बच्चे के लिए अधिक है।';
  }

  @override
  String reasonChildSugarModerate(String basis, String limit_g, String pct) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'एक सर्विंग में',
      'other': '100 ग्राम/मि.ली. में',
    });
    return '$_temp0 बच्चे की दैनिक चीनी सीमा (लगभग $limit_g ग्राम प्रतिदिन) का $pct% है। यह बच्चे के लिए थोड़ा अधिक है।';
  }

  @override
  String reasonConditionUnrecognised(String condition) {
    return '\"$condition\" के लिए हमारे पास अभी मार्गदर्शन उपलब्ध नहीं है।';
  }

  @override
  String reasonCustomAlert(String alert, String ingredients) {
    return 'इसमें $alert है: $ingredients।';
  }

  @override
  String reasonCustomAlertUnknown(String alerts) {
    return 'इन अलर्ट की जाँच नहीं हो सकी: $alerts।';
  }

  @override
  String reasonDietUnknown(String diet) {
    return 'हम यह नहीं बता सकते कि यह $diet आहार के अनुकूल है या नहीं।';
  }

  @override
  String reasonDietViolation(String diet, String ingredients) {
    return 'यह शायद $diet आहार के अनुरूप न हो: $ingredients।';
  }

  @override
  String reasonEnergyDense(String energy_kcal) {
    return 'यह ऊर्जा से भरपूर (अधिक कैलोरी वाला) भोजन है (प्रति 100 ग्राम/मि.ली. $energy_kcal किलो कैलोरी)। कम मात्रा लेने पर विचार करें।';
  }

  @override
  String get reasonGoodProteinDensity =>
      'अपनी कैलोरी के हिसाब से अच्छी मात्रा में प्रोटीन।';

  @override
  String reasonHiddenSugars(String ingredients) {
    return 'इसमें अन्य नामों से लिखी गई शर्कराएँ हैं: $ingredients।';
  }

  @override
  String get reasonInfantAddedSalt =>
      'इसमें अतिरिक्त नमक है, जो 2 साल से छोटे बच्चों के लिए अनुशंसित नहीं है।';

  @override
  String get reasonInfantAddedSugar =>
      'इसमें अतिरिक्त चीनी है, जो 2 साल से छोटे बच्चों के लिए अनुशंसित नहीं है।';

  @override
  String get reasonInfantCaffeine =>
      'इसमें कैफ़ीन है, जो 2 साल से छोटे बच्चों के लिए अनुशंसित नहीं है।';

  @override
  String get reasonInfantHoney =>
      'इसमें शहद है, जो 1 साल से छोटे शिशुओं को नहीं देना चाहिए। इससे बड़े छोटे बच्चों के लिए अपने डॉक्टर से पूछें।';

  @override
  String reasonInfantSaltHigh(String salt_g) {
    return 'प्रति 100 ग्राम/मि.ली. $salt_g ग्राम नमक 2 साल से छोटे बच्चे के लिए अधिक है।';
  }

  @override
  String reasonInfantSugarHigh(String sugars_g) {
    return 'प्रति 100 ग्राम/मि.ली. $sugars_g ग्राम चीनी 2 साल से छोटे बच्चे के लिए अधिक है।';
  }

  @override
  String get reasonIngredientsMissing =>
      'सामग्री की सूची पढ़ी नहीं जा सकी, इसलिए कुछ जाँचें नहीं हो सकीं।';

  @override
  String reasonMisleadingSugarClaim(String claim) {
    return 'पैक पर \"$claim\" लिखा है, लेकिन लेबल की जानकारी इस दावे का समर्थन नहीं करती।';
  }

  @override
  String reasonNutrientMissing(String nutrient) {
    return 'लेबल पर $nutrient की जानकारी नहीं है, इसलिए यह जाँच नहीं हो सकी।';
  }

  @override
  String reasonNutriscoreLow(String grade) {
    return 'Nutri-Score $grade कुल पोषण गुणवत्ता कम होने का संकेत देता है।';
  }

  @override
  String reasonSaltHigh(String salt_g) {
    return 'नमक अधिक है: प्रति 100 ग्राम/मि.ली. $salt_g ग्राम।';
  }

  @override
  String reasonSaltModerate(String salt_g) {
    return 'नमक मध्यम है: प्रति 100 ग्राम/मि.ली. $salt_g ग्राम।';
  }

  @override
  String reasonSodiumAdditives(String ingredients) {
    return 'इसमें सोडियम वाले योजक हैं: $ingredients।';
  }

  @override
  String reasonSugarHigh(String sugars_g) {
    return 'चीनी अधिक है: प्रति 100 ग्राम/मि.ली. $sugars_g ग्राम।';
  }

  @override
  String reasonSugarModerate(String sugars_g) {
    return 'चीनी मध्यम है: प्रति 100 ग्राम/मि.ली. $sugars_g ग्राम।';
  }

  @override
  String get reasonVariantCustomAlertFlagOnly =>
      'उत्पाद की जानकारी के अनुसार इसमें स्वीटनर हैं।';

  @override
  String reasonVariantDietViolationMarkOnly(String diet) {
    return 'पैक पर भूरे रंग का मांसाहारी निशान है, इसलिए यह शायद $diet आहार के अनुरूप न हो।';
  }

  @override
  String reasonVariantNutrientMissingLowConfidence(String nutrient) {
    return 'लेबल पर $nutrient साफ़ नहीं पढ़ा जा सका, इसलिए यह जाँच नहीं हो सकी।';
  }

  @override
  String get reportButton => 'समस्या बताएँ';

  @override
  String get reportNoteHint =>
      'कृपया निजी या स्वास्थ्य से जुड़ी जानकारी न लिखें।';

  @override
  String get reportNoteLabel => 'और बताएँ (वैकल्पिक)';

  @override
  String get reportReasonLabel => 'क्या गलत है?';

  @override
  String get reportReasonOther => 'कुछ और';

  @override
  String get reportReasonWrongIngredients => 'सामग्री गलत है';

  @override
  String get reportReasonWrongProduct => 'यह कोई दूसरा उत्पाद है';

  @override
  String get reportReasonWrongValues => 'पोषण के मान गलत हैं';

  @override
  String get reportSubmit => 'रिपोर्ट भेजें';

  @override
  String get reportThanks =>
      'धन्यवाद। हम इस उत्पाद की जानकारी की समीक्षा करेंगे।';

  @override
  String get reportTitle => 'इस उत्पाद की जानकारी में क्या गलत है?';

  @override
  String get resultFamilyTitle => 'आपके परिवार के लिए';

  @override
  String resultForMember(String name) {
    return '$name के लिए';
  }

  @override
  String resultGrade(String grade) {
    return 'न्यूट्री-स्कोर $grade';
  }

  @override
  String get resultHighInTitle => 'इनमें अधिक';

  @override
  String get resultIngredients => 'सामग्री';

  @override
  String get resultMembersTitle => 'आपके परिवार के लिए';

  @override
  String get resultNoIngredients => 'सामग्री उपलब्ध नहीं';

  @override
  String get resultNotOnLabel => 'लेबल पर नहीं';

  @override
  String get resultNutritionTitle => 'प्रति 100 ग्राम/मि.ली. पोषण';

  @override
  String get resultScanAnother => 'दूसरा उत्पाद स्कैन करें';

  @override
  String get resultTitle => 'परिणाम';

  @override
  String get resultYou => 'आप';

  @override
  String get scanCameraDenied =>
      'कैमरा की अनुमति बंद है। आप बारकोड टाइप कर सकते हैं।';

  @override
  String get scanCameraUnavailable =>
      'कैमरा नहीं मिला। आप बारकोड टाइप कर सकते हैं।';

  @override
  String get scanInvalid =>
      'बारकोड के नीचे लिखे 8, 12, 13 या 14 अंक दर्ज करें।';

  @override
  String get scanLabelHint => 'बारकोड नहीं है? इसके बजाय लेबल की फ़ोटो लें।';

  @override
  String get scanManualEntry => 'या बारकोड टाइप करें';

  @override
  String get scanManualPlaceholder => 'जैसे 8901063201089';

  @override
  String get scanNotFound => 'यह उत्पाद अभी हमें नहीं मिला।';

  @override
  String get scanOffUnavailable =>
      'उत्पाद डेटाबेस अभी व्यस्त है। कृपया थोड़ी देर बाद फिर कोशिश करें।';

  @override
  String get scanRetry => 'फिर से कोशिश करें';

  @override
  String get scanScanning => 'कैमरा बारकोड की ओर रखें';

  @override
  String get scanSubmit => 'यह उत्पाद जाँचें';

  @override
  String get scanSubtitle =>
      'कैमरे को बारकोड की ओर रखें, या नीचे नंबर टाइप करें।';

  @override
  String get scanTitle => 'बारकोड स्कैन करें';

  @override
  String get searchHint =>
      'नाम या ब्रांड से उत्पाद ढूँढें, फिर उसे खोलें या तुलना करें।';

  @override
  String get searchNoResults => 'कोई उत्पाद नहीं मिला।';

  @override
  String get searchOffDegraded => 'और परिणाम बाद में जोड़े जाएँगे।';

  @override
  String get searchPlaceholder => 'नाम या ब्रांड से खोजें';

  @override
  String get searchSourceOff => 'Open Food Facts';

  @override
  String get searchSourceOurs => 'SmartNutri';

  @override
  String get searchTitle => 'उत्पाद खोजें';

  @override
  String get searchTooShort => 'कम से कम 3 अक्षर लिखें।';

  @override
  String get settingsAboutTitle => 'SmartNutri के बारे में';

  @override
  String get settingsAccountTitle => 'खाता';

  @override
  String get settingsDeleteBody =>
      'इससे आपका खाता, आपके परिवार की प्रोफ़ाइलें और स्वास्थ्य डेटा, स्कैन, खाने की एंट्री, लेबल की फ़ोटो और आवाज़ वाले जवाब हमेशा के लिए हट जाएँगे। आपके जोड़े गए उत्पाद आपके नाम के बिना साझा सूची में रहेंगे। इसे वापस नहीं किया जा सकता।';

  @override
  String get settingsDeleteButton => 'खाता हटाएँ';

  @override
  String get settingsDeleteConfirm => 'हमेशा के लिए हटाएँ';

  @override
  String settingsDeleteConfirmLabel(String word) {
    return 'पुष्टि के लिए $word लिखें';
  }

  @override
  String get settingsDeleteConfirmWord => 'DELETE';

  @override
  String get settingsDeleteDialogTitle => 'अपना खाता हमेशा के लिए हटाएँ?';

  @override
  String get settingsDeleteRetrying =>
      'अभी भी हटाया जा रहा है। फिर से कोशिश कर रहे हैं…';

  @override
  String get settingsDeleteTitle => 'खाता हटाएँ';

  @override
  String get settingsDeleting => 'आपका खाता हटाया जा रहा है…';

  @override
  String get settingsLanguageBody => 'इस डिवाइस पर SmartNutri की भाषा चुनें।';

  @override
  String get settingsLanguageSystem => 'डिवाइस की भाषा';

  @override
  String get shareButton => 'शेयर करें';

  @override
  String get shareCopied => 'लिंक कॉपी हो गया';

  @override
  String get shareCopyLink => 'लिंक कॉपी करें';

  @override
  String get shareInclude => 'किसी व्यक्ति का नतीजा जोड़ें (वैकल्पिक)';

  @override
  String shareLink(String url) {
    return 'SmartNutri से जाँचा गया: $url';
  }

  @override
  String get sharePreview => 'संदेश का पूर्वावलोकन';

  @override
  String get sharePrivacyNote =>
      'केवल उत्पाद और उसका ग्रेड शेयर होता है, और जिन लोगों को आप चुनें उनका नतीजा। स्वास्थ्य की जानकारी निजी रहती है।';

  @override
  String get shareRelationChild => 'बच्चा';

  @override
  String get shareRelationOther => 'परिवार का सदस्य';

  @override
  String get shareRelationParent => 'माता/पिता';

  @override
  String get shareRelationSelf => 'मैं';

  @override
  String get shareRelationSpouse => 'जीवनसाथी';

  @override
  String shareResultMember(String status, String who) {
    return '$who: $status';
  }

  @override
  String shareResultProductOnly(String grade, String product) {
    return '$product — न्यूट्री-स्कोर $grade (गणना SmartNutri ने की है)।';
  }

  @override
  String shareResultProductOnlyUngraded(String product) {
    return '$product — न्यूट्री-स्कोर के लिए लेबल पर पर्याप्त जानकारी नहीं।';
  }

  @override
  String shareResultText(String grade, String members, String product) {
    return '$product — न्यूट्री-स्कोर $grade (गणना SmartNutri ने की है)। $members।';
  }

  @override
  String shareResultUngraded(String members, String product) {
    return '$product — न्यूट्री-स्कोर के लिए लेबल पर पर्याप्त जानकारी नहीं। $members।';
  }

  @override
  String shareWeekly(String logged, String scans) {
    return 'SmartNutri पर हमारा हफ़्ता — जाँचे गए उत्पाद: $scans, दर्ज की गई चीज़ें: $logged।';
  }

  @override
  String get shareWeeklyButton => 'हमारा हफ़्ता शेयर करें';

  @override
  String get shareWhatsapp => 'WhatsApp पर शेयर करें';

  @override
  String get statusAvoid => 'बचें';

  @override
  String get statusCaution => 'सावधानी';

  @override
  String get statusOk => 'ठीक है';

  @override
  String get statusUnknown => 'लेबल स्पष्ट नहीं';

  @override
  String get summaryBandNear => 'सीमा के करीब';

  @override
  String get summaryBandOk => 'सीमा के भीतर';

  @override
  String get summaryBandOver => 'सीमा से ज़्यादा';

  @override
  String get summaryBandUnknown => 'पर्याप्त जानकारी नहीं';

  @override
  String get summaryIncomplete =>
      'कुछ दर्ज चीज़ों के लेबल पर यह मान नहीं है, इसलिए असली कुल इससे ज़्यादा हो सकता है।';

  @override
  String get summaryKcalInfo =>
      'कैलोरी केवल जानकारी के लिए दिखाई गई है। अभी कोई निजी कैलोरी लक्ष्य नहीं है।';

  @override
  String summaryKcalTotal(String total) {
    return '$total kcal';
  }

  @override
  String get summaryLimitsNote => 'सीमाएँ अभी चिकित्सक की समीक्षा में हैं।';

  @override
  String get summaryNoProteinTarget =>
      'इस सदस्य के लिए प्रोटीन का कोई लक्ष्य नहीं है';

  @override
  String get summaryNothingLogged => 'इस दिन कुछ दर्ज नहीं किया गया।';

  @override
  String get summaryNutrientEnergyKcal => 'कैलोरी';

  @override
  String get summaryNutrientProteinG => 'प्रोटीन';

  @override
  String get summaryNutrientSaltG => 'नमक';

  @override
  String get summaryNutrientSugarsG => 'शर्करा';

  @override
  String summaryProteinOfTarget(String target, String total) {
    return '$target ग्राम के लक्ष्य में से $total ग्राम';
  }

  @override
  String get summarySugarNote =>
      'लेबल पर कुल शर्करा होती है, जिसमें प्राकृतिक शर्करा भी शामिल है, इसलिए यह कुल केवल अतिरिक्त चीनी से ज़्यादा हो सकता है।';

  @override
  String get summaryTitleDay => 'आज';

  @override
  String get summaryTitleWeek => 'पिछले 7 दिन';

  @override
  String summaryTotalG(String total) {
    return '$total ग्राम';
  }

  @override
  String summaryTotalOfLimit(String limit, String total) {
    return '$limit ग्राम में से $total ग्राम';
  }

  @override
  String get summaryWeekNote =>
      'हफ़्ते की तुलना हर उस दिन की दैनिक सीमा से की जाती है, जिस दिन कुछ दर्ज किया गया।';

  @override
  String verdictConfidenceNote(String reason) {
    String _temp0 = intl.Intl.selectLogic(reason, {
      'low_confidence': 'लेबल पढ़ना कठिन था, इसलिए यह परिणाम कम निश्चित है।',
      'other': 'कुछ डेटा अनिश्चित है।',
    });
    return '$_temp0';
  }

  @override
  String verdictForMember(String name, String status) {
    return '$name के लिए $status';
  }

  @override
  String verdictForYou(String status) {
    return 'आपके लिए $status';
  }

  @override
  String get verdictHideReasons => 'कारण छिपाएँ';

  @override
  String get verdictProfileNotSetUp =>
      'प्रोफ़ाइल सेट नहीं है: उम्र, एलर्जी और आहार की अभी जाँच नहीं हुई है।';

  @override
  String get verdictReasonUnavailable =>
      'इस नतीजे की जानकारी इस संस्करण में उपलब्ध नहीं है।';

  @override
  String verdictRuleApplied(String rule) {
    return 'लागू नियम: $rule';
  }

  @override
  String get verdictShowAllReasons => 'सभी कारण दिखाएँ';

  @override
  String get verdictSpokenAvoid => 'इस सदस्य के लिए, इस उत्पाद से बचें।';

  @override
  String get verdictSpokenCaution =>
      'इस सदस्य के लिए, इस उत्पाद के साथ सावधानी रखें।';

  @override
  String get verdictSpokenOk => 'इस सदस्य के लिए यह उत्पाद ठीक लगता है।';

  @override
  String get verdictSpokenUnknown =>
      'इस सदस्य के लिए लेबल स्पष्ट नहीं है, इसलिए हम कुछ नहीं कह सकते।';

  @override
  String get verdictStatusAvoid => 'बचें';

  @override
  String get verdictStatusCaution => 'सावधानी';

  @override
  String get verdictStatusOk => 'ठीक है';

  @override
  String get verdictStatusUnknown => 'लेबल स्पष्ट नहीं';

  @override
  String get voiceAiUnavailable =>
      'आवाज़ वाले जवाब अभी उपलब्ध नहीं हैं। कृपया बाद में फिर कोशिश करें।';

  @override
  String get voiceAnswerTitle => 'जवाब';

  @override
  String get voiceButtonHold => 'पूछने के लिए दबाकर रखें';

  @override
  String voiceElapsed(String seconds) {
    return '30 में से $seconds सेकंड';
  }

  @override
  String get voiceHint =>
      'बटन दबाकर रखें, इस उत्पाद के बारे में पूछें, फिर छोड़ दें। शुरू करने के लिए Space दबाएँ और भेजने के लिए फिर से दबाएँ।';

  @override
  String get voiceMicDenied =>
      'माइक्रोफ़ोन की अनुमति बंद है। आवाज़ से पूछने के लिए सेटिंग्स में इसे चालू करें।';

  @override
  String get voiceNoMic => 'इस डिवाइस पर माइक्रोफ़ोन नहीं मिला।';

  @override
  String get voiceNotUnderstood =>
      'हमें कोई सवाल सुनाई नहीं दिया। बटन दबाए रखें और साफ़ बोलें।';

  @override
  String get voicePlaying => 'जवाब सुनाया जा रहा है';

  @override
  String get voiceRateLimited =>
      'आज के आवाज़ वाले सवालों की सीमा पूरी हो गई है।';

  @override
  String get voiceRecording => 'सुन रहे हैं… भेजने के लिए छोड़ें';

  @override
  String get voiceReplay => 'फिर से सुनें';

  @override
  String get voiceThinking => 'आपका जवाब तैयार हो रहा है…';

  @override
  String get voiceTitle => 'सवाल पूछें';

  @override
  String get voiceTooLong => 'कृपया अपना सवाल 30 सेकंड से छोटा रखें।';

  @override
  String get voiceUnsupportedBrowser =>
      'इस ब्राउज़र में आवाज़ से सवाल नहीं पूछे जा सकते। Chrome, Edge या Firefox का नया संस्करण आज़माएँ।';

  @override
  String get voiceWordSafe => 'सुरक्षित';

  @override
  String voiceYouAsked(String question) {
    return 'आपने पूछा: $question';
  }

  @override
  String get warningBasisMismatch =>
      'हम समझ नहीं पाए कि ये मान प्रति 100 g हैं या प्रति सर्विंग। पैक पर जो दिखे, वह चुनें।';

  @override
  String get warningCategoryCheck =>
      'जाँचें कि उत्पाद का प्रकार सही है, क्योंकि इससे मानों को पढ़ने का तरीका बदलता है।';

  @override
  String get warningCategoryUnknown =>
      'हम समझ नहीं पाए कि यह किस तरह का उत्पाद है। एक चुनें।';

  @override
  String get warningDerivedFromServing =>
      'यह मान प्रति सर्विंग की मात्रा से निकाला गया है। इसे पैक से मिलाकर देखें।';

  @override
  String get warningEnergyMismatch =>
      'ऊर्जा का मान बाकी मानों से मेल नहीं खा रहा। इसे पैक पर जाँचें।';

  @override
  String get warningImplausibleValue =>
      'यह मान असामान्य लग रहा है। कृपया इसे पैक से मिलाकर देखें।';

  @override
  String get warningKcalKjMismatch =>
      'kcal और kJ के मान आपस में मेल नहीं खा रहे। दोनों पैक पर जाँचें।';

  @override
  String get warningLowConfidence =>
      'लेबल पढ़ना मुश्किल था। कृपया हर मान को पैक से मिलाकर जाँचें।';

  @override
  String get warningPer100gMissing =>
      'पैक पर प्रति 100 g के मान नहीं मिले। संख्याएँ जाँचें या पैक से भरें।';

  @override
  String get warningPerServingIgnored =>
      'पैक के प्रति सर्विंग वाले मान इस्तेमाल नहीं किए गए। जाँचें कि प्रति 100 g के मान सही हैं।';

  @override
  String get warningSaltSodiumMismatch =>
      'नमक और सोडियम के मान आपस में मेल नहीं खा रहे। दोनों पैक पर जाँचें।';

  @override
  String get warningUnitUnconfirmed =>
      'इस मान की इकाई साफ़ नहीं थी। जैसा छपा है, वैसा mg या g चुनें।';

  @override
  String get warningUnreadableField =>
      'हम यह मान पढ़ नहीं पाए। इसे पैक से भरें या खाली छोड़ें।';

  @override
  String get warningUpperBound =>
      'पैक पर लिखा है कि इतनी मात्रा से \"कम\"। अगर यह सही है तो पुष्टि करें।';
}
