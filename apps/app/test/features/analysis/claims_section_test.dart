import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/analysis/domain/report.dart';
import 'package:smartnutri_ai/features/analysis/presentation/claims_section.dart';

import '../../support/fixtures.dart';

final en = lookupAppLocalizations(const Locale('en'));

Widget wrap(Widget child) => MaterialApp(
  locale: const Locale('en'),
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(body: SingleChildScrollView(child: child)),
);

void main() {
  group('claimChecks (read-only report accessor)', () {
    test('reads the fixture claim exactly as the API sent it', () {
      final checks = claimChecks(analyzeJson('sf_biscuit')['report']);
      expect(checks, hasLength(1));
      expect(checks.single.claim, 'sugar_free');
      expect(checks.single.verdict, 'contradicted');
      expect(checks.single.reasonCode, 'exceeds_limit');
      expect(checks.single.params, {'limit': 0.5, 'value': 2.0});
    });

    test('skips malformed entries and unknown claim verdicts', () {
      final checks = claimChecks({
        'claims': [
          {'claim': 'low_fat', 'verdict': 'great', 'reason_code': 'ok'},
          {'claim': 3, 'verdict': 'supported', 'reason_code': 'ok'},
          'nope',
          {'claim': 'low_fat', 'verdict': 'supported', 'reason_code': 'ok'},
        ],
      });
      expect(checks.map((c) => c.verdict), ['supported']);
    });

    test('no claims key or not a list: empty', () {
      expect(claimChecks(null), isEmpty);
      expect(claimChecks({'claims': 'x'}), isEmpty);
    });
  });

  group('ClaimsSection', () {
    testWidgets('shows the claim, the check result and the reason', (t) async {
      final checks = claimChecks(analyzeJson('sf_biscuit')['report']);
      await t.pumpWidget(wrap(ClaimsSection(checks: checks)));
      expect(find.text(en.productClaimsHeading), findsOneWidget);
      expect(find.text(en.productLabelSays(en.claimSugarFree)), findsOneWidget);
      expect(find.text(en.claimVerdictContradicted), findsOneWidget);
      expect(find.text(en.claimReasonExceedsLimit('0.5', '2')), findsOneWidget);
    });

    testWidgets('protein below minimum (oats fixture)', (t) async {
      final checks = claimChecks(analyzeJson('oats')['report']);
      await t.pumpWidget(wrap(ClaimsSection(checks: checks)));
      expect(
        find.text(en.productLabelSays(en.claimHighProtein)),
        findsOneWidget,
      );
      expect(
        find.text(en.claimReasonBelowMinimum('20', '13.368')),
        findsOneWidget,
      );
    });

    testWidgets('maps nutrient and joins ingredient params', (t) async {
      await t.pumpWidget(
        wrap(
          ClaimsSection(
            checks: claimChecks({
              'claims': [
                {
                  'claim': 'low_sugar',
                  'verdict': 'unverifiable',
                  'reason_code': 'nutrient_missing',
                  'params': {'nutrient': 'sugars_g'},
                },
                {
                  'claim': 'no_added_sugar',
                  'verdict': 'contradicted',
                  'reason_code': 'added_sugar_ingredient',
                  'params': {
                    'ingredients': ['sugar', 'jaggery'],
                  },
                },
              ],
            }),
          ),
        ),
      );
      expect(find.text(en.claimVerdictUnverifiable), findsOneWidget);
      expect(
        find.text(en.claimReasonNutrientMissing(en.nutrientSugarsG)),
        findsOneWidget,
      );
      expect(
        find.text(en.claimReasonAddedSugarIngredient('sugar, jaggery')),
        findsOneWidget,
      );
    });

    testWidgets('an unknown claim code is not shown; an unknown reason code '
        'shows the claim without a reason line', (t) async {
      await t.pumpWidget(
        wrap(
          ClaimsSection(
            checks: claimChecks({
              'claims': [
                {
                  'claim': 'organic',
                  'verdict': 'supported',
                  'reason_code': 'ok',
                },
                {
                  'claim': 'low_fat',
                  'verdict': 'supported',
                  'reason_code': 'brand_new_code',
                },
              ],
            }),
          ),
        ),
      );
      expect(find.textContaining('organic'), findsNothing);
      expect(find.text(en.productLabelSays(en.claimLowFat)), findsOneWidget);
      expect(find.text(en.claimVerdictSupported), findsOneWidget);
    });

    testWidgets('nothing to show: renders nothing', (t) async {
      await t.pumpWidget(wrap(const ClaimsSection(checks: [])));
      expect(find.text(en.productClaimsHeading), findsNothing);
    });
  });
}
