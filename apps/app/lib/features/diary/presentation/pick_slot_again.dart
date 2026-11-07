import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/storage/meal_queue.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/states.dart';
import '../../meals/presentation/meals_providers.dart';
import 'move_entry_sheet.dart';

/// Queued rows the API refused because their meal was removed while the
/// phone was offline. Each asks for another meal, then re-sends with the
/// same `client_id` (so it is never stored twice).
final needingSlotProvider = StreamProvider.autoDispose<List<PendingMeal>>(
  (ref) => ref.watch(mealQueueProvider).watchNeedingSlot(),
);

class PickSlotAgain extends ConsumerWidget {
  const PickSlotAgain({super.key});

  static Key bannerKey(String clientId) => Key('pick-again-$clientId');
  static Key buttonKey(String clientId) => Key('pick-again-button-$clientId');

  Future<void> _pick(
    BuildContext context,
    WidgetRef ref,
    PendingMeal row,
  ) async {
    final slotId = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (sheet) => SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.only(bottom: SnTokens.space4),
          child: SlotChoiceList(onPick: (id) => Navigator.of(sheet).pop(id)),
        ),
      ),
    );
    if (slotId == null) return;
    await ref.read(mealQueueProvider).retryWithSlot(row.clientId, slotId);
    try {
      await ref.read(mealSyncProvider).flush();
    } on Object {
      // The row stays queued; the next sync tries again.
    }
    ref.read(mealsRevisionProvider.notifier).bump();
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final rows = ref.watch(needingSlotProvider).value ?? const <PendingMeal>[];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final r in rows)
          Padding(
            key: bannerKey(r.clientId),
            padding: const EdgeInsets.only(bottom: SnTokens.space3),
            child: InlineErrorBanner(
              message: l10n.diarySlotsPickAgain,
              action: TextButton(
                key: buttonKey(r.clientId),
                onPressed: () => _pick(context, ref, r),
                child: Text(l10n.diaryMove),
              ),
            ),
          ),
      ],
    );
  }
}
