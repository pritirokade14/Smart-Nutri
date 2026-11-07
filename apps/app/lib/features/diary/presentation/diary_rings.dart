import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../targets/domain/targets_format.dart';

/// The four rings of the day. Everything shown is what the API returned:
/// `remaining`, `progress` and `totals`. Nothing is added up, subtracted or
/// divided here (Ruling E13); a negative `remaining` is shown as "over" with
/// its absolute value, which is formatting.
enum RingNutrient { energy, protein, carbs, fat }

/// How one nutrient reads, decided only from API fields.
sealed class RingValue {
  const RingValue();
}

/// Hidden by the member's numbers setting: the fill shape only.
class RingHidden extends RingValue {
  const RingHidden();
}

/// Some entries lack this value: the grey chip, never a number.
class RingIncomplete extends RingValue {
  const RingIncomplete();
}

/// "X left" (>= 0) or "X over" (< 0, absolute value).
class RingRemaining extends RingValue {
  const RingRemaining(this.value);
  final num value;
}

/// What was eaten (a total the API summed).
class RingEaten extends RingValue {
  const RingEaten(this.value);
  final num value;
}

/// Nothing to show (no total, no target).
class RingNone extends RingValue {
  const RingNone();
}

num? _pick(Macro4? m, RingNutrient n) => m == null
    ? null
    : switch (n) {
        RingNutrient.energy => m.energyKcal,
        RingNutrient.protein => m.proteinG,
        RingNutrient.carbs => m.carbsG,
        RingNutrient.fat => m.fatG,
      };

bool ringHidden(DiaryDayOut d, RingNutrient n) =>
    n == RingNutrient.energy ? d.numbersHidden.energy : d.numbersHidden.macros;

bool ringIncomplete(DiaryDayOut d, RingNutrient n) => switch (n) {
  RingNutrient.energy => d.incomplete.energyKcal,
  RingNutrient.protein => d.incomplete.proteinG,
  RingNutrient.carbs => d.incomplete.carbsG,
  RingNutrient.fat => d.incomplete.fatG,
};

num? ringTotal(DiaryDayOut d, RingNutrient n) => switch (n) {
  RingNutrient.energy => d.totals.energyKcal,
  RingNutrient.protein => d.totals.proteinG,
  RingNutrient.carbs => d.totals.carbsG,
  RingNutrient.fat => d.totals.fatG,
};

/// Fill 0..1 from the API's `progress` (the shape for a hidden value too).
double? ringFill(DiaryDayOut d, RingNutrient n) {
  final p = _pick(d.progress, n);
  return p?.toDouble().clamp(0.0, 1.0);
}

/// Decides what [n] shows for [view]. Order matters: hidden first (no digit
/// leaves), then incomplete (never a number, never 0), then the API value.
RingValue ringValue(
  DiaryDayOut d,
  RingNutrient n,
  GoalSettingsOutSummaryView view,
) {
  if (ringHidden(d, n)) return const RingHidden();
  if (ringIncomplete(d, n)) return const RingIncomplete();
  if (view == GoalSettingsOutSummaryView.remaining) {
    final r = _pick(d.remaining, n);
    if (r != null) return RingRemaining(r);
  }
  final total = ringTotal(d, n);
  return total == null ? const RingNone() : RingEaten(total);
}

class DiaryRings extends StatelessWidget {
  const DiaryRings({
    super.key,
    required this.day,
    required this.view,
    this.onToggleView,
  });

  final DiaryDayOut day;
  final GoalSettingsOutSummaryView view;

  /// Null when there are no saved settings (the chip would have nothing to
  /// save to).
  final VoidCallback? onToggleView;

  static const toggleKey = Key('diary-view-toggle');
  static Key ringKey(RingNutrient n) => Key('diary-ring-${n.name}');
  static Key incompleteKey(RingNutrient n) => Key('diary-incomplete-${n.name}');
  static Key overKey(RingNutrient n) => Key('diary-over-${n.name}');

