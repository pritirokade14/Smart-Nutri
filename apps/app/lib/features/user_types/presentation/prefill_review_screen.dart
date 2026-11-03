import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../../members/data/members_repository.dart';
import '../../members/domain/member.dart';
import '../../members/presentation/consent_sheet.dart';
import '../../members/presentation/member_labels.dart';
import '../../members/presentation/members_providers.dart';
import '../domain/user_types.dart';
import 'user_types_flow.dart';
import 'user_types_providers.dart';

/// "Add these to your profile?": the API's suggested changes to the account
/// holder's own member, each a checkbox (current → new; lists show only what
/// is added). Nothing is saved unless the user confirms: "Add to profile"
/// sends one `PATCH /v1/members/{id}` with the ticked values only, behind the
/// health_data consent. "Not now" sends nothing.
class PrefillReviewScreen extends ConsumerStatefulWidget {
  const PrefillReviewScreen({super.key, this.edit = false});

  final bool edit;

  static Key changeKey(String field) => Key('prefill-change-$field');
  static Key goalKey(String? goal) => Key('prefill-goal-${goal ?? 'neither'}');
  static const applyKey = Key('prefill-apply');
  static const notNowKey = Key('prefill-not-now');

  @override
  ConsumerState<PrefillReviewScreen> createState() =>
      _PrefillReviewScreenState();
}

class _PrefillReviewScreenState extends ConsumerState<PrefillReviewScreen> {
  /// Ticked state per change field; filled from [tickedByDefault] on first
  /// sight of a change.
  final Map<PrefillChangeField, bool> _ticked = {};

  /// The goal picked in a goal conflict; null is "neither" (the default).
  String? _goal;
  bool _busy = false;
  String? _error;

  void _done() => context.go(flowEnd(widget.edit));

