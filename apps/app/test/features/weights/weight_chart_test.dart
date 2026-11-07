import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/features/weights/presentation/weight_chart.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';

Future<WeightChartPainter> _pump(WidgetTester t, WeightTrendOut trend) async {
  await t.pumpWidget(
    MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      theme: ThemeData(extensions: const [SnColors.light]),
      home: Scaffold(
        body: SizedBox(width: 400, child: WeightChart(trend: trend)),
      ),
    ),
  );
  final paint = t.widget<CustomPaint>(find.byKey(WeightChart.chartKey));
  return paint.painter! as WeightChartPainter;
}

void main() {
  testWidgets('outlier drawn hollow', (t) async {
    final trend = weightTrendFixture('single_outlier');
    final painter = await _pump(t, trend);
    final hollow = [for (final d in painter.layout.dots) d.hollow];
    expect(hollow, [for (final p in trend.points) p.outlier]);
    expect(hollow, contains(true));
    expect(hollow, contains(false));
    expect(
      painter.outlierLabel,
      lookupAppLocalizations(const Locale('en')).weightOutlier,
    );
  });

  testWidgets('line uses brand token not danger', (t) async {
    final painter = await _pump(t, weightTrendFixture('weekly_rate_loss'));
    final c = SnColors.light;
    expect(painter.lineColor, c.brand);
    for (final bad in [c.verdictAvoid, c.verdictCaution, c.verdictUnknown]) {
      expect(painter.lineColor, isNot(bad));
      expect(painter.dotColor, isNot(bad));
    }
  });

  testWidgets('draws from y only', (t) async {
    // The same shape under hide_all: no kilograms, the y values drive it.
    final trend = weightTrendFixture('hide_all');
    expect(trend.points.every((p) => p.weightKg == null), isTrue);
    final painter = await _pump(t, trend);
    expect(painter.layout.dots.map((d) => d.y), [
      for (final p in trend.points) p.y!.toDouble(),
    ]);
    expect(painter.layout.line.map((o) => o.dy), [
      for (final p in trend.trend) p.y!.toDouble(),
    ]);
    expect(painter.layout.dots.every((d) => d.kg == null), isTrue);
    expect(find.byKey(WeightChart.axisMaxKey), findsNothing);
    expect(find.byKey(WeightChart.axisMinKey), findsNothing);
  });

  testWidgets('axis labels appear only with kilograms', (t) async {
    await _pump(t, weightTrendFixture('weekly_rate_loss'));
    expect(find.byKey(WeightChart.axisMaxKey), findsOneWidget);
    expect(find.text('80'), findsOneWidget);
    expect(find.text('79'), findsOneWidget);
  });
}
