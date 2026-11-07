import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/targets/presentation/flag_notes.dart';

import '../../support/fixtures.dart';

void main() {
  for (final locale in ['en', 'hi', 'mr']) {
    test('every golden flag has a message in $locale', () {
      final l10n = lookupAppLocalizations(Locale(locale));
      final flags = <String>{};
      for (final stem in targetsFixtureStems()) {
        final json = targetsJson(stem);
        if (json['status'] == null) continue; // error expectations
        final t = targetsFixture(stem);
        for (final flag in t.flags) {
          flags.add(flag);
          expect(
            flagMessage(l10n, flag, t),
            isNotNull,
            reason: '$stem: $flag in $locale',
          );
        }
      }
      expect(flags, isNotEmpty);
    });
  }

  test('a flag this build does not know has no message', () {
    final l10n = lookupAppLocalizations(const Locale('en'));
    expect(
      flagMessage(l10n, 'from_the_future', targetsFixture('g1_build_muscle')),
      isNull,
    );
  });
}
