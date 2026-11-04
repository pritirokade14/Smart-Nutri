import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../auth/data/auth_repository.dart';
import '../data/user_types_repository.dart';
import '../domain/user_types.dart';

/// The account's user types (`GET /v1/me/user-types`). Presentation only:
/// they pick the layout and never reach a verdict. No analytics anywhere.
class UserTypesNotifier extends AsyncNotifier<UserTypesOut> {
  UserTypesRepository get _repo => ref.read(userTypesRepositoryProvider);

  @override
  Future<UserTypesOut> build() {
    // Signed out: nothing to load (the redirect sends the user to sign in).
    if (!ref.watch(signedInProvider)) {
      throw const UserTypesFailure('auth_required');
    }
    return ref.watch(userTypesRepositoryProvider).get();
  }

  /// Saves [types] and [followUps]; the response carries the pre-fill
  /// suggestions (nothing is applied).
  Future<UserTypesOut> save(List<String> types, FollowUps followUps) async {
    final out = await _repo.save(types, followUps);
    state = AsyncData(out);
    return out;
  }

  /// Switches the mode at once and rolls back if the API refuses.
  Future<void> setActive(String type) async {
    final before = state.value;
    if (before == null) return;
    state = AsyncData(_withActive(before, type));
    try {
      state = AsyncData(await _repo.setActive(type));
    } on Object {
      state = AsyncData(before);
      rethrow;
    }
  }

  static UserTypesOut _withActive(UserTypesOut o, String type) => UserTypesOut(
    activeType: UserTypesOutActiveType.fromJson(type),
    answered: o.answered,
    answeredAt: o.answeredAt,
    followUps: o.followUps,
    prefill: o.prefill,
    types: o.types,
  );
}

final userTypesProvider =
    AsyncNotifierProvider<UserTypesNotifier, UserTypesOut>(
      UserTypesNotifier.new,
      // The app goes on without the answer; no automatic retry.
      retry: (_, _) => null,
    );

/// Whether the picker is still to be answered. [UserTypesStatus.unknown]
/// while loading or after an error: the app goes on.
final userTypesStatusProvider = Provider<UserTypesStatus>((ref) {
  if (!ref.watch(signedInProvider)) return UserTypesStatus.unknown;
  final value = ref.watch(userTypesProvider).value;
  if (value == null) return UserTypesStatus.unknown;
  return value.answered ? UserTypesStatus.answered : UserTypesStatus.unanswered;
});

/// The picker and follow-up answers while the user goes through them.
class UserTypesDraft {
  const UserTypesDraft({
    this.types = const [],
    this.answers = const FollowUpAnswers(),
    this.consentDeclined = false,
  });

  /// Tap order, at most [maxUserTypes].
  final List<String> types;
  final FollowUpAnswers answers;

  /// The user declined health_data: the health tiles were dropped.
  final bool consentDeclined;

  UserTypesDraft copyWith({
    List<String>? types,
    FollowUpAnswers? answers,
    bool? consentDeclined,
  }) => UserTypesDraft(
    types: types ?? this.types,
    answers: answers ?? this.answers,
    consentDeclined: consentDeclined ?? this.consentDeclined,
  );

  bool get needsHealthConsent => typesNeedHealthConsent(types, answers);
}

class UserTypesDraftNotifier extends Notifier<UserTypesDraft> {
  @override
  UserTypesDraft build() => const UserTypesDraft();

  /// A fresh draft, or the stored answers when editing from Profile.
  void start(UserTypesOut? current) {
    state = current == null
        ? const UserTypesDraft()
        : UserTypesDraft(
            types: chosenTypes(current).take(maxUserTypes).toList(),
            answers: FollowUpAnswers.fromApi(current.followUps),
          );
  }

  /// Selects or deselects [type]. Returns false (nothing changes) when a
  /// fourth type is tapped.
  bool toggle(String type) {
    final types = state.types;
    if (types.contains(type)) {
      state = state.copyWith(types: [...types.where((t) => t != type)]);
      return true;
    }
    if (types.length >= maxUserTypes) return false;
    state = state.copyWith(types: [...types, type]);
    return true;
  }

  void setAnswers(FollowUpAnswers answers) =>
      state = state.copyWith(answers: answers);

  /// The user declined health_data: drop the health tiles and the health
  /// follow-ups; the rest is kept.
  void dropHealth() => state = UserTypesDraft(
    types: [...state.types.where((t) => !healthRevealingTypes.contains(t))],
    answers: state.answers.withoutHealth(),
    consentDeclined: true,
  );

  /// `PUT /v1/me/user-types` with the draft (only the chosen types'
  /// follow-ups). Never touches a member.
  Future<UserTypesOut> submit() => ref
      .read(userTypesProvider.notifier)
      .save(state.types, state.answers.toApi(state.types));

  /// "Skip for now": `types = []`.
  Future<UserTypesOut> skip() =>
      ref.read(userTypesProvider.notifier).save(const [], const FollowUps());
}

final userTypesDraftProvider =
    NotifierProvider<UserTypesDraftNotifier, UserTypesDraft>(
      UserTypesDraftNotifier.new,
    );

/// Whether the save left anything to review (`/welcome/review`).
bool hasPrefillToReview(UserTypesOut out) {
  final p = out.prefill;
  if (p == null) return false;
  return p.changes.isNotEmpty || (p.goalChoice?.isNotEmpty ?? false);
}
