import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/features/targets/presentation/targets_explanation.dart';
import 'package:smartnutri_ai/features/weights/presentation/progress_view.dart';
import 'package:smartnutri_ai/features/weights/presentation/weight_list.dart';

import '../../support/fixtures.dart';
import 'weights_harness.dart';

void main() {
  testWidgets('renders weights/expected weekly_rate_loss', (t) async {
    final env = WeightsEnv();
    await pumpWeights(t, env);
    final rate = env.weights.trend.weeklyRate!;
    expect(
      find.text(en.weightWeeklyRate('${rate.kg}', '${rate.pctBw}')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('weight-chart')), findsOneWidget);
    expect(find.text(en.weightTrend), findsOneWidget);
    expect(find.text(en.diaryDisclaimer), findsOneWidget);
    expect(find.byKey(ProgressView.pendingReviewKey), findsOneWidget);
    // The list shows the API's kilograms, newest first.
    expect(find.byKey(WeightList.tileKey('2026-01-10')), findsOneWidget);
    expect(find.textContaining('79 kg'), findsWidgets);
  });

  group('projection only when ready', () {
    testWidgets('ready shows the API date and target', (t) async {
      await pumpWeights(t, WeightsEnv(trend: 'projection_ready'));
      expect(find.byKey(ProgressView.projectionKey), findsOneWidget);
      expect(find.textContaining('75 kg'), findsWidgets);
      expect(find.byKey(ProgressView.noProjectionKey), findsNothing);
    });

    for (final (stem, copy) in [
      ('projection_too_few', en.weightNoProjectionTooFewWeighIns),
      ('projection_moving_away', en.weightNoProjectionMovingAway),
      ('no_target', en.weightNoProjectionNoTarget),
      ('projection_too_far', en.weightNoProjectionTooFar),
      ('projection_reached', en.weightNoProjectionReached),
    ]) {
      testWidgets('$stem shows its reason', (t) async {
        await pumpWeights(t, WeightsEnv(trend: stem));
        expect(find.byKey(ProgressView.projectionKey), findsNothing);
        expect(find.text(copy), findsOneWidget);
      });
    }
  });

  testWidgets('rapid loss card neutral', (t) async {
    final env = WeightsEnv(trend: 'rapid_loss_three_weeks');
    await pumpWeights(t, env);
    final card = find.byKey(ProgressView.rapidLossKey);
    expect(card, findsOneWidget);
    // The API's percentage goes into the string.
    expect(find.text(en.weightRapidLoss('1.5')), findsOneWidget);
    final container = find.descendant(
      of: card,
      matching: find.byType(Container),
    );
    final box = t.widget<Container>(container).decoration! as BoxDecoration;
    final c = SnColors.light;
    expect(box.color, c.muted);
    expect(box.color, isNot(c.verdictAvoid));
    expect(box.color, isNot(c.verdictCautionSurface));
  });

  testWidgets('hide_all leaves no digits on progress', (t) async {
    final env = WeightsEnv(trend: 'hide_all');
    await pumpWeights(t, env);
    expect(find.byKey(const Key('weight-chart')), findsOneWidget);
    expect(find.byKey(const Key('weight-axis-max')), findsNothing);
    final chips = find.byType(ChoiceChip);
    final inChips = {
      for (final w in t.widgetList<Text>(
        find.descendant(of: chips, matching: find.byType(Text)),
      ))
        w.data,
    };
    final date = RegExp(r'[A-Z][a-z]{2} \d{1,2}, \d{4}');
    for (final s in texts(t)) {
      if (inChips.contains(s)) continue;
      expect(s.replaceAll(date, ''), isNot(matches(r'\d')), reason: s);
      expect(s, isNot(contains('kg')), reason: s);
    }
  });

  testWidgets('consent card without health_data', (t) async {
    final env = WeightsEnv(consents: {'terms'});
    await pumpWeights(t, env);
    expect(find.byKey(ProgressView.consentKey), findsOneWidget);
    expect(find.text(en.weightConsent), findsOneWidget);
    expect(find.byKey(const Key('weight-chart')), findsNothing);
    expect(find.byKey(ProgressView.addKey), findsNothing);
    expect(env.weights.trendDays, isEmpty);
  });

  testWidgets('no streak or rating text', (t) async {
    await pumpWeights(t, WeightsEnv(trend: 'rapid_loss_three_weeks'));
    final all = texts(t).join(' ').toLowerCase();
    for (final w in ['streak', 'rating', 'score', 'great job', 'well done']) {
      expect(all, isNot(contains(w)));
    }
  });

  testWidgets('taper note comes from todays targets', (t) async {
    final env = WeightsEnv(targets: 'g5_taper_trend');
    await pumpWeights(t, env);
    expect(find.byKey(ProgressView.flagKey('taper_active')), findsOneWidget);
    expect(find.text(en.targetsFlagTaperActive), findsOneWidget);
  });

  testWidgets('how we got this names the weight source', (t) async {
    await t.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        home: Scaffold(
          body: TargetsExplanationTile(targetsFixture('g5_taper_trend')),
        ),
      ),
    );
    await t.tap(find.byKey(TargetsExplanationTile.tileKey));
    await t.pumpAndSettle();
    expect(find.text(en.targetsHowWeightTrend('76.2')), findsOneWidget);
  });
}
