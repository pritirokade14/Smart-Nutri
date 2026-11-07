// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/archive_out.dart';
import '../models/meal_slot_create_in.dart';
import '../models/meal_slot_out.dart';
import '../models/meal_slot_rename_in.dart';
import '../models/meal_slots_list_out.dart';
import '../models/meal_slots_order_in.dart';
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

  /// Meal Slots Create.
  ///
  /// Add a custom meal (at most 6 active; 422 `meal_slot_limit_reached` with `details.max`).
  /// The label is user text: 1 to 30 characters, trimmed, no control characters, unique.
  /// case-insensitively among active meals (422 `meal_slot_label_duplicate`, label not echoed).
  /// A repeated `client_id` returns the stored meal with 200.
  @POST('/v1/meal-slots')
  Future<MealSlotOut> mealSlotsCreate({@Body() required MealSlotCreateIn body});

  /// Meal Slots Reorder.
  ///
  /// Set the order. `ids` must be every active meal exactly once (else 422.
  /// `validation_error`, `fields: ["body.ids"]`); an unknown id is 404 `meal_slot_not_found`.
  @PUT('/v1/meal-slots/order')
  Future<MealSlotsListOut> mealSlotsReorder({
    @Body() required MealSlotsOrderIn body,
  });

  /// Meal Slots Archive.
  ///
  /// Remove a meal. One with logged entries is archived (they stay on their day); one.
  /// without is deleted. Repeating it is a no-op. 422 `meal_slot_last_active` for the last one.
  @DELETE('/v1/meal-slots/{slot_id}')
  Future<ArchiveOut> mealSlotsArchive({
    @Path('slot_id') required String slotId,
    @Query('member_id') String? memberId,
  });

  /// Meal Slots Rename.
  ///
  /// Rename a meal or change its usual time. Null fields are unchanged; use.
  /// `clear_custom_label` (default meals only) or `clear_time_window` to remove. Entries keep.
  /// their meal. 422 `meal_slot_archived` for a removed meal.
  @PATCH('/v1/meal-slots/{slot_id}')
  Future<MealSlotOut> mealSlotsRename({
    @Path('slot_id') required String slotId,
    @Body() required MealSlotRenameIn body,
    @Query('member_id') String? memberId,
  });
}
