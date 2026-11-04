import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../data/members_repository.dart';
import 'members_providers.dart';

/// Opens the health-data consent sheet. Returns true once `health_data` is
/// recorded as granted; false when the user declines or closes it.
Future<bool> showConsentSheet(BuildContext context) async {
  final granted = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    builder: (_) => const ConsentSheet(),
  );
  return granted ?? false;
}

/// Asks for `health_data` consent before allergies, conditions, a goal,
/// height or weight are saved (P5). `ai_processing` is offered as a separate,
/// optional, unticked choice: it only turns on the AI explanation.
class ConsentSheet extends ConsumerStatefulWidget {
  const ConsentSheet({super.key});

  static const agreeKey = Key('consent-sheet-agree');
  static const declineKey = Key('consent-sheet-decline');
  static const aiCheckboxKey = Key('consent-sheet-ai');

  @override
  ConsumerState<ConsentSheet> createState() => _ConsentSheetState();
}

class _ConsentSheetState extends ConsumerState<ConsentSheet> {
  bool _ai = false;
  bool _busy = false;
  String? _error;

  Future<void> _agree(bool aiAlreadyGranted) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(consentStateProvider.notifier).record({
        consentPurposeHealthData: true,
        if (_ai && !aiAlreadyGranted) consentPurposeAiProcessing: true,
      });
      if (mounted) Navigator.of(context).pop(true);
    } on MembersFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(AppLocalizations.of(context), e.code);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final states = ref.watch(consentStateProvider);
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(
        SnTokens.space5,
        0,
        SnTokens.space5,
        SnTokens.space5,
      ),
      child: states.when(
        loading: () => const LoadingSkeleton(lines: 4),
        error: (e, _) => ErrorState(
          message: localizedErrorCode(
            l10n,
            e is MembersFailure ? e.code : null,
          ),
          onRetry: () => ref.invalidate(consentStateProvider),
        ),
        data: (list) {
          final aiGranted =
              consentGranted(list, consentPurposeAiProcessing) ?? false;
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Icon(Icons.shield_outlined, color: c.brand),
                  const SizedBox(width: SnTokens.space2),
                  Expanded(
                    child: Text(
                      l10n.consentHealthDataTitle,
                      style: theme.textTheme.titleLarge,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: SnTokens.space3),
              Text(
                l10n.consentHealthDataBody,
                style: theme.textTheme.bodyMedium,
              ),
              if (!aiGranted) ...[
                const SizedBox(height: SnTokens.space4),
                Material(
                  color: c.muted,
                  borderRadius: BorderRadius.circular(SnTokens.radiusMd),
                  clipBehavior: Clip.antiAlias,
                  child: CheckboxListTile(
                    key: ConsentSheet.aiCheckboxKey,
                    value: _ai,
                    onChanged: _busy
                        ? null
                        : (v) => setState(() => _ai = v ?? false),
                    controlAffinity: ListTileControlAffinity.leading,
                    title: Text(l10n.consentAiProcessingTitle),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(l10n.consentAiProcessingBody),
                        const SizedBox(height: SnTokens.space1),
                        Text(
                          l10n.consentAiOptional,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: c.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
              if (_error case final message?) ...[
                const SizedBox(height: SnTokens.space3),
                InlineErrorBanner(message: message),
              ],
              const SizedBox(height: SnTokens.space5),
              PrimaryButton(
                buttonKey: ConsentSheet.agreeKey,
                label: l10n.consentAgree,
                busy: _busy,
                onPressed: () => _agree(aiGranted),
              ),
              const SizedBox(height: SnTokens.space2),
              TextButton(
                key: ConsentSheet.declineKey,
                onPressed: _busy
                    ? null
                    : () => Navigator.of(context).pop(false),
                child: Text(l10n.consentDecline),
              ),
            ],
          );
        },
      ),
    );
  }
}
