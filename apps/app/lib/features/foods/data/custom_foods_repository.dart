// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';
import 'package:uuid/uuid.dart';

import 'foods_repository.dart';

/// Wraps the generated `CustomFoodsClient`. Online only: the API stores what
/// the user typed and works out the per-100 values; nothing is computed here.
class CustomFoodsRepository {
  CustomFoodsRepository(this._client, {Uuid? uuid})
    : _uuid = uuid ?? const Uuid();

  final CustomFoodsClient _client;
  final Uuid _uuid;

  Future<CustomFoodsOut> list({String? cursor}) =>
      FoodsFailure.guard(() => _client.customFoodsList(cursor: cursor));

  /// A new food. [clientId] stays the same for one form, so a retry after a
  /// timeout never stores it twice.
  Future<CustomFoodOut> create(CustomFoodIn body, {String? clientId}) =>
      FoodsFailure.guard(
        () => _client.customFoodsCreate(
          body: CustomFoodIn(
            name: body.name,
            brand: body.brand,
            basis: body.basis,
            valuesPer: body.valuesPer,
            servingG: body.servingG,
            nutrients: body.nutrients,
            densityGPerMl: body.densityGPerMl,
            barcode: body.barcode,
            portions: body.portions,
            clientId: clientId ?? _uuid.v4(),
          ),
        ),
      );

  /// A full replace: a nutrient left out becomes unknown.
  Future<CustomFoodOut> update(String id, CustomFoodIn body) =>
      FoodsFailure.guard(
        () => _client.customFoodsUpdate(foodId: id, body: body),
      );

  Future<void> delete(String id) =>
      FoodsFailure.guard(() => _client.customFoodsDelete(foodId: id));
}
