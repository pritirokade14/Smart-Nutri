import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/section_header.dart';
import '../../meals/domain/meal_summary.dart';
import 'summary_display.dart';

/// The last 7 IST days for one member: one bar per nutrient per day. Sugar
/// and salt bars take the colour of the API's band for that day (an unknown
/// total is grey, never green); protein and kcal are neutral progress. The
/// limits note always shows; the incomplete note shows when any logged label
/// lacked a value.
class WeeklyDashboard extends StatelessWidget {
  const WeeklyDashboard({super.key, required this.summary});

  final MealSummary summary;

  static const incompleteNoteKey = Key('weekly-incomplete-note');
  static const limitsNoteKey = Key('weekly-limits-note');

  static Key barKey(SummaryNutrient n, DateTime day) => Key(
    'week-bar-${n.name}-${day.year}-${day.month.toString().padLeft(2, '0')}-'
    '${day.day.toString().padLeft(2, '0')}',
  );

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final s = summary;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SectionHeader(
              title: l10n.summaryTitleWeek,
              icon: Icons.bar_chart_rounded,
            ),
            for (final n in SummaryNutrient.values) _NutrientWeek(s, n),
            if (s.anyIncomplete)
              SummaryNote(key: incompleteNoteKey, text: l10n.summaryIncomplete),
            SummaryNote(
              key: limitsNoteKey,
              text: l10n.summaryLimitsNote,
              icon: Icons.pending_actions_rounded,
            ),
          ],
        ),
      ),
    );
  }
}

class _NutrientWeek extends StatelessWidget {
  const _NutrientWeek(this.summary, this.nutrient);

  final MealSummary summary;
  final SummaryNutrient nutrient;

  static const _barArea = SnTokens.space8 + SnTokens.space4;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final s = summary;
    final n = nutrient;
    if (s.isHidden(n)) {
      return Padding(
        padding: const EdgeInsets.only(bottom: SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(nutrientLabel(l10n, n), style: theme.textTheme.titleSmall),
            SummaryNote(text: l10n.diaryHiddenNumbers),
          ],
        ),
      );
    }
    final weekChip = hasLimitBand(n)
        ? shownBand(n, s.bands[n], s.totals[n])
        : null;
    // Scale only: the tallest of the day totals and the daily limit.
    final limit = s.limits[n];
    final scale = [
      ?limit,
      for (final d in s.days) ?d.totals[n],
    ].fold<num>(0, (a, b) => math.max(a, b));
    final weekday = DateFormat.E(l10n.localeName);
    return Padding(
      padding: const EdgeInsets.only(bottom: SnTokens.space4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  nutrientLabel(l10n, n),
                  style: theme.textTheme.titleSmall,
                ),
              ),
              if (weekChip != null) BandChip(band: weekChip),
            ],
          ),
          const SizedBox(height: SnTokens.space2),
          SizedBox(
            height: _barArea + SnTokens.space5,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                for (final d in s.days)
                  Expanded(
                    child: _DayBar(
                      key: ValueKey('${n.name}-${d.date}'),
                      nutrient: n,
                      day: d,
                      limit: limit,
                      scale: scale,
                      area: _barArea,
                      weekday: weekday.format(d.date),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DayBar extends StatelessWidget {
  const _DayBar({
    super.key,
    required this.nutrient,
    required this.day,
    required this.limit,
    required this.scale,
    required this.area,
    required this.weekday,
  });

  final SummaryNutrient nutrient;
  final SummaryDay day;
  final num? limit;
  final num scale;
  final double area;
  final String weekday;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final total = day.totals[nutrient];
    final band = shownBand(nutrient, day.bands[nutrient], total);
    // Limit-bearing nutrients use the band's verdict token; protein and kcal
    // are neutral progress; an unknown total is always the unknown token.
    final color = band != null ? bandTone(c, band).color : c.brand;
    final known = total != null && scale > 0;
    final height = known
        ? math.max(SnTokens.space1, area * (total / scale)).toDouble()
        : SnTokens.space1;
    final String detail;
    if (day.items == 0) {
      detail = l10n.summaryNothingLogged;
    } else if (total == null) {
      detail = l10n.summaryBandUnknown;
    } else {
      final t = formatAmount(total);
      final lim = limit;
      detail = switch (nutrient) {
        SummaryNutrient.kcal => l10n.summaryKcalTotal(t),
        SummaryNutrient.protein when lim != null => l10n.summaryProteinOfTarget(
          formatAmount(lim),
          t,
        ),
        _ when lim != null => l10n.summaryTotalOfLimit(formatAmount(lim), t),
        _ => l10n.historyItemAmount(t),
      };
    }
    final label = [
      weekday,
      detail,
      if (band != null && total != null) bandLabel(l10n, band),
    ].join(', ');
    return Semantics(
      label: label,
      excludeSemantics: true,
      child: Tooltip(
        message: label,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            Container(
              key: WeeklyDashboard.barKey(nutrient, day.date),
              width: SnTokens.space4,
              height: height,
              decoration: BoxDecoration(
                // Nothing logged: no bar, only a faint baseline.
                color: day.items == 0 ? null : color,
                border: day.items == 0 ? Border.all(color: c.border) : null,
                borderRadius: BorderRadius.circular(SnTokens.radiusSm),
              ),
            ),
            const SizedBox(height: SnTokens.space1),
            Text(
              weekday,
              maxLines: 1,
              overflow: TextOverflow.clip,
              style: Theme.of(
                context,
              ).textTheme.labelSmall?.copyWith(color: c.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}
