import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../scan/domain/number_text.dart';
import '../domain/report.dart';

/// Protein per serving, per 100 g and per 100 kcal from `report.protein`,
/// and the sweeteners and caffeine the ingredients list. Product facts, not
/// a member verdict: no verdict colour. A missing value shows "—" (read as
/// "Not on the label"), never 0.
class ProteinFactsRow extends StatelessWidget {
  const ProteinFactsRow({
    super.key,
    required this.facts,
    this.sweeteners = const [],
    this.caffeine = const [],
  });

  final ProteinFacts facts;
  final List<String> sweeteners;
  final List<String> caffeine;

  static const dash = '—';
  static Key valueKey(String which) => Key('protein-fact-$which');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    Widget cell(String which, String label, num? value) => Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
          ),
          Semantics(
            label: value == null ? l10n.proteinNotOnLabel : null,
            excludeSemantics: value == null,
            child: Text(
              value == null ? dash : formatForDisplay(value),
              key: valueKey(which),
              style: theme.textTheme.titleMedium?.copyWith(
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
          ),
        ],
      ),
    );
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                cell('serving', l10n.proteinPerServing, facts.perServing),
                const SizedBox(width: SnTokens.space2),
                cell('100g', l10n.proteinPer100g, facts.per100g),
                const SizedBox(width: SnTokens.space2),
                cell('100kcal', l10n.proteinPer100kcal, facts.per100kcal),
              ],
            ),
            if (sweeteners.isNotEmpty) ...[
              const SizedBox(height: SnTokens.space3),
              Text('${l10n.reportSweeteners}: ${sweeteners.join(', ')}'),
            ],
            if (caffeine.isNotEmpty) ...[
              const SizedBox(height: SnTokens.space2),
              Text('${l10n.reportCaffeine}: ${caffeine.join(', ')}'),
            ],
          ],
        ),
      ),
    );
  }
}
