import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../auth/data/auth_repository.dart';
import '../../members/presentation/members_providers.dart';

/// Whether the signed-in account has agreed to the current terms.
enum TermsStatus {
  /// Signed out, or the consent states are not loaded (or failed to load).
  /// The app does not block; a gated call's 403 opens the consent screen.
  unknown,
  accepted,

  /// Never agreed, withdrawn, or agreed to an older version
  /// (`needs_update`). The router shows the terms screen.
  required,
}

final termsStatusProvider = Provider<TermsStatus>((ref) {
  if (!ref.watch(signedInProvider)) return TermsStatus.unknown;
  final states = ref.watch(consentStateProvider).value;
  if (states == null) return TermsStatus.unknown;
  return consentGranted(states, consentPurposeTerms) == true
      ? TermsStatus.accepted
      : TermsStatus.required;
});

/// Purposes other than terms whose consent text changed since the user
/// agreed (`needs_update`): the user is asked to agree again.
List<String> consentsNeedingUpdate(List<ConsentState>? states) => [
  for (final s in states ?? const <ConsentState>[])
    if (s.needsUpdate && s.purpose != consentPurposeTerms) s.purpose,
];

/// The purposes of the latest 403 `consent_required`, until the router has
/// handled it.
class ConsentRequestNotifier extends Notifier<List<String>?> {
  @override
  List<String>? build() => null;

  void request(List<String> purposes) => state = [...purposes];

  void clear() => state = null;
}

final consentRequestProvider =
    NotifierProvider<ConsentRequestNotifier, List<String>?>(
      ConsentRequestNotifier.new,
    );
