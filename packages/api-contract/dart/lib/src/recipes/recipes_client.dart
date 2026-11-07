// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/recipe_in.dart';
import '../models/recipe_out.dart';
import '../models/recipes_out.dart';

part 'recipes_client.g.dart';

@RestApi()
abstract class RecipesClient {
  factory RecipesClient(Dio dio, {String? baseUrl}) = _RecipesClient;

  /// Recipes List.
  ///
  /// The account's recipes, most recently changed first (no nutrients: open one for those).
  @GET('/v1/recipes')
  Future<RecipesOut> recipesList({
    @Query('cursor') String? cursor,
    @Query('limit') int? limit = 50,
  });

  /// Recipes Create.
  ///
  /// Build a recipe from 1 to 50 ingredients. Each is a food, one of your custom foods, one.
  /// of our products or an Open Food Facts barcode, with a quantity and a household unit; a.
  /// unit with no grams is 422 `unit_grams_unknown` with the ingredient's `details.position`.
  /// The basis weight is the cooked weight, or else the raw total (422 `recipe_weight_invalid`:.
  /// `cooked_weight_required` or `out_of_range`, 0.2 to 3 times the raw total). A repeated.
  /// `client_id` returns the stored recipe with 200.
  @POST('/v1/recipes')
  Future<RecipeOut> recipesCreate({@Body() required RecipeIn body});

  /// Recipes Delete.
  ///
  /// Delete the recipe. Diary entries keep their name and values (their reference becomes.
  /// null).
  @DELETE('/v1/recipes/{recipe_id}')
  Future<void> recipesDelete({@Path('recipe_id') required String recipeId});

  /// Recipes Get.
  ///
  /// One recipe with its ingredients. Per-100 g and per-serving values are the sum of the.
  /// KNOWN ingredients: a nutrient in `incomplete_nutrients` is 'at least' that much. Numbers the.
  /// member hid are null.
  @GET('/v1/recipes/{recipe_id}')
  Future<RecipeOut> recipesGet({@Path('recipe_id') required String recipeId});

  /// Recipes Update.
  ///
  /// Replace the recipe and its ingredients. Past diary entries keep the values they were.
  /// logged with. An ingredient whose custom food was deleted must be replaced.
  @PUT('/v1/recipes/{recipe_id}')
  Future<RecipeOut> recipesUpdate({
    @Path('recipe_id') required String recipeId,
    @Body() required RecipeIn body,
  });
}
