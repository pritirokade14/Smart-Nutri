import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../members/presentation/consent_sheet.dart';
import '../../members/presentation/members_providers.dart';
import '../data/user_types_repository.dart';
import 'user_types_providers.dart';

/// `?edit=1` (opened from Profile) on the onboarding routes.
String editQuery(bool edit) => edit ? '?edit=1' : '';

/// Where the flow ends: Profile when editing, else Home.
String flowEnd(bool edit) => edit ? '/profile' : '/home';

void _snack(BuildContext context, String text) => ScaffoldMessenger.maybeOf(
  context,
)?.showSnackBar(SnackBar(content: Text(text)));

/// Opens the health-data consent sheet in context. Granted: true. Declined:
/// the health tiles and follow-ups are dropped with the note, and the result
/// says whether anything is left to save.
Future<bool> askHealthConsent(BuildContext context, WidgetRef ref) async {
  if (await showConsentSheet(context)) return true;
  ref.read(userTypesDraftProvider.notifier).dropHealth();
  if (context.mounted) {
    _snack(context, AppLocalizations.of(context).userTypesConsentNeeded);
  }
  return ref.read(userTypesDraftProvider).types.isNotEmpty;
}

/// Whether health_data is known to be missing for this draft.
bool consentMissingFor(WidgetRef ref) =>
    ref.read(userTypesDraftProvider).needsHealthConsent &&
    consentGranted(
          ref.read(consentStateProvider).value,
          consentPurposeHealthData,
        ) ==
        false;

/// Saves the draft (consent first when needed; a 403 asks once more), then
/// opens the review when the API suggests profile changes, else ends the
/// flow. Returns false when nothing was saved.
Future<bool> saveUserTypes(
  BuildContext context,
  WidgetRef ref, {
  required bool edit,
}) async {
  if (consentMissingFor(ref) && !await askHealthConsent(context, ref)) {
    return false;
  }
  var asked = false;
  while (true) {
    if (!context.mounted) return false;
    try {
      final out = await ref.read(userTypesDraftProvider.notifier).submit();
      if (!context.mounted) return true;
      context.go(
        hasPrefillToReview(out)
            ? '/welcome/review${editQuery(edit)}'
            : flowEnd(edit),
      );
      return true;
    } on UserTypesFailure catch (e) {
      if (!context.mounted) return false;
      if (e.isConsentRequired && !asked) {
        asked = true;
        ref.invalidate(consentStateProvider);
        if (!await askHealthConsent(context, ref)) return false;
        continue;
      }
      _snack(context, localizedErrorCode(AppLocalizations.of(context), e.code));
      return false;
    }
  }
}

/// "Skip for now": stores no types and lands on Home.
Future<void> skipUserTypes(BuildContext context, WidgetRef ref) async {
  try {
    await ref.read(userTypesDraftProvider.notifier).skip();
    if (context.mounted) context.go('/home');
  } on UserTypesFailure catch (e) {
    if (context.mounted) {
      _snack(context, localizedErrorCode(AppLocalizations.of(context), e.code));
    }
  }
}
