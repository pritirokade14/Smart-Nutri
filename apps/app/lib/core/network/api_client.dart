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
String localizedApiError(AppLocalizations l10n, Object error) =>
    localizedErrorCode(l10n, apiErrorCode(error));

/// The `error.<code>` string for an API error code (or `network`). Unknown
/// codes fall back to `error.internal_error`.
String localizedErrorCode(AppLocalizations l10n, String? code) {
  return switch (code) {
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
    'image_too_large' => l10n.errorImageTooLarge,
    'unsupported_image' => l10n.errorUnsupportedImage,
    'scan_image_not_found' => l10n.errorScanImageNotFound,
    'scan_not_found' => l10n.errorScanNotFound,
    'extraction_failed' => l10n.errorExtractionFailed,
    'extraction_unavailable' => l10n.errorExtractionUnavailable,
    'storage_unavailable' => l10n.errorStorageUnavailable,
    'implausible_value' => l10n.errorImplausibleValue,
    'product_exists' => l10n.errorProductExists,
    'product_not_found' => l10n.errorProductNotFound,
    'invalid_product_ref' => l10n.errorInvalidProductRef,
    'invalid_barcode' => l10n.errorInvalidBarcode,
    'off_unavailable' => l10n.errorOffUnavailable,
    'member_not_found' => l10n.errorMemberNotFound,
    'member_limit' => l10n.errorMemberLimit,
    'primary_member' => l10n.errorPrimaryMember,
    'consent_required' => l10n.errorConsentRequired,
    'consent_version_mismatch' => l10n.errorConsentVersionMismatch,
    'portion_required' => l10n.errorPortionRequired,
    'serving_size_unknown' => l10n.errorServingSizeUnknown,
    'eaten_at_out_of_range' => l10n.errorEatenAtOutOfRange,
    'meal_not_found' => l10n.errorMealNotFound,
    'internal_error' => l10n.errorInternalError,
    _ => l10n.errorInternalError,
  };
}
