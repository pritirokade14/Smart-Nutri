// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';

import 'analyze/analyze_client.dart';
import 'health/health_client.dart';
import 'me/me_client.dart';
import 'products/products_client.dart';

/// SmartNutri API `v0.0.0`
class SmartNutriApiClient {
  SmartNutriApiClient(Dio dio, {String? baseUrl})
    : _dio = dio,
      _baseUrl = baseUrl;

  final Dio _dio;
  final String? _baseUrl;

  static String get version => '0.0.0';

  AnalyzeClient? _analyze;
  HealthClient? _health;
  MeClient? _me;
  ProductsClient? _products;

  AnalyzeClient get analyze =>
      _analyze ??= AnalyzeClient(_dio, baseUrl: _baseUrl);

  HealthClient get health => _health ??= HealthClient(_dio, baseUrl: _baseUrl);

  MeClient get me => _me ??= MeClient(_dio, baseUrl: _baseUrl);

  ProductsClient get products =>
      _products ??= ProductsClient(_dio, baseUrl: _baseUrl);
}
