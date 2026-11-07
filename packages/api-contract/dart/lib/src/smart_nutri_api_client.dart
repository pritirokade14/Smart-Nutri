// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';

import 'analyze/analyze_client.dart';
import 'consents/consents_client.dart';
import 'custom_foods/custom_foods_client.dart';
import 'diary/diary_client.dart';
import 'favourites/favourites_client.dart';
import 'foods/foods_client.dart';
import 'health/health_client.dart';
import 'me/me_client.dart';
import 'meal_slots/meal_slots_client.dart';
import 'meals/meals_client.dart';
import 'members/members_client.dart';
import 'methodology/methodology_client.dart';
import 'products/products_client.dart';
import 'reports/reports_client.dart';
import 'recipes/recipes_client.dart';
import 'scans/scans_client.dart';
import 'targets/targets_client.dart';
import 'voice/voice_client.dart';
import 'weights/weights_client.dart';

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
  CustomFoodsClient? _customFoods;
  DiaryClient? _diary;
  FavouritesClient? _favourites;
  FoodsClient? _foods;
  HealthClient? _health;
  MeClient? _me;
  MealSlotsClient? _mealSlots;
  MealsClient? _meals;
  MembersClient? _members;
  MethodologyClient? _methodology;
  ProductsClient? _products;
  ReportsClient? _reports;
  RecipesClient? _recipes;
  ScansClient? _scans;
  TargetsClient? _targets;
  VoiceClient? _voice;
  WeightsClient? _weights;

  AnalyzeClient get analyze =>
      _analyze ??= AnalyzeClient(_dio, baseUrl: _baseUrl);

  ConsentsClient get consents =>
      _consents ??= ConsentsClient(_dio, baseUrl: _baseUrl);

  CustomFoodsClient get customFoods =>
      _customFoods ??= CustomFoodsClient(_dio, baseUrl: _baseUrl);

  DiaryClient get diary => _diary ??= DiaryClient(_dio, baseUrl: _baseUrl);

  FavouritesClient get favourites =>
      _favourites ??= FavouritesClient(_dio, baseUrl: _baseUrl);

  FoodsClient get foods => _foods ??= FoodsClient(_dio, baseUrl: _baseUrl);

  HealthClient get health => _health ??= HealthClient(_dio, baseUrl: _baseUrl);

  MeClient get me => _me ??= MeClient(_dio, baseUrl: _baseUrl);

  MealSlotsClient get mealSlots =>
      _mealSlots ??= MealSlotsClient(_dio, baseUrl: _baseUrl);

  MealsClient get meals => _meals ??= MealsClient(_dio, baseUrl: _baseUrl);

  MembersClient get members =>
      _members ??= MembersClient(_dio, baseUrl: _baseUrl);

  MethodologyClient get methodology =>
      _methodology ??= MethodologyClient(_dio, baseUrl: _baseUrl);

  ProductsClient get products =>
      _products ??= ProductsClient(_dio, baseUrl: _baseUrl);

  ReportsClient get reports =>
      _reports ??= ReportsClient(_dio, baseUrl: _baseUrl);

  RecipesClient get recipes =>
      _recipes ??= RecipesClient(_dio, baseUrl: _baseUrl);

  ScansClient get scans => _scans ??= ScansClient(_dio, baseUrl: _baseUrl);

  TargetsClient get targets =>
      _targets ??= TargetsClient(_dio, baseUrl: _baseUrl);

  VoiceClient get voice => _voice ??= VoiceClient(_dio, baseUrl: _baseUrl);

  WeightsClient get weights =>
      _weights ??= WeightsClient(_dio, baseUrl: _baseUrl);
}
