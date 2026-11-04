import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/features/analysis/presentation/verdict_card.dart';
import 'package:smartnutri_ai/shared/widgets/verdict_badge.dart';

import '../../support/fixtures.dart';

bool greenish(Color c) {
  final hsv = HSVColor.fromColor(c);
  return hsv.hue >= 70 && hsv.hue <= 185 && hsv.saturation >= 0.08;
}

/// Every colour painted by boxes, icons and text inside the card.
List<Color> paintedColors(WidgetTester t) {
  final card = find.byType(VerdictCard);
  final out = <Color>[];
  for (final c in t.widgetList<Container>(
    find.descendant(of: card, matching: find.byType(Container)),
  )) {
    final d = c.decoration;
    if (d is BoxDecoration) {
      if (d.color case final color?) out.add(color);
      if (d.border case Border(:final top)) out.add(top.color);
    }
    if (c.color case final color?) out.add(color);
  }
  for (final i in t.widgetList<Icon>(
    find.descendant(of: card, matching: find.byType(Icon)),
  )) {
    if (i.color case final color?) out.add(color);
  }
  return out;
}

void main() {
  final unknownCases = [
    for (final c in sharedFixtureCases())
      if (c.verdict.status.json == 'unknown') c,
  ];

  test('the shared fixtures include unknown verdicts', () {
    expect(unknownCases, isNotEmpty);
  });

  for (final dark in [false, true]) {
    final palette = dark ? SnColors.dark : SnColors.light;
    for (final c in unknownCases.take(3)) {
      testWidgets('unknown card is never green: ${c.product}.${c.member} '
          '(${dark ? 'dark' : 'light'})', (t) async {
        await t.pumpWidget(
          MaterialApp(
            theme: dark ? buildDarkAppTheme() : buildAppTheme(),
            locale: const Locale('en'),
            localizationsDelegates: AppLocalizations.localizationsDelegates,
            supportedLocales: AppLocalizations.supportedLocales,
            home: Scaffold(
              body: SingleChildScrollView(
                child: VerdictCard(verdict: c.verdict),
              ),
            ),
          ),
        );
        final colors = paintedColors(t);
        expect(colors, contains(palette.verdictUnknown));
        expect(colors, isNot(contains(palette.verdictOk)));
        expect(colors, isNot(contains(palette.verdictOkSurface)));
        for (final color in colors) {
          expect(greenish(color), isFalse, reason: '$color');
        }
        final l10n = lookupAppLocalizations(const Locale('en'));
        expect(find.text(l10n.statusUnknown), findsOneWidget);
        expect(
          find.byIcon(VerdictBadge.iconFor('unknown')),
          findsOneWidget,
          reason: 'status is never shown by colour alone',
        );
      });
    }
  }
}
