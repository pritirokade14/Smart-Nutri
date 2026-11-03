import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../domain/member.dart';

/// A failed members or consents call. [code] is the API `error.code`
/// (`consent_required`, `member_limit`, `primary_member`, ...), `network`
/// when there was no response, or null; screens map it with
/// `localizedErrorCode`.
class MembersFailure implements Exception {
  const MembersFailure(this.code, [this.cause]);

  final String? code;
  final Object? cause;

  /// 403 `consent_required`: open the health_data consent sheet, then retry.
  bool get isConsentRequired => code == 'consent_required';

  static Future<T> guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on Object catch (e) {
      throw MembersFailure(apiErrorCode(e), e);
    }
  }

  @override
  String toString() => 'MembersFailure($code)';
}

/// Wraps the generated `MembersClient`. Saves always send the whole form
/// ([MemberDraft]), never a partial patch.
class MembersRepository {
  MembersRepository(this._client);

  final MembersClient _client;

  Future<List<MemberOut>> list() => MembersFailure.guard(_client.membersList);

  Future<MemberOut> create(MemberDraft draft) => MembersFailure.guard(
    () => _client.membersCreate(body: draft.toMemberIn()),
  );

  Future<MemberOut> update(String id, MemberDraft draft) =>
      MembersFailure.guard(
        () => _client.membersUpdate(memberId: id, body: draft.toMemberPatch()),
      );

  Future<void> remove(String id) =>
      MembersFailure.guard(() => _client.membersDelete(memberId: id));
}

/// Wraps the generated `ConsentsClient`.
class ConsentsRepository {
  ConsentsRepository(this._client);

  final ConsentsClient _client;

  Future<List<ConsentState>> list() =>
      MembersFailure.guard(_client.consentsList);

  /// Records a grant or a withdrawal at [version] (the `current_version`
  /// from [list]). Returns the new states.
  Future<List<ConsentState>> record(
    String purpose, {
    required bool granted,
    required String version,
  }) => MembersFailure.guard(
    () => _client.consentsRecord(
      body: ConsentIn(
        purpose: ConsentInPurpose.fromJson(purpose),
        granted: granted,
        version: version,
      ),
    ),
  );
}

final membersRepositoryProvider = Provider<MembersRepository>(
  (ref) => MembersRepository(ref.watch(apiClientProvider).members),
);

final consentsRepositoryProvider = Provider<ConsentsRepository>(
  (ref) => ConsentsRepository(ref.watch(apiClientProvider).consents),
);
