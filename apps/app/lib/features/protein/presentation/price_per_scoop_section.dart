import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../scan/domain/number_text.dart';
import '../domain/price_per_scoop.dart';

/// Price per scoop for each side of a compare, from a pack price and pack
/// size the user types. The values live in this widget's state only: never
/// a provider, storage, request, URL or analytics event. Leaving the screen
/// forgets them.
class PricePerScoopSection extends StatefulWidget {
  const PricePerScoopSection({
    super.key,
    required this.servingA,
    required this.servingB,
  });

  /// The serving (scoop) size of each side, from the API; null leaves the
  /// price per scoop empty.
  final num? servingA;
  final num? servingB;

  static Key priceKey(String side) => Key('scoop-price-$side');
  static Key packKey(String side) => Key('scoop-pack-$side');
  static Key resultKey(String side) => Key('scoop-result-$side');

  @override
  State<PricePerScoopSection> createState() => _PricePerScoopSectionState();
}

class _PricePerScoopSectionState extends State<PricePerScoopSection> {
  final _price = {'a': TextEditingController(), 'b': TextEditingController()};
  final _pack = {'a': TextEditingController(), 'b': TextEditingController()};

  @override
  void dispose() {
    for (final c in [..._price.values, ..._pack.values]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final money = NumberFormat.simpleCurrency(locale: 'en_IN', name: 'INR');
    Widget side(String key, num? serving) {
      final value = pricePerScoop(
        parseNumber(_price[key]!.text).value,
        parseNumber(_pack[key]!.text).value,
        serving,
      );
      final inputs = [
        FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
        LengthLimitingTextInputFormatter(8),
      ];
      return Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              key: PricePerScoopSection.priceKey(key),
              controller: _price[key],
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              inputFormatters: inputs,
              decoration: InputDecoration(
                labelText: l10n.proteinPriceLabel,
                prefixText: money.currencySymbol,
              ),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: SnTokens.space2),
            TextField(
              key: PricePerScoopSection.packKey(key),
              controller: _pack[key],
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              inputFormatters: inputs,
              decoration: InputDecoration(labelText: l10n.proteinPackSizeLabel),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: SnTokens.space2),
            Text(
              value == null ? '—' : money.format(value),
              key: PricePerScoopSection.resultKey(key),
              style: theme.textTheme.titleMedium?.copyWith(
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(vertical: SnTokens.space3),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: c.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            l10n.proteinComparePriceScoop,
            style: theme.textTheme.titleSmall,
          ),
          const SizedBox(height: SnTokens.space2),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              side('a', widget.servingA),
              const SizedBox(width: SnTokens.space2),
              side('b', widget.servingB),
            ],
          ),
          const SizedBox(height: SnTokens.space2),
          Text(
            l10n.proteinPriceNote,
            style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
          ),
        ],
      ),
    );
  }
}
