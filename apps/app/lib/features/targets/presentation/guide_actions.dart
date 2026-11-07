import 'package:dio/dio.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../../members/data/members_repository.dart';
import '../../members/presentation/consent_sheet.dart';
import '../../members/presentation/members_providers.dart';
import '../data/targets_repository.dart';
import 'guide_draft.dart';
import 'targets_providers.dart';

/// What a preview or a save did. [cancelled] is a declined consent sheet;
/// otherwise [code] (with [details]) is the API's `error.code`.
class GuideOutcome {
  const GuideOutcome({
    this.targets,
    this.cancelled = false,
    this.code,
    this.details = const {},
  });

  final TargetsOut? targets;
  final bool cancelled;
  final String? code;
  final Map<String, Object?> details;

  bool get ok => targets != null;
}

GuideOutcome _failed(Object e) {
  if (e is TargetsFailure) {
    return GuideOutcome(code: e.code, details: e.details);
  }
  if (e is MembersFailure) {
    final cause = e.cause;
    var details = const <String, Object?>{};
    if (cause is DioException) {
      final raw = parseErrorEnvelope(cause.response?.data)?.error.details;
      if (raw is Map) details = Map<String, Object?>.from(raw);
    }
    return GuideOutcome(code: e.code, details: details);
  }
  return GuideOutcome(code: apiErrorCode(e));
}

bool _consentMissing(WidgetRef ref) =>
    consentGranted(
      ref.read(consentStateProvider).value,
      consentPurposeHealthData,
    ) ==
    false;

/// Opens the health-data consent sheet when it is known to be missing.
/// False when the user declined.
Future<bool> _ensureConsent(BuildContext context, WidgetRef ref) async {
  if (!_consentMissing(ref)) return true;
  return showConsentSheet(context);
}

/// Runs [call], asking for the health-data consent first when it is known
/// to be missing, and once more on a 403 `consent_required`.
Future<GuideOutcome> _withConsent(
  BuildContext context,
  WidgetRef ref,
  Future<TargetsOut> Function() call,
) async {
  if (!await _ensureConsent(context, ref)) {
    return const GuideOutcome(cancelled: true);
  }
  var asked = false;
  while (true) {
    try {
      return GuideOutcome(targets: await call());
    } on Object catch (e) {
      final out = _failed(e);
      if (out.code == 'consent_required' && !asked && context.mounted) {
        asked = true;
        ref.invalidate(consentStateProvider);
        if (await showConsentSheet(context)) continue;
        return const GuideOutcome(cancelled: true);
      }
      return out;
    }
  }
}

/// Targets for the unsaved answers (`targets_preview`).
Future<GuideOutcome> previewGuide(
  BuildContext context,
  WidgetRef ref,
  GuideDraft draft,
) => _withConsent(
  context,
  ref,
  () => ref.read(targetsRepositoryProvider).preview(draft.toPreview()),
);

/// Saves the body answers on the account holder's member, then the guide
/// settings, then reloads everything that shows a target.
Future<GuideOutcome> saveGuide(
  BuildContext context,
  WidgetRef ref,
  GuideDraft draft,
) async {
  final primary = draft.member;
  if (primary == null) return const GuideOutcome(code: 'member_not_found');
  final result = await _withConsent(context, ref, () async {
    await ref
        .read(membersProvider.notifier)
        .updateMember(primary.id, draft.toMemberDraft(primary));
    return ref.read(targetsRepositoryProvider).save(draft.toSettings());
  });
  if (result.ok) refreshTargets(ref);
  return result;
}
