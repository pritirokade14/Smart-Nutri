import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/states.dart';
import '../../members/data/members_repository.dart';
import '../../members/presentation/members_providers.dart';

/// Profile: the health-data and AI-explanation consents, each with its state
/// and a grant or withdraw action. Withdrawing does not delete saved data
/// (P5); it stops new health data being saved, or the AI explanation.
class ConsentsSection extends ConsumerStatefulWidget {
  const ConsentsSection({super.key});

  static Key actionKey(String purpose) => Key('consent-action-$purpose');

  @override
  ConsumerState<ConsentsSection> createState() => _ConsentsSectionState();
}

class _ConsentsSectionState extends ConsumerState<ConsentsSection> {
  String? _busy;
  String? _error;

  Future<void> _set(String purpose, bool granted) async {
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final states = ref.watch(consentStateProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: l10n.profileConsentsTitle,
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
              for (final (purpose, title, body) in [
                (
                  consentPurposeHealthData,
                  l10n.consentHealthDataTitle,
                  l10n.consentHealthDataBody,
                ),
                (
                  consentPurposeAiProcessing,
                  l10n.consentAiProcessingTitle,
                  l10n.consentAiProcessingBody,
                ),
              ])
                _ConsentTile(
                  purpose: purpose,
                  title: title,
                  body: body,
                  granted: consentGranted(list, purpose) ?? false,
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
    required this.busy,
    required this.enabled,
    required this.onChanged,
  });

  final String purpose;
  final String title;
  final String body;
  final bool granted;
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
                      : Icons.radio_button_unchecked_rounded,
                  size: SnTokens.fontSizeMd,
                  color: granted ? c.brand : c.textSecondary,
                ),
                const SizedBox(width: SnTokens.space1),
                Text(
                  granted ? l10n.consentGranted : l10n.consentNotGranted,
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
            const SizedBox(height: SnTokens.space2),
            Align(
              alignment: AlignmentDirectional.centerEnd,
              child: busy
                  ? const SizedBox.square(
                      dimension: SnTokens.space5,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : TextButton(
                      key: ConsentsSection.actionKey(purpose),
                      onPressed: enabled ? () => onChanged(!granted) : null,
                      child: Text(
                        granted ? l10n.consentWithdraw : l10n.consentAgree,
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
