import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/off_attribution.dart';
import '../../scan/domain/number_text.dart';
import '../../targets/domain/targets_format.dart';

/// Energy and macro keys whose absence makes an entry "incomplete" for the
/// rings (sugar and salt gaps are not marked here).
const _ringKeys = {'energy_kcal', 'protein_g', 'fat_g', 'carbs_g'};

/// One logged entry. Shows exactly what the API sent: kcal only when it is
/// known and not hidden; an unknown value gets the incomplete marker.
class EntryTile extends StatelessWidget {
  const EntryTile({super.key, required this.entry, this.onTap});

  final MealOut entry;
  final VoidCallback? onTap;

  static Key tileKey(String id) => Key('diary-entry-$id');
  static const quickBadgeKey = Key('diary-quick-badge');
  static const portionKey = Key('diary-entry-portion');

  bool get isQuick => entry.sourceKind == MealOutSourceKind.quickAdd;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final name = isQuick && entry.productName.trim().isEmpty
        ? l10n.diaryQuickAddName
        : entry.productName;
    final kcal = entry.nutrients.energyKcal;
    final grams = entry.grams;
    final incomplete = entry.incomplete.any(_ringKeys.contains);
    final barcode = entry.barcode;
    return ListTile(
      key: tileKey(entry.id),
      contentPadding: EdgeInsets.zero,
      onTap: onTap,
      title: Row(
        children: [
          Flexible(child: Text(name, style: theme.textTheme.titleSmall)),
          if (isQuick) ...[
            const SizedBox(width: SnTokens.space2),
            Container(
              key: quickBadgeKey,
              padding: const EdgeInsets.symmetric(
                horizontal: SnTokens.space2,
                vertical: SnTokens.space1 / 2,
              ),
              decoration: BoxDecoration(
                color: c.muted,
                borderRadius: BorderRadius.circular(SnTokens.radiusFull),
              ),
              child: Text(
                l10n.diaryQuickBadge,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: c.textSecondary,
                ),
              ),
            ),
          ],
        ],
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (grams != null)
            Text(
              l10n.diaryGramsLine(formatForDisplay(grams)),
              key: portionKey,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
          if (entry.attribution != null && barcode != null)
            OffAttribution(barcode: barcode),
        ],
      ),
      trailing: kcal != null
          ? Text(kcalText(l10n, kcal), style: theme.textTheme.bodyMedium)
          : incomplete
          ? Tooltip(
              message: l10n.diaryIncomplete,
              child: Icon(
                Icons.info_outline_rounded,
                color: c.textSecondary,
                semanticLabel: l10n.diaryIncomplete,
              ),
            )
          : null,
    );
  }
}
