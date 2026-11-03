// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

/// The 11 canonical allergen keys, in the API's order
/// (`apps/api/app/features/members/schemas.py` CANONICAL_ALLERGENS).
const canonicalAllergens = [
  'milk',
  'peanut',
  'gluten',
  'soy',
  'egg',
  'tree_nut',
  'sesame',
  'fish',
  'crustacean',
  'mustard',
  'sulphite',
];

/// Member ingredient alerts (the engine's CUSTOM_ALERT_KEYS).
const customAlertKeys = [
  'palm_oil',
  'maida',
  'added_sugar',
  'artificial_sweetener',
  'msg',
];

const conditionKeys = ['diabetes', 'prediabetes', 'pcos', 'hypertension'];
const dietKeys = ['veg', 'eggetarian', 'vegan', 'jain', 'non_veg'];
const sexKeys = ['female', 'male', 'other'];
const goalKeys = ['healthy_eating', 'weight_loss', 'weight_gain'];

/// Relations a new or edited non-primary member can have. Never `self`: the
/// primary (the account holder) is created by the API.
const newRelationKeys = ['child', 'parent', 'spouse', 'other'];

/// API limits (`members/schemas.py`).
const maxAllergens = 20;
const allergenMinLength = 2;
const allergenMaxLength = 40;
const birthYearMin = 1900;
const heightRange = (min: 30, max: 250);
const weightRange = (min: 2, max: 300);

/// The member form's state. Every field is sent on save, so a PATCH never
/// clears a field by accident (the generated `MemberPatch` sends unset
/// fields as null, and null clears sex, height, weight and goal).
class MemberDraft {
  const MemberDraft({
    this.name = '',
    this.relation,
    this.birthYear,
    this.sex,
    this.heightCm,
    this.weightKg,
    this.diet = 'non_veg',
    this.allergens = const [],
    this.conditions = const [],
    this.customAlerts = const [],
    this.goal,
    this.keepConditions = false,
    this.keepCustomAlerts = false,
  });

  /// A stored diet, condition or alert this app version doesn't know comes
  /// back as `$unknown`. It is never dropped or coerced: the diet stays null
  /// and the list is sent as null, which the API reads as "unchanged".
  factory MemberDraft.fromMember(MemberOut m) => MemberDraft(
    name: m.name,
    relation: m.relation.json,
    birthYear: m.birthYear,
    sex: m.sex?.json,
    heightCm: m.heightCm,
    weightKg: m.weightKg,
    diet: m.diet.json,
    allergens: List.unmodifiable(m.allergens),
    conditions: List.unmodifiable([
      for (final c in m.conditions)
        if (c.json case final String code) code,
    ]),
    customAlerts: List.unmodifiable([
      for (final a in m.customAlerts)
        if (a.json case final String code) code,
    ]),
    goal: m.goal?.json,
    keepConditions: m.conditions.any((c) => c.json == null),
    keepCustomAlerts: m.customAlerts.any((a) => a.json == null),
  );

  final String name;
  final String? relation;
  final int? birthYear;
  final String? sex;
  final num? heightCm;
  final num? weightKg;

  /// Null only for a stored diet this app version doesn't know.
  final String? diet;
  final List<String> allergens;
  final List<String> conditions;
  final List<String> customAlerts;
  final String? goal;

  /// The stored conditions hold a value this app doesn't know: send null
  /// (unchanged) instead of a list that would drop it.
  final bool keepConditions;

  /// As [keepConditions], for the custom alerts.
  final bool keepCustomAlerts;

  /// For `POST /v1/members`. [relation] and [birthYear] must be set.
  MemberIn toMemberIn() => MemberIn(
    name: name.trim(),
    relation: MemberInRelation.fromJson(relation!),
    birthYear: birthYear!,
    sex: sex == null ? null : MemberInSex.fromJson(sex!),
    heightCm: heightCm,
    weightKg: weightKg,
    diet: MemberInDiet.fromJson(diet ?? 'non_veg'),
    allergens: allergens,
    conditions: [for (final c in conditions) MemberInConditions.fromJson(c)],
    customAlerts: [
      for (final a in customAlerts) MemberInCustomAlerts.fromJson(a),
    ],
    goal: goal == null ? null : MemberInGoal.fromJson(goal!),
  );

  /// For `PATCH /v1/members/{id}`: the full current form state, never a
  /// partial one. A null sex, height, weight or goal here means the user
  /// cleared it.
  MemberPatch toMemberPatch() => MemberPatch(
    name: name.trim(),
    relation: relation == null ? null : MemberPatchRelation.fromJson(relation!),
    birthYear: birthYear,
    sex: sex == null ? null : MemberPatchSex.fromJson(sex!),
    heightCm: heightCm,
    weightKg: weightKg,
    diet: diet == null ? null : MemberPatchDiet.fromJson(diet!),
    allergens: allergens,
    conditions: keepConditions
        ? null
        : [for (final c in conditions) MemberPatchConditions.fromJson(c)],
    customAlerts: keepCustomAlerts
        ? null
        : [for (final a in customAlerts) MemberPatchCustomAlerts.fromJson(a)],
    goal: goal == null ? null : MemberPatchGoal.fromJson(goal!),
  );
}

/// Whether saving [draft] writes new health data, mirroring the API's
/// `health_data` consent gate (P5, Ruling P8.1): a health field set to a
/// non-empty value it doesn't already hold. Clearing a field, re-sending a
/// stored value, or removing entries from stored allergies or conditions is
/// not gated. The API still decides: a 403 `consent_required` also opens the
/// consent sheet.
bool writesHealthData(MemberDraft draft, {MemberOut? stored}) {
  final before = stored == null ? null : MemberDraft.fromMember(stored);
  bool listWrites(List<String> value, List<String>? old) {
    if (value.isEmpty) return false;
    if (old == null) return true;
    // A subset of what is stored (or the same list) adds nothing new.
    return value.toSet().difference(old.toSet()).isNotEmpty;
  }

  bool scalarWrites(Object? value, Object? old) =>
      value != null && (before == null || value != old);

  return listWrites(draft.allergens, before?.allergens) ||
      listWrites(draft.conditions, before?.conditions) ||
      scalarWrites(draft.goal, before?.goal) ||
      scalarWrites(draft.heightCm, before?.heightCm) ||
      scalarWrites(draft.weightKg, before?.weightKg);
}
