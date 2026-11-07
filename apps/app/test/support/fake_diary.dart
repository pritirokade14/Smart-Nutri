import 'package:smartnutri_api/src/export.dart';

import 'fixtures.dart';

/// `DiaryClient` over the golden diary files. Records every call.
class FakeDiaryClient implements DiaryClient {
  FakeDiaryClient({String day = 'day_empty', String week = 'week_mixed'})
    : day = diaryFixture(day),
      week = diaryWeekFixture(week);

  /// What `diaryDayGet` answers, unless [dayFor] is set.
  DiaryDayOut day;
  DiaryWeekOut week;

  /// Answers by the requested date (overrides [day]).
  DiaryDayOut Function(DateTime? date)? dayFor;

  Object? dayError;
  Object? weekError;
  Object? statusError;

  final dayDates = <DateTime?>[];
  final weekEnds = <DateTime?>[];
  final statuses = <(DateTime, bool)>[];
  final recentSlots = <String?>[];
  List<RecentItem> recents = [];

  @override
  Future<DiaryDayOut> diaryDayGet({String? memberId, DateTime? date}) async {
    dayDates.add(date);
    if (dayError case final e?) throw e;
    return dayFor?.call(date) ?? day;
  }

  @override
  Future<DiaryWeekOut> diaryWeekGet({String? memberId, DateTime? end}) async {
    weekEnds.add(end);
    if (weekError case final e?) throw e;
    return week;
  }

  @override
  Future<DiaryDayStatusOut> diaryDayStatusPut({
    required DateTime day,
    required DiaryDayStatusIn body,
  }) async {
    if (statusError case final e?) throw e;
    statuses.add((day, body.partialLogged));
    return DiaryDayStatusOut(date: day, partialLogged: body.partialLogged);
  }

  @override
  Future<RecentsOut> diaryRecentsList({
    int? limit = 30,
    String? memberId,
    String? slotId,
  }) async {
    recentSlots.add(slotId);
    return RecentsOut(items: recents);
  }
}

/// A saved slot row.
MealSlotOut slotOut(
  String id,
  String labelKey, {
  int position = 0,
  String? customLabel,
}) => MealSlotOut(
  archived: false,
  customLabel: customLabel,
  defaultTimeWindow: null,
  id: id,
  isDefault: customLabel == null,
  labelKey: customLabel == null ? labelKey : null,
  memberId: 'p1',
  position: position,
);

/// The four default slots, ids `slot-breakfast` ... `slot-dinner`.
List<MealSlotOut> defaultSlots() => [
  slotOut('slot-breakfast', 'diary.slot.breakfast', position: 0),
  slotOut('slot-lunch', 'diary.slot.lunch', position: 1),
  slotOut('slot-snack', 'diary.slot.snack', position: 2),
  slotOut('slot-dinner', 'diary.slot.dinner', position: 3),
];

class FakeMealSlotsClient implements MealSlotsClient {
  FakeMealSlotsClient({List<MealSlotOut>? items, this.suggested})
    : items = items ?? defaultSlots();

  List<MealSlotOut> items;
  String? suggested;
  Object? error;

  @override
  Future<MealSlotsOut> mealSlotsList({
    bool? includeArchived = false,
    String? memberId,
  }) async {
    if (error case final e?) throw e;
    return MealSlotsOut(
      items: items,
      suggestedSlotId: suggested ?? items.first.id,
    );
  }

  // Slot writes (create, rename, reorder, archive) arrive with the Meals screen (Task 15).
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

/// A recent item (what `diary_recents_list` returns).
RecentItem recentItem({
  String name = 'Masala Oats',
  String productId = 'p-oats',
  num grams = 40,
  String slotId = 'slot-breakfast',
}) => RecentItem(
  attribution: null,
  barcode: null,
  grade: null,
  grams: grams,
  lastEatenAt: DateTime.utc(2026, 11, 6, 8),
  mealSlotId: slotId,
  name: name,
  productId: productId,
  sourceKind: RecentItemSourceKind.product,
);
