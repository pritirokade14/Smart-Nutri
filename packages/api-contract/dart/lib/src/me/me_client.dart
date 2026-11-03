// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/active_type_in.dart';
import '../models/me_out.dart';
import '../models/user_types_in.dart';
import '../models/user_types_out.dart';

part 'me_client.g.dart';

@RestApi()
abstract class MeClient {
  factory MeClient(Dio dio, {String? baseUrl}) = _MeClient;

  /// Me Delete.
  ///
  /// Permanently erase the caller's account (DPDP erasure, F11).
  ///
  /// Order: storage objects (label photos, and voice answers in their own bucket), then every.
  /// account-owned row in one transaction (contributed products stay with no owner), then the.
  /// Supabase auth user. The row erasure also writes a tombstone (ruling D1/B1): until it is.
  /// purged (7 days), the caller's still-valid token gets 401 `auth_invalid` everywhere else.
  /// Idempotent: calling it again returns 204 (at most 5 calls a day, then 429). On 503.
  /// `deletion_incomplete`, retry: completed steps are skipped. Depends on `current_account`.
  /// (not `current_account_row`) so a repeat call never re-creates the account row.
  @DELETE('/v1/me')
  Future<void> meDelete();

  /// Me Get
  @GET('/v1/me')
  Future<MeOut> meGet();

  /// Me User Types Get.
  ///
  /// The account's user types. Without an answer yet: `answered=false`, `types=[]` and the.
  /// `eat_better` mode (clients then show the picker).
  @GET('/v1/me/user-types')
  Future<UserTypesOut> meUserTypesGet();

  /// Me User Types Put.
  ///
  /// Save up to 3 types (tap order) and their follow-ups; `types=[]` is "Skip for now".
  ///
  /// Presentation only: it never changes a member or a verdict. 422 `validation_error` for more.
  /// than 3 types or duplicates; 422 `follow_up_without_type` for a follow-up whose type is not.
  /// chosen.
  @PUT('/v1/me/user-types')
  Future<UserTypesOut> meUserTypesPut({@Body() required UserTypesIn body});

  /// Me User Types Set Active.
  ///
  /// Switch the focused mode. Needs no consent. 404 `user_types_not_found` before the first.
  /// PUT; 422 `user_type_not_selected` unless it is one of the chosen types (or `eat_better`.
  /// after "Skip for now").
  @PATCH('/v1/me/user-types/active')
  Future<UserTypesOut> meUserTypesSetActive({
    @Body() required ActiveTypeIn body,
  });
}
