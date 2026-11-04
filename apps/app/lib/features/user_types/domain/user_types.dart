// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../members/domain/member.dart';
import '../../modes/mode_layouts.dart';

/// The six user types (P9-R2), in the picker's display order.
const userTypeKeys = [
  'health_condition',
  'family',
  'weight_loss',
  'gym',
  'allergy_diet',
  'eat_better',
];

/// Types that reveal health information: saving one needs `health_data`.
const healthRevealingTypes = {
  'health_condition',
  'weight_loss',
  'allergy_diet',
};

/// At most this many types per account (decision 2).
const maxUserTypes = 3;

const familyWithKeys = ['children', 'parents', 'partner', 'others'];
const gymGoalKeys = ['build_muscle', 'lose_fat', 'stay_fit'];

/// Whether the account has answered the type picker. [unknown] while the
/// answer loads or failed to load: the app goes on (like the terms check).
enum UserTypesStatus { unknown, unanswered, answered }

/// The account's chosen types as keys, in the user's tap order. A type this
/// build doesn't know is left out.
List<String> chosenTypes(UserTypesOut out) => [
  for (final t in out.types)
    if (t.json case final String key) key,
];

/// The focused mode the API resolved, or [kDefaultType] for one this build
/// doesn't know.
String activeTypeOf(UserTypesOut out) => out.activeType.json ?? kDefaultType;

/// Types with a follow-up screen, in priority order. Weight loss has none.
List<String> followUpTypes(List<String> types) => [
  for (final t in kTypePriority)
    if (types.contains(t) && t != 'weight_loss') t,
];

/// The follow-up answers being edited. Each belongs to one type; only the
/// chosen types' answers are sent.
class FollowUpAnswers {
  const FollowUpAnswers({
    this.conditions = const [],
    this.familyWith = const [],
    this.gymGoal,
    this.allergens = const [],
    this.diet,
    this.alerts = const [],
  });

  /// The stored answers (editing from Profile). Unknown codes are left out.
  factory FollowUpAnswers.fromApi(FollowUps f) {
    List<String> keys(List<Object>? values, String? Function(Object) json) => [
      for (final v in values ?? const <Object>[])
        if (json(v) case final String k) k,
    ];
    return FollowUpAnswers(
      conditions: keys(f.conditions, (v) => (v as FollowUpsConditions).json),
      familyWith: keys(f.familyWith, (v) => (v as FollowUpsFamilyWith).json),
      gymGoal: f.gymGoal?.json,
      allergens: keys(f.allergens, (v) => (v as FollowUpsAllergens).json),
      diet: f.diet?.json,
      alerts: keys(f.alerts, (v) => (v as FollowUpsAlerts).json),
    );
  }

  final List<String> conditions;
  final List<String> familyWith;
  final String? gymGoal;
  final List<String> allergens;
  final String? diet;
  final List<String> alerts;

  FollowUpAnswers copyWith({
    List<String>? conditions,
    List<String>? familyWith,
    String? Function()? gymGoal,
    List<String>? allergens,
    String? Function()? diet,
    List<String>? alerts,
  }) => FollowUpAnswers(
    conditions: conditions ?? this.conditions,
    familyWith: familyWith ?? this.familyWith,
    gymGoal: gymGoal == null ? this.gymGoal : gymGoal(),
    allergens: allergens ?? this.allergens,
    diet: diet == null ? this.diet : diet(),
    alerts: alerts ?? this.alerts,
  );

  /// Only the answers of the chosen [types] (the API refuses a follow-up
  /// without its type). An empty answer is sent as null ("not answered").
  FollowUps toApi(List<String> types) {
    List<T>? list<T>(String type, List<String> v, T Function(String) parse) =>
        types.contains(type) && v.isNotEmpty
        ? [for (final k in v) parse(k)]
        : null;
    return FollowUps(
      conditions: list(
        'health_condition',
        conditions,
        FollowUpsConditions.fromJson,
      ),
      familyWith: list('family', familyWith, FollowUpsFamilyWith.fromJson),
      gymGoal: types.contains('gym') && gymGoal != null
          ? FollowUpsGymGoal.fromJson(gymGoal!)
          : null,
      allergens: list('allergy_diet', allergens, FollowUpsAllergens.fromJson),
      diet: types.contains('allergy_diet') && diet != null
          ? FollowUpsDiet.fromJson(diet!)
          : null,
      alerts: list('eat_better', alerts, FollowUpsAlerts.fromJson),
    );
  }

