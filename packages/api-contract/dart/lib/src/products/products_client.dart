// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/alternatives_out.dart';
import '../models/alternatives_sort.dart';
import '../models/compare_out.dart';
import '../models/language.dart';
import '../models/product_create.dart';
import '../models/product_out.dart';
import '../models/public_product_out.dart';
import '../models/search_hit.dart';
import '../models/search_sort.dart';

part 'products_client.g.dart';

@RestApi()
abstract class ProductsClient {
  factory ProductsClient(Dio dio, {String? baseUrl}) = _ProductsClient;

  /// Products Create.
  ///
  /// Save a confirmed label draft (``scan_id``) or a manual entry as a pending product.
  ///
  /// Then call ``analyze_create`` with the returned ``product_id``.
  @POST('/v1/products')
  Future<ProductOut> productsCreate({@Body() required ProductCreate body});

  /// Products Get By Barcode
  @GET('/v1/products/barcode/{code}')
  Future<ProductOut> productsGetByBarcode({@Path('code') required String code});

  /// Products Alternatives By Barcode.
  ///
  /// Up to 5 products from the same Open Food Facts category. ``sort=grade`` (default): a strictly better Nutri-Score (calculated by SmartNutri). ``sort=protein``: strictly more protein per 100 kcal and a Nutri-Score no worse, ranked for ``member_id`` or else the primary member. ``member_status`` comes from the rules engine; a product the engine rates ``avoid`` for the member is never suggested, and safer statuses rank first. Never an error for a product with no category: ``reason`` says why the list is empty. For products known by barcode (Open Food Facts).
  ///
  /// [sort] - grade: better Nutri-Score. protein: more protein per 100 kcal, never avoid for the member (member_id or the primary member), never a worse grade.
  @GET('/v1/products/barcode/{code}/alternatives')
  Future<AlternativesOut> productsAlternativesByBarcode({
    @Path('code') required String code,
    @Query('sort') AlternativesSort? sort = AlternativesSort.grade,
    @Query('member_id') String? memberId,
  });

  /// Products Compare.
  ///
  /// Two products side by side. Each side is exactly one of a product id or a barcode.
  /// (``invalid_product_ref`` otherwise). ``member_status`` comes from the rules engine.
  ///
  /// [a] - Side a: our product id.
  ///
  /// [aBarcode] - Side a: barcode.
  ///
  /// [b] - Side b: our product id.
  ///
  /// [bBarcode] - Side b: barcode.
  @GET('/v1/products/compare')
  Future<CompareOut> productsCompare({
    @Query('a') String? a,
    @Query('a_barcode') String? aBarcode,
    @Query('b') String? b,
    @Query('b_barcode') String? bBarcode,
    @Query('member_id') String? memberId,
  });

  /// Products Search.
  ///
  /// Our products first (name or brand), then Open Food Facts. ``q``: 3 to 80 characters.
  ///
  /// Open Food Facts search calls are capped for the whole server; over the cap a cached.
  /// result is served, else our own hits come back with ``off_degraded`` true, and.
  /// only with no local hits either 503 ``off_unavailable`` with Retry-After.
  ///
  /// ``member_status`` comes from the rules engine: with ``member_id`` (404 if not this.
  /// account's), or for the primary member with ``sort=protein``, which never returns a hit.
  /// the engine rates ``avoid`` for that member.
  ///
  /// [sort] - relevance: ours first, then Open Food Facts. protein: most protein per 100 kcal first (unknown last), never avoid for the member (member_id or the primary member).
  ///
  /// [q] - 3 to 80 characters after trimming and collapsing spaces; shorter is 422 search_query_too_short.
  @GET('/v1/products/search')
  Future<List<SearchHit>> productsSearch({
    @Query('q') required String q,
    @Query('member_id') String? memberId,
    @Query('limit') int? limit = 20,
    @Query('sort') SearchSort? sort = SearchSort.relevance,
  });

  /// Products Get Public
  @GET('/v1/products/{barcode}/public')
  Future<PublicProductOut> productsGetPublic({
    @Path('barcode') required String barcode,
    @Query('language') Language? language = Language.en,
  });

  /// Products Alternatives.
  ///
  /// Up to 5 products from the same Open Food Facts category. ``sort=grade`` (default): a strictly better Nutri-Score (calculated by SmartNutri). ``sort=protein``: strictly more protein per 100 kcal and a Nutri-Score no worse, ranked for ``member_id`` or else the primary member. ``member_status`` comes from the rules engine; a product the engine rates ``avoid`` for the member is never suggested, and safer statuses rank first. Never an error for a product with no category: ``reason`` says why the list is empty.
  ///
  /// [sort] - grade: better Nutri-Score. protein: more protein per 100 kcal, never avoid for the member (member_id or the primary member), never a worse grade.
  @GET('/v1/products/{product_id}/alternatives')
  Future<AlternativesOut> productsAlternatives({
    @Path('product_id') required String productId,
    @Query('sort') AlternativesSort? sort = AlternativesSort.grade,
    @Query('member_id') String? memberId,
  });
}
