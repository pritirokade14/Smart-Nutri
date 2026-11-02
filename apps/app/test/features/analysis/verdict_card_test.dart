import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/tokens.g.dart';
import 'package:smartnutri_ai/core/theme/verdict_colors.dart';
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
        if (c.verdict.reasons.isNotEmpty) {
          expect(find.text(topReasonText(l10n, c.verdict)), findsOneWidget);
        }
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

  testWidgets('extra reasons are listed in API order when expanded', (t) async {
    final v = fixtureVerdict('sf_biscuit', 'diabetic_adult');
    final l10n = lookupAppLocalizations(const Locale('en'));
    await t.pumpWidget(wrap(VerdictCard(verdict: v)));
    final rest = v.reasons.skip(1).map((r) => reasonText(l10n, r)).toList();
    for (final text in rest) {
      expect(find.text(text), findsNothing);
    }
    await t.tap(find.text(topReasonText(l10n, v)));
    await t.pumpAndSettle();
    final ys = [for (final text in rest) t.getTopLeft(find.text(text)).dy];
    expect(ys, [...ys]..sort());
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
    await t.tap(find.text(l10n.reasonSugarHigh('30')));
    await t.pumpAndSettle();
    expect(
      find.text(l10n.reasonNutrientMissing(l10n.nutrientSalt)),
      findsOneWidget,
    );
  });
}
