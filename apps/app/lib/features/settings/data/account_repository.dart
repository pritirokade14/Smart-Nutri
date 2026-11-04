import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';

/// A failed account call. [code] is the API `error.code`
/// (`deletion_incomplete`, ...), `network`, or null.
class AccountFailure implements Exception {
  const AccountFailure(this.code);

  final String? code;

  @override
  String toString() => 'AccountFailure($code)';
}

/// Wraps the generated `MeClient` for account deletion (F11).
class AccountRepository {
  AccountRepository(this._me);

  final MeClient _me;

  /// `DELETE /v1/me`: erases the account, its data and the sign-in.
  /// Idempotent. A 503 `deletion_incomplete` means "try again": the steps
  /// already done are skipped.
  Future<void> deleteAccount() async {
    try {
      await _me.meDelete();
    } on Object catch (e) {
      throw AccountFailure(apiErrorCode(e));
    }
  }
}

final accountRepositoryProvider = Provider<AccountRepository>(
  (ref) => AccountRepository(ref.watch(apiClientProvider).me),
);
