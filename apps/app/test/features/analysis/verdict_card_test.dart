import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/tokens.g.dart';
import 'package:smartnutri_ai/core/theme/verdict_colors.dart';
import 'package:smartnutri_ai/features/analysis/domain/reasons.dart';
import 'package:smartnutri_ai/features/analysis/presentation/reason_line.dart';
import 'package:smartnutri_ai/features/analysis/presentation/verdict_card.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';

Widget wrap(Widget child, {String locale = 'en'}) => MaterialApp(
  locale: Locale(locale),
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(body: SingleChildScrollView(child: child)),
);

Color cardColor(WidgetTester t) {
  final badge = t.widget<Container>(find.byKey(VerdictCard.statusBadgeKey));
  return (badge.decoration! as BoxDecoration).color!;
}

String expectedStatusText(AppLocalizations l10n, String status) =>
    switch (status) {
      'ok' => l10n.statusOk,
      'caution' => l10n.statusCaution,
      'unknown' => l10n.statusUnknown,
      'avoid' => l10n.statusAvoid,
      _ => throw ArgumentError(status),
    };

void main() {
  final cases = sharedFixtureCases();

  test('fixtures cover every status', () {
    expect(cases.map((c) => c.verdict.status.json).toSet(), {
      'ok',
      'caution',
      'unknown',
      'avoid',
    });
  });

  for (final locale in ['en', 'hi', 'mr']) {
    for (final c in cases) {
      testWidgets('VerdictCard ${c.product}.${c.member} [$locale]', (t) async {
        await t.pumpWidget(
          wrap(VerdictCard(verdict: c.verdict), locale: locale),
        );
        final l10n = lookupAppLocalizations(Locale(locale));
        final status = c.verdict.status.json!;

        // The golden response agrees with the engine expectation.
        final expected = expectedFixture(c.product, c.member);
        expect(status, expected['status']);
        expect(
          c.verdict.reasons.map((r) => r.code).toList(),
          (expected['reasons'] as List).map((r) => (r as Map)['code']).toList(),
        );

        expect(find.text(expectedStatusText(l10n, status)), findsOneWidget);
        expect(find.text(c.verdict.memberName), findsOneWidget);
        expect(cardColor(t), verdictColor(status));
        if (status != 'ok') {
          expect(cardColor(t), isNot(SnTokens.verdictOk));
        }
        final groups = splitReasons(displayReasons(c.verdict.reasons));
        for (final r in groups.visible) {
          expect(find.text(reasonText(l10n, r)), findsWidgets);
        }
        expect(
          find.byKey(VerdictCard.reasonsToggleKey),
          // R23: with nothing always-visible, the first collapsed one shows.
          groups.collapsed.length > (groups.visible.isEmpty ? 1 : 0)
              ? findsOneWidget
              : findsNothing,
        );
        expect(t.takeException(), isNull);
      });
    }
  }

  testWidgets('unknown is grey, never the ok colour', (t) async {
    await t.pumpWidget(
      wrap(VerdictCard(verdict: fixtureVerdict('cola', 'no_age'))),
    );
    expect(cardColor(t), SnTokens.verdictUnknown);
    expect(cardColor(t), isNot(SnTokens.verdictOk));
  });

  testWidgets('empty member name shows "You"', (t) async {
    final v = fixtureVerdict('curd', 'milk_allergic_child');
    await t.pumpWidget(
      wrap(
        VerdictCard(
          verdict: VerdictOut(
            memberId: v.memberId,
            memberName: '',
            profileSetUp: true,
            reasons: v.reasons,
            status: v.status,
          ),
        ),
      ),
    );
    final l10n = lookupAppLocalizations(const Locale('en'));
    expect(find.text(l10n.resultYou), findsOneWidget);
  });

  testWidgets('a status the client does not know renders as unknown (grey)', (
    t,
  ) async {
    await t.pumpWidget(
      wrap(
        VerdictCard(
          verdict: VerdictOut.fromJson({
            'member_id': 'm',
            'member_name': 'Asha',
            'profile_set_up': true,
            'status': 'something_new',
            'reasons': [
              {'code': 'brand_new', 'severity': 'something_new', 'params': {}},
            ],
          }),
        ),
      ),
    );
    final l10n = lookupAppLocalizations(const Locale('en'));
    expect(find.text(l10n.statusUnknown), findsOneWidget);
    expect(cardColor(t), SnTokens.verdictUnknown);
    expect(t.takeException(), isNull);
  });

  testWidgets('collapsed reasons appear in API order after the toggle', (
    t,
  ) async {
    final v = fixtureVerdict('sf_biscuit', 'diabetic_adult');
    final l10n = lookupAppLocalizations(const Locale('en'));
    final groups = splitReasons(displayReasons(v.reasons));
    await t.pumpWidget(wrap(VerdictCard(verdict: v)));
    final hidden = [
      for (final r in groups.collapsed.skip(groups.visible.isEmpty ? 1 : 0))
        reasonText(l10n, r),
    ];
    for (final text in hidden) {
      expect(find.text(text), findsNothing);
    }
    if (hidden.isNotEmpty) {
      await t.tap(find.text(l10n.verdictShowAllReasons));
      await t.pumpAndSettle();
      final ys = [for (final text in hidden) t.getTopLeft(find.text(text)).dy];
      expect(ys, [...ys]..sort());
      expect(find.text(l10n.verdictHideReasons), findsOneWidget);
    }
  });

  group('R22 visibility', () {
    final l10n = lookupAppLocalizations(const Locale('en'));
    ReasonOut r(String code, Map<String, Object?> p, String sev) => ReasonOut(
      code: code,
      params: p,
      severity: ReasonOutSeverity.fromJson(sev),
    );
    VerdictOut v(List<ReasonOut> rs, {bool setUp = true}) => VerdictOut(
      memberId: 'm',
      memberName: 'Asha',
      profileSetUp: setUp,
      reasons: rs,
      status: VerdictOutStatus.avoid,
    );

    testWidgets('(a) two allergen avoid reasons both visible', (t) async {
      await t.pumpWidget(
        wrap(
          VerdictCard(
            verdict: v([
              r('allergen_contains', {'allergen': 'milk'}, 'avoid'),
              r('allergen_contains', {'allergen': 'peanut'}, 'avoid'),
            ]),
          ),
        ),
      );
      expect(
        find.text(l10n.reasonAllergenContains(l10n.allergenMilk)),
        findsOneWidget,
      );
      expect(
        find.text(l10n.reasonAllergenContains(l10n.allergenPeanut)),
        findsOneWidget,
      );
      expect(find.byKey(VerdictCard.reasonsToggleKey), findsNothing);
    });

    testWidgets('(b) avoid and allergen_unknown both visible', (t) async {
      await t.pumpWidget(
        wrap(
          VerdictCard(
            verdict: v([
              r('sugar_high', {'sugars_g': 30}, 'avoid'),
              r('allergen_unknown', {'allergen': 'peanut'}, 'unknown'),
            ]),
          ),
        ),
      );
      expect(find.text(l10n.reasonSugarHigh('30')), findsOneWidget);
      expect(
        find.text(l10n.reasonAllergenUnknown(l10n.allergenPeanut)),
        findsOneWidget,
      );
    });

    testWidgets('(c) age_unknown and allergen_unknown both visible', (t) async {
      await t.pumpWidget(
        wrap(
          VerdictCard(
            verdict: v([
              r('age_unknown', {}, 'unknown'),
              r('allergen_unknown', {'allergen': 'peanut'}, 'unknown'),
            ]),
          ),
        ),
      );
      expect(find.text(l10n.reasonAgeUnknown), findsOneWidget);
      expect(
        find.text(l10n.reasonAllergenUnknown(l10n.allergenPeanut)),
        findsOneWidget,
      );
    });

    testWidgets('(d) caution lines hidden until the toggle is tapped', (
      t,
    ) async {
      final energy = l10n.reasonEnergyDense('500');
      final score = l10n.reasonNutriscoreLow('D');
      await t.pumpWidget(
        wrap(
          VerdictCard(
            verdict: v([
              r('sugar_high', {'sugars_g': 30}, 'avoid'),
              r('energy_dense', {'energy_kcal': 500}, 'caution'),
              r('nutriscore_low', {'grade': 'D'}, 'caution'),
            ]),
          ),
        ),
      );
      expect(find.text(l10n.reasonSugarHigh('30')), findsOneWidget);
      expect(find.text(energy), findsNothing);
      expect(find.text(score), findsNothing);
      await t.tap(find.text(l10n.verdictShowAllReasons));
      await t.pumpAndSettle();
      expect(find.text(energy), findsOneWidget);
      expect(find.text(score), findsOneWidget);
      await t.tap(find.text(l10n.verdictHideReasons));
      await t.pumpAndSettle();
      expect(find.text(energy), findsNothing);
    });

    testWidgets('(e) caution-only card shows first reason, rest toggled', (
      t,
    ) async {
      final energy = l10n.reasonEnergyDense('500');
      final score = l10n.reasonNutriscoreLow('D');
      await t.pumpWidget(
        wrap(
          VerdictCard(
            verdict: v([
              r('energy_dense', {'energy_kcal': 500}, 'caution'),
              r('nutriscore_low', {'grade': 'D'}, 'caution'),
            ]),
          ),
        ),
      );
      expect(find.text(energy), findsOneWidget);
      expect(find.text(score), findsNothing);
      await t.tap(find.text(l10n.verdictShowAllReasons));
      await t.pumpAndSettle();
      expect(find.text(score), findsOneWidget);
    });

    testWidgets('single caution reason: visible, no toggle', (t) async {
      await t.pumpWidget(
        wrap(
          VerdictCard(
            verdict: v([
              r('energy_dense', {'energy_kcal': 500}, 'caution'),
            ]),
          ),
        ),
      );
      expect(find.text(l10n.reasonEnergyDense('500')), findsOneWidget);
      expect(find.byKey(VerdictCard.reasonsToggleKey), findsNothing);
    });

    testWidgets('unrecognised severity reason is visible', (t) async {
      await t.pumpWidget(
        wrap(
          VerdictCard(
            verdict: v([
              r('sugar_high', {'sugars_g': 30}, 'avoid'),
              ReasonOut.fromJson({
                'code': 'allergen_contains',
                'severity': 'something_new',
                'params': {'allergen': 'milk'},
              }),
              ReasonOut.fromJson({
                'code': 'energy_dense',
                'severity': 'something_new',
                'params': {'energy_kcal': 500},
              }),
            ]),
          ),
        ),
      );
      expect(find.text(l10n.reasonEnergyDense('500')), findsOneWidget);
      expect(find.byKey(VerdictCard.reasonsToggleKey), findsNothing);
    });

    testWidgets('allergen reason with caution severity is visible', (t) async {
      await t.pumpWidget(
        wrap(
          VerdictCard(
            verdict: v([
              r('sugar_high', {'sugars_g': 30}, 'avoid'),
              r('allergen_may_contain', {'allergen': 'milk'}, 'caution'),
            ]),
          ),
        ),
      );
      expect(
        find.text(l10n.reasonAllergenMayContain(l10n.allergenMilk)),
        findsOneWidget,
      );
    });

    testWidgets('toggle exposes expanded state to semantics', (t) async {
      final h = t.ensureSemantics();
      await t.pumpWidget(
        wrap(
          VerdictCard(
            verdict: v([
              r('sugar_high', {'sugars_g': 30}, 'avoid'),
              r('energy_dense', {'energy_kcal': 500}, 'caution'),
            ]),
          ),
        ),
      );
      final finder = find.byKey(VerdictCard.reasonsToggleSemanticsKey);
      expect(
        t.getSemantics(finder),
        isSemantics(isButton: true, hasExpandedState: true, isExpanded: false),
      );
      h.dispose();
    });

    testWidgets('profile not set up shows a neutral note', (t) async {
      await t.pumpWidget(wrap(VerdictCard(verdict: v([], setUp: false))));
      expect(find.text(l10n.verdictProfileNotSetUp), findsOneWidget);
      await t.pumpWidget(wrap(VerdictCard(verdict: v([]))));
      expect(find.text(l10n.verdictProfileNotSetUp), findsNothing);
    });

    testWidgets('unrenderable reason shows verdictReasonUnavailable', (
      t,
    ) async {
      await t.pumpWidget(
        wrap(VerdictCard(verdict: v([r('brand_new_code', {}, 'avoid')]))),
      );
      expect(find.text(l10n.verdictReasonUnavailable), findsOneWidget);
    });
  });

  testWidgets('duplicate nutrient_missing lines collapse to one', (t) async {
    final l10n = lookupAppLocalizations(const Locale('en'));
    ReasonOut missing(String rule) => ReasonOut(
      code: 'nutrient_missing',
      params: {'nutrient': 'salt', 'rule': rule},
      severity: ReasonOutSeverity.unknown,
    );
    await t.pumpWidget(
      wrap(
        VerdictCard(
          verdict: VerdictOut(
            memberId: 'm',
            memberName: 'Asha',
            profileSetUp: true,
            reasons: [
              const ReasonOut(
                code: 'sugar_high',
                params: {'sugars_g': 30},
                severity: ReasonOutSeverity.avoid,
              ),
              missing('hypertension'),
              missing('blood_sugar'),
            ],
            status: VerdictOutStatus.unknown,
          ),
        ),
      ),
    );
    expect(
      find.text(l10n.reasonNutrientMissing(l10n.nutrientSalt)),
      findsOneWidget,
    );
  });
}
