import 'package:intl/intl.dart' show toBeginningOfSentenceCase;

import '../../../core/l10n/app_localizations.dart';
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart' show MemberOut;
import '../../../shared/share/share_text.dart' show shareRelation;

/// i18n labels for member field codes. A code this build does not know is
/// shown as-is.

String relationLabel(AppLocalizations l, String? code) => switch (code) {
  'self' => l.membersRelationSelf,
  'child' => l.membersRelationChild,
  'parent' => l.membersRelationParent,
  'spouse' => l.membersRelationSpouse,
  'other' => l.membersRelationOther,
  _ => code ?? '',
};

String sexLabel(AppLocalizations l, String code) => switch (code) {
  'female' => l.membersSexFemale,
  'male' => l.membersSexMale,
  'other' => l.membersSexOther,
  _ => code,
};

String goalLabel(AppLocalizations l, String code) => switch (code) {
  'healthy_eating' => l.membersGoalHealthyEating,
  'weight_loss' => l.membersGoalWeightLoss,
  'weight_gain' => l.membersGoalWeightGain,
  'build_muscle' => l.membersGoalBuildMuscle,
  _ => code,
};

String dietLabel(AppLocalizations l, String code) => switch (code) {
  'veg' => l.dietVeg,
  'eggetarian' => l.dietEggetarian,
  'vegan' => l.dietVegan,
  'jain' => l.dietJain,
  'non_veg' => l.dietNonVeg,
  _ => code,
};

String conditionLabel(AppLocalizations l, String code) => switch (code) {
  'diabetes' => l.conditionDiabetes,
  'prediabetes' => l.conditionPrediabetes,
  'pcos' => l.conditionPcos,
  'hypertension' => l.conditionHypertension,
  _ => code,
};

/// A canonical allergen's label; free text is the member's own wording.
String allergenLabel(AppLocalizations l, String code) => switch (code) {
  'milk' => l.allergenMilk,
  'peanut' => l.allergenPeanut,
  'gluten' => l.allergenGluten,
  'soy' => l.allergenSoy,
  'egg' => l.allergenEgg,
  'tree_nut' => l.allergenTreeNut,
  'sesame' => l.allergenSesame,
  'fish' => l.allergenFish,
  'crustacean' => l.allergenCrustacean,
  'mustard' => l.allergenMustard,
  'sulphite' => l.allergenSulphite,
  _ => code,
};

/// `alert.*` labels are lower-case (they sit mid-sentence in reasons); as a
/// standalone switch label the first letter is capitalised where the script
/// has case.
String alertLabel(AppLocalizations l, String code) {
  final label = switch (code) {
    'palm_oil' => l.alertPalmOil,
    'maida' => l.alertMaida,
    'added_sugar' => l.alertAddedSugar,
    'artificial_sweetener' => l.alertArtificialSweetener,
    'msg' => l.alertMsg,
    _ => code,
  };
  return toBeginningOfSentenceCase(label);
}

/// "You" for the account holder, else the name, else the relation.
String memberOutLabel(AppLocalizations l10n, MemberOut m) {
  if (m.isPrimary) return l10n.resultYou;
  final name = m.name.trim();
  return name.isNotEmpty ? name : shareRelation(l10n, m.relation.json);
}
