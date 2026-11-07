// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';
import 'package:uuid/uuid.dart';

import '../../foods/data/foods_repository.dart';

/// Wraps the generated `RecipesClient`. The API sums the ingredients; the
/// app never computes a recipe nutrient.
class RecipesRepository {
  RecipesRepository(this._client, {Uuid? uuid}) : _uuid = uuid ?? const Uuid();

  final RecipesClient _client;
  final Uuid _uuid;

  Future<RecipesOut> list({String? cursor}) =>
      FoodsFailure.guard(() => _client.recipesList(cursor: cursor));

  Future<RecipeOut> get(String id) =>
      FoodsFailure.guard(() => _client.recipesGet(recipeId: id));

  Future<RecipeOut> create(RecipeIn body, {String? clientId}) =>
      FoodsFailure.guard(
        () => _client.recipesCreate(
          body: RecipeIn(
            name: body.name,
            servings: body.servings,
            cookedWeightG: body.cookedWeightG,
            ingredients: body.ingredients,
            clientId: clientId ?? _uuid.v4(),
          ),
        ),
      );

  Future<RecipeOut> update(String id, RecipeIn body) =>
      FoodsFailure.guard(() => _client.recipesUpdate(recipeId: id, body: body));

  Future<void> delete(String id) =>
      FoodsFailure.guard(() => _client.recipesDelete(recipeId: id));
}
