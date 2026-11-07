import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/features/history/presentation/day_summary_card.dart';
import 'package:smartnutri_ai/features/history/presentation/weekly_dashboard.dart';
import 'package:smartnutri_ai/features/meals/domain/meal_summary.dart';
import 'package:smartnutri_ai/features/protein/presentation/protein_progress.dart';
import 'package:smartnutri_api/src/export.dart';

import '../home/home_cards_test.dart' show daySummary;
import '../user_types/user_types_harness.dart' show en;

MealSummary _summary({
  bool hidden = false,
  String? basis,
  String? status,
  num? target = 119,
  num? perKg = 2,
  num? left = 99,
}) {
  final json =
      jsonDecode(
            jsonEncode(
              daySummary(
                'p1',
                hidden: hidden,
                proteinTarget: hidden ? null : target,
                proteinPerKg: hidden ? null : perKg,
                proteinLeft: hidden ? null : left,
              ),
            ),
          )
          as Map<String, Object?>;
  final limits = Map<String, Object?>.from(json['limits']! as Map)
    ..['protein_basis'] = basis
    ..['protein_target_status'] = status;
  json['limits'] = limits;
  return MealSummary.fromApi(Summary.fromJson(json));
}

Future<void> _pump(WidgetTester t, Widget child) async {
  t.view.physicalSize = const Size(900, 3600);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  await t.pumpWidget(
    MaterialApp(
      theme: buildAppTheme(),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(body: SingleChildScrollView(child: child)),
    ),
  );
}

void main() {
  testWidgets('history day hides totals when numbers_hidden', (t) async {
    await _pump(t, DaySummaryCard(summary: _summary(hidden: true)));
    // One note per hidden nutrient, never "Not enough data".
    expect(find.text(en.diaryHiddenNumbers), findsNWidgets(4));
    expect(find.text(en.summaryBandUnknown), findsNothing);
    expect(find.textContaining(RegExp(r'\d+ ?(g|kcal)')), findsNothing);
  });

  testWidgets('history week hides totals when numbers_hidden', (t) async {
    await _pump(t, WeeklyDashboard(summary: _summary(hidden: true)));
    expect(find.text(en.diaryHiddenNumbers), findsWidgets);
    expect(find.text(en.summaryBandUnknown), findsNothing);
  });

  testWidgets('shown totals still render without numbers_hidden', (t) async {
    await _pump(t, DaySummaryCard(summary: _summary()));
    expect(find.text(en.diaryHiddenNumbers), findsNothing);
  });

  testWidgets('protein card lean basis copy', (t) async {
    await _pump(t, ProteinProgress(summary: _summary(basis: 'lean_mass')));
    expect(find.text(en.proteinGuideLean('2', '119')), findsOneWidget);
  });

  testWidgets('protein card adjusted basis copy', (t) async {
    await _pump(
      t,
      ProteinProgress(summary: _summary(basis: 'adjusted_weight', perKg: 1.2)),
    );
    expect(find.text(en.proteinGuideAdjusted('1.2', '119')), findsOneWidget);
  });

  testWidgets('protein card actual basis keeps the plain guide', (t) async {
    await _pump(t, ProteinProgress(summary: _summary(basis: 'actual_weight')));
    expect(find.text(en.proteinGuide('2', '119')), findsOneWidget);
  });

  testWidgets('protein card paused for pregnancy', (t) async {
    await _pump(
      t,
      ProteinProgress(
        summary: _summary(
          status: 'paused_pregnancy',
          target: null,
          perKg: null,
          left: null,
        ),
        onAddDetails: () {},
      ),
    );
    expect(find.byKey(ProteinProgress.pausedKey), findsOneWidget);
    expect(find.text(en.targetsPregnancyPaused), findsOneWidget);
    expect(find.text(en.proteinNoTarget), findsNothing);
  });

  testWidgets('protein card hidden shows the note, no numbers', (t) async {
    await _pump(t, ProteinProgress(summary: _summary(hidden: true)));
    expect(find.byKey(ProteinProgress.hiddenKey), findsOneWidget);
    expect(find.text(en.diaryHiddenNumbers), findsOneWidget);
    expect(find.text(en.summaryBandUnknown), findsNothing);
    expect(find.byKey(ProteinProgress.noTargetKey), findsNothing);
  });
}
