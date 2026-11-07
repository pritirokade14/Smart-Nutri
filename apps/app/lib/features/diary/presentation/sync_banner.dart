import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/states.dart';
import '../../meals/presentation/meals_providers.dart';

/// Logs the API refused during a sync (shown until the user dismisses it).
/// Logs still waiting show in their slot as "waiting to sync" rows, and as
/// one note here.
class SyncBanner extends ConsumerWidget {
  const SyncBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final pending = ref.watch(pendingMealsCountProvider).value ?? 0;
    final failed = ref.watch(failedMealsCountProvider).value ?? 0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (pending > 0)
          Container(
            margin: const EdgeInsets.only(bottom: SnTokens.space3),
            padding: const EdgeInsets.all(SnTokens.space3),
            decoration: BoxDecoration(
              color: c.muted,
              borderRadius: BorderRadius.circular(SnTokens.radiusMd),
            ),
            child: Row(
              children: [
                Icon(Icons.cloud_upload_outlined, color: c.textSecondary),
                const SizedBox(width: SnTokens.space2),
                Expanded(child: Text(l10n.mealsQueuedOffline)),
              ],
            ),
          ),
        if (failed > 0)
          Padding(
            padding: const EdgeInsets.only(bottom: SnTokens.space3),
            child: InlineErrorBanner(
              message: l10n.mealsSyncFailed,
              action: TextButton(
                onPressed: () => ref.read(mealQueueProvider).clearFailed(),
                child: Text(MaterialLocalizations.of(context).okButtonLabel),
              ),
            ),
          ),
      ],
    );
  }
}
