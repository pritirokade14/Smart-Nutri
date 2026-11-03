import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';

/// A failed methodology call; [code] is the API `error.code`, `network`, or
/// null.
class MethodologyFailure implements Exception {
  const MethodologyFailure(this.code);

  final String? code;

  @override
  String toString() => 'MethodologyFailure($code)';
}

/// Wraps `GET /v1/methodology` (F12, public). The body is shown as sent: the
/// thresholds come from the rules engine config and are never written here.
class MethodologyRepository {
  MethodologyRepository(this._client);

  final MethodologyClient _client;

  Future<Methodology> get(String language) async {
    final lang = MethodologyLanguage.fromJson(language);
    try {
      return await _client.methodologyGet(
        language: lang == MethodologyLanguage.$unknown
            ? MethodologyLanguage.en
            : lang,
      );
    } on Object catch (e) {
      throw MethodologyFailure(apiErrorCode(e));
    }
  }
}

final methodologyRepositoryProvider = Provider<MethodologyRepository>(
  (ref) => MethodologyRepository(ref.watch(apiClientProvider).methodology),
);
