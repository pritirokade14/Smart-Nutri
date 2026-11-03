import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../data/members_repository.dart';
import '../domain/member.dart';

/// The account's members, primary first, as the API lists them.
class MembersNotifier extends AsyncNotifier<List<MemberOut>> {
  MembersRepository get _repo => ref.read(membersRepositoryProvider);

  @override
  Future<List<MemberOut>> build() =>
      ref.watch(membersRepositoryProvider).list();

  List<MemberOut> get _current => state.value ?? const [];

  Future<MemberOut> create(MemberDraft draft) async {
    final member = await _repo.create(draft);
    state = AsyncData([..._current, member]);
    return member;
  }

  /// Named `updateMember`: `update` is taken by `AsyncNotifier.update`.
  Future<MemberOut> updateMember(String id, MemberDraft draft) async {
    final member = await _repo.update(id, draft);
    state = AsyncData([for (final m in _current) m.id == id ? member : m]);
    return member;
  }

  Future<void> remove(String id) async {
    await _repo.remove(id);
    state = AsyncData([
      for (final m in _current)
        if (m.id != id) m,
    ]);
  }
}

final membersProvider = AsyncNotifierProvider<MembersNotifier, List<MemberOut>>(
  MembersNotifier.new,
  // The screen shows the failure; the user retries explicitly.
  retry: (_, _) => null,
);

/// Consent purposes. Terms is asked for after the first sign-in (the terms
/// screen) and again whenever its version changes.
const consentPurposeTerms = 'terms';
const consentPurposeHealthData = 'health_data';
const consentPurposeAiProcessing = 'ai_processing';

/// The account's consent states (`GET /v1/consents`).
class ConsentStateNotifier extends AsyncNotifier<List<ConsentState>> {
  ConsentsRepository get _repo => ref.read(consentsRepositoryProvider);

  @override
  Future<List<ConsentState>> build() =>
      ref.watch(consentsRepositoryProvider).list();

  /// Grants or withdraws each purpose in [changes], in order, at the
  /// `current_version` the API listed. On `consent_version_mismatch` the
  /// states are reloaded and the failure is rethrown.
  Future<void> record(Map<String, bool> changes) async {
    var states = state.value ?? await future;
    try {
      for (final MapEntry(key: purpose, value: granted) in changes.entries) {
        final current = states.firstWhere((s) => s.purpose == purpose);
        states = await _repo.record(
          purpose,
          granted: granted,
          version: current.currentVersion,
        );
        state = AsyncData(states);
      }
    } on MembersFailure catch (e) {
      if (e.code == 'consent_version_mismatch') ref.invalidateSelf();
      rethrow;
    }
  }
}

final consentStateProvider =
    AsyncNotifierProvider<ConsentStateNotifier, List<ConsentState>>(
      ConsentStateNotifier.new,
      retry: (_, _) => null,
    );

/// Whether [purpose] is granted at its current version, or null while the
/// states are not loaded.
bool? consentGranted(List<ConsentState>? states, String purpose) {
  if (states == null) return null;
  for (final s in states) {
    if (s.purpose == purpose) return s.granted;
  }
  return false;
}