  /// The answers without the health follow-ups (conditions, allergens, diet).
  FollowUpAnswers withoutHealth() =>
      FollowUpAnswers(familyWith: familyWith, gymGoal: gymGoal, alerts: alerts);
}

/// Whether saving [types] with [answers] needs the `health_data` consent:
/// a health-revealing type or a health follow-up (mirrors the API's gate).
bool typesNeedHealthConsent(List<String> types, FollowUpAnswers answers) {
  if (types.any(healthRevealingTypes.contains)) return true;
  final sent = answers.toApi(types);
  return sent.conditions != null || sent.allergens != null || sent.diet != null;
}

/// Whether the review screen ticks [change] by default: only when the user's
/// own follow-up answer chose it. Conditions, allergens, the diet and the
/// alerts come only from follow-up answers; a goal does only when the gym
/// follow-up picked it (a weight-loss or eating-better goal is a suggestion
/// from the type alone).
bool tickedByDefault(PrefillChange change) => switch (change.field) {
  PrefillChangeField.conditions ||
  PrefillChangeField.allergens ||
  PrefillChangeField.diet ||
  PrefillChangeField.customAlerts => true,
  PrefillChangeField.goal => change.reason == PrefillChangeReason.gym,
  _ => false,
};

/// Goals the members API saves (from the contract).
final _saveableGoals = {for (final g in MemberPatchGoal.$valuesDefined) g.json};

/// A list value from a pre-fill change (`value` / `current`), or null.
List<String>? prefillList(Object? value) =>
    value is List ? [for (final v in value) '$v'] : null;

/// The member form the review sends: the primary member as stored, with only
/// the [confirmed] changes and the picked [goal] (null: keep it) applied.
/// Each change carries the full new value (current plus added), so nothing
/// is ever removed. A value this build cannot represent is left unchanged.
MemberDraft applyPrefill(
  MemberOut primary,
  Iterable<PrefillChange> confirmed, {
  String? goal,
}) {
  final d = MemberDraft.fromMember(primary);
  var conditions = d.conditions;
  var keepConditions = d.keepConditions;
  var allergens = d.allergens;
  var diet = d.diet;
  var newGoal = d.goal;
  var alerts = d.customAlerts;
  var keepAlerts = d.keepCustomAlerts;
  for (final c in confirmed) {
    final list = prefillList(c.value);
    final scalar = c.value is String ? c.value as String : null;
    switch (c.field) {
      case PrefillChangeField.conditions
          when list != null && list.every(conditionKeys.contains):
        conditions = list;
        keepConditions = false;
      case PrefillChangeField.allergens when list != null:
        allergens = list;
      case PrefillChangeField.diet when dietKeys.contains(scalar):
        diet = scalar;
      case PrefillChangeField.goal when _saveableGoals.contains(scalar):
        newGoal = scalar;
      case PrefillChangeField.customAlerts
          when list != null && list.every(customAlertKeys.contains):
        alerts = list;
        keepAlerts = false;
      default:
        break;
    }
  }
  if (goal != null && _saveableGoals.contains(goal)) newGoal = goal;
  return MemberDraft(
    name: d.name,
    relation: d.relation,
    birthYear: d.birthYear,
    sex: d.sex,
    heightCm: d.heightCm,
    weightKg: d.weightKg,
    diet: diet,
    allergens: allergens,
    conditions: conditions,
    customAlerts: alerts,
    goal: newGoal,
    keepConditions: keepConditions,
    keepCustomAlerts: keepAlerts,
  );
}
