// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/favourite_in.dart';
import '../models/favourite_log_in.dart';
import '../models/favourite_log_out.dart';
import '../models/favourite_meal_in.dart';
import '../models/favourite_out.dart';
import '../models/favourites_out.dart';

part 'favourites_client.g.dart';

@RestApi()
abstract class FavouritesClient {
  factory FavouritesClient(Dio dio, {String? baseUrl}) = _FavouritesClient;

  /// Favourites List.
  ///
  /// The member's favourite foods and saved meals, newest first (at most 200, no cursor).
  ///
  /// [memberId] - Defaults to the primary member.
  @GET('/v1/favourites')
  Future<FavouritesOut> favouritesList({@Query('member_id') String? memberId});

  /// Favourites Add.
  ///
  /// Star a food with an optional default portion (the one a tap logs). 201 for a new.
  /// favourite, 200 with the stored one when the food is already starred. 422 `favourite_limit`.
  /// past 200, `food_retired`, `unit_grams_unknown`, `invalid_product_ref`.
  @POST('/v1/favourites')
  Future<FavouriteOut> favouritesAdd({@Body() required FavouriteIn body});

  /// Favourites Add Meal.
  ///
  /// Save one meal (a slot on a day) under a name you type, exactly as typed. The entries are.
  /// kept as they were (no food is read again). 422 `copy_source_empty`, `copy_too_many` (more.
  /// than 50), `date_in_future`, `favourite_limit`; 404 `meal_slot_not_found`.
  @POST('/v1/favourites/meals')
  Future<FavouriteOut> favouritesAddMeal({
    @Body() required FavouriteMealIn body,
  });

  /// Favourites Delete.
  ///
  /// Remove a favourite. Entries already logged from it stay.
  @DELETE('/v1/favourites/{favourite_id}')
  Future<void> favouritesDelete({
    @Path('favourite_id') required String favouriteId,
  });

  /// Favourites Log.
  ///
  /// Log a favourite MEAL again, from its saved entries, onto today or a day up to 30 days.
  /// back. ``client_id`` is required: a retry returns the same rows with 200 and creates.
  /// nothing. Each entry counts against the daily log limit. A food favourite is logged with.
  /// `meals_log` instead (422 `validation_error` here). 422 `food_retired` if a saved dish was.
  /// retired; a deleted custom food or recipe logs with a null reference. The response is.
  /// redacted with the member's numbers display.
  @POST('/v1/favourites/{favourite_id}/log')
  Future<FavouriteLogOut> favouritesLog({
    @Path('favourite_id') required String favouriteId,
    @Body() required FavouriteLogIn body,
  });
}
