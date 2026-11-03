import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';

/// Report reasons, in the order the dialog shows them.
const reportReasons = [
  ReportCreateReason.wrongValues,
  ReportCreateReason.wrongIngredients,
  ReportCreateReason.wrongProduct,
  ReportCreateReason.other,
];

/// The longest note the API accepts.
const reportNoteMaxLength = 500;

/// A failed report; [code] is the API `error.code` (`rate_limited`,
/// `product_not_found`, ...), `network`, or null.
class ReportFailure implements Exception {
  const ReportFailure(this.code);

  final String? code;

  @override
  String toString() => 'ReportFailure($code)';
}

/// Wraps `POST /v1/products/{id}/reports` (F14). A repeat of an open report
/// returns the existing one, so a double tap is harmless.
class ReportsRepository {
  ReportsRepository(this._client);

  final ReportsClient _client;

  /// [note] is trimmed; a blank note is sent as null.
  Future<ReportOut> submit(
    String productId, {
    required ReportCreateReason reason,
    String? note,
  }) async {
    final text = note?.trim();
    try {
      return await _client.reportsCreate(
        productId: productId,
        body: ReportCreate(
          reason: reason,
          note: text == null || text.isEmpty ? null : text,
        ),
      );
    } on Object catch (e) {
      throw ReportFailure(apiErrorCode(e));
    }
  }
}

final reportsRepositoryProvider = Provider<ReportsRepository>(
  (ref) => ReportsRepository(ref.watch(apiClientProvider).reports),
);
