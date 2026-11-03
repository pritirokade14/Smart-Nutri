import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';

/// The consent purposes the app knows, in the API's order.
const knownConsentPurposes = ['terms', 'health_data', 'ai_processing'];

/// The purposes a 403 `consent_required` names, or null when [error] is not
/// one.
///
/// The route gate (analyze, scans, meals, product create, voice) sends
/// `details.purposes`. The members gate for health fields sends
/// `details.purpose` (singular). Both are accepted. Unknown purposes are
/// dropped.
List<String>? consentPurposesOf(Object? error) {
  if (error is! DioException) return null;
  if (error.response?.statusCode != 403) return null;
  final envelope = parseErrorEnvelope(error.response?.data);
  if (envelope == null || envelope.error.code != 'consent_required') {
    return null;
  }
  final details = envelope.error.details;
  final raw = <Object?>[
    if (details is Map) ...[
      if (details['purposes'] case final List<Object?> list) ...list,
      if (details['purpose'] case final String one) one,
    ],
  ];
  return [
    for (final p in knownConsentPurposes)
      if (raw.contains(p)) p,
  ];
}

/// True when [error] came from the route gate (`details.purposes`), which the
/// app answers with the consent screen, rather than the members gate.
bool isRouteConsentError(Object? error) {
  if (consentPurposesOf(error) == null) return false;
  final details = parseErrorEnvelope(
    (error! as DioException).response?.data,
  )?.error.details;
  return details is Map && details['purposes'] is List;
}
