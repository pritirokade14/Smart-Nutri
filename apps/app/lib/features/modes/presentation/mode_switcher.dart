import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../user_types/data/user_types_repository.dart';
import '../../user_types/presentation/user_type_labels.dart';
import '../../user_types/presentation/user_types_providers.dart';
import '../mode_providers.dart';

/// Switches the focused mode between the account's 2–3 types (hidden with
/// fewer). Switches at once and rolls back if the API refuses. Scanning,
/// results and allergy checks are the same in every mode.
class ModeSwitcher extends ConsumerWidget {
  const ModeSwitcher({super.key, this.showNote = false});

  /// Profile shows the label and the "same checks" note.
  final bool showNote;

  static const switcherKey = Key('mode-switcher');
  static Key segmentKey(String type) => Key('mode-segment-$type');

  Future<void> _select(BuildContext context, WidgetRef ref, String type) async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.maybeOf(context);
    try {
      await ref.read(userTypesProvider.notifier).setActive(type);
    } on UserTypesFailure catch (e) {
      messenger?.showSnackBar(
        SnackBar(content: Text(localizedErrorCode(l10n, e.code))),
      );
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final types = ref.watch(chosenTypesProvider);
    if (types.length < 2) return const SizedBox.shrink();
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final active = ref.watch(activeModeProvider);
    final control = SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SegmentedButton<String>(
        key: switcherKey,
        showSelectedIcon: false,
        segments: [
          for (final t in types)
            ButtonSegment<String>(
              value: t,
              label: Text(modeName(l10n, t), key: segmentKey(t)),
              tooltip: l10n.modesSwitchTo(modeName(l10n, t)),
            ),
        ],
        selected: {if (types.contains(active)) active},
        emptySelectionAllowed: true,
        onSelectionChanged: (s) {
          if (s.isEmpty || s.first == active) return;
          _select(context, ref, s.first);
        },
      ),
    );
    return Semantics(
      label: l10n.modesCurrent(modeName(l10n, active)),
      container: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (showNote) ...[
            Text(l10n.modesSwitcherLabel, style: theme.textTheme.titleSmall),
            const SizedBox(height: SnTokens.space2),
          ],
          control,
          if (showNote) ...[
            const SizedBox(height: SnTokens.space2),
            Text(
              l10n.modesSameChecks,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
