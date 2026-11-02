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
  String get allergenTreeNut => 'सूखे मेवे (ट्री नट्स)';

  @override
  String get appName => 'SmartNutri AI';

  @override
  String get authCodeLabel => '6 अंकों का कोड';

  @override
  String get authEmail => 'ईमेल से जारी रखें';

  @override
  String get authEmailLabel => 'ईमेल पता';

  @override
  String get authGoogle => 'Google से जारी रखें';

  @override
  String get authPhone => 'फ़ोन से जारी रखें';

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
    return '$value इस दावे के न्यूनतम मान $limit से कम है।';
  }

  @override
  String claimReasonExceedsLimit(String limit, String value) {
    return '$value इस दावे की सीमा $limit से अधिक है।';
  }

  @override
  String get claimReasonIngredientsUnknown =>
      'सामग्री की सूची उपलब्ध नहीं है, इसलिए इस दावे की जाँच नहीं हो सकती।';

  @override
  String claimReasonNoStandard(String claim) {
    return '\"$claim\" की जाँच के लिए हमारे पास कोई मानक नहीं है।';
  }

  @override
  String claimReasonNutrientMissing(String nutrient) {
    return 'लेबल पर $nutrient नहीं दिया गया है, इसलिए इस दावे की जाँच नहीं हो सकती।';
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
  String get errorInternalError => 'कुछ गड़बड़ हो गई। कृपया फिर से कोशिश करें।';

  @override
  String get errorNetwork => 'इंटरनेट कनेक्शन नहीं है।';

  @override
  String get errorNotFound => 'नहीं मिला।';

  @override
  String get errorRateLimited => 'बहुत अधिक अनुरोध। कृपया थोड़ी देर रुकें।';

  @override
  String get errorRateLimitedScans =>
      'आप आज की लेबल-स्कैन सीमा तक पहुँच गए हैं।';

  @override
  String get errorRateLimitedVoice =>
      'आप आज की आवाज़ से प्रश्न पूछने की सीमा तक पहुँच गए हैं।';

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
  String homeWelcome(String name) {
    return 'नमस्ते, $name';
  }

  @override
  String get nutriscoreCalculatedBy =>
      'Nutri-Score की गणना SmartNutri ने की है';

  @override
  String get nutriscoreInsufficientData =>
      'Nutri-Score की गणना के लिए लेबल पर पर्याप्त जानकारी नहीं है।';

  @override
  String reasonAddedSugars(String ingredients) {
    return 'इसमें अतिरिक्त शर्करा मिलाई गई है: $ingredients।';
  }

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
  String reasonCarbsPerServingHigh(String carbs_g) {
    return 'प्रति सर्विंग $carbs_g ग्राम कार्बोहाइड्रेट। यह आपकी स्थिति के लिए उपयुक्त नहीं हो सकता; अपने डॉक्टर से पूछें।';
  }

  @override
  String get reasonChildCaffeine =>
      'इसमें कैफ़ीन है, जो बच्चों के लिए अनुशंसित नहीं है।';

  @override
  String reasonChildSaltHigh(String limit_g, String salt_g) {
    return 'बच्चे के लिए $salt_g ग्राम नमक अधिक है (मार्गदर्शक सीमा: लगभग $limit_g ग्राम)।';
  }

  @override
  String reasonChildSugarHigh(String limit_g, String sugars_g) {
    return 'बच्चे के लिए $sugars_g ग्राम चीनी अधिक है (मार्गदर्शक सीमा: लगभग $limit_g ग्राम)।';
  }

  @override
  String reasonChildSugarModerate(String limit_g, String sugars_g) {
    return 'बच्चे के लिए $sugars_g ग्राम चीनी थोड़ी अधिक है (मार्गदर्शक सीमा: लगभग $limit_g ग्राम)।';
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
    return 'यह $diet आहार से मेल नहीं खा सकता: $ingredients।';
  }

  @override
  String get reasonEnergyDense =>
      'यह ऊर्जा से भरपूर (अधिक कैलोरी वाला) भोजन है। कम मात्रा में लेना बेहतर है।';

  @override
  String get reasonGoodProteinDensity =>
      'अपनी कैलोरी के हिसाब से अच्छी मात्रा में प्रोटीन।';

  @override
  String reasonHiddenSugars(String ingredients) {
    return 'इसमें अन्य नामों से लिखी गई शर्कराएँ हैं: $ingredients।';
  }

  @override
  String get reasonInfantAddedSalt =>
      'इसमें अतिरिक्त नमक है, जो शिशुओं के लिए अनुशंसित नहीं है।';

  @override
  String get reasonInfantAddedSugar =>
      'इसमें अतिरिक्त चीनी है, जो शिशुओं के लिए अनुशंसित नहीं है।';

  @override
  String get reasonInfantCaffeine =>
      'इसमें कैफ़ीन है, जो शिशुओं के लिए अनुशंसित नहीं है।';

  @override
  String get reasonInfantHoney =>
      'इसमें शहद है, जो 12 महीने से छोटे शिशुओं को नहीं देना चाहिए।';

  @override
  String reasonInfantSaltHigh(String salt_g) {
    return 'शिशु के लिए $salt_g ग्राम नमक अधिक है।';
  }

  @override
  String reasonInfantSugarHigh(String sugars_g) {
    return 'शिशु के लिए $sugars_g ग्राम चीनी अधिक है।';
  }

  @override
  String get reasonIngredientsMissing =>
      'सामग्री की सूची पढ़ी नहीं जा सकी, इसलिए कुछ जाँचें नहीं हो सकीं।';

  @override
  String reasonMisleadingSugarClaim(String ingredients, String mark) {
    return 'पैक पर \"$mark\" लिखा है, लेकिन सामग्री में चीनी शामिल है: $ingredients।';
  }

  @override
  String reasonNutrientMissing(String nutrient) {
    return 'लेबल पर $nutrient नहीं दिया गया है, इसलिए यह जाँच नहीं हो सकी।';
  }

  @override
  String reasonNutriscoreLow(String grade) {
    return 'Nutri-Score $grade कुल पोषण गुणवत्ता कम होने का संकेत देता है।';
  }

  @override
  String reasonSaltHigh(String basis, String salt_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्विंग',
      'other': 'प्रति 100 ग्राम',
    });
    return 'नमक अधिक है: $salt_g ग्राम $_temp0।';
  }

  @override
  String reasonSaltModerate(String basis, String salt_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्विंग',
      'other': 'प्रति 100 ग्राम',
    });
    return 'नमक मध्यम है: $salt_g ग्राम $_temp0।';
  }

  @override
  String reasonSodiumAdditives(String ingredients) {
    return 'इसमें सोडियम वाले योजक हैं: $ingredients।';
  }

  @override
  String reasonSugarHigh(String basis, String sugars_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्विंग',
      'other': 'प्रति 100 ग्राम',
    });
    return 'चीनी अधिक है: $sugars_g ग्राम $_temp0।';
  }

  @override
  String reasonSugarModerate(String basis, String sugars_g) {
    String _temp0 = intl.Intl.selectLogic(basis, {
      'per_serving': 'प्रति सर्विंग',
      'other': 'प्रति 100 ग्राम',
    });
    return 'चीनी मध्यम है: $sugars_g ग्राम $_temp0।';
  }

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
  String verdictRuleApplied(String rule) {
    return 'लागू नियम: $rule';
  }

  @override
  String get verdictStatusAvoid => 'बचें';

  @override
  String get verdictStatusCaution => 'सावधानी';

  @override
  String get verdictStatusOk => 'ठीक है';

  @override
  String get verdictStatusUnknown => 'लेबल स्पष्ट नहीं';
}
