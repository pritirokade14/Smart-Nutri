import 'package:smartnutri_api/src/export.dart';

import 'fake_meals.dart';

FavouriteOut favouriteOut({
  String id = 'fav-1',
  String name = 'Masala Oats',
  FavouriteOutKind kind = FavouriteOutKind.food,
  String? productId = 'p-oats',
  String? foodId,
  num? quantity = 40,
  String? unit = 'g',
  int itemCount = 1,
  List<String>? attributions,
  String? barcode,
  List<FavouriteItemOut>? items,
}) => FavouriteOut(
  barcode: barcode,
  createdAt: DateTime.utc(2026, 11, 6),
  customFoodId: null,
  defaultQuantity: quantity,
  defaultUnit: unit,
  foodId: foodId,
  id: id,
  itemCount: itemCount,
  items: items,
  kind: kind,
  memberId: 'p1',
  name: name,
  productId: kind == FavouriteOutKind.meal ? null : productId,
  recipeId: null,
  sourceKind: kind == FavouriteOutKind.meal
      ? null
      : FavouriteOutSourceKind.product,
  attributions: attributions,
);

/// `FavouritesClient` that keeps a list and records every call. An error in
/// [errors] (by method name) is thrown once.
class FakeFavouritesClient implements FavouritesClient {
  FakeFavouritesClient({List<FavouriteOut>? items}) : items = items ?? [];

  List<FavouriteOut> items;
  final added = <FavouriteIn>[];
  final meals = <FavouriteMealIn>[];
  final deleted = <String>[];
  final logs = <(String, FavouriteLogIn)>[];
  final errors = <String, List<Object>>{};

  /// What `favouritesLog` answers.
  int logCount = 2;

  void _maybeThrow(String m) {
    final q = errors[m];
    if (q != null && q.isNotEmpty) throw q.removeAt(0);
  }

  @override
  Future<FavouritesOut> favouritesList({String? memberId}) async {
    _maybeThrow('list');
    return FavouritesOut(items: items);
  }

  @override
  Future<FavouriteOut> favouritesAdd({required FavouriteIn body}) async {
    added.add(body);
    _maybeThrow('add');
    final f = favouriteOut(
      id: 'fav-new-${added.length}',
      productId: body.productId,
      foodId: body.foodId,
      quantity: body.defaultQuantity,
      unit: body.defaultUnit?.json,
    );
    items = [f, ...items];
    return f;
  }

  @override
  Future<FavouriteOut> favouritesAddMeal({
    required FavouriteMealIn body,
  }) async {
    meals.add(body);
    _maybeThrow('addMeal');
    final f = favouriteOut(
      id: 'fav-meal-${meals.length}',
      name: body.name,
      kind: FavouriteOutKind.meal,
      itemCount: 3,
    );
    items = [f, ...items];
    return f;
  }

  @override
  Future<void> favouritesDelete({required String favouriteId}) async {
    deleted.add(favouriteId);
    _maybeThrow('delete');
    items = [
      for (final f in items)
        if (f.id != favouriteId) f,
    ];
  }

  @override
  Future<FavouriteLogOut> favouritesLog({
    required String favouriteId,
    required FavouriteLogIn body,
  }) async {
    logs.add((favouriteId, body));
    _maybeThrow('log');
    return FavouriteLogOut(
      created: [for (var i = 0; i < logCount; i++) mealOut(id: 'fav-log-$i')],
    );
  }
}
