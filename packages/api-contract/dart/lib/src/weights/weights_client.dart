// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/days.dart';
import '../models/weight_in.dart';
import '../models/weight_out.dart';
import '../models/weight_trend_out.dart';
import '../models/weights_out.dart';

part 'weights_client.g.dart';

@RestApi()
abstract class WeightsClient {
  factory WeightsClient(Dio dio, {String? baseUrl}) = _WeightsClient;

  /// Weights List.
  ///
  /// The member's weigh-ins, oldest first. Default the last 90 local days; a range longer.
  /// than 400 days is 422 `date_range_too_long`.
  ///
  /// [memberId] - Defaults to the primary member.
  ///
  /// [from] - Local date; default 89 days back.
  ///
  /// [to] - Local date; default today.
  @GET('/v1/weights')
  Future<WeightsOut> weightsList({
    @Query('member_id') String? memberId,
    @Query('from') DateTime? from,
    @Query('to') DateTime? to,
  });

  /// Weights Trend Get.
  ///
  /// The weight trend, weekly rate and projection, computed from the member's full history.
  /// and sliced to the window. Every kg, the rate and the target are null under `hide_all`.
  /// (`y` is kept for the chart's shape). Information, not medical advice; the thresholds are.
  /// pending clinician review.
  ///
  /// [memberId] - Defaults to the primary member.
  ///
  /// [days] - Window in days: 30, 90 or 365.
  @GET('/v1/weights/trend')
  Future<WeightTrendOut> weightsTrendGet({
    @Query('days') Days? days = Days.value90,
    @Query('member_id') String? memberId,
  });

  /// Weights Delete.
  ///
  /// Delete a weigh-in. Needs only `terms`: erasure is never gated. 404 `weight_not_found`.
  ///
  /// [memberId] - Defaults to the primary member.
  @DELETE('/v1/weights/{day}')
  Future<void> weightsDelete({
    @Path('day') required DateTime day,
    @Query('member_id') String? memberId,
  });

  /// Weights Put.
  ///
  /// Create or replace the weigh-in of a local day (200 either way; one per day). 422.
  /// `weight_out_of_range` (outside 2 to 300 kg), `weight_needs_confirm` (outside 30 to 200 kg,.
  /// or a big change since the last weigh-in; resend with `confirm_unusual`; `details.previous` is.
  /// null under `hide_all`), `date_in_future`, `date_too_old` (over 400 days). A repeated.
  /// `client_id` returns the stored row. Today's daily guide is recomputed.
  @PUT('/v1/weights/{day}')
  Future<WeightOut> weightsPut({
    @Path('day') required DateTime day,
    @Body() required WeightIn body,
  });
}
