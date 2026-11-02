import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations_en.dart';
import 'package:smartnutri_ai/core/network/api_client.dart';

DioException _withBody(Object? data, {int status = 429}) {
  final ro = RequestOptions(path: '/v1/me');
  return DioException(
    requestOptions: ro,
    response: Response<Object?>(
      requestOptions: ro,
      statusCode: status,
      data: data,
    ),
  );
}

void main() {
  test('parses the error envelope with the generated model', () {
    final envelope = parseErrorEnvelope({
      'error': {
        'code': 'rate_limited_scans',
        'message_key': 'error.rate_limited_scans',
        'details': {'retry_after': 30},
      },
    });
    expect(envelope?.error.code, 'rate_limited_scans');
    expect(envelope?.error.messageKey, 'error.rate_limited_scans');
    expect(envelope?.error.details, {'retry_after': 30});
  });

  test('non-envelope bodies are not parsed', () {
    expect(parseErrorEnvelope(null), isNull);
    expect(parseErrorEnvelope('<html>bad gateway</html>'), isNull);
    expect(parseErrorEnvelope({'detail': []}), isNull);
    expect(
      parseErrorEnvelope({
        'error': {'code': 5},
      }),
      isNull,
    );
  });

  test('apiErrorCode reads the envelope, or network without a response', () {
    final body = {
      'error': {
        'code': 'auth_invalid',
        'message_key': 'error.auth_invalid',
        'details': <String, Object?>{},
      },
    };
    expect(apiErrorCode(_withBody(body, status: 401)), 'auth_invalid');
    expect(apiErrorCode(_withBody('oops', status: 502)), isNull);
    expect(
      apiErrorCode(DioException(requestOptions: RequestOptions(path: '/'))),
      'network',
    );
  });

  test('localizedApiError maps generic HTTP codes and falls back', () {
    final l10n = AppLocalizationsEn();
    Object err(String code) => _withBody({
      'error': {'code': code, 'message_key': 'error.$code', 'details': {}},
    });
    expect(
      localizedApiError(l10n, err('method_not_allowed')),
      l10n.errorMethodNotAllowed,
    );
    expect(localizedApiError(l10n, err('forbidden')), l10n.errorForbidden);
    expect(
      localizedApiError(l10n, err('something_new')),
      l10n.errorInternalError,
    );
  });
}
