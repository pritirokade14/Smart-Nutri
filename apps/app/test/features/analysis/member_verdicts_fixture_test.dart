import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/core/theme/tokens.g.dart';
import 'package:smartnutri_ai/core/theme/verdict_colors.dart';
import 'package:smartnutri_ai/features/analysis/presentation/reason_line.dart';
import 'package:smartnutri_ai/features/analysis/presentation/verdict_card.dart';
import 'package:smartnutri_ai/shared/widgets/reason_list.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';

Widget wrap(Widget child, {String locale = 'en'}) => MaterialApp(
  theme: buildAppTheme(),
  locale: Locale(locale),
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(body: SingleChildScrollView(child: child)),
);

String statusLabel(AppLocalizations l, String status) => switch (status) {
  'ok' => l.statusOk,
  'caution' => l.statusCaution,
  'unknown' => l.statusUnknown,
  'avoid' => l.statusAvoid,
  _ => throw ArgumentError(status),
};

Color badgeColor(WidgetTester t) {
  final badge = t.widget<Container>(find.byKey(VerdictCard.statusBadgeKey));
  return (badge.decoration! as BoxDecoration).color!;
}

VerdictOut withJson(VerdictOut v, Map<String, Object?> changes) =>
    VerdictOut.fromJson({
      ...jsonDecode(jsonEncode(v.toJson())) as Map<String, Object?>,
      ...changes,
    });

ReasonOut reason(String code, String severity, [Map<String, Object?>? p]) =>
    ReasonOut.fromJson({'code': code, 'severity': severity, 'params': p ?? {}});

void main() {
  final cases = sharedFixtureCases();

  for (final locale in ['en', 'hi', 'mr']) {
    final l = lookupAppLocalizations(Locale(locale));
    for (final c in cases) {
      testWidgets('per-member card ${c.product}.${c.member} [$locale]', (
        t,
      ) async {
        final v = c.verdict;
        final status = v.status.json!;
        // The golden response still matches the engine's expectation.
        final expected = expectedFixture(c.product, c.member);
        expect(status, expected['status']);

        await t.pumpWidget(wrap(VerdictCard(verdict: v), locale: locale));

        // Colour token per status; unknown is never green.
        expect(badgeColor(t), verdictColor(status));
        if (status != 'ok') expect(badgeColor(t), isNot(SnTokens.verdictOk));
        if (status == 'unknown') {
          expect(find.text(l.statusUnknown), findsWidgets);
        }

        // Headline: "<status> for <name>" ("for you" for the primary).
        final label = statusLabel(l, status);
        expect(
          find.text(
            v.isPrimary
                ? l.verdictForYou(label)
                : l.verdictForMember(v.memberName, label),
          ),
          findsOneWidget,
        );

        // The first line is the engine's top reason, reasons[0].
        if (v.reasons.isNotEmpty) {
          final bullets = t.widgetList<ReasonBullet>(find.byType(ReasonBullet));
          expect(bullets.first.text, reasonText(l, v.reasons.first));
        }
        expect(t.takeException(), isNull);
      });
    }
  }

  testWidgets('the primary member reads "for you"', (t) async {
    final l = lookupAppLocalizations(const Locale('en'));
    final v = withJson(cases.first.verdict, {
      'is_primary': true,
      'relation': 'self',
      'member_name': 'Ravi',
    });
    await t.pumpWidget(wrap(VerdictCard(verdict: v)));
    final label = statusLabel(l, v.status.json!);
    expect(find.text(l.verdictForYou(label)), findsOneWidget);
    expect(find.text(l.verdictForMember('Ravi', label)), findsNothing);
  });

  testWidgets('reasons[0] shows first even when it would collapse (R22)', (
    t,
  ) async {
    final l = lookupAppLocalizations(const Locale('en'));
    final v = withJson(cases.first.verdict, {
      'status': 'caution',
      'reasons': [
        reason('sugar_moderate', 'caution', {'sugars_g': 12}).toJson(),
        reason('allergen_may_contain', 'caution', {
          'allergen': 'peanut',
        }).toJson(),
        reason('salt_moderate', 'caution', {'salt_g': 1.2}).toJson(),
      ],
    });
    await t.pumpWidget(wrap(VerdictCard(verdict: v)));
    final texts = [
      for (final b in t.widgetList<ReasonBullet>(find.byType(ReasonBullet)))
        b.text,
    ];
    // Top reason, then the always-visible allergen line; the rest collapse.
    expect(texts, [
      l.reasonSugarModerate('12'),
      l.reasonAllergenMayContain(l.allergenPeanut),
    ]);
    await t.tap(find.byKey(VerdictCard.reasonsToggleKey));
    await t.pump();
    expect(find.text(l.reasonSaltModerate('1.2')), findsOneWidget);
  });

  testWidgets('custom alert reasons render from alert.* labels', (t) async {
    final l = lookupAppLocalizations(const Locale('en'));
    final v = withJson(cases.first.verdict, {
      'status': 'unknown',
      'reasons': [
        reason('custom_alert_unknown', 'unknown', {
          'alerts': ['palm_oil', 'maida'],
        }).toJson(),
        reason('custom_alert', 'caution', {
          'alert': 'palm_oil',
          'ingredients': ['palmolein'],
        }).toJson(),
        reason('custom_alert', 'caution', {
          'alert': 'artificial_sweetener',
          'ingredients': <String>[],
        }).toJson(),
      ],
    });
    await t.pumpWidget(wrap(VerdictCard(verdict: v)));
    await t.tap(find.byKey(VerdictCard.reasonsToggleKey));
    await t.pump();
    expect(
      find.text(
        l.reasonCustomAlertUnknown('${l.alertPalmOil}, ${l.alertMaida}'),
      ),
      findsOneWidget,
    );
    expect(
      find.text(l.reasonCustomAlert(l.alertPalmOil, 'palmolein')),
      findsOneWidget,
    );
    expect(find.text(l.reasonVariantCustomAlertFlagOnly), findsOneWidget);
    expect(badgeColor(t), isNot(SnTokens.verdictOk));
  });
}
