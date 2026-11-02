import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../features/auth/data/auth_repository.dart';
import '../config/app_config.dart';
import '../l10n/app_localizations.dart';
import 'auth_interceptor.dart';

final apiClientProvider = Provider<SmartNutriApiClient>((ref) {
  final config = ref.watch(appConfigProvider);
  final auth = ref.watch(authRepositoryProvider);
  final dio = Dio(BaseOptions(baseUrl: config.apiBaseUrl))
    ..interceptors.add(AuthInterceptor(auth.accessToken, auth.signOut));
  return SmartNutriApiClient(dio);
});

/// Parses the API error envelope (`{"error": {"code", "message_key",
/// "details"}}`) with the generated model, or null if [data] is not one.
ErrorEnvelope? parseErrorEnvelope(Object? data) {
  if (data is! Map) return null;
  try {
    return ErrorEnvelope.fromJson(Map<String, Object?>.from(data));
  } on Object {
    return null; // not the envelope (proxy HTML, empty body, wrong types)
  }
}

/// Extracts `error.code` from the API error envelope, `network` when there was
/// no response at all, or null.
String? apiErrorCode(Object error) {
  if (error is DioException) {
    final envelope = parseErrorEnvelope(error.response?.data);
    if (envelope != null) return envelope.error.code;
    if (error.response == null) return 'network';
  }
  return null;
}

/// Maps an API error to an `error.<code>` string. Unknown codes fall back to
/// `error.internal_error`.
String localizedApiError(AppLocalizations l10n, Object error) {
  return switch (apiErrorCode(error)) {
    'auth_required' => l10n.errorAuthRequired,
    'auth_invalid' => l10n.errorAuthInvalid,
    'unauthorized' => l10n.errorUnauthorized,
    'forbidden' => l10n.errorForbidden,
    'method_not_allowed' => l10n.errorMethodNotAllowed,
    'http_error' => l10n.errorHttpError,
    'not_found' => l10n.errorNotFound,
    'validation_error' => l10n.errorValidationError,
    'rate_limited' => l10n.errorRateLimited,
    'rate_limited_scans' => l10n.errorRateLimitedScans,
    'rate_limited_voice' => l10n.errorRateLimitedVoice,
    'network' => l10n.errorNetwork,
    _ => l10n.errorInternalError,
  };
}
