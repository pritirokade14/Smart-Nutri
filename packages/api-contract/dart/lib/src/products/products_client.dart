// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/alternatives_out.dart';
import '../models/compare_out.dart';
import '../models/language.dart';
import '../models/product_create.dart';
import '../models/product_out.dart';
import '../models/public_product_out.dart';
import '../models/search_hit.dart';

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
  /// Up to 5 products from the same Open Food Facts category with a strictly better Nutri-Score (calculated by SmartNutri). ``member_status`` comes from the rules engine. Never an error for a product with no category: ``reason`` says why the list is empty. For products known by barcode (Open Food Facts).
  @GET('/v1/products/barcode/{code}/alternatives')
  Future<AlternativesOut> productsAlternativesByBarcode({
    @Path('code') required String code,
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
  /// Our products first (name or brand), then Open Food Facts. ``q``: 2 to 80 characters.
  @GET('/v1/products/search')
  Future<List<SearchHit>> productsSearch({
    @Query('q') required String q,
    @Query('limit') int? limit = 20,
  });

  /// Products Get Public
  @GET('/v1/products/{barcode}/public')
  Future<PublicProductOut> productsGetPublic({
    @Path('barcode') required String barcode,
    @Query('language') Language? language = Language.en,
  });

  /// Products Alternatives.
  ///
  /// Up to 5 products from the same Open Food Facts category with a strictly better Nutri-Score (calculated by SmartNutri). ``member_status`` comes from the rules engine. Never an error for a product with no category: ``reason`` says why the list is empty.
  @GET('/v1/products/{product_id}/alternatives')
  Future<AlternativesOut> productsAlternatives({
    @Path('product_id') required String productId,
    @Query('member_id') String? memberId,
  });
}
