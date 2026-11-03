// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/meal_in.dart';
import '../models/meal_out.dart';
import '../models/summary.dart';
import '../models/summary_period.dart';
import '../models/week_counts.dart';

part 'meals_client.g.dart';

@RestApi()
abstract class MealsClient {
  factory MealsClient(Dio dio, {String? baseUrl}) = _MealsClient;

  /// Meals List.
  ///
  /// A member's logs, newest first (at most 200). Default range: the last 7 IST days.
  @GET('/v1/meals')
  Future<List<MealOut>> mealsList({
    @Query('member_id') required String memberId,
    @Query('from') DateTime? from,
    @Query('to') DateTime? to,
  });

  /// Meals Log.
  ///
  /// Log "I ate this" for a member: 201 for a new log, 200 with the stored log when.
  /// ``client_id`` was already used (offline retries never duplicate).
  @POST('/v1/meals')
  Future<MealOut> mealsLog({@Body() required MealIn body});

  /// Meals Summary.
  ///
  /// Totals of sugar, salt, protein and kcal against the member's daily limits (pending.
  /// clinician review). A nutrient missing on any logged label sets ``incomplete`` and is never.
  /// counted as 0.
  ///
  /// [date] - IST date; default today.
  @GET('/v1/meals/summary')
  Future<Summary> mealsSummary({
    @Query('member_id') required String memberId,
    @Query('date') DateTime? date,
    @Query('period') SummaryPeriod? period = SummaryPeriod.day,
  });

  /// Meals Week Counts.
  ///
  /// Counts for the weekly share text (products checked, items logged), whole family.
  ///
  /// [date] - IST date; default today.
  @GET('/v1/meals/week_counts')
  Future<WeekCounts> mealsWeekCounts({@Query('date') DateTime? date});

  /// Meals Delete
  @DELETE('/v1/meals/{meal_id}')
  Future<void> mealsDelete({@Path('meal_id') required String mealId});
}
