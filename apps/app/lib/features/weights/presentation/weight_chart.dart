import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../targets/domain/targets_format.dart';

/// One raw weigh-in on the chart, in 0..1 coordinates.
class ChartDot {
  const ChartDot({
    required this.date,
    required this.x,
    required this.y,
    required this.hollow,
    this.kg,
  });

  final DateTime date;

  /// 0 (left, the range start) to 1 (right, the range end).
  final double x;

  /// The API's `y`: 1 is the top, 0 the bottom.
  final double y;

  /// An outlier (left out of the trend) is drawn as a ring.
  final bool hollow;

  /// Only for the accessibility label; null when numbers are hidden.
  final num? kg;
}

/// Where the dots and the line go. Positions come only from the API's `y`
/// (a point without one is skipped); the dates give the horizontal spacing.
class ChartLayout {
  const ChartLayout({required this.dots, required this.line});

  final List<ChartDot> dots;

  /// The trend line as (x, y) pairs in 0..1.
  final List<Offset> line;

  static ChartLayout of(WeightTrendOut t) {
    final start = t.from.millisecondsSinceEpoch;
    final span = (t.to.millisecondsSinceEpoch - start).abs();
    double x(DateTime d) => span == 0
        ? 0.5
        : ((d.millisecondsSinceEpoch - start) / span).clamp(0.0, 1.0);
    return ChartLayout(
      dots: [
        for (final p in t.points)
          if (p.y != null)
            ChartDot(
              date: p.date,
              x: x(p.date),
              y: p.y!.toDouble().clamp(0.0, 1.0),
              hollow: p.outlier,
              kg: t.numbersHidden ? null : p.weightKg,
            ),
      ],
      line: [
        for (final p in t.trend)
          if (p.y != null) Offset(x(p.date), p.y!.toDouble().clamp(0.0, 1.0)),
      ],
    );
  }
}

/// The weigh-ins as dots and the trend as a line. The brand colour is the
/// line and a neutral one the dots; no verdict or danger colour is used.
/// With hidden numbers the shape stays and there are no axis labels.
class WeightChart extends StatelessWidget {
  const WeightChart({super.key, required this.trend});

  final WeightTrendOut trend;

  static const chartKey = Key('weight-chart');
  static const axisMaxKey = Key('weight-axis-max');
  static const axisMinKey = Key('weight-axis-min');

  /// The highest and lowest kg the API sent, for the two axis labels; null
  /// when numbers are hidden or there are none.
  (num, num)? get _range {
    if (trend.numbersHidden) return null;
    final kgs = <num>[
      for (final p in trend.points)
        if (p.weightKg != null) p.weightKg!,
      for (final p in trend.trend)
        if (p.trendKg != null) p.trendKg!,
    ];
    if (kgs.isEmpty) return null;
    kgs.sort();
    return (kgs.first, kgs.last);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final theme = Theme.of(context);
    final layout = ChartLayout.of(trend);
    final range = _range;
    final labelStyle = theme.textTheme.bodySmall?.copyWith(
      color: c.textSecondary,
    );
    return Semantics(
      container: true,
      label: l10n.weightTitle,
      child: SizedBox(
        height: 180,
        child: Row(
          children: [
            if (range != null)
              Padding(
                padding: const EdgeInsets.only(right: SnTokens.space2),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      formatDecimal(range.$2),
                      key: axisMaxKey,
                      style: labelStyle,
                    ),
                    Text(
                      formatDecimal(range.$1),
                      key: axisMinKey,
                      style: labelStyle,
                    ),
                  ],
                ),
              ),
            Expanded(
              child: CustomPaint(
                key: chartKey,
                painter: WeightChartPainter(
                  layout: layout,
                  lineColor: c.brand,
                  dotColor: c.textSecondary,
                  gridColor: c.border,
                  outlierLabel: l10n.weightOutlier,
                  textDirection: Directionality.of(context),
                  dotLabel: (dot) => dot.kg == null
                      ? l10n.weightTitle
                      : l10n.weightKgValue(formatDecimal(dot.kg!)),
                ),
                size: Size.infinite,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class WeightChartPainter extends CustomPainter {
  WeightChartPainter({
    required this.layout,
    required this.lineColor,
    required this.dotColor,
    required this.gridColor,
    required this.outlierLabel,
    required this.dotLabel,
    required this.textDirection,
  });

  final ChartLayout layout;
  final Color lineColor;
  final Color dotColor;
  final Color gridColor;
  final String outlierLabel;
  final String Function(ChartDot dot) dotLabel;
  final TextDirection textDirection;

  static const _pad = SnTokens.space2;
  static const _radius = 4.0;

  Offset _at(Size size, double x, double y) => Offset(
    _pad + x * (size.width - 2 * _pad),
    _pad + (1 - y) * (size.height - 2 * _pad),
  );

  @override
  void paint(Canvas canvas, Size size) {
    final grid = Paint()
      ..color = gridColor
      ..strokeWidth = 1;
    canvas.drawLine(
      Offset(0, size.height - 1),
      Offset(size.width, size.height - 1),
      grid,
    );
    if (layout.line.length > 1) {
      final path = Path();
      for (var i = 0; i < layout.line.length; i++) {
        final p = _at(size, layout.line[i].dx, layout.line[i].dy);
        i == 0 ? path.moveTo(p.dx, p.dy) : path.lineTo(p.dx, p.dy);
      }
      canvas.drawPath(
        path,
        Paint()
          ..color = lineColor
          ..style = PaintingStyle.stroke
          ..strokeWidth = 3
          ..strokeJoin = StrokeJoin.round,
      );
    }
    for (final d in layout.dots) {
      final p = _at(size, d.x, d.y);
      canvas.drawCircle(
        p,
        _radius,
        Paint()
          ..color = dotColor
          ..style = d.hollow ? PaintingStyle.stroke : PaintingStyle.fill
          ..strokeWidth = 2,
      );
    }
  }

  @override
  SemanticsBuilderCallback get semanticsBuilder =>
      (size) => [
        for (final d in layout.dots)
          CustomPainterSemantics(
            rect: Rect.fromCircle(center: _at(size, d.x, d.y), radius: 8),
            properties: SemanticsProperties(
              textDirection: textDirection,
              label: d.hollow ? '${dotLabel(d)}, $outlierLabel' : dotLabel(d),
            ),
          ),
      ];

  @override
  bool shouldRepaint(WeightChartPainter oldDelegate) =>
      oldDelegate.layout != layout ||
      oldDelegate.lineColor != lineColor ||
      oldDelegate.dotColor != dotColor;

  @override
  bool shouldRebuildSemantics(WeightChartPainter oldDelegate) =>
      oldDelegate.layout != layout;
}
