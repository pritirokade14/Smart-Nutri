import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../shared/widgets/reason_list.dart';
import '../domain/reasons.dart';

/// Generic line for a reason the app cannot render: a reason code this build
/// does not know, or params that do not match the message. Never throws.
String reasonFallbackText(AppLocalizations l10n) =>
    l10n.verdictReasonUnavailable;

/// Localized text for one API reason (`packages/i18n/README.md`, "Rendering
/// reasons"): picks `reason.<code>` or its `reason_variant.*`, maps code params
/// through their label sets, joins lists and formats numbers for the locale.
String reasonText(AppLocalizations l10n, ReasonOut reason) {
  try {
    return _ReasonFormatter(l10n, reasonParams(reason)).format(reason);
  } on _BadParam {
    return reasonFallbackText(l10n);
  }
}

class ReasonLine extends StatelessWidget {
  const ReasonLine({super.key, required this.reason});

  final ReasonOut reason;

  @override
  Widget build(BuildContext context) =>
      ReasonBullet(text: reasonText(AppLocalizations.of(context), reason));
}

class _BadParam implements Exception {
  const _BadParam();
}

class _ReasonFormatter {
  _ReasonFormatter(this.l10n, this.p);

  final AppLocalizations l10n;
  final Map<String, Object?> p;

  // Latin digits in every locale (R21).
  static final _latinNumbers = NumberFormat.decimalPattern('en');

  // Separator for joined lists ({ingredients}, {high_in}).
  static const _listSeparator = ', ';

  String format(ReasonOut r) {
    switch (reasonMessageKey(r)) {
      case 'reason_variant.nutrient_missing_low_confidence':
        return l10n.reasonVariantNutrientMissingLowConfidence(
          _nutrient(_str('nutrient')),
        );
      case 'reason_variant.diet_violation_mark_only':
        return l10n.reasonVariantDietViolationMarkOnly(_diet(_str('diet')));
      case 'reason_variant.custom_alert_flag_only':
        return l10n.reasonVariantCustomAlertFlagOnly;
    }
    return switch (r.code) {
      'added_sugars' => l10n.reasonAddedSugars(_list('ingredients')),
      'age_unknown' => l10n.reasonAgeUnknown,
      'allergen_contains' => l10n.reasonAllergenContains(_allergen()),
      'allergen_may_contain' => l10n.reasonAllergenMayContain(_allergen()),
      'allergen_unknown' => l10n.reasonAllergenUnknown(_allergen()),
      'allergen_unrecognised' => l10n.reasonAllergenUnrecognised(_allergen()),
      'carbs_per_serving_high' => l10n.reasonCarbsPerServingHigh(
        _str('basis'),
        _num('carbs_g'),
      ),
      'cardio_risk_high_in' => l10n.reasonCardioRiskHighIn(
        _list('high_in', _nutrient),
      ),
      'child_caffeine' => l10n.reasonChildCaffeine,
      'child_salt_high' => l10n.reasonChildSaltHigh(_num('salt_g')),
      'child_sugar_high' => l10n.reasonChildSugarHigh(
        _str('basis'),
        _num('limit_g'),
        _num('pct'),
      ),
      'child_sugar_moderate' => l10n.reasonChildSugarModerate(
        _str('basis'),
        _num('limit_g'),
        _num('pct'),
      ),
      // The member's own wording: shown as-is.
      'condition_unrecognised' => l10n.reasonConditionUnrecognised(
        _str('condition'),
      ),
      'custom_alert' => l10n.reasonCustomAlert(
        _alert(_str('alert')),
        _nonEmptyList('ingredients'),
      ),
      'custom_alert_unknown' => l10n.reasonCustomAlertUnknown(
        _list('alerts', _alert),
      ),
      'diet_unknown' => l10n.reasonDietUnknown(_diet(_str('diet'))),
      // Mark-only (no ingredients) is handled above; any other empty or
      // missing ingredient list cannot be rendered.
      'diet_violation' => l10n.reasonDietViolation(
        _diet(_str('diet')),
        _nonEmptyList('ingredients'),
      ),
      'energy_dense' => l10n.reasonEnergyDense(_num('energy_kcal')),
      'good_protein_density' => l10n.reasonGoodProteinDensity,
      'hidden_sugars' => l10n.reasonHiddenSugars(_list('ingredients')),
      'infant_added_salt' => l10n.reasonInfantAddedSalt,
      'infant_added_sugar' => l10n.reasonInfantAddedSugar,
      'infant_caffeine' => l10n.reasonInfantCaffeine,
      'infant_honey' => l10n.reasonInfantHoney,
      'infant_salt_high' => l10n.reasonInfantSaltHigh(_num('salt_g')),
      'infant_sugar_high' => l10n.reasonInfantSugarHigh(_num('sugars_g')),
      'ingredients_missing' => l10n.reasonIngredientsMissing,
      'misleading_sugar_claim' => l10n.reasonMisleadingSugarClaim(
        _claim(_str('claim')),
      ),
      'nutrient_missing' => l10n.reasonNutrientMissing(
        _nutrient(_str('nutrient')),
      ),
      'nutriscore_low' => l10n.reasonNutriscoreLow(_str('grade')),
      'salt_high' => l10n.reasonSaltHigh(_num('salt_g')),
      'salt_moderate' => l10n.reasonSaltModerate(_num('salt_g')),
      'sodium_additives' => l10n.reasonSodiumAdditives(_list('ingredients')),
      'sugar_high' => l10n.reasonSugarHigh(_num('sugars_g')),
      'sugar_moderate' => l10n.reasonSugarModerate(_num('sugars_g')),
      'supplement_child' => l10n.reasonSupplementChild,
      'supplement_infant' => l10n.reasonSupplementInfant,
      _ => reasonFallbackText(l10n),
    };
  }

