// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppLocalizationsHi extends AppLocalizations {
  AppLocalizationsHi([String locale = 'hi']) : super(locale);

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
  String get authPhone => 'फ़ोन से जारी रखें';

  @override
  String get authPhoneLabel => 'फ़ोन नंबर (देश कोड सहित)';

  @override
  String get authSendCode => 'कोड भेजें';

  @override
  String get authSignOut => 'साइन आउट करें';

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
  String get commonDisclaimer => 'यह जानकारी है, चिकित्सकीय सलाह नहीं।';

  @override
  String get commonLoading => 'लोड हो रहा है…';

  @override
  String get commonRetry => 'फिर से कोशिश करें';

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
  String get errorAuthInvalid =>
      'आपका सत्र समाप्त हो गया है। कृपया फिर से साइन इन करें।';

  @override
  String get errorAuthRequired => 'कृपया साइन इन करें।';

  @override
  String get errorExtractionFailed =>
      'हम यह लेबल नहीं पढ़ पाए। दूसरी फ़ोटो आज़माएँ या जानकारी खुद भरें।';

  @override
  String get errorExtractionUnavailable =>
      'लेबल पढ़ने की सुविधा अभी उपलब्ध नहीं है। बाद में फिर कोशिश करें या जानकारी खुद भरें।';

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
  String get errorStorageUnavailable =>
      'हम अभी फ़ोटो संभाल नहीं पाए। कृपया थोड़ी देर बाद फिर कोशिश करें।';

  @override
  String get errorUnauthorized => 'कृपया साइन इन करें।';

  @override
  String get errorUnsupportedImage =>
      'कृपया JPEG, PNG या WebP फ़ोटो इस्तेमाल करें।';

  @override
  String get errorValidationError => 'कृपया चिह्नित फ़ील्ड जाँचें।';

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
  String get homeScanCta => 'उत्पाद स्कैन करें';

  @override
  String homeWelcome(String name) {
    return 'नमस्ते, $name';
  }

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
  String get productPublicCta => 'अपने परिवार के लिए जाँचें';

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
    return 'आपकी प्रोफ़ाइल में दिए गए एलर्जन \"$allergen\" को हम पहचान नहीं पाए।';
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
  String reasonVariantDietViolationMarkOnly(String diet) {
    return 'पैक पर भूरे रंग का मांसाहारी निशान है, इसलिए यह शायद $diet आहार के अनुरूप न हो।';
  }

  @override
  String reasonVariantNutrientMissingLowConfidence(String nutrient) {
    return 'लेबल पर $nutrient साफ़ नहीं पढ़ा जा सका, इसलिए यह जाँच नहीं हो सकी।';
  }

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
  String get resultNoIngredients => 'सामग्री उपलब्ध नहीं';

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
  String get scanTitle => 'बारकोड स्कैन करें';

  @override
  String get statusAvoid => 'बचें';

  @override
  String get statusCaution => 'सावधानी';

  @override
  String get statusOk => 'ठीक है';

  @override
  String get statusUnknown => 'लेबल स्पष्ट नहीं';

  @override
  String verdictConfidenceNote(String reason) {
    String _temp0 = intl.Intl.selectLogic(reason, {
      'low_confidence': 'लेबल पढ़ना कठिन था, इसलिए यह परिणाम कम निश्चित है।',
      'other': 'कुछ डेटा अनिश्चित है।',
    });
    return '$_temp0';
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
  String get verdictStatusAvoid => 'बचें';

  @override
  String get verdictStatusCaution => 'सावधानी';

  @override
  String get verdictStatusOk => 'ठीक है';

  @override
  String get verdictStatusUnknown => 'लेबल स्पष्ट नहीं';

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
