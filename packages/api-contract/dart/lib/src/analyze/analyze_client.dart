// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/analyze_out.dart';
import '../models/analyze_request.dart';

part 'analyze_client.g.dart';

@RestApi()
abstract class AnalyzeClient {
  factory AnalyzeClient(Dio dio, {String? baseUrl}) = _AnalyzeClient;

  /// Analyze Create
  @POST('/v1/analyze')
  Future<AnalyzeOut> analyzeCreate({@Body() required AnalyzeRequest body});
}
