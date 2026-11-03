// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/me_out.dart';

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
}
