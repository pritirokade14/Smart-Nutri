import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_diary.dart';
import '../../support/fake_foods.dart';
import '../../support/fake_meals.dart';
import '../../support/fake_recipes.dart';
import '../../support/fake_members.dart';
import '../../support/fake_targets.dart';
import '../../support/fake_user_types.dart';
import '../user_types/user_types_harness.dart';

export '../user_types/user_types_harness.dart' show AppHarness, en, pumpApp;

MemberOut diaryPrimary() => memberOut(
  id: 'p1',
  name: 'Ravi',
  relation: MemberOutRelation.self,
  birthYear: 1997,
  weightKg: 70,
  isPrimary: true,
);

class DiaryEnv {
  DiaryEnv({
    String day = 'day_complete_under',
    String week = 'week_mixed',
    String targets = 'g1_build_muscle',
    GoalSettingsOut? settings,
    List<MealSlotOut>? slots,
    FakeMealsClient? meals,
    FakeFoodsClient? foods,
    FakeCustomFoodsClient? customFoods,
    FakeRecipesClient? recipes,
  }) : diary = FakeDiaryClient(day: day, week: week),
       slots = FakeMealSlotsClient(items: slots),
       meals = meals ?? FakeMealsClient(),
       foods = foods ?? FakeFoodsClient(),
       customFoods = customFoods ?? FakeCustomFoodsClient(),
       recipes = recipes ?? FakeRecipesClient() {
    this.targets = FakeTargetsClient(
      today: targets,
      settings: settings ?? goalSettingsOut(activity: 'moderate'),
    );
  }

  final FakeDiaryClient diary;
  final FakeMealSlotsClient slots;
  final FakeMealsClient meals;
  final FakeFoodsClient foods;
  final FakeCustomFoodsClient customFoods;
  final FakeRecipesClient recipes;
  final queue = MemoryMealQueue();
  late final FakeTargetsClient targets;

  /// Gives the slot list the ids of the day's own slots (as the API would).
  void slotsFromDay() => slots.items = [
    for (final s in diary.day.slots.where((s) => !s.archived))
      slotOut(
        s.slotId,
        s.labelKey ?? '',
        position: s.position,
        customLabel: s.customLabel,
      ),
  ];

  /// Every analytics event with its filtered props.
  final events = <(String, Map<String, Object>)>[];

  FakeUserTypesApi get api => FakeUserTypesApi(
    me: FakeUserTypesMe(userTypesOut(types: ['gym'])),
    members: FakeMembersClient([diaryPrimary()]),
    consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
    targets: targets,
    diary: diary,
    mealSlots: slots,
    foods: foods,
    customFoods: customFoods,
    recipes: recipes,
  );
}

/// Pumps the signed-in app on the Diary tab.
Future<AppHarness> pumpDiary(
  WidgetTester t,
  DiaryEnv env, {
  String initial = '/diary',
  Size? size,
  String locale = 'en',
}) => pumpApp(
  t,
  env.api,
  meals: env.meals,
  queue: env.queue,
  locale: locale,
  initial: initial,
  size: size ?? const Size(900, 3600),
  onEvent: (e, p) => env.events.add((e, p)),
);

/// Every visible `Text` string under [root] (default: the whole app).
List<String> texts(WidgetTester t, {Finder? root}) {
  final finder = root == null
      ? find.byType(Text)
      : find.descendant(of: root, matching: find.byType(Text));
  return [
    for (final w in t.widgetList<Text>(finder))
      if (w.data != null) w.data! else w.textSpan?.toPlainText() ?? '',
  ];
}
