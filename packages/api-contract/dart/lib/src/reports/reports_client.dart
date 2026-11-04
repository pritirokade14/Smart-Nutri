// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/report_create.dart';
import '../models/report_out.dart';

part 'reports_client.g.dart';

@RestApi()
abstract class ReportsClient {
  factory ReportsClient(Dio dio, {String? baseUrl}) = _ReportsClient;

  /// Reports Create.
  ///
  /// Report a problem with a product's data, for review. 201 with the new report, or 200.
  /// with the existing one when the same reason is already open (idempotent). Rate-limited.
  /// per account per day.
  @POST('/v1/products/{product_id}/reports')
  Future<ReportOut> reportsCreate({
    @Path('product_id') required String productId,
    @Body() required ReportCreate body,
  });
}
