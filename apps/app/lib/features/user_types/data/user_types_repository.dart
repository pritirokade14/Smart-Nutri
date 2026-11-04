import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';

/// A failed user-types call. [code] is the API `error.code`
/// (`consent_required`, `follow_up_without_type`, `user_type_not_selected`,
/// ...), `network` when there was no response, or null.
class UserTypesFailure implements Exception {
  const UserTypesFailure(this.code, [this.cause]);

  final String? code;
  final Object? cause;

  /// 403 `consent_required`: the health_data consent is missing.
  bool get isConsentRequired => code == 'consent_required';

  static Future<T> guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on UserTypesFailure {
      rethrow;
    } on Object catch (e) {
      throw UserTypesFailure(apiErrorCode(e), e);
    }
  }

  @override
  String toString() => 'UserTypesFailure($code)';
}

/// Wraps the generated `MeClient` user-types routes. Presentation only: none
/// of these calls changes a member or a verdict, and none is tracked.
class UserTypesRepository {
  UserTypesRepository(this._client);

  final MeClient _client;

  Future<UserTypesOut> get() => UserTypesFailure.guard(_client.meUserTypesGet);

  /// Saves up to 3 [types] (tap order) and their follow-ups; `[]` is "Skip
  /// for now".
  Future<UserTypesOut> save(List<String> types, FollowUps followUps) =>
      UserTypesFailure.guard(
        () => _client.meUserTypesPut(
          body: UserTypesIn(
            types: [for (final t in types) UserTypesInTypes.fromJson(t)],
            followUps: followUps,
          ),
        ),
      );

  /// Switches the focused mode (needs no consent).
  Future<UserTypesOut> setActive(String type) => UserTypesFailure.guard(
    () => _client.meUserTypesSetActive(
      body: ActiveTypeIn(activeType: ActiveTypeInActiveType.fromJson(type)),
    ),
  );
}

final userTypesRepositoryProvider = Provider<UserTypesRepository>(
  (ref) => UserTypesRepository(ref.watch(apiClientProvider).me),
);
