import 'package:smartnutri_api/src/export.dart';

import 'fake_diary.dart';
import 'fake_foods.dart';
import 'fake_recipes.dart';
import 'fake_members.dart';
import 'fake_targets.dart';

/// Builds a [UserTypesOut] the way the API returns it.
UserTypesOut userTypesOut({
  List<String> types = const [],
  bool answered = true,
  String? active,
  PrefillSuggestion? prefill,
  FollowUps followUps = const FollowUps(),
}) => UserTypesOut(
  activeType: UserTypesOutActiveType.fromJson(
    active ??
        (types.isEmpty
            ? 'eat_better'
            : [
                'allergy_diet',
                'health_condition',
                'family',
                'weight_loss',
                'gym',
                'eat_better',
              ].firstWhere(types.contains)),
  ),
  answered: answered,
  answeredAt: answered ? DateTime.utc(2026, 11, 4) : null,
  followUps: followUps,
  prefill: prefill,
  types: [for (final t in types) UserTypesOutTypes.fromJson(t)],
);

/// The unanswered state (`GET` before the first `PUT`).
UserTypesOut unansweredTypes() => userTypesOut(answered: false);

PrefillChange prefillChange(
  String field, {
  Object? current,
  required Object value,
  List<String> added = const [],
  String reason = 'eat_better',
}) => PrefillChange(
  field: PrefillChangeField.fromJson(field),
  current: current,
  value: value,
  added: added,
  reason: PrefillChangeReason.fromJson(reason),
);

PrefillSuggestion prefillSuggestion({
  List<PrefillChange> changes = const [],
  List<String>? goalChoice,
  String memberId = 'p1',
  bool needsHealthConsent = false,
}) => PrefillSuggestion(
  changes: changes,
  goalChoice: goalChoice == null
      ? null
      : [for (final g in goalChoice) PrefillSuggestionGoalChoice.fromJson(g)],
  memberId: memberId,
  needsHealthConsent: needsHealthConsent,
);

/// `MeClient` with in-memory user types. Records every write.
class FakeUserTypesMe implements MeClient {
  FakeUserTypesMe([UserTypesOut? current])
    : current = current ?? unansweredTypes();

  UserTypesOut current;
  final puts = <UserTypesIn>[];
  final actives = <String>[];
  int gets = 0;

  /// The `prefill` the next PUT returns (null: none).
  PrefillSuggestion? Function(UserTypesIn body)? prefillAfterPut;

  /// Thrown by the next PUTs, in order.
  final putErrors = <Object>[];

  /// Thrown by the next set-active calls, in order.
  final activeErrors = <Object>[];

  /// Thrown by GET when set.
  Object? getError;

  @override
  Future<MeOut> meGet() async => MeOut(
    createdAt: DateTime(2026),
    displayName: 'Asha',
    email: 'a@b.c',
    id: 'u1',
    language: MeOutLanguage.en,
    timezone: 'Asia/Kolkata',
  );

  @override
  Future<MeOut> meTimezonePut({required TimezoneIn body}) async => meGet();

  @override
  Future<void> meDelete() async {}

  @override
  Future<UserTypesOut> meUserTypesGet() async {
    gets++;
    if (getError case final e?) throw e;
    return current;
  }

  @override
  Future<UserTypesOut> meUserTypesPut({required UserTypesIn body}) async {
    puts.add(body);
    if (putErrors.isNotEmpty) throw putErrors.removeAt(0);
    final types = [for (final t in body.types) t.json!];
    current = userTypesOut(
      types: types,
      followUps: body.followUps ?? const FollowUps(),
      prefill: prefillAfterPut?.call(body) ?? prefillSuggestion(),
    );
    return current;
  }

  @override
  Future<UserTypesOut> meUserTypesSetActive({
    required ActiveTypeIn body,
  }) async {
    actives.add(body.activeType.json!);
    if (activeErrors.isNotEmpty) throw activeErrors.removeAt(0);
    current = userTypesOut(
      types: [for (final t in current.types) t.json!],
      active: body.activeType.json,
      followUps: current.followUps,
      prefill: current.prefill,
    );
    return current;
  }
}

/// The generated client with fake me (user types), members and consents.
/// Every other client throws.
class FakeUserTypesApi implements SmartNutriApiClient {
  FakeUserTypesApi({
    FakeUserTypesMe? me,
    FakeMembersClient? members,
    FakeConsentsClient? consents,
    FakeTargetsClient? targets,
    FakeDiaryClient? diary,
    FakeMealSlotsClient? mealSlots,
    FakeFoodsClient? foods,
    FakeCustomFoodsClient? customFoods,
    FakeRecipesClient? recipes,
  }) : me = me ?? FakeUserTypesMe(),
       diary = diary ?? FakeDiaryClient(),
       foods = foods ?? FakeFoodsClient(),
       customFoods = customFoods ?? FakeCustomFoodsClient(),
       recipes = recipes ?? FakeRecipesClient(),
       mealSlots = mealSlots ?? FakeMealSlotsClient(),
       targets = targets ?? FakeTargetsClient(),
       members = members ?? FakeMembersClient(),
       consents = consents ?? FakeConsentsClient(granted: {'terms'});

  @override
  final FakeUserTypesMe me;
  @override
  final FakeMembersClient members;
  @override
  final FakeConsentsClient consents;
  @override
  final FakeTargetsClient targets;
  @override
  final FakeDiaryClient diary;
  @override
  final FakeMealSlotsClient mealSlots;
  @override
  final FakeFoodsClient foods;
  @override
  final FakeCustomFoodsClient customFoods;
  @override
  final FakeRecipesClient recipes;

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}