  String _str(String name) {
    final v = p[name];
    if (v is String) return v;
    throw const _BadParam();
  }

  String _num(String name) {
    final v = p[name];
    if (v is num) return _latinNumbers.format(v);
    throw const _BadParam();
  }

  String _nonEmptyList(String name) {
    final v = p[name];
    if (v is List && v.isEmpty) throw const _BadParam();
    return _list(name);
  }

  String _list(String name, [String Function(String)? label]) {
    final v = p[name];
    if (v is! List || v.any((e) => e is! String)) throw const _BadParam();
    final items = v.cast<String>();
    return (label == null ? items : items.map(label)).join(_listSeparator);
  }

  // Unrecognised allergen codes are the member's own wording: shown as-is.
  String _allergen() => switch (_str('allergen')) {
    'milk' => l10n.allergenMilk,
    'peanut' => l10n.allergenPeanut,
    'gluten' => l10n.allergenGluten,
    'soy' => l10n.allergenSoy,
    'egg' => l10n.allergenEgg,
    'tree_nut' => l10n.allergenTreeNut,
    'sesame' => l10n.allergenSesame,
    'fish' => l10n.allergenFish,
    'crustacean' => l10n.allergenCrustacean,
    'mustard' => l10n.allergenMustard,
    'sulphite' => l10n.allergenSulphite,
    final other => other,
  };

  String _diet(String code) => switch (code) {
    'veg' => l10n.dietVeg,
    'eggetarian' => l10n.dietEggetarian,
    'vegan' => l10n.dietVegan,
    'jain' => l10n.dietJain,
    'non_veg' => l10n.dietNonVeg,
    _ => code,
  };

  String _claim(String code) => switch (code) {
    'no_added_sugar' => l10n.claimNoAddedSugar,
    'sugar_free' => l10n.claimSugarFree,
    'low_sugar' => l10n.claimLowSugar,
    'low_fat' => l10n.claimLowFat,
    'low_sodium' => l10n.claimLowSodium,
    'high_protein' => l10n.claimHighProtein,
    'source_of_protein' => l10n.claimSourceOfProtein,
    'no_refined_sugar' => l10n.claimNoRefinedSugar,
    'diabetic_friendly' => l10n.claimDiabeticFriendly,
    _ => code,
  };

  // Member ingredient alerts (`alert.*`). An alert key this build does not
  // know cannot be named, so the whole line falls back.
  String _alert(String code) => switch (code) {
    'palm_oil' => l10n.alertPalmOil,
    'maida' => l10n.alertMaida,
    'added_sugar' => l10n.alertAddedSugar,
    'artificial_sweetener' => l10n.alertArtificialSweetener,
    'msg' => l10n.alertMsg,
    _ => throw const _BadParam(),
  };

  String _nutrient(String code) => switch (code) {
    'energy_kcal' => l10n.nutrientEnergyKcal,
    'protein_g' => l10n.nutrientProteinG,
    'carbs_g' => l10n.nutrientCarbsG,
    'sugars_g' => l10n.nutrientSugarsG,
    'fat_g' => l10n.nutrientFatG,
    'sat_fat' => l10n.nutrientSatFat,
    'salt' => l10n.nutrientSalt,
    'sodium_mg' => l10n.nutrientSodiumMg,
    _ => code,
  };
}
