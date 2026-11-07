// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../../diary/domain/diary_dates.dart';
import '../../foods/data/foods_repository.dart';

/// A failed favourites call. [code] is the API `error.code`
/// (`favourite_limit`, `food_retired`, ...), `network` or null; screens map
/// it with `localizedErrorCode`.
class FavouritesFailure implements Exception {
  const FavouritesFailure(this.code, [this.cause]);

  final String? code;
  final Object? cause;

  static Future<T> guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on Object catch (e) {
      throw FavouritesFailure(apiErrorCode(e), e);
    }
  }

  @override
  String toString() => 'FavouritesFailure($code)';
}

/// Wraps the generated `FavouritesClient`. Online only; it never converts a
/// unit or computes a nutrient. Names are user text and go nowhere but the
/// API.
class FavouritesRepository {
  FavouritesRepository(this._client);

  final FavouritesClient _client;

  Future<List<FavouriteOut>> list({String? memberId}) =>
      FavouritesFailure.guard(
        () async => (await _client.favouritesList(memberId: memberId)).items,
      );

  /// Stars a food. [quantity] and [unit] go together (the default portion)
  /// or both stay null.
  Future<FavouriteOut> addFood(
    FoodRef food, {
    String? memberId,
    num? quantity,
    String? unit,
  }) {
    final both = quantity != null && unit != null;
    return FavouritesFailure.guard(
      () => _client.favouritesAdd(
        body: FavouriteIn(
          memberId: memberId,
          foodId: food.kind == FoodKindPath.food ? food.id : null,
          productId: food.kind == FoodKindPath.product ? food.id : null,
          barcode: food.kind == FoodKindPath.off ? food.id : null,
          customFoodId: food.kind == FoodKindPath.customFood ? food.id : null,
          recipeId: food.kind == FoodKindPath.recipe ? food.id : null,
          defaultQuantity: both ? quantity : null,
          defaultUnit: both ? favouriteUnit(unit) : null,
        ),
      ),
    );
  }

  /// Saves a slot of a day as a favourite meal. [name] is sent exactly as
  /// typed; [clientId] makes a retry safe.
  Future<FavouriteOut> addMeal({
    required String fromDate,
    required String fromSlotId,
    required String name,
    required String clientId,
    String? memberId,
  }) => FavouritesFailure.guard(
    () => _client.favouritesAddMeal(
      body: FavouriteMealIn(
        fromDate: parseDateKey(fromDate)!,
        fromSlotId: fromSlotId,
        name: name,
        clientId: clientId,
        memberId: memberId,
      ),
    ),
  );

  Future<void> delete(String id) =>
      FavouritesFailure.guard(() => _client.favouritesDelete(favouriteId: id));

  /// Logs a favourite meal again. [clientId] is made once per user action
  /// and reused by every retry.
  Future<List<MealOut>> log(
    String id, {
    required String clientId,
    String? slotId,
    String? localDate,
  }) => FavouritesFailure.guard(
    () async => (await _client.favouritesLog(
      favouriteId: id,
      body: FavouriteLogIn(
        clientId: clientId,
        mealSlotId: slotId,
        localDate: parseDateKey(localDate),
      ),
    )).created,
  );
}

/// The API's unit enum for a unit code, or null when it has none.
FavouriteInDefaultUnit? favouriteUnit(String code) {
  for (final u in FavouriteInDefaultUnit.values) {
    if (u.json == code) return u;
  }
  return null;
}
