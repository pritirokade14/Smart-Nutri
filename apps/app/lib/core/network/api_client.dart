import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../features/auth/data/auth_repository.dart';
import '../../features/consent/data/consent_required_interceptor.dart';
import '../../features/consent/domain/consent_error.dart';
import '../../features/consent/presentation/consent_providers.dart';
import '../config/app_config.dart';
import '../l10n/app_localizations.dart';
import 'auth_interceptor.dart';
import 'date_only_interceptor.dart';

final apiClientProvider = Provider<SmartNutriApiClient>((ref) {
  final config = ref.watch(appConfigProvider);
  final auth = ref.watch(authRepositoryProvider);
  // Rebuilt on every sign-in and sign-out, which drops every account-scoped
  // provider's cached data (members, consents, results) with it.
  ref.watch(signedInProvider);
  final dio = Dio(BaseOptions(baseUrl: config.apiBaseUrl))
    ..interceptors.add(DateOnlyInterceptor())
    ..interceptors.add(AuthInterceptor(auth.accessToken, auth.signOut))
    ..interceptors.add(
      ConsentRequiredInterceptor(
        (purposes) =>
            ref.read(consentRequestProvider.notifier).request(purposes),
      ),
    );
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
    isRouteConsentError(error)
    ? l10n.consentRequiredToContinue
    : localizedErrorCode(l10n, apiErrorCode(error));

/// For screens whose calls sit behind the route consent gate (scans, product
/// create, voice): `consent_required` there means "agree to continue", and
/// the consent screen is already open. Other codes as [localizedErrorCode].
String localizedGatedErrorCode(AppLocalizations l10n, String? code) =>
    code == 'consent_required'
    ? l10n.consentRequiredToContinue
    : localizedErrorCode(l10n, code);

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
    'image_quality_low' => l10n.errorImageQualityLow,
    'goal_not_allowed_minor' => l10n.errorGoalNotAllowedMinor,
    'goal_not_allowed_underweight' => l10n.errorGoalNotAllowedUnderweight,
    'target_weight_too_low' => l10n.errorTargetWeightTooLow,
    'rate_not_allowed' => l10n.errorRateNotAllowed,
    'fat_pct_out_of_range' => l10n.errorFatPctOutOfRange,
    'adaptive_not_enabled' => l10n.errorAdaptiveNotEnabled,
    'body_fat_out_of_range' => l10n.errorBodyFatOutOfRange,
    'diary_member_not_enabled' => l10n.errorDiaryMemberNotEnabled,
    'date_in_future' => l10n.errorDateInFuture,
    'goal_settings_not_found' => l10n.errorGoalSettingsNotFound,
    'quick_add_energy_required' => l10n.errorQuickAddEnergyRequired,
    'copy_source_empty' => l10n.errorCopySourceEmpty,
    'copy_too_many' => l10n.errorCopyTooMany,
    'date_too_old' => l10n.errorDateTooOld,
    'meal_slot_not_found' => l10n.errorMealSlotNotFound,
    'meal_slot_archived' => l10n.errorMealSlotArchived,
    'meal_slot_limit_reached' => l10n.errorMealSlotLimitReached,
    'meal_slot_last_active' => l10n.errorMealSlotLastActive,
    'meal_slot_label_duplicate' => l10n.errorMealSlotLabelDuplicate,
    'timezone_invalid' => l10n.errorTimezoneInvalid,
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
    'unit_grams_unknown' => l10n.errorUnitGramsUnknown,
    'unit_not_supported' => l10n.errorUnitNotSupported,
    'quantity_out_of_range' => l10n.errorQuantityOutOfRange,
    'food_not_found' => l10n.errorFoodNotFound,
    'custom_food_not_found' => l10n.errorCustomFoodNotFound,
    'custom_food_nutrients_empty' => l10n.errorCustomFoodNutrientsEmpty,
    'barcode_already_used' => l10n.errorBarcodeAlreadyUsed,
    'recipe_not_found' => l10n.errorRecipeNotFound,
    'recipe_ingredient_limit' => l10n.errorRecipeIngredientLimit,
    'recipe_weight_invalid' => l10n.errorRecipeWeightInvalid,
    'food_retired' => l10n.errorFoodRetired,
    'favourite_not_found' => l10n.errorFavouriteNotFound,
    'favourite_limit' => l10n.errorFavouriteLimit,
    'weight_out_of_range' => l10n.errorWeightOutOfRange,
    'weight_needs_confirm' => l10n.errorWeightNeedsConfirm,
    'weight_not_found' => l10n.errorWeightNotFound,
    'date_range_too_long' => l10n.errorDateRangeTooLong,
    'eaten_at_out_of_range' => l10n.errorEatenAtOutOfRange,
    'meal_not_found' => l10n.errorMealNotFound,
    'audio_too_long' => l10n.errorAudioTooLong,
    'audio_too_large' => l10n.errorAudioTooLarge,
    'audio_unsupported' => l10n.errorAudioUnsupported,
    'voice_not_understood' => l10n.errorVoiceNotUnderstood,
    'ai_unavailable' => l10n.errorAiUnavailable,
    'deletion_incomplete' => l10n.errorDeletionIncomplete,
    'phone_otp_disabled' => l10n.errorPhoneOtpDisabled,
    'payload_too_large' => l10n.errorPayloadTooLarge,
    'search_query_too_short' => l10n.errorSearchQueryTooShort,
    'user_type_not_selected' => l10n.errorUserTypeNotSelected,
    'follow_up_without_type' => l10n.errorFollowUpWithoutType,
    'user_types_not_found' => l10n.errorUserTypesNotFound,
    'internal_error' => l10n.errorInternalError,
    _ => l10n.errorInternalError,
  };
}
