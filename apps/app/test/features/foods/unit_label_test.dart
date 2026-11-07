import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/foods/domain/unit_label.dart';

AppLocalizations _l(String code) => lookupAppLocalizations(Locale(code));

void main() {
  test('katori sizes show ml', () {
    final l10n = _l('en');
    expect(
      unitChipLabel(l10n, 'katori_medium', 1, ml: 155),
      'medium katori (155 ml)',
    );
    expect(unitChipLabel(l10n, 'katori', 1, ml: 200), 'katori (200 ml)');
    // A unit with no volume, and ml itself, get no hint.
    expect(unitChipLabel(l10n, 'roti', 1), 'roti');
    expect(unitChipLabel(l10n, 'ml', 30, ml: 30), 'ml');
  });

  test('plural forms per locale', () {
    expect(unitLabel(_l('en'), 'katori', 1), 'katori');
    expect(unitLabel(_l('en'), 'katori', 2), 'katoris');
    expect(unitLabel(_l('en'), 'glass', 0.5), 'glasses');
    expect(unitLabel(_l('hi'), 'katori', 1), 'कटोरी');
    expect(unitLabel(_l('hi'), 'katori', 2), 'कटोरियाँ');
    expect(unitLabel(_l('mr'), 'katori', 1), 'वाटी');
    expect(unitLabel(_l('mr'), 'katori', 2), 'वाट्या');
  });

  test('an unknown code is shown as is', () {
    expect(unitLabel(_l('en'), 'bowl', 1), 'bowl');
  });
}
