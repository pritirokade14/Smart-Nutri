// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/diary_day_out.dart';
import '../models/diary_day_status_in.dart';
import '../models/diary_day_status_out.dart';
import '../models/diary_week_out.dart';
import '../models/recents_out.dart';

part 'diary_client.g.dart';

@RestApi()
abstract class DiaryClient {
  factory DiaryClient(Dio dio, {String? baseUrl}) = _DiaryClient;

  /// Diary Day Get.
  ///
  /// One local day of the diary: meal slots with their entries and totals, that day's frozen.
  /// targets, `remaining` and `progress` (all computed here; clients never compute them), and the.
  /// sugar and salt bands. Needs only `terms`: without `health_data`, `targets` is null with.
  /// `targets_status: consent_required` and the entries still load. Numbers the member hid are.
  /// null. Information, not medical advice.
  ///
  /// [memberId] - Defaults to the primary member.
  ///
  /// [date] - Local date; default the account's today.
  @GET('/v1/diary/day')
  Future<DiaryDayOut> diaryDayGet({
    @Query('member_id') String? memberId,
    @Query('date') DateTime? date,
  });

  /// Diary Day Status Put.
  ///
  /// Mark a day as not fully logged (`partial_logged: true`) or clear the mark. A marked day.
  /// is left out of the week averages. 422 `date_in_future` for a future day.
  @PUT('/v1/diary/days/{day}/status')
  Future<DiaryDayStatusOut> diaryDayStatusPut({
    @Path('day') required DateTime day,
    @Body() required DiaryDayStatusIn body,
  });

  /// Diary Recents List.
  ///
  /// Foods the member logged lately, newest first, one per product (quick adds excluded), at.
  /// most 30 from the last 90 days. Needs only `terms`.
  ///
  /// [memberId] - Defaults to the primary member.
  ///
  /// [slotId] - Its items come first.
  @GET('/v1/diary/recents')
  Future<RecentsOut> diaryRecentsList({
    @Query('limit') int? limit = 30,
    @Query('member_id') String? memberId,
    @Query('slot_id') String? slotId,
  });

  /// Diary Week Get.
  ///
  /// The 7 local days ending at `end`, oldest first, each against that day's own frozen.
  /// targets. Averages cover days with items that are not marked partial, and an average with an.
  /// unknown value is flagged. Needs only `terms`.
  ///
  /// [memberId] - Defaults to the primary member.
  ///
  /// [end] - Last day; default the account's today.
  @GET('/v1/diary/week')
  Future<DiaryWeekOut> diaryWeekGet({
    @Query('member_id') String? memberId,
    @Query('end') DateTime? end,
  });
}
