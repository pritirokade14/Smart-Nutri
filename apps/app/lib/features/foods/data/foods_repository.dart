// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';

/// A failed foods call. [code] is the API `error.code` (`food_not_found`,
/// `unit_not_supported`, ...), `network` when there was no response, or null.
class FoodsFailure implements Exception {
  const FoodsFailure(this.code, [this.cause]);

  final String? code;
  final Object? cause;

  static Future<T> guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on Object catch (e) {
      throw FoodsFailure(apiErrorCode(e), e);
    }
  }

  @override
  String toString() => 'FoodsFailure($code)';
}

/// Which food a search hit or an entry points at.
typedef FoodRef = ({FoodKindPath kind, String id});

/// Wraps the generated `FoodsClient`. It never converts a unit or computes a
/// nutrient: the API does.
class FoodsRepository {
  FoodsRepository(this._client);

  final FoodsClient _client;

  Future<FoodSearchOut> search(String q) =>
      FoodsFailure.guard(() => _client.foodsSearch(q: q));

  Future<FoodDetailOut> detail(FoodRef ref, {String? memberId}) =>
      FoodsFailure.guard(
        () => _client.foodsGet(kind: ref.kind, id: ref.id, memberId: memberId),
      );

  /// Sets the account's own grams (or ml) for one unit of this food.
  Future<FoodDetailOut> putPortion(
    FoodRef ref,
    String unit,
    num gramsPerUnit, {
    String? memberId,
  }) => FoodsFailure.guard(
    () => _client.foodsPortionPut(
      kind: ref.kind,
      id: ref.id,
      unit: unit,
      body: PortionIn(gramsPerUnit: gramsPerUnit),
      memberId: memberId,
    ),
  );

  Future<void> deletePortion(FoodRef ref, String unit) => FoodsFailure.guard(
    () => _client.foodsPortionDelete(kind: ref.kind, id: ref.id, unit: unit),
  );
}
