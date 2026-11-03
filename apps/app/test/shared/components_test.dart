import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/core/theme/tokens.g.dart';
import 'package:smartnutri_ai/core/theme/verdict_colors.dart';
import 'package:smartnutri_ai/shared/widgets/buttons.dart';
import 'package:smartnutri_ai/shared/widgets/disclaimer_footer.dart';
import 'package:smartnutri_ai/shared/widgets/nutri_score_chip.dart';
import 'package:smartnutri_ai/shared/widgets/nutrient_row.dart';
import 'package:smartnutri_ai/shared/widgets/reason_list.dart';
import 'package:smartnutri_ai/shared/widgets/section_header.dart';
import 'package:smartnutri_ai/shared/widgets/states.dart';
import 'package:smartnutri_ai/shared/widgets/verdict_badge.dart';

final en = lookupAppLocalizations(const Locale('en'));

bool greenish(Color c) {
  final hsv = HSVColor.fromColor(c);
  return hsv.hue >= 70 && hsv.hue <= 185 && hsv.saturation >= 0.08;
}

Widget wrap(Widget child, {bool dark = false, String locale = 'en'}) =>
    MaterialApp(
      locale: Locale(locale),
      theme: dark ? buildDarkAppTheme() : buildAppTheme(),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(body: SingleChildScrollView(child: child)),
    );

/// Every colour the badge paints: its fill, its text and its icon.
List<Color> badgeColors(WidgetTester t) {
  final badge = find.byType(VerdictBadge);
  final box = t.widget<Container>(
    find.descendant(of: badge, matching: find.byType(Container)).first,
  );
  return [
    (box.decoration! as BoxDecoration).color!,
    for (final icon in t.widgetList<Icon>(
      find.descendant(of: badge, matching: find.byType(Icon)),
    ))
      icon.color!,
    for (final text in t.widgetList<Text>(
      find.descendant(of: badge, matching: find.byType(Text)),
    ))
      text.style!.color!,
  ];
}

