import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../domain/slot_label.dart';
import 'entry_tile.dart';

/// One meal slot of the day. The title is the user's own label verbatim or
/// the translated default; entries are the API's, in its order.
class SlotSection extends StatelessWidget {
  const SlotSection({
    super.key,
    required this.slot,
    this.onEntryTap,
    this.onAdd,
    this.menu,
    this.pending = const [],
  });

  final SlotDayOut slot;
  final void Function(MealOut entry)? onEntryTap;
  final VoidCallback? onAdd;

  /// A trailing menu (copy this meal, ...).
  final Widget? menu;

  /// Entries waiting to sync on this phone (name and "waiting to sync" only).
  final List<Widget> pending;

  static Key sectionKey(String slotId) => Key('diary-slot-$slotId');
  static Key titleKey(String slotId) => Key('diary-slot-title-$slotId');
  static Key addKey(String slotId) => Key('diary-slot-add-$slotId');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final title = slotLabel(
      l10n,
      labelKey: slot.labelKey,
      customLabel: slot.customLabel,
    );
    return Card(
      key: sectionKey(slot.slotId),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          SnTokens.space4,
          SnTokens.space2,
          SnTokens.space2,
          SnTokens.space2,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    title,
                    key: titleKey(slot.slotId),
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                if (onAdd != null)
                  IconButton(
                    key: addKey(slot.slotId),
                    tooltip: l10n.diaryAddToSlot(title),
                    icon: const Icon(Icons.add_rounded),
                    onPressed: onAdd,
                  ),
                ?menu,
              ],
            ),
            for (final e in slot.entries)
              EntryTile(
                entry: e,
                onTap: onEntryTap == null ? null : () => onEntryTap!(e),
              ),
            ...pending,
          ],
        ),
      ),
    );
  }
}