  String _label(AppLocalizations l10n, RingNutrient n) => switch (n) {
    RingNutrient.energy => l10n.targetsEnergy,
    RingNutrient.protein => l10n.targetsProtein,
    RingNutrient.carbs => l10n.targetsCarbs,
    RingNutrient.fat => l10n.targetsFat,
  };

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final remaining = view == GoalSettingsOutSummaryView.remaining;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    remaining ? l10n.diaryRemaining : l10n.diaryConsumed,
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                ),
                if (onToggleView != null)
                  ActionChip(
                    key: toggleKey,
                    label: Text(
                      remaining ? l10n.diaryConsumed : l10n.diaryRemaining,
                    ),
                    onPressed: onToggleView,
                  ),
              ],
            ),
            const SizedBox(height: SnTokens.space3),
            _EnergyRing(
              label: _label(l10n, RingNutrient.energy),
              value: ringValue(day, RingNutrient.energy, view),
              fill: ringFill(day, RingNutrient.energy),
            ),
            const SizedBox(height: SnTokens.space3),
            for (final n in const [
              RingNutrient.protein,
              RingNutrient.carbs,
              RingNutrient.fat,
            ])
              _MacroBar(
                nutrient: n,
                label: _label(l10n, n),
                value: ringValue(day, n, view),
                fill: ringFill(day, n),
                track: c.muted,
              ),
          ],
        ),
      ),
    );
  }
}

String _valueText(AppLocalizations l10n, RingNutrient n, RingValue v) {
  String unit(num x) => n == RingNutrient.energy
      ? l10n.targetsKcalValue(formatDecimal(x))
      : gramsText(l10n, x);
  return switch (v) {
    RingRemaining(:final value) =>
      value < 0
          ? l10n.diaryOver(unit(value.abs()))
          : l10n.diaryLeft(unit(value)),
    RingEaten(:final value) => unit(value),
    _ => '',
  };
}

Widget _valueWidget(
  BuildContext context,
  RingNutrient n,
  RingValue v, {
  TextStyle? style,
}) {
  final l10n = AppLocalizations.of(context);
  final c = SnColors.of(context);
  return switch (v) {
    RingIncomplete() => Container(
      key: DiaryRings.incompleteKey(n),
      padding: const EdgeInsets.symmetric(
        horizontal: SnTokens.space2,
        vertical: SnTokens.space1,
      ),
      decoration: BoxDecoration(
        color: c.muted,
        borderRadius: BorderRadius.circular(SnTokens.radiusFull),
      ),
      child: Text(
        l10n.diaryIncomplete,
        style: Theme.of(
          context,
        ).textTheme.bodySmall?.copyWith(color: c.textSecondary),
      ),
    ),
    RingRemaining(:final value) => Text(
      _valueText(l10n, n, v),
      key: value < 0 ? DiaryRings.overKey(n) : null,
      // Over is neutral: the same text colour, never a verdict colour.
      style: style?.copyWith(color: c.textPrimary),
    ),
    RingEaten() => Text(_valueText(l10n, n, v), style: style),
    _ => const SizedBox.shrink(),
  };
}

class _EnergyRing extends StatelessWidget {
  const _EnergyRing({
    required this.label,
    required this.value,
    required this.fill,
  });

  final String label;
  final RingValue value;
  final double? fill;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    final theme = Theme.of(context);
    return Row(
      key: DiaryRings.ringKey(RingNutrient.energy),
      children: [
        SizedBox(
          width: 96,
          height: 96,
          child: CircularProgressIndicator(
            value: fill ?? 0,
            strokeWidth: 10,
            color: c.brand,
            backgroundColor: c.muted,
          ),
        ),
        const SizedBox(width: SnTokens.space4),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: theme.textTheme.titleSmall),
              const SizedBox(height: SnTokens.space1),
              _valueWidget(
                context,
                RingNutrient.energy,
                value,
                style: theme.textTheme.titleLarge,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _MacroBar extends StatelessWidget {
  const _MacroBar({
    required this.nutrient,
    required this.label,
    required this.value,
    required this.fill,
    required this.track,
  });

  final RingNutrient nutrient;
  final String label;
  final RingValue value;
  final double? fill;
  final Color track;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    final theme = Theme.of(context);
    return Padding(
      key: DiaryRings.ringKey(nutrient),
      padding: const EdgeInsets.symmetric(vertical: SnTokens.space1),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Text(label, style: theme.textTheme.bodyMedium),
              const SizedBox(width: SnTokens.space3),
              Expanded(
                child: Align(
                  alignment: AlignmentDirectional.centerEnd,
                  child: _valueWidget(
                    context,
                    nutrient,
                    value,
                    style: theme.textTheme.bodyMedium,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: SnTokens.space1),
          if (fill != null && value is! RingIncomplete)
            LinearProgressIndicator(
              value: fill,
              color: c.brand,
              backgroundColor: track,
              minHeight: 6,
              borderRadius: BorderRadius.circular(SnTokens.radiusFull),
            ),
        ],
      ),
    );
  }
}
