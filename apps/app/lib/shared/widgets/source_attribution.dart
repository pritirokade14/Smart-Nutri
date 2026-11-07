import 'package:flutter/material.dart';

import '../../core/l10n/app_localizations.dart';
import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';
import 'off_attribution.dart';

/// The credit lines for the API's attribution keys (`attribution.off`,
/// `attribution.usda_fdc`, `attribution.smartnutri_recipe`), one per key.
/// An Open Food Facts credit links to the product page when [offBarcode] is
/// known. A key this build has no string for is skipped.
class SourceAttribution extends StatelessWidget {
  const SourceAttribution({super.key, required this.keys, this.offBarcode});

  final List<String> keys;
  final String? offBarcode;

  static const offKey = 'attribution.off';
  static const usdaKey = 'attribution.usda_fdc';
  static const recipeKey = 'attribution.smartnutri_recipe';

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final lines = <Widget>[];
    for (final key in keys.toSet()) {
      final text = switch (key) {
        offKey => l10n.attributionOff,
        usdaKey => l10n.attributionUsdaFdc,
        recipeKey => l10n.attributionSmartnutriRecipe,
        _ => null,
      };
      if (text == null) continue;
      if (key == offKey && offBarcode != null) {
        lines.add(OffAttribution(barcode: offBarcode!));
      } else {
        lines.add(
          Padding(
            padding: const EdgeInsets.symmetric(vertical: SnTokens.space1),
            child: Text(
              text,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
          ),
        );
      }
    }
    if (lines.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: lines,
    );
  }
}