void main() {
  group('VerdictBadge', () {
    for (final dark in [false, true]) {
      final palette = dark ? SnColors.dark : SnColors.light;
      for (final status in ['ok', 'caution', 'unknown', 'avoid']) {
        testWidgets('$status (${dark ? 'dark' : 'light'}): colour, icon and '
            'label', (t) async {
          await t.pumpWidget(wrap(VerdictBadge(status: status), dark: dark));
          final fill = badgeColors(t).first;
          expect(fill, verdictTone(palette, status).color);
          expect(find.byIcon(VerdictBadge.iconFor(status)), findsOneWidget);
          expect(find.text(verdictStatusLabel(en, status)), findsOneWidget);
        });
      }

      testWidgets('unknown is never green (${dark ? 'dark' : 'light'})', (
        t,
      ) async {
        await t.pumpWidget(
          wrap(const VerdictBadge(status: 'unknown'), dark: dark),
        );
        for (final c in badgeColors(t)) {
          expect(greenish(c), isFalse, reason: '$c');
        }
        expect(badgeColors(t).first, isNot(palette.verdictOk));
        expect(find.text(en.statusUnknown), findsOneWidget);
        expect(en.statusUnknown, 'Label unclear');
      });
    }

    testWidgets('an unrecognised status is shown as unknown, never ok', (
      t,
    ) async {
      await t.pumpWidget(wrap(const VerdictBadge(status: 'green')));
      expect(badgeColors(t).first, SnTokens.verdictUnknown);
      expect(find.text(en.statusUnknown), findsOneWidget);
      expect(find.byIcon(VerdictBadge.iconFor('unknown')), findsOneWidget);
    });

    test('each status has its own icon (never colour alone)', () {
      final icons = {
        for (final s in ['ok', 'caution', 'unknown', 'avoid'])
          VerdictBadge.iconFor(s),
      };
      expect(icons, hasLength(4));
    });

    testWidgets('the badge carries its label for screen readers', (t) async {
      final h = t.ensureSemantics();
      await t.pumpWidget(wrap(const VerdictBadge(status: 'avoid')));
      expect(find.bySemanticsLabel(en.statusAvoid), findsOneWidget);
      h.dispose();
    });
  });

  test('palettes: unknown and its tint are never green', () {
    for (final p in [SnColors.light, SnColors.dark]) {
      expect(greenish(p.verdictUnknown), isFalse);
      expect(greenish(p.verdictUnknownSurface), isFalse);
      expect(p.verdictUnknown, isNot(p.verdictOk));
    }
  });

  testWidgets('ReasonList shows every reason in order', (t) async {
    await t.pumpWidget(wrap(const ReasonList(reasons: ['first', 'second'])));
    expect(
      t.getTopLeft(find.text('first')).dy,
      lessThan(t.getTopLeft(find.text('second')).dy),
    );
  });

  group('NutriScoreChip', () {
    testWidgets('shows the grade tile and "calculated by SmartNutri"', (
      t,
    ) async {
      await t.pumpWidget(wrap(const NutriScoreChip(grade: 'C')));
      expect(
        find.descendant(
          of: find.byKey(NutriScoreChip.gradeTileKey),
          matching: find.text('C'),
        ),
        findsOneWidget,
      );
      expect(find.text(en.nutriscoreCalculatedBy), findsOneWidget);
    });

    testWidgets('no grade: says there is not enough data, shows no tile', (
      t,
    ) async {
      await t.pumpWidget(wrap(const NutriScoreChip(grade: null)));
      expect(find.text(en.nutriscoreInsufficientData), findsOneWidget);
      expect(find.byKey(NutriScoreChip.gradeTileKey), findsNothing);
    });
  });

  testWidgets('NutrientRow shows the value, or "not on the label"', (t) async {
    await t.pumpWidget(
      wrap(
        const Column(
          children: [
            NutrientRow(label: 'Protein (g)', value: '3.5'),
            NutrientRow(label: 'Salt (g)', value: null),
          ],
        ),
      ),
    );
    expect(find.text('3.5'), findsOneWidget);
    expect(find.text(en.resultNotOnLabel), findsOneWidget);
    expect(find.text('0'), findsNothing, reason: 'missing is never 0');
  });

  group('buttons', () {
    testWidgets('PrimaryButton is a FilledButton and calls back', (t) async {
      var taps = 0;
      await t.pumpWidget(
        wrap(PrimaryButton(label: 'Go', onPressed: () => taps++)),
      );
      await t.tap(find.widgetWithText(FilledButton, 'Go'));
      expect(taps, 1);
    });

    testWidgets('busy PrimaryButton is disabled', (t) async {
      await t.pumpWidget(
        wrap(PrimaryButton(label: 'Go', busy: true, onPressed: () {})),
      );
      expect(
        t.widget<FilledButton>(find.byType(FilledButton)).onPressed,
        isNull,
      );
    });

    testWidgets('SecondaryButton is an OutlinedButton', (t) async {
      var taps = 0;
      await t.pumpWidget(
        wrap(
          SecondaryButton(
            label: 'Back',
            icon: Icons.arrow_back,
            onPressed: () => taps++,
          ),
        ),
      );
      await t.tap(find.text('Back'));
      expect(taps, 1);
      expect(find.byType(OutlinedButton), findsOneWidget);
    });
  });

  testWidgets('SectionHeader shows title and trailing action', (t) async {
    await t.pumpWidget(
      wrap(SectionHeader(title: 'Recent', trailing: const Text('All'))),
    );
    expect(find.text('Recent'), findsOneWidget);
    expect(find.text('All'), findsOneWidget);
  });

  testWidgets('EmptyState shows icon, title, body and action', (t) async {
    await t.pumpWidget(
      wrap(
        EmptyState(
          icon: Icons.history,
          title: 'Nothing yet',
          body: 'Later',
          action: TextButton(onPressed: () {}, child: const Text('Act')),
        ),
      ),
    );
    expect(find.byIcon(Icons.history), findsOneWidget);
    expect(find.text('Nothing yet'), findsOneWidget);
    expect(find.text('Later'), findsOneWidget);
    expect(find.text('Act'), findsOneWidget);
  });

  group('ErrorState', () {
    testWidgets('shows the message and a retry that calls back', (t) async {
      var retries = 0;
      await t.pumpWidget(
        wrap(ErrorState(message: 'Network down', onRetry: () => retries++)),
      );
      expect(find.text('Network down'), findsOneWidget);
      await t.tap(find.text(en.commonRetry));
      expect(retries, 1);
    });

    testWidgets('no retry callback, no retry button', (t) async {
      await t.pumpWidget(wrap(const ErrorState(message: 'Bad code')));
      expect(find.text(en.commonRetry), findsNothing);
    });

    testWidgets('custom retry label', (t) async {
      await t.pumpWidget(
        wrap(
          ErrorState(message: 'x', onRetry: () {}, retryLabel: en.scanRetry),
        ),
      );
      expect(find.text(en.scanRetry), findsOneWidget);
    });
  });

  testWidgets('LoadingSkeleton announces loading and paints placeholders', (
    t,
  ) async {
    final h = t.ensureSemantics();
    await t.pumpWidget(wrap(const LoadingSkeleton(lines: 3)));
    expect(find.bySemanticsLabel(en.commonLoading), findsOneWidget);
    expect(find.byType(SkeletonBox), findsNWidgets(3));
    h.dispose();
  });

  for (final locale in ['en', 'hi', 'mr']) {
    testWidgets('DisclaimerFooter shows the i18n disclaimer ($locale)', (
      t,
    ) async {
      await t.pumpWidget(wrap(const DisclaimerFooter(), locale: locale));
      final l10n = lookupAppLocalizations(Locale(locale));
      expect(find.text(l10n.commonDisclaimer), findsOneWidget);
    });
  }
}
