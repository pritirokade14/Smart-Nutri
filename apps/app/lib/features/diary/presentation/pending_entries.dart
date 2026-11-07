import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/storage/meal_queue.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../domain/diary_dates.dart';

/// The queued rows that belong in [slot] on [day]. A row with no slot goes
/// in [fallbackSlotId] (the API's suggestion) or, without one, the first
/// active slot. Dates are compared, never worked out.
List<PendingMeal> pendingForSlot(
  List<PendingMeal> rows,
  DiaryDayOut day,
  SlotDayOut slot, {
  String? fallbackSlotId,
}) {
  final shown = dateKey(day.date);
  final today = dateKey(day.today);
  final active = day.slots.where((s) => !s.archived).toList();
  final fallback = active.any((s) => s.slotId == fallbackSlotId)
      ? fallbackSlotId
      : active.firstOrNull?.slotId;
  return [
    for (final r in rows)
      if ((r.localDate ?? today) == shown &&
          (r.mealSlotId == null
              ? slot.slotId == fallback
              : r.mealSlotId == slot.slotId))
        r,
  ];
}

/// A queued entry: its name and "waiting to sync". Never a number.
class PendingEntryTile extends StatelessWidget {
  const PendingEntryTile({super.key, required this.row});

  final PendingMeal row;

  static Key tileKey(String clientId) => Key('diary-pending-$clientId');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final name = row.displayName?.trim() ?? '';
    return ListTile(
      key: tileKey(row.clientId),
      contentPadding: EdgeInsets.zero,
      leading: Icon(Icons.cloud_upload_outlined, color: c.textSecondary),
      title: Text(
        name.isNotEmpty
            ? name
            : (row.quickEnergyKcal != null ? l10n.diaryQuickAddName : ''),
        style: theme.textTheme.titleSmall,
      ),
      subtitle: Padding(
        padding: const EdgeInsets.only(top: SnTokens.space1 / 2),
        child: Text(
          l10n.diaryWaitingSync,
          style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
        ),
      ),
    );
  }
}
