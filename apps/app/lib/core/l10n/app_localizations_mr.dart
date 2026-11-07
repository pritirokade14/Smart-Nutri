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
  String get alternativesCompare => 'तुलना करा';

  @override
  String alternativesForMember(String name) {
    return '$name साठी';
  }

  @override
  String get alternativesReasonNoBetterFound =>
      'या प्रकारात अधिक चांगल्या न्यूट्री-स्कोअरचे उत्पादन सापडले नाही.';

  @override
  String get alternativesReasonNoCategory =>
      'या उत्पादनासाठी आम्ही अजून पर्याय सुचवू शकत नाही.';

  @override
  String get alternativesReasonSourceProteinUnknown =>
      'प्रथिनांची तुलना करण्यासाठी या उत्पादनाच्या लेबलवर प्रथिने आणि ऊर्जेची पुरेशी माहिती नाही.';

  @override
  String get alternativesReasonSourceSupplement =>
      'सप्लिमेंटसाठी आम्ही इतर उत्पादने सुचवत नाही.';

  @override
  String get alternativesReasonSourceUngraded =>
      'तुलनेसाठी या उत्पादनाच्या लेबलवर पुरेशी माहिती नाही.';

  @override
  String get alternativesSubtitle =>
      'त्याच प्रकारचे उत्पादन, अधिक चांगल्या न्यूट्री-स्कोअरसह (गणना SmartNutri ने केली आहे)';

  @override
  String alternativesSugars(String value) {
    return 'साखर: $value ग्रॅम प्रति 100 ग्रॅम/मि.ली.';
  }

  @override
  String get alternativesTitle => 'अधिक चांगले पर्याय';

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
  String get categorySupplement => 'सप्लिमेंट';

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
  String get claimProteinAmount => 'प्रथिनांचे प्रमाण';

  @override
  String claimReasonAddedSugarIngredient(String ingredients) {
    return 'घटकांमध्ये वरून घातलेली साखर आहे: $ingredients.';
  }

  @override
  String get claimReasonBasisUnknown =>
      'हा दावा प्रति 100 ग्रॅम आहे की प्रति सर्व्हिंग हे स्पष्ट लिहिलेले नाही, त्यामुळे तो तक्त्याशी तपासता येत नाही.';

  @override
  String claimReasonBelowClaimed(String basis, String claimed, String value) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्व्हिंग',
      'other': 'प्रति 100 ग्रॅम',
    });
    return 'पोषण तक्त्यात $_temp0 $value ग्रॅम प्रथिने आहेत, जी दावा केलेल्या $claimed ग्रॅमपेक्षा कमी आहेत.';
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
  String claimReasonOtherProteinSource(String ingredients) {
    return 'घटकांमध्ये प्रथिनांचा दुसरा स्रोतही आहे: $ingredients.';
  }

  @override
  String claimReasonRefinedSugarIngredient(String ingredients) {
    return 'घटकांमध्ये रिफाइंड साखर आहे: $ingredients.';
  }

  @override
  String get claimReasonWheyNotListed => 'घटकांच्या यादीत व्हे नाही.';

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
  String get claimWheyOnly => '100% व्हे';

  @override
  String get claimWheyProtein => 'व्हे प्रोटीन';

  @override
  String get commonCancel => 'रद्द करा';

  @override
  String get commonClose => 'बंद करा';

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
  String get commonOpenSettings => 'सेटिंग्ज उघडा';

  @override
  String get commonRetry => 'पुन्हा प्रयत्न करा';

  @override
  String get commonSkipToContent => 'थेट मुख्य मजकुराकडे जा';

  @override
  String get compareBetterA => 'इथे पहिले उत्पादन अधिक चांगले आहे';

  @override
  String get compareBetterB => 'इथे दुसरे उत्पादन अधिक चांगले आहे';

  @override
  String get compareBetterChip => 'अधिक चांगले';

  @override
  String get compareBetterSame => 'जवळपास सारखे';

  @override
  String get compareBetterUnknown =>
      'तुलना करता येत नाही: एखाद्या लेबलवर हे मूल्य नाही';

  @override
  String get comparePickSecond => 'तुलनेसाठी एक उत्पादन निवडा';

  @override
  String get compareRowEnergyKcal => 'कॅलरी (प्रति 100 ग्रॅम/मि.ली.)';

  @override
  String get compareRowFiberG => 'तंतू (प्रति 100 ग्रॅम/मि.ली.)';

  @override
  String get compareRowGrade => 'न्यूट्री-स्कोअर (गणना SmartNutri ने केली आहे)';

  @override
  String get compareRowProteinG => 'प्रथिने (प्रति 100 ग्रॅम/मि.ली.)';

  @override
  String get compareRowSaltG => 'मीठ (प्रति 100 ग्रॅम/मि.ली.)';

  @override
  String get compareRowSatFatG => 'संपृक्त चरबी (प्रति 100 ग्रॅम/मि.ली.)';

  @override
  String get compareRowSugarsG => 'साखर (प्रति 100 ग्रॅम/मि.ली.)';

  @override
  String get compareTitle => 'तुलना करा';

  @override
  String get conditionBuildMuscle => 'स्नायू बळकट करणे';

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
  String get confirmCategoryOptionFat => 'तेल, चरबी, नट्स किंवा बिया';

  @override
  String get confirmCategoryOptionGeneral => 'खाद्यपदार्थ';

  @override
  String get confirmCategoryOptionSupplement =>
      'सप्लिमेंट (प्रोटीन पावडर, व्हे, हेल्थ सप्लिमेंट)';

  @override
  String get confirmCategoryOptionWater => 'पॅक्ड पाणी';

  @override
  String get confirmCategorySuggestionSupplement =>
      'घटक किंवा प्रथिनांच्या प्रमाणावरून हे सप्लिमेंट (प्रोटीन पावडर किंवा व्हे) असू शकते असे दिसते. तसे असल्यास, प्रकारात सप्लिमेंट निवडा.';

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
  String get consentNeedsUpdate => 'अपडेट झाले आहे, कृपया पाहा';

  @override
  String get consentNotGranted => 'संमती दिलेली नाही';

  @override
  String get consentPromptBody =>
      'पुढे जाण्यासाठी कृपया यांना संमती द्या. तुम्ही तुमच्या प्रोफाइलमधून कधीही संमती मागे घेऊ शकता.';

  @override
  String get consentPromptTitle => 'तुमची संमती हवी आहे';

  @override
  String get consentRequiredNote =>
      'ॲलर्जी, आरोग्य स्थिती, उद्दिष्ट, उंची किंवा वजन जतन करण्यासाठी आवश्यक.';

  @override
  String get consentRequiredToContinue =>
      'पुढे जाण्यासाठी कृपया पाहा आणि संमती द्या.';

  @override
  String get consentReviewAgree => 'वाचा आणि संमती द्या';

  @override
  String get consentTermsBody =>
      'मी SmartNutri च्या वापराच्या अटी आणि गोपनीयता धोरणाशी सहमत आहे.';

  @override
  String get consentTermsStepBody =>
      'कृपया आमच्या वापराच्या अटी आणि गोपनीयता सूचना वाचा. उत्पादने तपासण्यासाठी आणि स्कॅन करण्यासाठी तुम्हाला त्यांना संमती द्यावी लागेल.';

  @override
  String get consentTermsStepLeaveNote =>
      'संमती द्यायची नाही? तुम्ही साइन आउट करू शकता, किंवा तुमच्या प्रोफाइलमधून तुमचे खाते हटवू शकता.';

  @override
  String get consentTermsStepReadPrivacy => 'गोपनीयता सूचना';

  @override
  String get consentTermsStepReadTerms => 'वापराच्या अटी';

  @override
  String get consentTermsStepTitle => 'सुरू करण्यापूर्वी';

  @override
  String get consentTermsStepUpdatedBody =>
      'आमच्या वापराच्या अटी किंवा गोपनीयता सूचना बदलल्या आहेत. उत्पादने तपासणे आणि स्कॅन करणे सुरू ठेवण्यासाठी कृपया त्या वाचा आणि पुन्हा संमती द्या.';

  @override
  String get consentTermsStepUpdatedTitle =>
      'आम्ही आमच्या अटी अपडेट केल्या आहेत';

  @override
  String get consentTermsTitle => 'वापराच्या अटी';

  @override
  String get consentTermsWithdrawConfirm =>
      'संमती मागे घेतल्यास, पुन्हा संमती देईपर्यंत तुम्ही उत्पादने तपासू किंवा स्कॅन करू शकणार नाही. तुमचे खाते हटवेपर्यंत तुमचा जतन केलेला डेटा राहील.';

  @override
  String get consentUpdateNote =>
      'आम्ही हा मजकूर अद्ययावत केला आहे. कृपया तो वाचा आणि पुन्हा संमती द्या.';

  @override
  String get consentUpdatesBanner =>
      'आम्ही काही संमतीचे मजकूर अद्ययावत केले आहेत. कृपया ते पाहा.';

  @override
  String get consentWithdraw => 'संमती मागे घ्या';

  @override
  String get diaryDisclaimer =>
      'ही माहिती आहे, वैद्यकीय सल्ला नाही. दैनिक मार्गदर्शक हे अंदाज आहेत आणि डॉक्टरांच्या तपासणीसाठी प्रलंबित आहेत.';

  @override
  String get diaryEyeHide => 'संख्या लपवा';

  @override
  String get diaryEyeShow => 'संख्या दाखवा';

  @override
  String get diaryHiddenNumbers =>
      'संख्या लपवल्या आहेत. तुम्ही हे सेटिंग्जमध्ये बदलू शकता.';

  @override
  String get diaryIncomplete =>
      'काही पदार्थांमध्ये हे मूल्य दिसत नाही, म्हणून खरी बेरीज जास्त असू शकते.';

  @override
  String diaryOfTarget(String eaten, String target) {
    return '$target पैकी $eaten';
  }

  @override
  String get diaryTargetsConsent =>
      'तुमचा दैनिक मार्गदर्शक पाहण्यासाठी, SmartNutri ला तुमची आरोग्य माहिती वापरण्याची परवानगी द्या.';

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
  String get errorAdaptiveNotEnabled => 'हा पर्याय अजून उपलब्ध नाही.';

  @override
  String get errorAiUnavailable =>
      'आवाजातील उत्तरे सध्या उपलब्ध नाहीत. कृपया नंतर पुन्हा प्रयत्न करा.';

  @override
  String get errorAudioTooLarge =>
      'हे रेकॉर्डिंग खूप मोठे आहे. कृपया छोटा प्रश्न विचारा.';

  @override
  String get errorAudioTooLong =>
      'हे रेकॉर्डिंग 30 सेकंदांपेक्षा मोठे आहे. कृपया छोटा प्रश्न विचारा.';

  @override
  String get errorAudioUnsupported =>
      'आम्ही हे रेकॉर्डिंग चालवू शकलो नाही. कृपया पुन्हा प्रयत्न करा.';

  @override
  String get errorAuthInvalid =>
      'तुमचे सत्र संपले आहे. कृपया पुन्हा साइन इन करा.';

  @override
  String get errorAuthRequired => 'कृपया साइन इन करा.';

  @override
  String get errorBodyFatOutOfRange =>
      'कृपया 3 ते 70 दरम्यान शरीरातील चरबीची टक्केवारी भरा.';

  @override
  String get errorConsentRequired =>
      'ॲलर्जी, आरोग्य स्थिती, उद्दिष्ट, उंची किंवा वजन जतन करण्यासाठी, कृपया आधी आरोग्य डेटाच्या वापराला संमती द्या.';

  @override
  String get errorConsentVersionMismatch =>
      'संमतीचा मजकूर अद्ययावत झाला आहे. कृपया पुन्हा लोड करून तो पुन्हा पाहा.';

  @override
  String get errorDateInFuture => 'ती तारीख अजून आलेली नाही.';

  @override
  String get errorDeletionIncomplete =>
      'आम्ही तुमचे खाते पूर्णपणे हटवू शकलो नाही. कृपया पुन्हा प्रयत्न करा; जे हटले आहे ते परत येणार नाही.';

  @override
  String get errorDiaryMemberNotEnabled =>
      'दैनिक मार्गदर्शक सध्या फक्त तुमच्या स्वतःच्या प्रोफाइलसाठी उपलब्ध आहेत.';

  @override
  String get errorEatenAtOutOfRange => 'गेल्या 30 दिवसांतील वेळ निवडा.';

  @override
  String get errorExtractionFailed =>
      'आम्हाला हे लेबल वाचता आले नाही. दुसरा फोटो वापरून पाहा किंवा माहिती स्वतः भरा.';

  @override
  String get errorExtractionUnavailable =>
      'लेबल वाचण्याची सुविधा सध्या उपलब्ध नाही. नंतर पुन्हा प्रयत्न करा किंवा माहिती स्वतः भरा.';

  @override
  String get errorFatPctOutOfRange =>
      'कृपया कॅलरीतील चरबीचा वाटा 20% ते 30% दरम्यान निवडा.';

  @override
  String get errorFollowUpWithoutType =>
      'कृपया तुमची उत्तरे तपासा आणि पुन्हा प्रयत्न करा.';

  @override
  String get errorForbidden => 'तुम्हाला याचा प्रवेश नाही.';

  @override
  String get errorGoalNotAllowedMinor =>
      'दैनिक मार्गदर्शक प्रौढांसाठी आहेत. तुम्ही तरीही जेवण नोंदवू शकता.';

  @override
  String get errorGoalNotAllowedUnderweight =>
      'त्याऐवजी आम्ही तुम्हाला स्थिर वजन राखण्यास मदत करू शकतो.';

  @override
  String get errorGoalSettingsNotFound => 'आधी तुमचा दैनिक मार्गदर्शक सेट करा.';

  @override
  String get errorHttpError => 'काहीतरी चुकले. कृपया पुन्हा प्रयत्न करा.';

  @override
  String get errorImageQualityLow =>
      'हा फोटो नीट वाचता येत नाही. कृपया पुन्हा फोटो काढा.';

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
  String get errorMealNotFound => 'ही खाण्याची नोंद सापडली नाही.';

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
  String get errorPayloadTooLarge =>
      'ही विनंती खूप मोठी आहे. कृपया कमी डेटासह पुन्हा प्रयत्न करा.';

  @override
  String get errorPhoneOtpDisabled =>
      'फोनने साइन-इन अद्याप उपलब्ध नाही. कृपया ईमेल किंवा Google ने साइन इन करा.';

  @override
  String get errorPortionRequired =>
      'किती खाल्ले ते निवडा: सर्व्हिंग किंवा ग्रॅम.';

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
  String get errorRateNotAllowed =>
      'ती गती उपलब्ध नाही. कृपया दाखवलेल्या पर्यायांपैकी निवडा.';

  @override
  String get errorScanImageNotFound =>
      'तो फोटो आम्हाला सापडला नाही. कृपया फोटो पुन्हा काढा किंवा अपलोड करा.';

  @override
  String get errorScanNotFound =>
      'हा लेबल स्कॅन सापडला नाही. कृपया लेबल पुन्हा स्कॅन करा.';

  @override
  String get errorSearchQueryTooShort => 'शोधण्यासाठी किमान 3 अक्षरे लिहा.';

  @override
  String get errorServingSizeUnknown =>
      'या पॅकवर सर्व्हिंगचा आकार दिलेला नाही. प्रमाण ग्रॅममध्ये भरा.';

  @override
  String get errorStorageUnavailable =>
      'आम्ही सध्या फोटो हाताळू शकलो नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.';

  @override
  String get errorTargetWeightTooLow => 'कृपया जास्त लक्ष्य वजन निवडा.';

  @override
  String get errorUnauthorized => 'कृपया साइन इन करा.';

  @override
  String get errorUnsupportedImage => 'कृपया JPEG, PNG किंवा WebP फोटो वापरा.';

  @override
  String get errorUserTypeNotSelected =>
      'तुम्ही स्वतःसाठी निवडलेल्या पर्यायांपैकी एक निवडा.';

  @override
  String get errorUserTypesNotFound =>
      'आधी सांगा की तुम्ही SmartNutri का वापरत आहात.';

  @override
  String get errorValidationError => 'कृपया अधोरेखित केलेली फील्ड तपासा.';

  @override
  String get errorVoiceNotUnderstood =>
      'आम्हाला प्रश्न ऐकू आला नाही. कृपया बटण दाबून ठेवा आणि स्पष्ट बोला.';

  @override
  String get explanationAiNote =>
      'वरील निकालांवरून AI ने लिहिले आहे. यामुळे कोणताही निकाल बदलत नाही.';

  @override
  String get explanationFallbackTip1 =>
      'सारख्या उत्पादनांची लेबले तुलना करा आणि कमी साखर व कमी मीठ असलेले उत्पादन निवडा.';

  @override
  String get explanationFallbackTip2 =>
      'पॅकवरील सर्व्हिंगचा आकार पाहा: लेबलवरील मूल्ये प्रति 100 ग्रॅम किंवा 100 मि.ली. असतात.';

  @override
  String get explanationFallbackTip3 =>
      'तुम्हाला आरोग्याची काही समस्या असल्यास, बदल करण्यापूर्वी तुमच्या डॉक्टरांना किंवा आहारतज्ज्ञांना विचारा.';

  @override
  String get explanationSourceFallbackNote =>
      'AI स्पष्टीकरण सध्या उपलब्ध नाही, म्हणून हा सारांश आमच्या नियमांवरून तयार केला आहे.';

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
  String get footerLinksLabel => 'SmartNutri विषयी';

  @override
  String get footerTagline => 'भारतीय कुटुंबांसाठी पॅकबंद अन्नाची माहिती.';

  @override
  String get goalBuildMuscle => 'स्नायू वाढवणे';

  @override
  String get goalHealthyEating => 'चांगले खाणे';

  @override
  String get goalWeightGain => 'वजन वाढवणे';

  @override
  String get goalWeightLoss => 'वजन कमी करणे';

  @override
  String get goodbyeAction => 'साइन इनकडे परत जा';

  @override
  String get goodbyeBody =>
      'तुमचे खाते आणि त्याचा डेटा हटवला गेला आहे, आणि तुम्ही साइन आउट झाला आहात. SmartNutri वापरून पाहिल्याबद्दल धन्यवाद.';

  @override
  String get goodbyeMetaTitle => 'खाते हटवले';

  @override
  String get goodbyeTitle => 'तुमचे खाते हटवले गेले आहे';

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
  String get historyEmpty => 'अजून काहीही नोंदवलेले नाही.';

  @override
  String historyItemAmount(String grams) {
    return '$grams ग्रॅम';
  }

  @override
  String get historyLoggedTitle => 'काय खाल्ले';

  @override
  String get historyMember => 'कुटुंबातील सदस्य';

  @override
  String get historyNextDay => 'पुढील दिवस';

  @override
  String get historyPreviousDay => 'मागील दिवस';

  @override
  String get historyRemove => 'काढा';

  @override
  String get historyRemoveConfirm => 'हे नोंदीतून काढायचे?';

  @override
  String get historyThisWeek => 'या आठवड्यात';

  @override
  String get historyTitle => 'इतिहास';

  @override
  String get historyToday => 'आज';

  @override
  String get homeCardsAllergyCheckAddCta => 'अॅलर्जी जोडा';

  @override
  String homeCardsAllergyCheckMemberLine(String allergens, String name) {
    return '$name: $allergens';
  }

  @override
  String get homeCardsAllergyCheckNone => 'अजून कोणतीही अॅलर्जी जोडलेली नाही.';

  @override
  String get homeCardsAllergyCheckTitle => 'अॅलर्जी तपासणी';

  @override
  String get homeCardsAllergyCheckUnknownNote =>
      'अज्ञात म्हणजे आम्ही तपासू शकलो नाही, म्हणून ते कधीही सुरक्षित म्हणून दाखवले जात नाही.';

  @override
  String get homeCardsClaimsTipBody =>
      'शुगर-फ्री? आम्ही दावे लेबलशी जुळवून तपासतो.';

  @override
  String get homeCardsClaimsTipTitle => 'पॅकवरील दावे';

  @override
  String get homeCardsCustomAlertsSetupBody =>
      'लेबलवर आम्ही दाखवावेत असे घटक निवडा.';

  @override
  String get homeCardsCustomAlertsSetupCta => 'अलर्ट सेट करा';

  @override
  String get homeCardsCustomAlertsSetupTitle => 'घटक अलर्ट';

  @override
  String get homeCardsFamilyStripAdd => 'सदस्य जोडा';

  @override
  String get homeCardsFamilyStripTitle => 'तुमचे कुटुंब';

  @override
  String get homeCardsNotCoveredBody =>
      'अजून समाविष्ट नाही: थायरॉईड, कोलेस्टेरॉल, मूत्रपिंडाचा आजार, गर्भधारणा.';

  @override
  String get homeCardsNotCoveredTitle => 'अजून समाविष्ट नाही';

  @override
  String get homeCardsProteinClaimsTipBody =>
      'आम्ही प्रथिनांचे दावे पोषण तक्त्याशी जुळवून तपासतो.';

  @override
  String get homeCardsProteinClaimsTipTitle => 'प्रथिनांचे दावे';

  @override
  String get homeCardsProteinSwapsCta => 'जास्त प्रथिनांचे पर्याय शोधा';

  @override
  String get homeCardsProteinSwapsTitle => 'जास्त प्रथिनांचे पर्याय';

  @override
  String get homeCardsRecentScansTitle => 'अलीकडील स्कॅन';

  @override
  String get homeCardsTodayProteinTitle => 'आज: प्रथिने';

  @override
  String get homeCardsTodaySugarSaltTitle => 'आज: साखर आणि मीठ';

  @override
  String get homeCardsTodayTargetsTitle => 'आज';

  @override
  String get homeCardsUnknownExplainerBody =>
      'लेबलवर घटक नसतील किंवा वाचणे कठीण असेल, तेव्हा आम्ही तपासू शकत नाही. आम्ही ते कधीही सुरक्षित दाखवत नाही.';

  @override
  String get homeCardsUnknownExplainerTitle => '\"अज्ञात\" सुरक्षित का नाही';

  @override
  String homeCardsWeeklyFamilyBody(String count) {
    return 'गेल्या 7 दिवसांत तुमच्या कुटुंबासाठी $count गोष्टी नोंदवल्या';
  }

  @override
  String get homeCardsWeeklyFamilyTitle => 'या आठवड्यात';

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
  String get imageQualityBlur =>
      'फोटो धूसर आहे. फोन स्थिर धरा आणि फोकससाठी लेबलवर टॅप करा.';

  @override
  String get imageQualityGlare =>
      'प्रकाशामुळे फोटो फिका पडला आहे. फ्लॅश बंद करा किंवा पॅक प्रकाशापासून थोडा वळवा.';

  @override
  String get imageQualityHintGeneric =>
      'चांगल्या प्रकाशात संपूर्ण लेबल फ्रेममध्ये घेऊन फोटो काढा.';

  @override
  String get imageQualityTitle => 'कृपया फोटो पुन्हा काढा';

  @override
  String get imageQualityTooSmall =>
      'फोटो खूप लहान आहे. जवळून फोटो काढा, म्हणजे लेबल पूर्ण फ्रेममध्ये येईल.';

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
  String get legalDraftNotice =>
      'मसुदा: लॉन्चपूर्वी एक वकील या दस्तऐवजाचे पुनरावलोकन करत आहेत.';

  @override
  String get legalEnglishOnly => 'हा दस्तऐवज सध्या फक्त इंग्रजीत उपलब्ध आहे.';

  @override
  String get legalPrivacyDescription =>
      'भारताच्या DPDP कायदा, 2023 अंतर्गत SmartNutri AI तुमच्या कुटुंबाचा डेटा कसा गोळा करते, वापरते आणि सुरक्षित ठेवते.';

  @override
  String get legalPrivacyTitle => 'गोपनीयता सूचना';

  @override
  String get legalTermsDescription =>
      'SmartNutri AI वापरण्याच्या अटी. ही माहिती आहे, वैद्यकीय सल्ला नाही.';

  @override
  String get legalTermsTitle => 'वापराच्या अटी';

  @override
  String legalVersion(String version) {
    return 'आवृत्ती $version';
  }

  @override
  String get mealsLogAmountGrams => 'प्रमाण ग्रॅममध्ये';

  @override
  String mealsLogAmountInvalid(String max) {
    return '0 पेक्षा जास्त आणि $max पर्यंत प्रमाण टाका.';
  }

  @override
  String get mealsLogAmountServings => 'सर्व्हिंगची संख्या';

  @override
  String get mealsLogCta => 'मी हे खाल्ले';

  @override
  String mealsLogCtaFor(String name) {
    return 'मी हे खाल्ले, $name';
  }

  @override
  String get mealsLogEatenAt => 'केव्हा';

  @override
  String get mealsLogGrams => 'ग्रॅम';

  @override
  String get mealsLogMember => 'कोणी खाल्ले?';

  @override
  String get mealsLogNow => 'आता';

  @override
  String get mealsLogPortion => 'किती खाल्ले?';

  @override
  String get mealsLogSave => 'जतन करा';

  @override
  String mealsLogSaved(String who) {
    return '$who साठी नोंदवले';
  }

  @override
  String get mealsLogSavedYou => 'तुमच्यासाठी नोंदवले';

  @override
  String mealsLogServingSize(String grams) {
    return '1 सर्व्हिंग = $grams ग्रॅम';
  }

  @override
  String get mealsLogServings => 'सर्व्हिंग';

  @override
  String get mealsLogTitle => 'काय खाल्ले ते नोंदवा';

  @override
  String get mealsLogUndo => 'पूर्ववत करा';

  @override
  String get mealsLogUndone => 'नोंदीतून काढले';

  @override
  String get mealsOnlineOnly =>
      'वेबवर नोंद करण्यासाठी इंटरनेट लागते. ऑफलाइन काहीही जतन होत नाही.';

  @override
  String get mealsQueuedOffline =>
      'या फोनवर जतन केले. ऑनलाइन आल्यावर ते नोंदीत जोडले जाईल.';

  @override
  String get mealsSyncFailed =>
      'काही गोष्टी नोंदीत जोडता आल्या नाहीत. कृपया त्या पुन्हा नोंदवा.';

  @override
  String get mealsSyncing => 'नोंदवलेल्या गोष्टी सिंक होत आहेत…';

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
  String get membersGoalBuildMuscle => 'स्नायू बळकट करणे';

  @override
  String get membersGoalBuildMuscleAdultsOnly =>
      'स्नायू बळकट करणे हे प्रौढांसाठी (18 वर्षे आणि त्याहून अधिक) असलेले ध्येय आहे. या सदस्यासाठी दुसरे ध्येय निवडा.';

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
  String get methodologyBasedOn => 'आधार:';

  @override
  String get methodologyIntro =>
      'SmartNutri प्रत्येक पॅकबंद अन्न त्याच्या लेबलवरून आणि कुटुंबातील प्रत्येक सदस्याच्या प्रोफाइलवरून ठरलेल्या नियमांनुसार तपासते. AI फक्त निकाल समजावून सांगते, तो कधीच ठरवत नाही. ही माहिती आहे, वैद्यकीय सल्ला नाही.';

  @override
  String get methodologyMetaDescription =>
      'SmartNutri कुटुंबातील प्रत्येक सदस्यासाठी पॅकबंद अन्न कसे तपासते: ठरलेले नियम, त्यांच्या मर्यादा आणि स्रोत. ही माहिती आहे, वैद्यकीय सल्ला नाही.';

  @override
  String get methodologyPendingReview =>
      'या मर्यादा सध्या कामचलाऊ मूल्ये आहेत आणि डॉक्टरांचे पुनरावलोकन बाकी आहे.';

  @override
  String get methodologySectionAllergensDescription =>
      'आम्ही प्रत्येक ॲलर्जी घटकाची घटक-नावे आणि पॅकवरील ॲलर्जीची माहिती पाहतो. घटक वाचता आले नाहीत, तर आम्ही लेबल स्पष्ट नाही असे सांगतो, कधीच ठीक आहे असे नाही.';

  @override
  String get methodologySectionAllergensTitle => 'ॲलर्जी घटक';

  @override
  String get methodologySectionBloodSugarDescription =>
      'रक्तातील साखरेकडे लक्ष देणाऱ्या सदस्यांसाठी (मधुमेह, प्रीडायबिटीज किंवा PCOS) आम्ही जास्त साखर, प्रति सर्व्हिंग जास्त कार्बोहायड्रेट आणि जास्त मीठ किंवा संतृप्त फॅट असलेली उत्पादने दाखवतो.';

  @override
  String get methodologySectionBloodSugarTitle => 'रक्तातील साखर';

  @override
  String get methodologySectionBuildMuscleDescription =>
      'स्नायू बळकट करू इच्छिणाऱ्या प्रौढ सदस्यांसाठी (18 वर्षे आणि त्याहून अधिक) आम्ही कॅलरीच्या मानाने चांगले प्रथिन असलेली उत्पादने सांगतो. हे ध्येय कधीही सावधगिरी किंवा टाळा जोडत नाही, आणि 18 वर्षांखालील सदस्यांसाठी ते निवडता येत नाही. फूड लॉगमध्ये, ज्या प्रौढांचे वजन नोंदवले आहे त्यांना शरीराच्या वजनावर आधारित रोजच्या प्रथिनांचे मार्गदर्शन दिसते. तुम्हाला मूत्रपिंडाचा आजार असल्यास, जास्त प्रथिने खाण्यापूर्वी तुमच्या डॉक्टरांना विचारा.';

  @override
  String get methodologySectionBuildMuscleTitle => 'स्नायू बळकट करणे';

  @override
  String get methodologySectionChildDescription =>
      'मुलांसाठी आम्ही 100 ग्रॅम किंवा एका सर्व्हिंगमधील साखर त्यांच्या वयाच्या दैनिक साखर मर्यादेशी तुलना करतो.';

  @override
  String get methodologySectionChildTitle => 'मुले';

  @override
  String get methodologySectionClaimsDescription =>
      '\"शुगर फ्री\" किंवा \"हाय प्रोटीन\" यांसारखे दावे आम्ही लेबलवरील मूल्ये आणि FSSAI मर्यादांशी जुळवून तपासतो.';

  @override
  String get methodologySectionClaimsTitle => 'पॅकच्या पुढील दावे';

  @override
  String get methodologySectionCustomAlertsDescription =>
      'ज्या घटकांबद्दल सदस्याने सांगायला सांगितले आहे, जसे पाम तेल किंवा मैदा. या आवडीनिवडी आहेत, त्यामुळे त्यांना कोणताही स्रोत नाही.';

  @override
  String get methodologySectionCustomAlertsTitle => 'तुमचे घटक अलर्ट';

  @override
  String get methodologySectionDailyLimitsDescription =>
      'फूड लॉगमध्ये आम्ही प्रत्येक सदस्यासाठी एका दिवसात नोंदवलेली साखर आणि मीठ एकत्र करतो आणि एकूण प्रमाणाची त्यांच्या वयाच्या दैनिक मर्यादेशी तुलना करतो. प्रथिने दैनिक लक्ष्याकडे प्रगती म्हणून दाखवली जातात. लेबलवर एकूण साखर दिलेली असते, फक्त वरून घातलेली साखर नाही, त्यामुळे हे गरजेपेक्षा जास्त इशारा देऊ शकते.';

  @override
  String get methodologySectionDailyLimitsTitle => 'दैनिक मर्यादा';

  @override
  String get methodologySectionDietDescription =>
      'सदस्याच्या आहाराशी (शाकाहारी, अंडाहारी, व्हीगन किंवा जैन) न जुळणारे घटक आम्ही शोधतो आणि पॅकवरील हिरवी किंवा तपकिरी खूण तपासतो.';

  @override
  String get methodologySectionDietTitle => 'आहार';

  @override
  String get methodologySectionEnergyTargetsDescription =>
      'तुमचा दैनिक मार्गदर्शक हा एक अंदाज आहे. आम्ही वय, लिंग, उंची आणि वजन वापरून मिफ्लिन-सेंट जिओर समीकरण घेतो, त्याला हालचालीच्या पातळीने गुणतो, निवडलेल्या ध्येयासाठी हळुवार बदल करतो आणि निकालावरून प्रथिने, चरबी आणि कार्ब्स ठरवतो. किमान मर्यादा आणि गतीच्या मर्यादा नेहमी लागू असतात. प्रत्येक मूल्य डॉक्टरांच्या तपासणीसाठी प्रलंबित आहे. ही माहिती आहे, वैद्यकीय सल्ला नाही.';

  @override
  String get methodologySectionEnergyTargetsTitle =>
      'आम्ही दैनिक मार्गदर्शक कसा ठरवतो';

  @override
  String get methodologySectionHighInDescription =>
      'एखाद्या पोषक घटकाचे प्रमाण प्रति 100 ग्रॅम किंवा 100 मि.ली. या मर्यादांइतके किंवा त्यापेक्षा जास्त असल्यास, उत्पादनात तो घटक जास्त असल्याचे दाखवले जाते.';

  @override
  String get methodologySectionHighInTitle =>
      'साखर, फॅट, संतृप्त फॅट किंवा मीठ जास्त';

  @override
  String get methodologySectionHypertensionDescription =>
      'उच्च रक्तदाब असलेल्या सदस्यांसाठी आम्ही जास्त मीठ असलेली उत्पादने दाखवतो.';

  @override
  String get methodologySectionHypertensionTitle => 'रक्तदाब';

  @override
  String get methodologySectionInfantDescription =>
      'बाळांसाठी आणि लहान मुलांसाठी आम्ही अतिरिक्त साखर, अतिरिक्त मीठ, मध आणि कॅफिन, तसेच जास्त साखर किंवा मीठ दाखवतो.';

  @override
  String get methodologySectionInfantTitle => 'बाळे आणि लहान मुले';

  @override
  String get methodologySectionNutriscore2023Description =>
      'आम्ही लेबलवरून न्यूट्री-स्कोर ग्रेड काढतो, या पद्धतीच्या 2023 च्या अद्यतनानुसार. तो SmartNutri मोजते; ते FSSAI रेटिंग नाही.';

  @override
  String get methodologySectionNutriscore2023Title =>
      'न्यूट्री-स्कोर (SmartNutri ने मोजलेला)';

  @override
  String get methodologySectionSupplementsDescription =>
      'प्रोटीन पावडर, व्हे आणि इतर सप्लिमेंटना न्यूट्री-स्कोअर ग्रेड दिला जात नाही आणि ते कधीही पर्याय म्हणून सुचवले जात नाहीत. तरीही आम्ही ॲलर्जी, आहार, दावे आणि प्रत्येक सदस्याचे नियम तपासतो, आणि मुलांसाठी व किशोरवयीनांसाठी सावधगिरी जोडतो (2 वर्षांखालील मुलांसाठी टाळा). लेबलवर व्हे किंवा प्रोटीन आयसोलेट असल्यास, किंवा 100 ग्रॅममध्ये 50 ग्रॅम किंवा त्याहून अधिक प्रथिने असल्यास, पुष्टी स्क्रीन हे सप्लिमेंट आहे का ते विचारते, आणि अशी उत्पादने 18 वर्षांखालील सदस्यांसाठी प्रथिनांच्या क्रमाने दाखवलेल्या निकालांमध्ये दाखवली जात नाहीत.';

  @override
  String get methodologySectionSupplementsTitle => 'सप्लिमेंट';

  @override
  String get methodologySectionWeightLossDescription =>
      'वजन कमी करणाऱ्या सदस्यांसाठी आम्ही जास्त कॅलरी असलेली उत्पादने आणि कमी न्यूट्री-स्कोर ग्रेड दाखवतो, आणि प्रौढांसाठी (18 वर्षे आणि त्याहून अधिक) कॅलरीच्या मानाने चांगले प्रथिन असलेली उत्पादनेही सांगतो.';

  @override
  String get methodologySectionWeightLossTitle => 'वजन कमी करणे';

  @override
  String get methodologySourcesTitle => 'स्रोत';

  @override
  String get methodologyTitle => 'आम्ही कसे तपासतो';

  @override
  String get methodologyUnavailable =>
      'आम्ही सध्या तपासणीचे नियम लोड करू शकलो नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.';

  @override
  String get methodologyUrlUnverified => 'लिंक अजून तपासलेली नाही';

  @override
  String get methodologyValues => 'नियमांची मूल्ये';

  @override
  String methodologyVersion(String version) {
    return 'नियम आवृत्ती $version';
  }

  @override
  String modesCurrent(String mode) {
    return 'सध्याचा मोड: $mode';
  }

  @override
  String get modesMore => 'अधिक';

  @override
  String get modesMoreTitle => 'अधिक';

  @override
  String get modesNameAllergyDiet => 'अॅलर्जी किंवा आहार';

  @override
  String get modesNameEatBetter => 'चांगले खाणे';

  @override
  String get modesNameFamily => 'कुटुंब';

  @override
  String get modesNameGym => 'जिम आणि फिटनेस';

  @override
  String get modesNameHealthCondition => 'आरोग्य स्थिती';

  @override
  String get modesNameWeightLoss => 'वजन कमी करणे';

  @override
  String get modesSameChecks =>
      'प्रत्येक मोडमध्ये स्कॅन, निकाल आणि अॅलर्जी तपासणी सारखीच असते.';

  @override
  String modesSwitchTo(String mode) {
    return '$mode वर जा';
  }

  @override
  String get modesSwitcherLabel => 'मोड';

  @override
  String get navCompare => 'तुलना';

  @override
  String get navFamily => 'कुटुंब';

  @override
  String get navHistory => 'इतिहास';

  @override
  String get navHome => 'होम';

  @override
  String get navHowWeScore => 'आम्ही स्कोर कसा देतो';

  @override
  String get navLabel => 'मुख्य मेनू';

  @override
  String get navMore => 'अधिक';

  @override
  String get navProfile => 'प्रोफाइल';

  @override
  String get navProtein => 'प्रथिने';

  @override
  String get navScan => 'स्कॅन';

  @override
  String get navSearch => 'शोधा';

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
  String get nutrientServingSizeG => 'सर्व्हिंगचा आकार';

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
  String get nutriscoreNotScoredSupplement =>
      'सप्लिमेंटसाठी न्यूट्री-स्कोअर काढला जात नाही.';

  @override
  String get policyOpenFailed =>
      'पान उघडता आले नाही. कृपया पुन्हा प्रयत्न करा.';

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
  String get proteinComparePriceScoop => 'प्रति स्कूप किंमत';

  @override
  String get proteinCompareProtein100kcal => 'प्रति 100 kcal प्रथिने';

  @override
  String get proteinCompareProteinServing => 'प्रति सर्व्हिंग प्रथिने';

  @override
  String get proteinCompareSugar => 'साखर';

  @override
  String proteinGuide(String per_kg, String target) {
    return 'दैनिक प्रथिने मार्गदर्शक: $target ग्रॅम, प्रति किलो $per_kg ग्रॅमवर आधारित. ही माहिती आहे, वैद्यकीय सल्ला नाही.';
  }

  @override
  String proteinGuideAdjusted(String per_kg, String target) {
    return 'दैनिक प्रथिन मार्गदर्शक: $target ग्रॅम, समायोजित वजनाच्या प्रति किग्रॅ $per_kg ग्रॅमवर आधारित. ही माहिती आहे, वैद्यकीय सल्ला नाही.';
  }

  @override
  String proteinGuideLean(String per_kg, String target) {
    return 'दैनिक प्रथिन मार्गदर्शक: $target ग्रॅम, लीन मासच्या प्रति किग्रॅ $per_kg ग्रॅमवर आधारित. ही माहिती आहे, वैद्यकीय सल्ला नाही.';
  }

  @override
  String get proteinKidneyNote =>
      'तुम्हाला मूत्रपिंडाचा आजार असेल, तर जास्त प्रथिने खाण्यापूर्वी डॉक्टरांना विचारा.';

  @override
  String proteinLeftToday(String left) {
    return 'आज $left ग्रॅम बाकी';
  }

  @override
  String get proteinNoTarget =>
      'अजून दैनिक प्रथिने मार्गदर्शक नाही. पाहण्यासाठी प्रौढ व्यक्तीचे वजन आणि जन्मवर्ष जोडा.';

  @override
  String get proteinNotOnLabel => 'लेबलवर नाही';

  @override
  String get proteinPackSizeLabel => 'पॅकचा आकार (ग्रॅम)';

  @override
  String get proteinPer100g => 'प्रति 100 ग्रॅम प्रथिने';

  @override
  String get proteinPer100kcal => 'प्रति 100 kcal प्रथिने';

  @override
  String get proteinPerServing => 'प्रति सर्व्हिंग प्रथिने';

  @override
  String get proteinPriceLabel => 'पॅकची किंमत';

  @override
  String get proteinPriceNote =>
      'तुम्ही टाकलेली किंमत फक्त या स्क्रीनवर वापरली जाते आणि कधीही जतन केली जात नाही.';

  @override
  String get proteinPricePerScoop => 'प्रति स्कूप किंमत';

  @override
  String proteinProgress(String target, String total) {
    return '$target ग्रॅमपैकी $total ग्रॅम';
  }

  @override
  String get proteinSortHigher => 'जास्त प्रथिने';

  @override
  String get proteinSwapsEmpty =>
      'या प्रकारचा जास्त प्रथिनांचा पर्याय सापडला नाही.';

  @override
  String get proteinSwapsTitle => 'जास्त प्रथिनांचे पर्याय';

  @override
  String get proteinTitle => 'प्रथिने';

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
    return 'या अलर्टची तपासणी करता आली नाही: $alerts.';
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
  String get reasonSupplementChild =>
      'हे एक सप्लिमेंट आहे, जे मुलांसाठी आणि किशोरवयीनांसाठी शिफारस केलेले नाही. आधी तुमच्या डॉक्टरांना विचारा.';

  @override
  String get reasonSupplementInfant =>
      'हे एक सप्लिमेंट आहे, जे 2 वर्षांखालील मुलांसाठी शिफारस केलेले नाही.';

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
  String get reportButton => 'समस्या कळवा';

  @override
  String get reportCaffeine => 'यात कॅफीन आहे';

  @override
  String get reportNoteHint =>
      'कृपया वैयक्तिक किंवा आरोग्याविषयी माहिती लिहू नका.';

  @override
  String get reportNoteLabel => 'अधिक सांगा (ऐच्छिक)';

  @override
  String get reportReasonLabel => 'काय चुकीचे आहे?';

  @override
  String get reportReasonOther => 'दुसरे काही';

  @override
  String get reportReasonWrongIngredients => 'घटक चुकीचे आहेत';

  @override
  String get reportReasonWrongProduct => 'हे दुसरेच उत्पादन आहे';

  @override
  String get reportReasonWrongValues => 'पोषण मूल्ये चुकीची आहेत';

  @override
  String get reportSubmit => 'रिपोर्ट पाठवा';

  @override
  String get reportSweeteners => 'यात गोडवा देणारे पदार्थ आहेत';

  @override
  String get reportThanks =>
      'धन्यवाद. आम्ही या उत्पादनाच्या माहितीचे पुनरावलोकन करू.';

  @override
  String get reportTitle => 'या उत्पादनाच्या माहितीत काय चूक आहे?';

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
  String get searchHint =>
      'नाव किंवा ब्रँडने उत्पादन शोधा, मग ते उघडा किंवा तुलना करा.';

  @override
  String get searchNoResults => 'कोणतेही उत्पादन सापडले नाही.';

  @override
  String get searchOffDegraded => 'आणखी निकाल नंतर जोडले जातील.';

  @override
  String get searchPlaceholder => 'नाव किंवा ब्रँडने शोधा';

  @override
  String get searchSortLabel => 'क्रम';

  @override
  String get searchSortRelevance => 'सर्वात जुळणारे';

  @override
  String get searchSourceOff => 'Open Food Facts';

  @override
  String get searchSourceOurs => 'SmartNutri';

  @override
  String get searchTitle => 'उत्पादने शोधा';

  @override
  String get searchTooShort => 'किमान 3 अक्षरे लिहा.';

  @override
  String get settingsAboutTitle => 'SmartNutri बद्दल';

  @override
  String get settingsAccountTitle => 'खाते';

  @override
  String get settingsDeleteBody =>
      'यामुळे तुमचे खाते, तुमच्या कुटुंबाच्या प्रोफाइल आणि आरोग्य डेटा, स्कॅन, खाण्याच्या नोंदी आणि लेबलचे फोटो कायमचे हटवले जातील. तुम्ही जोडलेली उत्पादने तुमच्या नावाशिवाय सामायिक यादीत राहतील. हे परत करता येणार नाही.';

  @override
  String get settingsDeleteButton => 'खाते हटवा';

  @override
  String get settingsDeleteConfirm => 'कायमचे हटवा';

  @override
  String settingsDeleteConfirmLabel(String word) {
    return 'पुष्टीसाठी $word लिहा';
  }

  @override
  String get settingsDeleteConfirmWord => 'DELETE';

  @override
  String get settingsDeleteDialogTitle => 'तुमचे खाते कायमचे हटवायचे?';

  @override
  String get settingsDeleteRetrying =>
      'अजून हटवले जात आहे. पुन्हा प्रयत्न करत आहोत…';

  @override
  String get settingsDeleteTitle => 'खाते हटवा';

  @override
  String get settingsDeleting => 'तुमचे खाते हटवले जात आहे…';

  @override
  String get settingsDiaryBodyFat => 'शरीरातील चरबी %';

  @override
  String get settingsDiaryNumbersHideAll => 'सर्व संख्या लपवा';

  @override
  String get settingsDiaryNumbersHideEnergy => 'कॅलरी लपवा';

  @override
  String get settingsDiaryNumbersHideNote =>
      'तुम्ही तरीही जेवण नोंदवू शकता. तुमचा मार्गदर्शक पार्श्वभूमीत काम करत राहतो.';

  @override
  String get settingsDiaryNumbersShow => 'संख्या दाखवा';

  @override
  String get settingsDiaryNumbersTitle => 'संख्या';

  @override
  String get settingsDiaryReset => 'दैनिक मार्गदर्शक रीसेट करा';

  @override
  String get settingsDiaryResetConfirm =>
      'तुमचा दैनिक मार्गदर्शक रीसेट करायचा? तुमचा फूड लॉग तसाच राहील.';

  @override
  String get settingsDiaryTitle => 'डायरी आणि दैनिक मार्गदर्शक';

  @override
  String get settingsLanguageBody => 'या डिव्हाइसवर SmartNutri ची भाषा निवडा.';

  @override
  String get settingsLanguageSystem => 'डिव्हाइसची भाषा';

  @override
  String get shareButton => 'शेअर करा';

  @override
  String get shareCopied => 'लिंक कॉपी झाली';

  @override
  String get shareCopyLink => 'लिंक कॉपी करा';

  @override
  String get shareInclude => 'एखाद्या व्यक्तीचा निकाल जोडा (ऐच्छिक)';

  @override
  String shareLink(String url) {
    return 'SmartNutri ने तपासले: $url';
  }

  @override
  String get sharePreview => 'संदेशाचे पूर्वावलोकन';

  @override
  String get sharePrivacyNote =>
      'फक्त उत्पादन आणि त्याचा ग्रेड शेअर होतो, आणि तुम्ही निवडलेल्या व्यक्तींचा निकाल. आरोग्याची माहिती खासगी राहते.';

  @override
  String get shareRelationChild => 'मूल';

  @override
  String get shareRelationOther => 'कुटुंबातील सदस्य';

  @override
  String get shareRelationParent => 'आई/वडील';

  @override
  String get shareRelationSelf => 'मी';

  @override
  String get shareRelationSpouse => 'जोडीदार';

  @override
  String shareResultMember(String status, String who) {
    return '$who: $status';
  }

  @override
  String shareResultProductOnly(String grade, String product) {
    return '$product — न्यूट्री-स्कोअर $grade (गणना SmartNutri ने केली आहे).';
  }

  @override
  String shareResultProductOnlyUngraded(String product) {
    return '$product — न्यूट्री-स्कोअरसाठी लेबलवर पुरेशी माहिती नाही.';
  }

  @override
  String shareResultText(String grade, String members, String product) {
    return '$product — न्यूट्री-स्कोअर $grade (गणना SmartNutri ने केली आहे). $members.';
  }

  @override
  String shareResultUngraded(String members, String product) {
    return '$product — न्यूट्री-स्कोअरसाठी लेबलवर पुरेशी माहिती नाही. $members.';
  }

  @override
  String shareWeekly(String logged, String scans) {
    return 'SmartNutri वर आमचा आठवडा — तपासलेली उत्पादने: $scans, नोंदवलेल्या गोष्टी: $logged.';
  }

  @override
  String get shareWeeklyButton => 'आमचा आठवडा शेअर करा';

  @override
  String get shareWhatsapp => 'WhatsApp वर शेअर करा';

  @override
  String get statusAvoid => 'टाळा';

  @override
  String get statusCaution => 'सावधगिरी';

  @override
  String get statusOk => 'ठीक आहे';

  @override
  String get statusUnknown => 'लेबल स्पष्ट नाही';

  @override
  String get summaryBandNear => 'मर्यादेच्या जवळ';

  @override
  String get summaryBandOk => 'मर्यादेत';

  @override
  String get summaryBandOver => 'मर्यादेपेक्षा जास्त';

  @override
  String get summaryBandUnknown => 'पुरेशी माहिती नाही';

  @override
  String get summaryIncomplete =>
      'काही नोंदवलेल्या गोष्टींच्या लेबलवर हे मूल्य नाही, त्यामुळे खरी एकूण रक्कम यापेक्षा जास्त असू शकते.';

  @override
  String get summaryKcalInfo =>
      'कॅलरी फक्त माहितीसाठी दाखवल्या आहेत. अजून कोणतेही वैयक्तिक कॅलरी लक्ष्य नाही.';

  @override
  String summaryKcalTotal(String total) {
    return '$total kcal';
  }

  @override
  String get summaryLimitsNote =>
      'मर्यादा अजून डॉक्टरांच्या पुनरावलोकनात आहेत.';

  @override
  String get summaryNoProteinTarget =>
      'या सदस्यासाठी प्रथिनांचे कोणतेही लक्ष्य नाही';

  @override
  String get summaryNothingLogged => 'या दिवशी काहीही नोंदवलेले नाही.';

  @override
  String get summaryNutrientEnergyKcal => 'कॅलरी';

  @override
  String get summaryNutrientProteinG => 'प्रथिने';

  @override
  String get summaryNutrientSaltG => 'मीठ';

  @override
  String get summaryNutrientSugarsG => 'साखर';

  @override
  String summaryProteinOfTarget(String target, String total) {
    return '$target ग्रॅमच्या लक्ष्यापैकी $total ग्रॅम';
  }

  @override
  String get summarySugarNote =>
      'लेबलवर एकूण साखर असते, त्यात नैसर्गिक साखरही असते, त्यामुळे ही एकूण साखर फक्त जोडलेल्या साखरेपेक्षा जास्त असू शकते.';

  @override
  String get summaryTitleDay => 'आज';

  @override
  String get summaryTitleWeek => 'मागील 7 दिवस';

  @override
  String summaryTotalG(String total) {
    return '$total ग्रॅम';
  }

  @override
  String summaryTotalOfLimit(String limit, String total) {
    return '$limit ग्रॅमपैकी $total ग्रॅम';
  }

  @override
  String get summaryWeekNote =>
      'ज्या दिवशी काही नोंदवले आहे, त्या प्रत्येक दिवसाच्या दैनिक मर्यादेशी आठवड्याची तुलना केली जाते.';

  @override
  String get targetsActivityLight => 'हलके सक्रिय';

  @override
  String get targetsActivityLightHint =>
      'दिवसाचा काही वेळ उभे राहणे, किंवा आठवड्यात 1 ते 3 दिवस हलका व्यायाम';

  @override
  String get targetsActivityModerate => 'सक्रिय';

  @override
  String get targetsActivityModerateHint =>
      'सक्रिय काम, किंवा आठवड्यात 3 ते 5 दिवस व्यायाम';

  @override
  String get targetsActivitySedentary => 'बहुतेक बसून';

  @override
  String get targetsActivitySedentaryHint => 'डेस्कवरचे काम आणि कमी चालणे';

  @override
  String get targetsActivityVery => 'खूप सक्रिय';

  @override
  String get targetsActivityVeryHint =>
      'कठीण शारीरिक काम, किंवा आठवड्यात 6 ते 7 दिवस कठीण प्रशिक्षण';

  @override
  String get targetsBodyFatHint =>
      'तुम्हाला माहीत असल्यास, उदाहरणार्थ बॉडी-कंपोझिशन स्केलवरून, आम्ही तुमचा प्रथिन मार्गदर्शक लीन मासवर आधारित करतो. रिकामे सोडल्यास आम्ही तुमचे वजन वापरतो.';

  @override
  String get targetsBodyFatLabel => 'शरीरातील चरबी % (ऐच्छिक)';

  @override
  String targetsBodyFatOutOfRange(String max, String min) {
    return 'कृपया $min ते $max दरम्यानची संख्या भरा.';
  }

  @override
  String get targetsCarbs => 'कार्ब्स';

  @override
  String get targetsDirectionGain => 'हळूहळू वजन वाढवा';

  @override
  String get targetsDirectionLose => 'हळूहळू वजन कमी करा';

  @override
  String get targetsDirectionMaintain => 'वजन तसेच ठेवा';

  @override
  String get targetsEnergy => 'कॅलरी';

  @override
  String get targetsFat => 'चरबी';

  @override
  String get targetsFieldActivity => 'हालचालीची पातळी';

  @override
  String get targetsFieldBirthYear => 'जन्म वर्ष';

  @override
  String get targetsFieldBodyFat => 'शरीरातील चरबी';

  @override
  String get targetsFieldHeight => 'उंची';

  @override
  String get targetsFieldSex => 'लिंग';

  @override
  String get targetsFieldWeight => 'वजन';

  @override
  String get targetsFlagAverageSexReference =>
      'हा मार्गदर्शक दोन्हींच्या मधला अंदाज वापरतो.';

  @override
  String get targetsFlagCarbsBelowReference =>
      'कार्ब्स नेहमीच्या किमान 130 ग्रॅम प्रतिदिनपेक्षा कमी आहेत. आहारतज्ज्ञ तुम्हाला ते समायोजित करण्यात मदत करू शकतात.';

  @override
  String get targetsFlagCarbsBelowReferenceHidden =>
      'कार्ब्स नेहमीच्या किमान प्रमाणापेक्षा कमी आहेत. आहारतज्ज्ञ तुम्हाला ते समायोजित करण्यास मदत करू शकतात.';

  @override
  String get targetsFlagDeficitCapped => 'आम्ही रोजचा बदल सौम्य ठेवला आहे.';

  @override
  String targetsFlagFloorApplied(String value) {
    return 'आम्ही दररोज $value किलोकॅलरीपेक्षा कमी सुचवत नाही. डॉक्टर किंवा आहारतज्ज्ञ तुम्हाला सल्ला देऊ शकतात.';
  }

  @override
  String get targetsFlagFloorAppliedHidden =>
      'आम्ही यापेक्षा कमी सुचवत नाही. डॉक्टर किंवा आहारतज्ज्ञ तुम्हाला सल्ला देऊ शकतात.';

  @override
  String get targetsFlagFloorLimitsDeficit =>
      'तुमची निवडलेली गती सुरक्षित किमान मर्यादेत शक्य नाही, म्हणून हा मार्गदर्शक वजन तसेच ठेवण्यासाठी आहे.';

  @override
  String get targetsFlagGoalWeightReached =>
      'तुम्ही तुमच्या लक्ष्य वजनावर आहात. आता मार्गदर्शक वजन तसेच ठेवण्यासाठी आहे.';

  @override
  String get targetsFlagOutsideEquationAgeRange =>
      'तुमच्या वयात हा अंदाज कमी निश्चित आहे.';

  @override
  String get targetsFlagProteinCapped =>
      'आम्ही प्रथिने तुमच्या कॅलरीचा मध्यम वाटा ठेवली आहेत.';

  @override
  String get targetsFlagRateCapped =>
      'आम्ही गती उपलब्ध असलेल्या सर्वात जवळच्या पर्यायावर ठेवली आहे.';

  @override
  String get targetsFlagTaperActive =>
      'तुम्ही तुमच्या लक्ष्याच्या जवळ आहात, म्हणून गती कमी होत आहे.';

  @override
  String get targetsFlagUnderweightMaintenance =>
      'त्याऐवजी आम्ही तुम्हाला स्थिर वजन राखण्यास मदत करू शकतो.';

  @override
  String targetsGValue(String value) {
    return '$value ग्रॅम';
  }

  @override
  String targetsHowActivity(String value) {
    return 'हालचाल गुणक: $value';
  }

  @override
  String targetsHowAdjustment(String value) {
    return 'तुमच्या ध्येयासाठी बदल: दररोज $value किलोकॅलरी';
  }

  @override
  String targetsHowBmr(String value) {
    return 'विश्रांतीतील अंदाजे ऊर्जा: $value किलोकॅलरी';
  }

  @override
  String targetsHowFloor(String value) {
    return 'आम्ही यापेक्षा कमी सुचवत नाही: दररोज $value किलोकॅलरी';
  }

  @override
  String targetsHowMaintenance(String value) {
    return 'वजन स्थिर ठेवण्यासाठी अंदाजे ऊर्जा: $value किलोकॅलरी';
  }

  @override
  String targetsHowProtein(String per_kg, String weight) {
    return 'प्रथिने: तुमच्या वजनाच्या ($weight किग्रॅ) प्रति किग्रॅ $per_kg ग्रॅम';
  }

  @override
  String targetsHowProteinAdjusted(String per_kg, String weight) {
    return 'प्रथिने: समायोजित वजनाच्या ($weight किग्रॅ) प्रति किग्रॅ $per_kg ग्रॅम';
  }

  @override
  String targetsHowProteinLean(String per_kg, String weight) {
    return 'प्रथिने: लीन मासच्या ($weight किग्रॅ) प्रति किग्रॅ $per_kg ग्रॅम';
  }

  @override
  String get targetsHowSources => 'स्रोत आणि पद्धत';

  @override
  String get targetsHowTitle => 'आम्ही हे कसे काढले';

  @override
  String get targetsIntroBody =>
      'तुमच्या माहितीवर आधारित, तुम्हाला दिशा देणारा एक अंदाज. ही माहिती आहे, वैद्यकीय सल्ला नाही.';

  @override
  String get targetsIntroTitle => 'तुमचा दैनिक मार्गदर्शक';

  @override
  String targetsKcalValue(String value) {
    return '$value किलोकॅलरी';
  }

  @override
  String get targetsMinor =>
      'दैनिक मार्गदर्शक प्रौढांसाठी आहेत. तुम्ही तरीही जेवण नोंदवू शकता.';

  @override
  String targetsNeedsBodyData(String fields) {
    return 'दैनिक मार्गदर्शक पाहण्यासाठी $fields जोडा.';
  }

  @override
  String get targetsPendingReview => 'डॉक्टरांची तपासणी प्रलंबित';

  @override
  String get targetsPregnancyNo => 'नाही';

  @override
  String get targetsPregnancyPaused =>
      'गर्भधारणा आणि स्तनपानाच्या काळात दैनिक मार्गदर्शक थांबवलेला असतो. तुमच्या गरजांबद्दल कृपया डॉक्टरांना विचारा. तुम्ही तरीही जेवण नोंदवू शकता.';

  @override
  String get targetsPregnancyPreferNot => 'सांगायचे नाही';

  @override
  String get targetsPregnancyQuestion =>
      'तुम्ही गर्भवती आहात का किंवा स्तनपान करत आहात का?';

  @override
  String get targetsPregnancyYes => 'होय';

  @override
  String get targetsProtein => 'प्रथिने';

  @override
  String targetsRateOption(String kg, String pct) {
    return 'सुमारे $kg किग्रॅ दर आठवड्याला (शरीराच्या वजनाच्या $pct%)';
  }

  @override
  String get targetsRateTitle => 'गती';

  @override
  String get targetsSave => 'माझा दैनिक मार्गदर्शक जतन करा';

  @override
  String get targetsSetupCta => 'तुमचा दैनिक मार्गदर्शक सेट करा';

  @override
  String get targetsSexReferenceAverage => 'दोन्हींच्या मधला';

  @override
  String get targetsSexReferenceFemale => 'महिलांसाठीचा अंदाज';

  @override
  String get targetsSexReferenceMale => 'पुरुषांसाठीचा अंदाज';

  @override
  String get targetsSexReferenceTitle => 'आम्ही कोणता अंदाज वापरावा?';

  @override
  String get targetsSkip => 'वगळा, फक्त जेवण नोंदवा';

  @override
  String get targetsStepAbout => 'तुमच्याबद्दल';

  @override
  String get targetsStepActivity => 'हालचाल';

  @override
  String get targetsStepGoal => 'तुमचे ध्येय';

  @override
  String get targetsStepGuide => 'तुमचा मार्गदर्शक';

  @override
  String get targetsTargetWeight => 'लक्ष्य वजन (ऐच्छिक)';

  @override
  String targetsTargetWeightTooLow(String min) {
    return 'कृपया $min किग्रॅ किंवा त्याहून जास्त निवडा.';
  }

  @override
  String get targetsTitle => 'तुमचा दैनिक मार्गदर्शक';

  @override
  String get targetsUnderweight =>
      'त्याऐवजी आम्ही तुम्हाला स्थिर वजन राखण्यास मदत करू शकतो.';

  @override
  String targetsUnusualConfirm(String fields) {
    return 'कृपया $fields तपासा. हे बरोबर आहे का?';
  }

  @override
  String get userTypesChangeLater => 'तुम्ही हे प्रोफाइलमध्ये बदलू शकता';

  @override
  String get userTypesConsentNeeded =>
      'आरोग्य माहिती जतन करण्यासाठी आरोग्य डेटावर तुमची संमती आवश्यक आहे.';

  @override
  String get userTypesConsentNote =>
      'यातील काही निवडल्यास तुमच्या प्रोफाइलमध्ये माहिती जोडण्याची सूचना येऊ शकते. तुम्ही पुष्टी केली तरच आणि आरोग्य डेटासाठी तुमची संमती असेल तरच ती जतन होईल.';

  @override
  String get userTypesContinue => 'पुढे जा';

  @override
  String get userTypesEdit => 'तुमची निवड बदला';

  @override
  String get userTypesFollowUpAllergyDietAllergensQuestion =>
      'आम्ही कोणत्या अॅलर्जींसाठी तपासावे?';

  @override
  String get userTypesFollowUpAllergyDietDietQuestion =>
      'तुम्ही कोणता आहार पाळता?';

  @override
  String get userTypesFollowUpEatBetterHint =>
      'उदाहरणार्थ पाम तेल किंवा कृत्रिम गोडवा. तुम्ही हे आत्ता किंवा नंतर जोडू शकता.';

  @override
  String get userTypesFollowUpEatBetterQuestion => 'आम्ही दाखवावेत असे घटक';

  @override
  String get userTypesFollowUpFamilyChildren => 'मुले';

  @override
  String get userTypesFollowUpFamilyOthers => 'इतर';

  @override
  String get userTypesFollowUpFamilyParents => 'आई-वडील';

  @override
  String get userTypesFollowUpFamilyPartner => 'जोडीदार';

  @override
  String get userTypesFollowUpFamilyQuestion =>
      'तुम्ही कोणासाठी अन्न तपासत आहात?';

  @override
  String get userTypesFollowUpGymBuildMuscle => 'स्नायू वाढवणे';

  @override
  String get userTypesFollowUpGymLoseFat => 'चरबी कमी करणे';

  @override
  String get userTypesFollowUpGymQuestion => 'तुमचे मुख्य ध्येय काय आहे?';

  @override
  String get userTypesFollowUpGymStayFit => 'तंदुरुस्त राहणे';

  @override
  String get userTypesFollowUpHealthConditionQuestion =>
      'यातील कोणते लागू होते?';

  @override
  String get userTypesMaxReached => 'तुम्ही जास्तीत जास्त 3 निवडू शकता.';

  @override
  String get userTypesNotCoveredBody =>
      'थायरॉईड, कोलेस्टेरॉल, मूत्रपिंडाचा आजार आणि गर्भधारणा अजून समाविष्ट नाहीत, म्हणून निकालात त्यांचा विचार केला जात नाही.';

  @override
  String get userTypesNotCoveredTitle => 'अजून समाविष्ट नाही';

  @override
  String get userTypesPickUpTo => 'जास्तीत जास्त 3 निवडा';

  @override
  String get userTypesPrefillApply => 'प्रोफाइलमध्ये जोडा';

  @override
  String get userTypesPrefillBody =>
      'तुमच्या पुष्टीशिवाय काहीही जोडले जात नाही. ही माहिती आहे, वैद्यकीय सल्ला नाही.';

  @override
  String get userTypesPrefillGoalConflict =>
      'तुम्ही वजन कमी करणे आणि जिम दोन्ही निवडले आहे. प्रोफाइलसाठी एक ध्येय निवडा.';

  @override
  String get userTypesPrefillGoalNeither =>
      'यापैकी नाही (माझे सध्याचे ध्येय ठेवा)';

  @override
  String userTypesPrefillLineAllergens(String values) {
    return 'अॅलर्जी: $values';
  }

  @override
  String userTypesPrefillLineConditions(String values) {
    return 'आरोग्य स्थिती: $values';
  }

  @override
  String userTypesPrefillLineCustomAlerts(String values) {
    return 'घटक अलर्ट: $values';
  }

  @override
  String userTypesPrefillLineDiet(String value) {
    return 'आहार: $value';
  }

  @override
  String userTypesPrefillLineGoal(String value) {
    return 'ध्येय: $value';
  }

  @override
  String get userTypesPrefillNotNow => 'आत्ता नको';

  @override
  String get userTypesPrefillNothing => 'जोडण्यासारखे काही नाही.';

  @override
  String get userTypesPrefillTitle => 'हे तुमच्या प्रोफाइलमध्ये जोडायचे का?';

  @override
  String get userTypesSaved => 'जतन केले';

  @override
  String get userTypesSkip => 'आत्ता वगळा';

  @override
  String get userTypesSubtitle =>
      'आम्ही अॅप तुमच्या गरजेनुसार मांडतो. स्कॅन आणि निकाल तसेच राहतात.';

  @override
  String get userTypesTileAllergyDietSubtitle =>
      'अॅलर्जन, शाकाहारी, वीगन किंवा जैनसाठी लेबल तपासा';

  @override
  String get userTypesTileAllergyDietTitle => 'अन्नाची अॅलर्जी किंवा खास आहार';

  @override
  String get userTypesTileEatBetterSubtitle =>
      'उत्पादनांची तुलना करा आणि लेबल समजून घ्या';

  @override
  String get userTypesTileEatBetterTitle => 'फक्त चांगले खाणे';

  @override
  String get userTypesTileFamilySubtitle =>
      'मुले, आई-वडील किंवा घरातील सर्वांसाठी अन्न तपासा';

  @override
  String get userTypesTileFamilyTitle => 'माझे कुटुंब';

  @override
  String get userTypesTileGymSubtitle =>
      'प्रथिने नोंदवा आणि प्रथिन उत्पादनांची तुलना करा';

  @override
  String get userTypesTileGymTitle => 'जिम आणि फिटनेस';

  @override
  String get userTypesTileHealthConditionSubtitle =>
      'मधुमेह, प्री-डायबिटीस, PCOS किंवा उच्च रक्तदाब';

  @override
  String get userTypesTileHealthConditionTitle => 'एखादी आरोग्य स्थिती';

  @override
  String get userTypesTileWeightLossSubtitle =>
      'तुम्ही जे खाता त्यातील साखर, मीठ, कॅलरी आणि प्रथिने पहा';

  @override
  String get userTypesTileWeightLossTitle => 'वजन कमी करणे';

  @override
  String get userTypesTitle => 'तुम्ही SmartNutri वर कशासाठी आला आहात?';

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
  String get verdictSpokenAvoid => 'या सदस्यासाठी, हे उत्पादन टाळा.';

  @override
  String get verdictSpokenCaution =>
      'या सदस्यासाठी, हे उत्पादन घेताना काळजी घ्या.';

  @override
  String get verdictSpokenOk => 'या सदस्यासाठी हे उत्पादन ठीक दिसते.';

  @override
  String get verdictSpokenUnknown =>
      'या सदस्यासाठी लेबल स्पष्ट नाही, त्यामुळे आम्ही सांगू शकत नाही.';

  @override
  String get verdictStatusAvoid => 'टाळा';

  @override
  String get verdictStatusCaution => 'सावधगिरी';

  @override
  String get verdictStatusOk => 'ठीक आहे';

  @override
  String get verdictStatusUnknown => 'लेबल स्पष्ट नाही';

  @override
  String get voiceAiUnavailable =>
      'आवाजातील उत्तरे सध्या उपलब्ध नाहीत. कृपया नंतर पुन्हा प्रयत्न करा.';

  @override
  String get voiceAnswerTitle => 'उत्तर';

  @override
  String get voiceButtonHold => 'विचारण्यासाठी दाबून ठेवा';

  @override
  String voiceButtonHoldFor(String name) {
    return 'विचारण्यासाठी दाबून ठेवा, $name';
  }

  @override
  String voiceElapsed(String seconds) {
    return '30 पैकी $seconds सेकंद';
  }

  @override
  String get voiceHint =>
      'बटण दाबून ठेवा, या उत्पादनाबद्दल विचारा, मग सोडा. सुरू करण्यासाठी Space दाबा आणि पाठवण्यासाठी पुन्हा दाबा.';

  @override
  String get voiceMicDenied =>
      'मायक्रोफोनची परवानगी बंद आहे. आवाजाने विचारण्यासाठी सेटिंग्जमध्ये ती सुरू करा.';

  @override
  String get voiceNoMic => 'या डिव्हाइसवर मायक्रोफोन सापडला नाही.';

  @override
  String get voiceNotUnderstood =>
      'आम्हाला प्रश्न ऐकू आला नाही. बटण दाबून ठेवा आणि स्पष्ट बोला.';

  @override
  String get voicePlaying => 'उत्तर ऐकवले जात आहे';

  @override
  String get voiceRateLimited =>
      'आजच्या आवाजातील प्रश्नांची मर्यादा पूर्ण झाली आहे.';

  @override
  String get voiceRecording => 'ऐकत आहोत… पाठवण्यासाठी सोडा';

  @override
  String get voiceReplay => 'पुन्हा ऐका';

  @override
  String get voiceThinking => 'तुमचे उत्तर तयार होत आहे…';

  @override
  String get voiceTitle => 'प्रश्न विचारा';

  @override
  String get voiceTooLong => 'कृपया तुमचा प्रश्न 30 सेकंदांपेक्षा लहान ठेवा.';

  @override
  String get voiceUnsupportedBrowser =>
      'या ब्राउझरमध्ये आवाजाने प्रश्न विचारता येत नाहीत. Chrome, Edge किंवा Firefox ची नवी आवृत्ती वापरून पाहा.';

  @override
  String get voiceWordSafe => 'सुरक्षित';

  @override
  String voiceYouAsked(String question) {
    return 'तुम्ही विचारले: $question';
  }

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
  String get warningColumnMismatch =>
      'या पोषक घटकाची प्रति 100 ग्रॅम आणि प्रति सर्व्हिंग मूल्ये सर्व्हिंग आकाराशी जुळत नाहीत. दोन्ही पॅकवर तपासा.';

  @override
  String get warningDecimalShift =>
      'या मूल्यातील दशांश चिन्ह कदाचित चुकीचे वाचले गेले आहे. ते पॅकवर तपासा.';

  @override
  String get warningDerivedFromServing =>
      'हे मूल्य प्रति सर्व्हिंगच्या प्रमाणावरून काढले आहे. ते पॅकशी जुळवून पाहा.';

  @override
  String get warningEnergyMismatch =>
      'ऊर्जेचे मूल्य इतर मूल्यांशी जुळत नाही. ते पॅकवर तपासा.';

  @override
  String get warningFatPartsMismatch =>
      'संपृक्त आणि ट्रान्स फॅट मिळून एकूण फॅटपेक्षा जास्त होत आहेत. ही मूल्ये पॅकवर तपासा.';

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
  String get warningSodiumUnitSuspect =>
      'या उत्पादनासाठी सोडियम खूप कमी दिसत आहे. पॅकवर ते mg मध्ये छापले आहे की g मध्ये ते तपासा आणि तेच एकक निवडा.';

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
