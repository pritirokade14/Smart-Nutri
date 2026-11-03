import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';

/// i18n labels and icons for user-type codes. A code this build does not
/// know is shown as-is.

String userTypeTitle(AppLocalizations l, String type) => switch (type) {
  'health_condition' => l.userTypesTileHealthConditionTitle,
  'family' => l.userTypesTileFamilyTitle,
  'weight_loss' => l.userTypesTileWeightLossTitle,
  'gym' => l.userTypesTileGymTitle,
  'allergy_diet' => l.userTypesTileAllergyDietTitle,
  'eat_better' => l.userTypesTileEatBetterTitle,
  _ => type,
};

String userTypeSubtitle(AppLocalizations l, String type) => switch (type) {
  'health_condition' => l.userTypesTileHealthConditionSubtitle,
  'family' => l.userTypesTileFamilySubtitle,
  'weight_loss' => l.userTypesTileWeightLossSubtitle,
  'gym' => l.userTypesTileGymSubtitle,
  'allergy_diet' => l.userTypesTileAllergyDietSubtitle,
  'eat_better' => l.userTypesTileEatBetterSubtitle,
  _ => '',
};

/// `modes.name.*`: the short name of a focused mode.
String modeName(AppLocalizations l, String type) => switch (type) {
  'health_condition' => l.modesNameHealthCondition,
  'family' => l.modesNameFamily,
  'weight_loss' => l.modesNameWeightLoss,
  'gym' => l.modesNameGym,
  'allergy_diet' => l.modesNameAllergyDiet,
  'eat_better' => l.modesNameEatBetter,
  _ => type,
};

IconData userTypeIcon(String type) => switch (type) {
  'health_condition' => Icons.monitor_heart_outlined,
  'family' => Icons.family_restroom_rounded,
  'weight_loss' => Icons.trending_down_rounded,
  'gym' => Icons.fitness_center_rounded,
  'allergy_diet' => Icons.no_food_outlined,
  _ => Icons.eco_outlined,
};

String familyWithLabel(AppLocalizations l, String code) => switch (code) {
  'children' => l.userTypesFollowUpFamilyChildren,
  'parents' => l.userTypesFollowUpFamilyParents,
  'partner' => l.userTypesFollowUpFamilyPartner,
  'others' => l.userTypesFollowUpFamilyOthers,
  _ => code,
};

String gymGoalLabel(AppLocalizations l, String code) => switch (code) {
  'build_muscle' => l.userTypesFollowUpGymBuildMuscle,
  'lose_fat' => l.userTypesFollowUpGymLoseFat,
  'stay_fit' => l.userTypesFollowUpGymStayFit,
  _ => code,
};
