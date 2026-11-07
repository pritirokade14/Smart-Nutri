// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/custom_food_in.dart';
import '../models/custom_food_out.dart';
import '../models/custom_foods_out.dart';

part 'custom_foods_client.g.dart';

@RestApi()
abstract class CustomFoodsClient {
  factory CustomFoodsClient(Dio dio, {String? baseUrl}) = _CustomFoodsClient;

  /// Custom Foods List.
  ///
  /// The account's own foods, most recently changed first. `next_cursor` is opaque.
  @GET('/v1/custom-foods')
  Future<CustomFoodsOut> customFoodsList({
    @Query('cursor') String? cursor,
    @Query('limit') int? limit = 50,
  });

  /// Custom Foods Create.
  ///
  /// Save a food from its label. A blank nutrient is unknown (never 0); energy, or one of.
  /// protein, carbs and fat, is required (422 `custom_food_nutrients_empty`); implausible values.
  /// are 422 `implausible_value`; a barcode already on another of your foods is 422.
  /// `barcode_already_used`. A repeated `client_id` returns the stored food with 200. It is never.
  /// in the public catalogue and never reaches a verdict.
  @POST('/v1/custom-foods')
  Future<CustomFoodOut> customFoodsCreate({@Body() required CustomFoodIn body});

  /// Custom Foods Delete.
  ///
  /// Delete the food. Diary entries and recipe ingredients keep their name and values (their.
  /// reference becomes null); recipes using it show it as unavailable.
  @DELETE('/v1/custom-foods/{food_id}')
  Future<void> customFoodsDelete({@Path('food_id') required String foodId});

  /// Custom Foods Update.
  ///
  /// Replace the food (a nutrient left out becomes unknown; the portions are replaced). Past.
  /// diary entries keep the values they were logged with.
  @PUT('/v1/custom-foods/{food_id}')
  Future<CustomFoodOut> customFoodsUpdate({
    @Path('food_id') required String foodId,
    @Body() required CustomFoodIn body,
  });
}
