import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';

/// Typed failures of [AnalysisRepository.analyzeBarcode].
sealed class AnalysisFailure implements Exception {
  const AnalysisFailure();
}

/// `product_not_found` (404): neither our catalogue nor Open Food Facts has it.
class AnalysisNotFound extends AnalysisFailure {
  const AnalysisNotFound();
}

/// `off_unavailable` (503): Open Food Facts could not be reached.
class AnalysisUnavailable extends AnalysisFailure {
  const AnalysisUnavailable();
}

/// `invalid_barcode` (422).
class AnalysisInvalidBarcode extends AnalysisFailure {
  const AnalysisInvalidBarcode();
}

/// No response at all (offline, DNS, timeout).
class AnalysisNetworkFailure extends AnalysisFailure {
  const AnalysisNetworkFailure();
}

/// Any other API error; [cause] is passed to `localizedApiError`.
class AnalysisApiFailure extends AnalysisFailure {
  const AnalysisApiFailure(this.cause);
  final Object cause;
}

/// Wraps `POST /v1/analyze`. Returns the API body unchanged: verdicts, their
/// order and their reasons come only from the rules engine.
class AnalysisRepository {
  AnalysisRepository(this._client);

  final AnalyzeClient _client;

  Future<AnalyzeOut> analyzeBarcode(
    String barcode, {
    String language = 'en',
  }) async {
    final lang = AnalyzeRequestLanguage.fromJson(language);
    try {
      return await _client.analyzeCreate(
        body: AnalyzeRequest(
          barcode: barcode,
          language: lang == AnalyzeRequestLanguage.$unknown
              ? AnalyzeRequestLanguage.en
              : lang,
        ),
      );
    } on Object catch (e) {
      throw switch (apiErrorCode(e)) {
        'product_not_found' => const AnalysisNotFound(),
        'off_unavailable' => const AnalysisUnavailable(),
        'invalid_barcode' => const AnalysisInvalidBarcode(),
        'network' => const AnalysisNetworkFailure(),
        _ => AnalysisApiFailure(e),
      };
    }
  }
}

final analysisRepositoryProvider = Provider<AnalysisRepository>(
  (ref) => AnalysisRepository(ref.watch(apiClientProvider).analyze),
);