  Future<void> _apply(PrefillSuggestion p) async {
    final confirmed = [
      for (final c in p.changes)
        if (_ticked[c.field] ?? tickedByDefault(c)) c,
    ];
    if (confirmed.isEmpty && _goal == null) {
      _done();
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final l10n = AppLocalizations.of(context);
    try {
      final members = await ref.read(membersProvider.future);
      final primary = members.where((m) => m.id == p.memberId).firstOrNull;
      if (primary == null) throw const MembersFailure('member_not_found');
      final draft = applyPrefill(primary, confirmed, goal: _goal);
      final consents = ref.read(consentStateProvider).value;
      if (!mounted) return;
      if (writesHealthData(draft, stored: primary) &&
          consentGranted(consents, consentPurposeHealthData) == false &&
          !await showConsentSheet(context)) {
        if (mounted) setState(() => _busy = false);
        return;
      }
      await _save(primary.id, draft, consentRetry: true);
    } on MembersFailure catch (e) {
      if (mounted) {
        setState(() {
          _busy = false;
          _error = localizedErrorCode(l10n, e.code);
        });
      }
    }
  }

  Future<void> _save(
    String id,
    MemberDraft draft, {
    required bool consentRetry,
  }) async {
    try {
      await ref.read(membersProvider.notifier).updateMember(id, draft);
    } on MembersFailure catch (e) {
      // A 403 goes through the consent sheet, then one retry.
      if (e.isConsentRequired && consentRetry && mounted) {
        if (await showConsentSheet(context)) {
          return _save(id, draft, consentRetry: false);
        }
        if (mounted) setState(() => _busy = false);
        return;
      }
      rethrow;
    }
    // The suggestions are recomputed from the member (now empty).
    ref.invalidate(userTypesProvider);
    if (!mounted) return;
    ScaffoldMessenger.maybeOf(context)?.showSnackBar(
      SnackBar(content: Text(AppLocalizations.of(context).membersSaved)),
    );
    _done();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    // Load the consent states so a missing consent is asked for first.
    ref.watch(consentStateProvider);
    final out = ref.watch(userTypesProvider).value;
    final p = out?.prefill;
    final hasAny = out != null && hasPrefillToReview(out);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.userTypesPrefillTitle),
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(SnTokens.space4),
          children: [
            Text(
              l10n.userTypesPrefillBody,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: c.textSecondary,
              ),
            ),
            const SizedBox(height: SnTokens.space3),
            if (p == null || !hasAny)
              Text(l10n.userTypesPrefillNothing)
            else ...[
              for (final change in p.changes)
                CheckboxListTile(
                  key: PrefillReviewScreen.changeKey(change.field.json ?? ''),
                  contentPadding: EdgeInsets.zero,
                  controlAffinity: ListTileControlAffinity.leading,
                  value: _ticked[change.field] ?? tickedByDefault(change),
                  onChanged: _busy
                      ? null
                      : (v) =>
                            setState(() => _ticked[change.field] = v ?? false),
                  title: Text(_line(l10n, change)),
                ),
              if (p.goalChoice case final choices? when choices.isNotEmpty) ...[
                const SizedBox(height: SnTokens.space3),
                Text(
                  l10n.userTypesPrefillGoalConflict,
                  style: theme.textTheme.titleSmall,
                ),
                RadioGroup<String>(
                  groupValue: _goal ?? '',
                  onChanged: (v) => _busy
                      ? null
                      : setState(
                          () => _goal = (v == null || v.isEmpty) ? null : v,
                        ),
                  child: Column(
                    children: [
                      for (final g in choices)
                        if (g.json case final String goal)
                          RadioListTile<String>(
                            key: PrefillReviewScreen.goalKey(goal),
                            contentPadding: EdgeInsets.zero,
                            value: goal,
                            title: Text(goalLabel(l10n, goal)),
                          ),
                      RadioListTile<String>(
                        key: PrefillReviewScreen.goalKey(null),
                        contentPadding: EdgeInsets.zero,
                        value: '',
                        title: Text(l10n.userTypesPrefillGoalNeither),
                      ),
                    ],
                  ),
                ),
              ],
            ],
            if (_error case final message?) ...[
              const SizedBox(height: SnTokens.space3),
              InlineErrorBanner(message: message),
            ],
            const SizedBox(height: SnTokens.space5),
            if (p != null && hasAny) ...[
              PrimaryButton(
                buttonKey: PrefillReviewScreen.applyKey,
                label: l10n.userTypesPrefillApply,
                icon: Icons.check_rounded,
                busy: _busy,
                onPressed: () => _apply(p),
              ),
              const SizedBox(height: SnTokens.space2),
              TextButton(
                key: PrefillReviewScreen.notNowKey,
                onPressed: _busy ? null : _done,
                child: Text(l10n.userTypesPrefillNotNow),
              ),
            ] else
              PrimaryButton(
                buttonKey: PrefillReviewScreen.notNowKey,
                label: l10n.userTypesContinue,
                onPressed: _done,
              ),
          ],
        ),
      ),
    );
  }

  /// One change as text: lists show only what is added; diet and goal show
  /// current → new.
  static String _line(AppLocalizations l10n, PrefillChange change) {
    String scalar(Object? v, String Function(String) label) =>
        v is String ? label(v) : l10n.membersFormNotSet;
    String arrow(String Function(String) label) =>
        '${scalar(change.current, label)} → ${scalar(change.value, label)}';
    String added(String Function(String) label) =>
        [for (final a in change.added) label(a)].join(', ');
    return switch (change.field) {
      PrefillChangeField.conditions => l10n.userTypesPrefillLineConditions(
        added((k) => conditionLabel(l10n, k)),
      ),
      PrefillChangeField.allergens => l10n.userTypesPrefillLineAllergens(
        added((k) => allergenLabel(l10n, k)),
      ),
      PrefillChangeField.customAlerts => l10n.userTypesPrefillLineCustomAlerts(
        added((k) => alertLabel(l10n, k)),
      ),
      PrefillChangeField.diet => l10n.userTypesPrefillLineDiet(
        arrow((k) => dietLabel(l10n, k)),
      ),
      PrefillChangeField.goal => l10n.userTypesPrefillLineGoal(
        arrow((k) => goalLabel(l10n, k)),
      ),
      _ => l10n.userTypesPrefillNothing,
    };
  }
}
