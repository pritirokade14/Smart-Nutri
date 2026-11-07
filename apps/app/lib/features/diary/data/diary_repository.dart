// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../domain/diary_dates.dart';

/// A failed diary call. [code] is the API `error.code` (`date_in_future`,
/// `meal_not_found`, ...), `network` when there was no response, or null;
/// screens map it with `localizedErrorCode`.
class DiaryFailure implements Exception {
  const DiaryFailure(this.code, [this.cause]);

  final String? code;
  final Object? cause;

  static Future<T> guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on Object catch (e) {
      throw DiaryFailure(apiErrorCode(e), e);
    }
  }

  @override
  String toString() => 'DiaryFailure($code)';
}

/// Wraps the generated `DiaryClient` and the edit calls of `MealsClient`.
/// Dates are calendar-date strings (`2026-11-07`); null means the account's
/// local today, which the API decides.
class DiaryRepository {
  DiaryRepository(this._diary, this._meals);

  final DiaryClient _diary;
  final MealsClient _meals;

  Future<DiaryDayOut> day({String? date}) =>
      DiaryFailure.guard(() => _diary.diaryDayGet(date: parseDateKey(date)));

  Future<DiaryWeekOut> week({String? end}) =>
      DiaryFailure.guard(() => _diary.diaryWeekGet(end: parseDateKey(end)));

  Future<MealOut> update(String mealId, MealPatch patch) =>
      DiaryFailure.guard(() => _meals.mealsUpdate(mealId: mealId, body: patch));

  Future<void> delete(String mealId) =>
      DiaryFailure.guard(() => _meals.mealsDelete(mealId: mealId));

  Future<DiaryDayStatusOut> setPartial(String date, bool partial) =>
      DiaryFailure.guard(
        () => _diary.diaryDayStatusPut(
          day: parseDateKey(date)!,
          body: DiaryDayStatusIn(partialLogged: partial),
        ),
      );

  Future<List<RecentItem>> recents({String? slotId}) => DiaryFailure.guard(
    () async => (await _diary.diaryRecentsList(slotId: slotId)).items,
  );

  /// Copies a meal or a whole day (`mealsCopy`); [body.clientId] makes a
  /// retry safe.
  Future<CopyOut> copy(CopyIn body) =>
      DiaryFailure.guard(() => _meals.mealsCopy(body: body));
}
