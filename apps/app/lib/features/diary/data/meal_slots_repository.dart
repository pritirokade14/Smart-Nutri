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
}
