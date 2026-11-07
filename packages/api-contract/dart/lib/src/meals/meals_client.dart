// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/copy_in.dart';
import '../models/copy_out.dart';
import '../models/meal_in.dart';
import '../models/meal_out.dart';
import '../models/meal_patch.dart';
import '../models/summary.dart';
import '../models/summary_period.dart';
import '../models/week_counts.dart';

part 'meals_client.g.dart';

@RestApi()
abstract class MealsClient {
  factory MealsClient(Dio dio, {String? baseUrl}) = _MealsClient;

  /// Meals List.
  ///
  /// A member's logs, newest first (at most 200), redacted with their numbers display.
  /// ``local_date`` returns one local day. Default range: the last 7 local days.
  ///
  /// [memberId] - Defaults to the primary member.
  ///
  /// [localDate] - One local day; wins over from and to.
  @GET('/v1/meals')
  Future<List<MealOut>> mealsList({
    @Query('member_id') String? memberId,
    @Query('from') DateTime? from,
    @Query('to') DateTime? to,
    @Query('local_date') DateTime? localDate,
  });

  /// Meals Log.
  ///
  /// Log "I ate this" for a member (default: the primary): 201 for a new log, 200 with the.
  /// stored log when ``client_id`` was already used (offline retries never duplicate).
  ///
  /// The slot defaults to the server's pick for the local time; ``local_date`` logs onto a past.
  /// day; ``quick`` logs typed kcal and macros (blanks stay unknown). The response is redacted.
  /// with the member's numbers display.
  @POST('/v1/meals')
  Future<MealOut> mealsLog({@Body() required MealIn body});

  /// Meals Copy.
  ///
  /// Copy one meal (``from_slot_id``) or the whole day onto another day (today or up to 30.
  /// days back). Each copy keeps its source's saved food and portion, never reads the product.
  /// again, and counts against the daily log limit. ``client_id`` is required: a retry returns.
  /// the same rows with 200 and creates nothing. The response is redacted with the member's.
  /// numbers display.
  @POST('/v1/meals/copy')
  Future<CopyOut> mealsCopy({@Body() required CopyIn body});

  /// Meals Summary.
  ///
  /// Totals of sugar, salt, protein and kcal against the member's daily limits (pending.
  /// clinician review). A nutrient missing on any logged label sets ``incomplete`` and is never.
  /// counted as 0.
  ///
  /// [date] - Local date; default today.
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

  /// Meals Update.
  ///
  /// Edit an entry: portion, slot, time or (quick adds only) the typed values. ``null`` means.
  /// unchanged. A new portion is recomputed from the entry's own saved food, so editing one.
  /// entry never changes another and never reads the product again.
  @PATCH('/v1/meals/{meal_id}')
  Future<MealOut> mealsUpdate({
    @Path('meal_id') required String mealId,
    @Body() required MealPatch body,
  });
}
