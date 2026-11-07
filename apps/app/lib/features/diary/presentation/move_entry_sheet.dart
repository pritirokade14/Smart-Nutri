import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/states.dart';
import '../../meals/presentation/meals_providers.dart';
import '../data/diary_repository.dart';
import '../domain/slot_label.dart';
import 'diary_providers.dart';

/// Lists the active meals and returns the one picked (or null).
class SlotChoiceList extends ConsumerWidget {
  const SlotChoiceList({
    super.key,
    required this.onPick,
    this.currentSlotId,
    this.busy = false,
  });

  final void Function(String slotId) onPick;
  final String? currentSlotId;
  final bool busy;

  static Key optionKey(String slotId) => Key('slot-choice-$slotId');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final slots = ref.watch(mealSlotsProvider);
    return slots.when(
      loading: () => const LoadingSkeleton(lines: 3),
      error: (e, _) => ErrorState(
        message: localizedErrorCode(l10n, e is DiaryFailure ? e.code : null),
        onRetry: () => ref.invalidate(mealSlotsProvider),
      ),
      data: (out) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          for (final s in out.items.where(
            (s) => !s.archived && s.id != currentSlotId,
          ))
            ListTile(
              key: optionKey(s.id),
              enabled: !busy,
              title: Text(
                slotLabel(
                  l10n,
                  labelKey: s.labelKey,
                  customLabel: s.customLabel,
                ),
              ),
              onTap: () => onPick(s.id),
            ),
        ],
      ),
    );
  }
}

/// Moves an entry to another meal: sends only `meal_slot_id`. Returns true
/// when it moved.
Future<bool?> showMoveEntrySheet(BuildContext context, MealOut entry) =>
    showModalBottomSheet<bool>(
      context: context,
      showDragHandle: true,
      builder: (_) => MoveEntrySheet(entry: entry),
    );

class MoveEntrySheet extends ConsumerStatefulWidget {
  const MoveEntrySheet({super.key, required this.entry});

  final MealOut entry;

  static const errorKey = Key('move-entry-error');

  @override
  ConsumerState<MoveEntrySheet> createState() => _MoveEntrySheetState();
}

class _MoveEntrySheetState extends ConsumerState<MoveEntrySheet> {
  bool _busy = false;
  String? _error;

  Future<void> _move(String slotId) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref
          .read(diaryRepositoryProvider)
          .update(widget.entry.id, MealPatch(mealSlotId: slotId));
      ref.read(mealsRevisionProvider.notifier).bump();
      if (mounted) Navigator.of(context).pop(true);
    } on DiaryFailure catch (e) {
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
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(
          SnTokens.space4,
          0,
          SnTokens.space4,
          SnTokens.space4,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.diaryMove, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: SnTokens.space2),
            if (_error case final msg?)
              InlineErrorBanner(key: MoveEntrySheet.errorKey, message: msg),
            SlotChoiceList(
              currentSlotId: widget.entry.mealSlotId,
              busy: _busy,
              onPick: _move,
            ),
          ],
        ),
      ),
    );
  }
}
