// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/food_detail_out.dart';
import '../models/food_kind_path.dart';
import '../models/food_search_out.dart';
import '../models/portion_in.dart';
import '../models/search_kind.dart';
import '../models/unit_out.dart';

part 'foods_client.g.dart';

@RestApi()
abstract class FoodsClient {
  factory FoodsClient(Dio dio, {String? baseUrl}) = _FoodsClient;

  /// Foods By Barcode.
  ///
  /// Look a scanned barcode up for LOGGING: your own custom food with that barcode first, then.
  /// our product, then Open Food Facts. For the verdict use `products_get_by_barcode` and.
  /// `analyze`: they never see custom foods. 422 `invalid_barcode`, 404 `product_not_found`, 503.
  /// `off_unavailable`.
  ///
  /// [memberId] - Defaults to the primary member.
  @GET('/v1/foods/barcode/{barcode}')
  Future<FoodDetailOut> foodsByBarcode({
    @Path('barcode') required String barcode,
    @Query('member_id') String? memberId,
  });

  /// Foods Search.
  ///
  /// Search generic foods and Indian dishes first, then packaged products (our catalogue and.
  /// Open Food Facts). Hits carry no nutrients. When Open Food Facts cannot answer, the other.
  /// results still come back with `partial: true` and `failed_sources: ["off"]`. USDA and.
  /// Open Food Facts credits ride on each hit.
  ///
  /// [kinds] - Which sources to search; default all (food = generic foods and dishes; custom_food and recipe = yours, listed first).
  ///
  /// [q] - 2 to 80 characters after trimming and collapsing spaces; shorter is 422 search_query_too_short.
  @GET('/v1/foods/search')
  Future<FoodSearchOut> foodsSearch({
    @Query('q') required String q,
    @Query('limit') int? limit = 20,
    @Query('kinds') List<SearchKind>? kinds,
  });

  /// Foods Units List.
  ///
  /// The household units (kind, volume or grams) in display order. Whether a unit applies to.
  /// a food is `foods_get`'s `units`; the label is the i18n key `unit.<code>`.
  @GET('/v1/foods/units')
  Future<List<UnitOut>> foodsUnitsList();

  /// Foods Get.
  ///
  /// One food with the per-100 values and ONLY the units that resolve (a unit with nothing to.
  /// convert it by is never listed), the default unit, the units the user may set their own.
  /// grams for, credits and, for a dish, its ingredients. `id` is a uuid, or the barcode for.
  /// `off`. Per-100 values the member hid are null. Household measures and dishes are pending.
  /// dietitian review.
  ///
  /// [memberId] - Defaults to the primary member.
  @GET('/v1/foods/{kind}/{id}')
  Future<FoodDetailOut> foodsGet({
    @Path('kind') required FoodKindPath kind,
    @Path('id') required String id,
    @Query('member_id') String? memberId,
  });

  /// Foods Portion Delete.
  ///
  /// Remove YOUR value for this unit; ours applies again. 204 even when you had none.
  @DELETE('/v1/foods/{kind}/{id}/portions/{unit}')
  Future<void> foodsPortionDelete({
    @Path('kind') required FoodKindPath kind,
    @Path('id') required String id,
    @Path('unit') required String unit,
  });

  /// Foods Portion Put.
  ///
  /// Set YOUR grams for one unit of one food (for example one roti = 35 g). Count and volume.
  /// units only; `serving` and the mass units are 422 `unit_not_supported`. The value belongs to.
  /// the account, replaces ours for you, and never changes a past diary entry.
  ///
  /// [memberId] - Defaults to the primary member.
  @PUT('/v1/foods/{kind}/{id}/portions/{unit}')
  Future<FoodDetailOut> foodsPortionPut({
    @Path('kind') required FoodKindPath kind,
    @Path('id') required String id,
    @Path('unit') required String unit,
    @Body() required PortionIn body,
    @Query('member_id') String? memberId,
  });
}
