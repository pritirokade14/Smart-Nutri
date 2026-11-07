import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/features/history/presentation/day_summary_card.dart';
import 'package:smartnutri_ai/features/history/presentation/weekly_dashboard.dart';
import 'package:smartnutri_ai/features/meals/domain/meal_summary.dart';
import 'package:smartnutri_api/src/export.dart';

final en = lookupAppLocalizations(const Locale('en'));
const c = SnColors.light;

Map<String, Object?> _fixtureJson() =>
    jsonDecode(
          File(
            '../../packages/test-fixtures/meals/expected/'
            'week_family.dad_diabetic.json',
          ).readAsStringSync(),
        )
        as Map<String, Object?>;

MealSummary _fixture() => MealSummary.fromApi(Summary.fromJson(_fixtureJson()));

Widget _wrap(Widget child) => MaterialApp(
  locale: const Locale('en'),
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(body: SingleChildScrollView(child: child)),
);

String _ymd(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-'
    '${d.month.toString().padLeft(2, '0')}-'
    '${d.day.toString().padLeft(2, '0')}';

Color? _barColor(WidgetTester t, SummaryNutrient n, DateTime day) {
  final box = t.widget<Container>(find.byKey(WeeklyDashboard.barKey(n, day)));
  return (box.decoration as BoxDecoration?)?.color;
}

/// A summary JSON as the API will send it after Ruling M1 (nullable totals).
Map<String, Object?> _summaryJson({
  required String period,
  required List<Map<String, Object?>> days,
  Map<String, Object?>? totals,
  Map<String, Object?>? bands,
  Map<String, Object?>? incomplete,
  Map<String, Object?>? limits,
}) => {
  'member_id': 'm1',
  'period': period,
  'start': days.first['date'],
  'end': days.last['date'],
  'totals':
      totals ??
      {
        'energy_kcal': 0,
        'sugars_g': 0,
        'salt_g': 0,
        'fat_g': null,
        'carbs_g': null,
        'fibre_g': null,
        'protein_g': 0,
      },
  'incomplete':
      incomplete ??
      {
        'energy_kcal': false,
        'sugars_g': false,
        'salt_g': false,
        'fat_g': false,
        'carbs_g': false,
        'fibre_g': false,
        'protein_g': false,
      },
  'limits':
      limits ??
      {'sugar_g': 25, 'salt_g': 5, 'protein_target_g': 58.1, 'kcal': null},
  'bands':
      bands ??
      {
        'sugar_g': 'unknown',
        'salt_g': 'unknown',
        'protein_g': 'unknown',
        'kcal': 'unknown',
      },
  'days': days,
  'pending_clinician_review': true,
};

Map<String, Object?> _day(
  String date, {
  int items = 1,
  Map<String, Object?>? totals,
  Map<String, Object?>? bands,
  Map<String, Object?>? incomplete,
}) => {
  'date': date,
  'items': items,
  'totals':
      totals ??
      {
        'energy_kcal': 100,
        'sugars_g': 5,
        'salt_g': 1,
        'fat_g': null,
        'carbs_g': null,
        'fibre_g': null,
        'protein_g': 3,
      },
  'incomplete':
      incomplete ??
      {
        'energy_kcal': false,
        'sugars_g': false,
        'salt_g': false,
        'fat_g': false,
        'carbs_g': false,
        'fibre_g': false,
        'protein_g': false,
      },
  'bands':
      bands ??
      {
        'sugar_g': 'ok',
        'salt_g': 'ok',
        'protein_g': 'unknown',
        'kcal': 'unknown',
      },
};

void main() {
  testWidgets('renders week_family for Dad', (t) async {
    final raw = _fixtureJson();
    final summary = _fixture();
    await t.pumpWidget(_wrap(WeeklyDashboard(summary: summary)));

    expect(find.text(en.summaryTitleWeek), findsOneWidget);
    // One bar per nutrient per day.
    for (final n in SummaryNutrient.values) {
      for (final d in summary.days) {
        expect(find.byKey(WeeklyDashboard.barKey(n, d.date)), findsOneWidget);
      }
    }
    expect(summary.days, hasLength(7));

    // Every day's sugar and salt bar uses the API band's token.
    final days = (raw['days']! as List).cast<Map<String, Object?>>();
    var sawOver = false;
    for (final d in days) {
      final date = DateTime.parse(d['date']! as String);
      final bands = (d['bands']! as Map).cast<String, String>();
      final items = d['items']! as int;
      for (final (n, key) in [
        (SummaryNutrient.sugars, 'sugar_g'),
        (SummaryNutrient.salt, 'salt_g'),
      ]) {
        final color = _barColor(t, n, date);
        final band = bands[key];
        if (band == 'over') {
          sawOver = true;
          expect(color, c.verdictAvoid, reason: '${_ymd(date)} $key over');
        }
        if (band == 'unknown' || items == 0) {
          expect(color, isNot(c.verdictOk), reason: 'unknown is never green');
        }
      }
    }
    expect(sawOver, isTrue, reason: 'the fixture has an over-limit sugar day');

    // The incomplete day (an OFF product without sugars) is never green and
    // never a known 0.
    final incompleteDay = summary.days.firstWhere((d) => d.incomplete.sugars);
    expect(incompleteDay.totals.sugars, isNull);
    expect(
      _barColor(t, SummaryNutrient.sugars, incompleteDay.date),
      isNot(c.verdictOk),
    );

    expect(find.byKey(WeeklyDashboard.incompleteNoteKey), findsOneWidget);
    expect(find.text(en.summaryIncomplete), findsOneWidget);
    expect(find.text(en.summaryLimitsNote), findsOneWidget);
  });

  test('days with nothing logged have no totals (never 0)', () {
    final summary = _fixture();
    for (final d in summary.days.where((d) => d.items == 0)) {
      for (final n in SummaryNutrient.values) {
        expect(d.totals[n], isNull, reason: '${_ymd(d.date)} $n');
      }
    }
  });

  testWidgets('limits note shows even with nothing incomplete', (t) async {
    final s = MealSummary.fromApi(
      Summary.fromJson(
        _summaryJson(
          period: 'week',
          days: [for (var i = 1; i <= 7; i++) _day('2026-11-0$i')],
        ),
      ),
    );
    await t.pumpWidget(_wrap(WeeklyDashboard(summary: s)));
    expect(find.text(en.summaryLimitsNote), findsOneWidget);
    expect(find.byKey(WeeklyDashboard.incompleteNoteKey), findsNothing);
  });

  testWidgets('an unknown or unrecognised band is never green', (t) async {
    final s = MealSummary.fromApi(
      Summary.fromJson(
        _summaryJson(
          period: 'week',
          days: [
            _day(
              '2026-11-01',
              bands: {
                'sugar_g': 'unknown',
                'salt_g': 'something_new',
                'protein_g': 'ok',
                'kcal': 'unknown',
              },
            ),
          ],
        ),
      ),
    );
    await t.pumpWidget(_wrap(WeeklyDashboard(summary: s)));
    final day = DateTime.parse('2026-11-01');
    expect(_barColor(t, SummaryNutrient.sugars, day), c.verdictUnknown);
    expect(_barColor(t, SummaryNutrient.salt, day), c.verdictUnknown);
    // Protein is progress towards a target, not a limit: never a verdict
    // colour.
    expect(
      _barColor(t, SummaryNutrient.protein, day),
      isNot(anyOf(c.verdictOk, c.verdictCaution, c.verdictAvoid)),
    );
  });

  group('DaySummaryCard', () {
    MealSummary day({
      Map<String, Object?>? totals,
      Map<String, Object?>? bands,
      Map<String, Object?>? incomplete,
      Map<String, Object?>? limits,
      int items = 2,
    }) => MealSummary.fromApi(
      Summary.fromJson(
        _summaryJson(
          period: 'day',
          totals: totals,
          bands: bands,
          incomplete: incomplete,
          limits: limits,
          days: [
            _day(
              '2026-11-03',
              items: items,
              totals: totals,
              bands: bands,
              incomplete: incomplete,
            ),
          ],
        ),
      ),
    );

    testWidgets('totals against limits with the API bands', (t) async {
      await t.pumpWidget(
        _wrap(
          DaySummaryCard(
            summary: day(
              totals: {
                'energy_kcal': 420,
                'sugars_g': 30,
                'salt_g': 2.5,
                'fat_g': null,
                'carbs_g': null,
                'fibre_g': null,
                'protein_g': 12,
              },
              bands: {
                'sugar_g': 'over',
                'salt_g': 'ok',
                'protein_g': 'ok',
                'kcal': 'unknown',
              },
            ),
          ),
        ),
      );
      expect(find.text(en.summaryTotalOfLimit('25', '30')), findsOneWidget);
      expect(find.text(en.summaryTotalOfLimit('5', '2.5')), findsOneWidget);
      expect(find.text(en.summaryBandOver), findsOneWidget);
      expect(find.text(en.summaryBandOk), findsOneWidget, reason: 'salt only');
      expect(
        find.text(en.summaryProteinOfTarget('58.1', '12')),
        findsOneWidget,
      );
      expect(find.text(en.summaryKcalTotal('420')), findsOneWidget);
      expect(find.text(en.summaryKcalInfo), findsOneWidget);
      expect(find.text(en.summaryLimitsNote), findsOneWidget);
      expect(find.text(en.commonDisclaimer), findsOneWidget);
    });

    testWidgets('protein never reads "Within limit", even when the band is '
        'ok', (t) async {
      await t.pumpWidget(
        _wrap(
          DaySummaryCard(
            summary: day(
              totals: {
                'energy_kcal': 100,
                'sugars_g': 1,
                'salt_g': 0.1,
                'fat_g': null,
                'carbs_g': null,
                'fibre_g': null,
                'protein_g': 2,
              },
              bands: {
                'sugar_g': 'unknown',
                'salt_g': 'unknown',
                'protein_g': 'ok',
                'kcal': 'unknown',
              },
            ),
          ),
        ),
      );
      expect(find.text(en.summaryBandOk), findsNothing);
      expect(find.text(en.summaryProteinOfTarget('58.1', '2')), findsOneWidget);
    });

    testWidgets('null totals (Ruling M1) read "Not enough data", never 0', (
      t,
    ) async {
      // The generated client cannot parse null totals until the contract is
      // regenerated, so build the display model directly.
      const nulls = SummaryTotals(
        sugars: null,
        salt: null,
        protein: null,
        kcal: null,
      );
      const all = PerNutrient(
        sugars: true,
        salt: true,
        protein: true,
        kcal: true,
      );
      // Even if a band said ok, an unknown total is not fine.
      const bands = PerNutrient(
        sugars: Band.ok,
        salt: Band.unknown,
        protein: Band.unknown,
        kcal: Band.unknown,
      );
      final s = MealSummary(
        memberId: 'm1',
        period: SummaryPeriod.day,
        start: DateTime(2026, 11, 3),
        end: DateTime(2026, 11, 3),
        totals: nulls,
        incomplete: all,
        limits: const PerNutrient(
          sugars: 25,
          salt: 5,
          protein: 58.1,
          kcal: null,
        ),
        bands: bands,
        days: [
          SummaryDay(
            date: DateTime(2026, 11, 3),
            items: 2,
            totals: nulls,
            incomplete: all,
            bands: bands,
          ),
        ],
        pendingClinicianReview: true,
      );
      await t.pumpWidget(_wrap(DaySummaryCard(summary: s)));
      expect(find.text(en.summaryBandUnknown), findsNWidgets(4));
      expect(find.text(en.summaryBandOk), findsNothing);
      expect(find.textContaining('0 g'), findsNothing);
      expect(find.text(en.summaryIncomplete), findsOneWidget);
    });

    testWidgets('no protein target: says so, no band', (t) async {
      await t.pumpWidget(
        _wrap(
          DaySummaryCard(
            summary: day(
              limits: {
                'sugar_g': 25,
                'salt_g': 5,
                'protein_target_g': null,
                'kcal': null,
              },
            ),
          ),
        ),
      );
      expect(find.text(en.summaryNoProteinTarget), findsOneWidget);
    });

    testWidgets('nothing logged', (t) async {
      await t.pumpWidget(_wrap(DaySummaryCard(summary: day(items: 0))));
      expect(find.text(en.summaryNothingLogged), findsOneWidget);
      expect(find.text(en.summaryBandOk), findsNothing);
      expect(find.text(en.summaryLimitsNote), findsOneWidget);
    });
  });
}
