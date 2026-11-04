import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/scan/domain/draft_warnings.dart';
import 'package:smartnutri_ai/features/scan/presentation/label_capture_screen.dart';
import 'package:smartnutri_ai/features/scan/presentation/warning_banner.dart';

void main() {
  final en = lookupAppLocalizations(const Locale('en'));

  test('label v2 warnings have their own text', () {
    expect(warningText(en, 'fat_parts_mismatch'), en.warningFatPartsMismatch);
    expect(warningText(en, 'decimal_shift'), en.warningDecimalShift);
    expect(warningText(en, 'column_mismatch'), en.warningColumnMismatch);
    for (final code in [
      'fat_parts_mismatch',
      'decimal_shift',
      'column_mismatch',
    ]) {
      expect(warningText(en, code), isNot(en.confirmSubtitle), reason: code);
    }
  });

  test('decimal_shift and column_mismatch highlight the field they name', () {
    final warnings = [
      DraftWarning.parse('decimal_shift:per_100g.sugars_g'),
      DraftWarning.parse('column_mismatch:protein_g'),
      DraftWarning.parse('fat_parts_mismatch'),
    ];
    expect(highlightedFields(warnings), {'sugars_g', 'protein_g'});
  });

  test('retake hints follow details.reasons', () {
    expect(retakeHints(en, ['too_small']), [en.imageQualityTooSmall]);
    expect(retakeHints(en, ['blur', 'blur']), [en.imageQualityBlur]);
    expect(retakeHints(en, ['unknown_reason']), [en.imageQualityHintGeneric]);
    expect(retakeHints(en, const []), [en.imageQualityHintGeneric]);
  });
}
