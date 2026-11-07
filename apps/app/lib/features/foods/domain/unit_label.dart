import '../../../core/l10n/app_localizations.dart';
import '../../scan/domain/number_text.dart';

/// The label of a unit code for [count] (plural forms per locale). An unknown
/// code is shown as the code itself: the API may know more units than this
/// build.
String unitLabel(AppLocalizations l10n, String code, num count) =>
    switch (code) {
      'g' => l10n.unitG(count),
      'ml' => l10n.unitMl(count),
      'serving' => l10n.unitServing(count),
      'piece' => l10n.unitPiece(count),
      'piece_small' => l10n.unitPieceSmall(count),
      'piece_medium' => l10n.unitPieceMedium(count),
      'piece_large' => l10n.unitPieceLarge(count),
      'roti' => l10n.unitRoti(count),
      'slice' => l10n.unitSlice(count),
      'katori' => l10n.unitKatori(count),
      'katori_small' => l10n.unitKatoriSmall(count),
      'katori_medium' => l10n.unitKatoriMedium(count),
      'katori_large' => l10n.unitKatoriLarge(count),
      'cup' => l10n.unitCup(count),
      'glass' => l10n.unitGlass(count),
      'tbsp' => l10n.unitTbsp(count),
      'tsp' => l10n.unitTsp(count),
      _ => code,
    };

/// A chip label: the unit, plus its volume as the API gives it for volume
/// units (so "medium katori (155 ml)" is never mistaken for a bigger bowl).
String unitChipLabel(AppLocalizations l10n, String code, num count, {num? ml}) {
  final label = unitLabel(l10n, code, count);
  if (ml == null || code == 'ml') return label;
  return '$label (${l10n.unitMlHint(formatForDisplay(ml))})';
}
