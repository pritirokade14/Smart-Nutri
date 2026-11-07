// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/display_in.dart';
import '../models/goal_settings_in.dart';
import '../models/goal_settings_out.dart';
import '../models/targets_out.dart';
import '../models/targets_preview_in.dart';

part 'targets_client.g.dart';

@RestApi()
abstract class TargetsClient {
  factory TargetsClient(Dio dio, {String? baseUrl}) = _TargetsClient;

  /// Targets Get.
  ///
  /// Today's targets, computed live. A past date has no stored guide in this version, so it.
  /// returns status `none`; a future date is 422 `date_in_future`.
  ///
  /// [memberId] - Defaults to the primary member.
  ///
  /// [date] - Local date; default today.
  @GET('/v1/targets')
  Future<TargetsOut> targetsGet({
    @Query('member_id') String? memberId,
    @Query('date') DateTime? date,
  });

  /// Targets Display Put.
  ///
  /// The eye toggle: change only how numbers are shown. Needs only `terms`, so hiding.
  /// numbers works even after `health_data` was withdrawn (Ruling D4).
  @PUT('/v1/targets/display')
  Future<GoalSettingsOut> targetsDisplayPut({@Body() required DisplayIn body});

  /// Targets Preview.
  ///
  /// Targets for unsaved settings and optional unsaved body data. Nothing is saved.
  /// `needs_body_data` is a status here, not an error.
  @POST('/v1/targets/preview')
  Future<TargetsOut> targetsPreview({@Body() required TargetsPreviewIn body});

  /// Targets Settings Delete.
  ///
  /// Erase the member's daily-guide settings. Needs only `terms`: erasure is never gated.
  ///
  /// [memberId] - Defaults to the primary member.
  @DELETE('/v1/targets/settings')
  Future<void> targetsSettingsDelete({@Query('member_id') String? memberId});

  /// Targets Settings Get.
  ///
  /// The member's saved daily-guide settings, or null before setup.
  ///
  /// [memberId] - Defaults to the primary member.
  @GET('/v1/targets/settings')
  Future<GoalSettingsOut?> targetsSettingsGet({
    @Query('member_id') String? memberId,
  });

  /// Targets Settings Put.
  ///
  /// Validate and save the settings; returns today's targets, recomputed. Information, not.
  /// medical advice: the numbers are estimates pending clinician review.
  @PUT('/v1/targets/settings')
  Future<TargetsOut> targetsSettingsPut({@Body() required GoalSettingsIn body});
}
