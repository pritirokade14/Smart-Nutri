import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/states.dart';
import '../../consent/presentation/consent_screen.dart';
import '../../consent/presentation/policy_links.dart';
import '../../members/data/members_repository.dart';
import '../../members/presentation/members_providers.dart';

/// Profile: every consent (terms, health data, AI explanations), each with its
/// state and an agree, agree-again (`needs_update`) or withdraw action.
/// Withdrawing does not delete saved data (ADR 0018). Withdrawing terms stops
/// every product check, so it asks first; the terms screen then follows.
class ConsentsSection extends ConsumerStatefulWidget {
  const ConsentsSection({super.key});

  static Key actionKey(String purpose) => Key('consent-action-$purpose');
  static Key withdrawKey(String purpose) => Key('consent-withdraw-$purpose');
  static const confirmWithdrawKey = Key('consent-withdraw-terms-confirm');

  @override
  ConsumerState<ConsentsSection> createState() => _ConsentsSectionState();
}

class _ConsentsSectionState extends ConsumerState<ConsentsSection> {
  String? _busy;
  String? _error;

  Future<void> _set(String purpose, bool granted) async {
    if (purpose == consentPurposeTerms && !granted) {
      if (!await _confirmWithdrawTerms()) return;
    }
    if (!mounted) return;
    setState(() {
      _busy = purpose;
      _error = null;
    });
    try {
      await ref.read(consentStateProvider.notifier).record({purpose: granted});
    } on MembersFailure catch (e) {
      if (mounted) {
        _error = localizedErrorCode(AppLocalizations.of(context), e.code);
      }
    } finally {
      if (mounted) setState(() => _busy = null);
    }
  }

  Future<bool> _confirmWithdrawTerms() async {
    final l10n = AppLocalizations.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        content: Text(l10n.consentWithdrawTermsConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.commonCancel),
          ),
          TextButton(
            key: ConsentsSection.confirmWithdrawKey,
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.consentWithdraw),
          ),
        ],
      ),
    );
    return ok ?? false;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final states = ref.watch(consentStateProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: l10n.profilePrivacyTitle,
          icon: Icons.shield_outlined,
        ),
        states.when(
          loading: () => const LoadingSkeleton(lines: 3),
          error: (e, _) => ErrorState(
            message: localizedErrorCode(
              l10n,
              e is MembersFailure ? e.code : null,
            ),
            onRetry: () => ref.invalidate(consentStateProvider),
          ),
          data: (list) => Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              for (final purpose in const [
                consentPurposeTerms,
                consentPurposeHealthData,
                consentPurposeAiProcessing,
              ])
                _ConsentTile(
                  purpose: purpose,
                  title: consentTitle(l10n, purpose),
                  body: consentBody(l10n, purpose),
                  granted: consentGranted(list, purpose) ?? false,
                  needsUpdate: list.any(
                    (s) => s.purpose == purpose && s.needsUpdate,
                  ),
                  busy: _busy == purpose,
                  enabled: _busy == null,
                  onChanged: (granted) => _set(purpose, granted),
                ),
              if (_error case final message?)
                InlineErrorBanner(message: message),
            ],
          ),
        ),
      ],
    );
  }
}

class _ConsentTile extends StatelessWidget {
  const _ConsentTile({
    required this.purpose,
    required this.title,
    required this.body,
    required this.granted,
    required this.needsUpdate,
    required this.busy,
    required this.enabled,
    required this.onChanged,
  });

  final String purpose;
  final String title;
  final String body;
  final bool granted;

  /// Agreed to an older text: shown as "Updated, please review", with both
  /// "I agree" (to the new text) and "Withdraw".
  final bool needsUpdate;
  final bool busy;
  final bool enabled;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: SnTokens.space3),
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(title, style: theme.textTheme.titleMedium),
                ),
                Icon(
                  granted
                      ? Icons.check_circle_rounded
                      : needsUpdate
                      ? Icons.update_rounded
                      : Icons.radio_button_unchecked_rounded,
                  size: SnTokens.fontSizeMd,
                  color: granted ? c.brand : c.textSecondary,
                ),
                const SizedBox(width: SnTokens.space1),
                Text(
                  granted
                      ? l10n.consentGranted
                      : needsUpdate
                      ? l10n.consentNeedsUpdate
                      : l10n.consentNotGranted,
                  style: theme.textTheme.labelMedium?.copyWith(
                    color: c.textSecondary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: SnTokens.space2),
            Text(
              body,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
            if (needsUpdate) ...[
              const SizedBox(height: SnTokens.space2),
              Text(
                l10n.consentUpdateNote,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: c.textSecondary,
                ),
              ),
            ],
            if (purpose == consentPurposeTerms) const PolicyLinks(),
            const SizedBox(height: SnTokens.space2),
            Align(
              alignment: AlignmentDirectional.centerEnd,
              child: busy
                  ? const SizedBox.square(
                      dimension: SnTokens.space5,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Wrap(
                      alignment: WrapAlignment.end,
                      spacing: SnTokens.space2,
                      children: [
                        if (needsUpdate)
                          TextButton(
                            key: ConsentsSection.withdrawKey(purpose),
                            onPressed: enabled ? () => onChanged(false) : null,
                            child: Text(l10n.consentWithdraw),
                          ),
                        TextButton(
                          key: ConsentsSection.actionKey(purpose),
                          onPressed: enabled ? () => onChanged(!granted) : null,
                          child: Text(
                            granted ? l10n.consentWithdraw : l10n.consentAgree,
                          ),
                        ),
                      ],
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
