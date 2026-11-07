// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import 'diary_repository.dart';

/// Wraps the generated `MealSlotsClient`.
class MealSlotsRepository {
  MealSlotsRepository(this._client);

  final MealSlotsClient _client;

  Future<MealSlotsOut> list({bool includeArchived = false}) =>
      DiaryFailure.guard(
        () => _client.mealSlotsList(includeArchived: includeArchived),
      );

  /// Adds a meal named [label] (user text, sent exactly as typed).
  Future<MealSlotOut> create(String label, {TimeWindow? window}) =>
      DiaryFailure.guard(
        () => _client.mealSlotsCreate(
          body: MealSlotCreateIn(customLabel: label, defaultTimeWindow: window),
        ),
      );

  /// Renames a meal, or with [clearName] goes back to the default name.
  Future<MealSlotOut> rename(
    String slotId, {
    String? label,
    bool clearName = false,
    TimeWindow? window,
    bool clearWindow = false,
  }) => DiaryFailure.guard(
    () => _client.mealSlotsRename(
      slotId: slotId,
      body: MealSlotRenameIn(
        customLabel: label,
        clearCustomLabel: clearName,
        defaultTimeWindow: window,
        clearTimeWindow: clearWindow,
      ),
    ),
  );

  /// Sends every active id, in the new order.
  Future<List<MealSlotOut>> reorder(List<String> ids) => DiaryFailure.guard(
    () async => (await _client.mealSlotsReorder(
      body: MealSlotsOrderIn(ids: ids),
    )).items,
  );

  /// Removes a meal: archived when it has entries (or is a default),
  /// deleted when unused.
  Future<ArchiveOutResult> archive(String slotId) => DiaryFailure.guard(
    () async => (await _client.mealSlotsArchive(slotId: slotId)).result,
  );
}
