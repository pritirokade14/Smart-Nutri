import '../../../core/l10n/app_localizations.dart';
import '../../scan/domain/number_text.dart';
import 'unit_label.dart';

/// Whether `unit_source` says the grams came from a per-food weight or a
/// density: an estimate, shown with "≈" (never as an exact amount).
bool isApproxUnitSource(String? source) =>
    source == 'portion' || source == 'density';

/// "2 roti · 136 g", "200 ml" or "≈ 136 g": the amount in the food's own
/// basis (ml for an ml food, never "g"), as the API resolved it. [approx]
/// puts "≈" before the amount.
String portionLine(
  AppLocalizations l10n, {
  required num amount,
  required bool ml,
  num? quantity,
  String? unit,
  bool approx = false,
}) {
  final a = '${approx ? '≈ ' : ''}${formatForDisplay(amount)}';
  if (unit == null || quantity == null || unit == 'g' || (ml && unit == 'ml')) {
    return ml ? '$a ${l10n.unitMl(amount)}' : l10n.diaryGramsLine(a);
  }
  final q = formatForDisplay(quantity);
  final u = unitLabel(l10n, unit, quantity);
  return ml ? l10n.diaryPortionLineMl(a, q, u) : l10n.diaryPortionLine(a, q, u);
}
