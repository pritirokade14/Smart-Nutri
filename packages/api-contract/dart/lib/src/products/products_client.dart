// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/language.dart';
import '../models/product_create.dart';
import '../models/product_out.dart';
import '../models/public_product_out.dart';

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

  /// Products Get Public
  @GET('/v1/products/{barcode}/public')
  Future<PublicProductOut> productsGetPublic({
    @Path('barcode') required String barcode,
    @Query('language') Language? language = Language.en,
  });
}
