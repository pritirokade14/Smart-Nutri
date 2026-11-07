import 'package:dio/dio.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';

/// A failed targets call. [code] is the API `error.code`
/// (`consent_required`, `goal_not_allowed_underweight`, ...), `network` when
/// there was no response, or null; [details] is the envelope's `details`
/// (`min`, `max`, `min_kg`, ...). Screens map the code with
/// `localizedErrorCode`.
class TargetsFailure implements Exception {
  const TargetsFailure(this.code, [this.details = const {}, this.cause]);

  final String? code;
  final Map<String, Object?> details;
  final Object? cause;

  /// 403 `consent_required`: open the health-data consent sheet, then retry.
  bool get isConsentRequired => code == 'consent_required';

  /// 404: no settings exist yet (the display call needs a stored row).
  bool get isNotFound {
    final c = cause;
    return (c is DioException && c.response?.statusCode == 404) ||
        (code?.endsWith('not_found') ?? false);
  }

  static Future<T> guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on Object catch (e) {
      var details = const <String, Object?>{};
      if (e is DioException) {
        final raw = parseErrorEnvelope(e.response?.data)?.error.details;
        if (raw is Map) details = Map<String, Object?>.from(raw);
      }
      throw TargetsFailure(apiErrorCode(e), details, e);
    }
  }

  @override
  String toString() => 'TargetsFailure($code)';
}

/// Wraps the generated `TargetsClient`. The app never computes a target: it
/// sends the user's answers and shows what the API returns.
class TargetsRepository {
  TargetsRepository(this._client);

  final TargetsClient _client;

  /// Today's targets for [memberId] (null: the account holder).
  Future<TargetsOut> get({String? memberId}) =>
      TargetsFailure.guard(() => _client.targetsGet(memberId: memberId));

  /// The saved settings, or null when none exist.
  Future<GoalSettingsOut?> settings({String? memberId}) => TargetsFailure.guard(
    () => _client.targetsSettingsGet(memberId: memberId),
  );

  /// Targets for unsaved answers; nothing is stored.
  Future<TargetsOut> preview(TargetsPreviewIn body) =>
      TargetsFailure.guard(() => _client.targetsPreview(body: body));

  /// Saves the settings; the answer is today's targets.
  Future<TargetsOut> save(GoalSettingsIn body) =>
      TargetsFailure.guard(() => _client.targetsSettingsPut(body: body));

  /// The eye toggle and the Numbers setting. Terms-only on the API.
  Future<DisplayOut> setDisplay(DisplayIn body) =>
      TargetsFailure.guard(() => _client.targetsDisplayPut(body: body));

  /// Deletes the settings (the food log stays).
  Future<void> reset({String? memberId}) => TargetsFailure.guard(
    () => _client.targetsSettingsDelete(memberId: memberId),
  );
}
