// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/meal_slots_out.dart';

part 'meal_slots_client.g.dart';

@RestApi()
abstract class MealSlotsClient {
  factory MealSlotsClient(Dio dio, {String? baseUrl}) = _MealSlotsClient;

  /// Meal Slots List.
  ///
  /// The member's meal slots in order, plus `suggested_slot_id`, the server's pick for the.
  /// current moment (clients preselect it and never compute a slot). Creates the four defaults on.
  /// the first call. Needs only `terms`: slots hold no health data. 404 `member_not_found` for.
  /// another account's member; 422 `diary_member_not_enabled` for a non-primary member.
  @GET('/v1/meal-slots')
  Future<MealSlotsOut> mealSlotsList({
    @Query('include_archived') bool? includeArchived = false,
    @Query('member_id') String? memberId,
  });
}
