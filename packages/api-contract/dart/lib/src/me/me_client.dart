// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/active_type_in.dart';
import '../models/me_out.dart';
import '../models/timezone_in.dart';
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
  /// Order: storage objects (label photos; voice audio is never stored), then every.
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

  /// Me Timezone Put.
  ///
  /// Set the account's time zone (an IANA name such as `Asia/Kolkata`). Needs only sign-in:.
  /// it is not health data. Changing it never moves an entry already logged. 422.
  /// `timezone_invalid` for an unknown name.
  @PUT('/v1/me/timezone')
  Future<MeOut> meTimezonePut({@Body() required TimezoneIn body});

  /// Me User Types Get.
  ///
  /// The account's user types. Without an answer yet: `answered=false`, `types=[]` and the.
  /// `eat_better` mode (clients then show the picker).
  ///
  /// `prefill` lists suggested changes to the account holder's own member, recomputed on every.
  /// call (empty once confirmed). Nothing is applied: the client sends only the confirmed ones.
  /// to `PATCH /v1/members/{member_id}`, which keeps its health_data check.
  @GET('/v1/me/user-types')
  Future<UserTypesOut> meUserTypesGet();

  /// Me User Types Put.
  ///
  /// Save up to 3 types (tap order) and their follow-ups; `types=[]` is "Skip for now".
  ///
  /// Presentation only: it never changes a member or a verdict. 422 `validation_error` for more.
  /// than 3 types or duplicates; 422 `follow_up_without_type` for a follow-up whose type is not.
  /// chosen. The response's `prefill` only suggests member changes; none is applied.
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
