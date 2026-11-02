import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/analysis/data/analysis_repository.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';

class _FakeAnalyze implements AnalyzeClient {
  _FakeAnalyze(this.respond);
  final Future<AnalyzeOut> Function() respond;
  final requests = <AnalyzeRequest>[];

  @override
  Future<AnalyzeOut> analyzeCreate({required AnalyzeRequest body}) {
    requests.add(body);
    return respond();
  }
}

DioException _apiError(String code, int status) {
  final ro = RequestOptions(path: '/v1/analyze');
  return DioException(
    requestOptions: ro,
    response: Response<Object?>(
      requestOptions: ro,
      statusCode: status,
      data: {
        'error': {
          'code': code,
          'message_key': 'error.$code',
          'details': <String, Object?>{},
        },
      },
    ),
  );
}

void main() {
  test(
    'sends the barcode and language, returns the API body unchanged',
    () async {
      final body = analyzeFixture('sf_biscuit');
      final fake = _FakeAnalyze(() async => body);
      final repo = AnalysisRepository(fake);
      final out = await repo.analyzeBarcode('8901063201089', language: 'hi');
      expect(identical(out, body), isTrue);
      expect(fake.requests.single.barcode, '8901063201089');
      expect(fake.requests.single.language, AnalyzeRequestLanguage.hi);
      expect(fake.requests.single.productId, isNull);
      expect(fake.requests.single.memberIds, isNull);
    },
  );

  test('unsupported language falls back to en', () async {
    final fake = _FakeAnalyze(() async => analyzeFixture('water'));
    await AnalysisRepository(fake).analyzeBarcode('12345678', language: 'fr');
    expect(fake.requests.single.language, AnalyzeRequestLanguage.en);
  });

  Future<Object?> failureFor(Object error) async {
    final repo = AnalysisRepository(_FakeAnalyze(() => Future.error(error)));
    try {
      await repo.analyzeBarcode('12345678');
    } on Object catch (e) {
      return e;
    }
    return null;
  }

  test('maps API error codes to typed failures', () async {
    expect(
      await failureFor(_apiError('product_not_found', 404)),
      isA<AnalysisNotFound>(),
    );
    expect(
      await failureFor(_apiError('off_unavailable', 503)),
      isA<AnalysisUnavailable>(),
    );
    expect(
      await failureFor(_apiError('invalid_barcode', 422)),
      isA<AnalysisInvalidBarcode>(),
    );
    final net = DioException(
      requestOptions: RequestOptions(path: '/v1/analyze'),
      type: DioExceptionType.connectionError,
    );
    expect(await failureFor(net), isA<AnalysisNetworkFailure>());
    final other = await failureFor(_apiError('rate_limited', 429));
    expect(other, isA<AnalysisApiFailure>());
    expect((other! as AnalysisApiFailure).cause, isA<DioException>());
  });
}
