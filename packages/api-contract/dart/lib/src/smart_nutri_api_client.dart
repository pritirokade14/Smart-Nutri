// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';

import 'analyze/analyze_client.dart';
import 'consents/consents_client.dart';
import 'health/health_client.dart';
import 'me/me_client.dart';
import 'meals/meals_client.dart';
import 'members/members_client.dart';
import 'products/products_client.dart';
import 'scans/scans_client.dart';

/// SmartNutri API `v0.0.0`
class SmartNutriApiClient {
  SmartNutriApiClient(Dio dio, {String? baseUrl})
    : _dio = dio,
      _baseUrl = baseUrl;

  final Dio _dio;
  final String? _baseUrl;

  static String get version => '0.0.0';

  AnalyzeClient? _analyze;
  ConsentsClient? _consents;
  HealthClient? _health;
  MeClient? _me;
  MealsClient? _meals;
  MembersClient? _members;
  ProductsClient? _products;
  ScansClient? _scans;

  AnalyzeClient get analyze =>
      _analyze ??= AnalyzeClient(_dio, baseUrl: _baseUrl);

  ConsentsClient get consents =>
      _consents ??= ConsentsClient(_dio, baseUrl: _baseUrl);

  HealthClient get health => _health ??= HealthClient(_dio, baseUrl: _baseUrl);

  MeClient get me => _me ??= MeClient(_dio, baseUrl: _baseUrl);

  MealsClient get meals => _meals ??= MealsClient(_dio, baseUrl: _baseUrl);

  MembersClient get members =>
      _members ??= MembersClient(_dio, baseUrl: _baseUrl);

  ProductsClient get products =>
      _products ??= ProductsClient(_dio, baseUrl: _baseUrl);

  ScansClient get scans => _scans ??= ScansClient(_dio, baseUrl: _baseUrl);
}
