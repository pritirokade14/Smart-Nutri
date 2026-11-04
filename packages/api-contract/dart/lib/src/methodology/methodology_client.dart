// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/methodology.dart';
import '../models/methodology_language.dart';

part 'methodology_client.g.dart';

@RestApi()
abstract class MethodologyClient {
  factory MethodologyClient(Dio dio, {String? baseUrl}) = _MethodologyClient;

  /// Methodology Get.
  ///
  /// How SmartNutri scores products: every rule's live thresholds and their sources.
  ///
  /// Public (no token). The values come from the rules engine config, never written by hand;.
  /// `pending_clinician_review` stays true until a clinician signs the thresholds off.
  /// Section titles and descriptions are client strings (`methodology.section.<id>.*`).
  @GET('/v1/methodology')
  Future<Methodology> methodologyGet({
    @Query('language') MethodologyLanguage? language = MethodologyLanguage.en,
  });
}
