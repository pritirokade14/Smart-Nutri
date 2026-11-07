// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

/// A summary band exactly as the API sent it. Anything this build does not
/// recognise is [unknown] ("Not enough data"), never [ok].
enum Band {
  ok,
  near,
  over,
  unknown;

  static Band fromApi(NutrientBand band) => switch (band) {
    NutrientBand.ok => Band.ok,
    NutrientBand.near => Band.near,
    NutrientBand.over => Band.over,
    _ => Band.unknown,
  };
}

/// The four summary nutrients, in display order.
enum SummaryNutrient { sugars, salt, protein, kcal }

/// One value per [SummaryNutrient].
class PerNutrient<T> {
  const PerNutrient({
    required this.sugars,
    required this.salt,
    required this.protein,
    required this.kcal,
  });

  final T sugars;
  final T salt;
  final T protein;
  final T kcal;

  T operator [](SummaryNutrient n) => switch (n) {
    SummaryNutrient.sugars => sugars,
    SummaryNutrient.salt => salt,
    SummaryNutrient.protein => protein,
    SummaryNutrient.kcal => kcal,
  };
}

/// Totals as the screens may show them. `null` means unknown: nothing was
/// logged, or no logged item shows the value. It is never shown as 0.
typedef SummaryTotals = PerNutrient<num?>;

/// A total the screen can show, or null. Display rules only, no arithmetic:
/// - a nutrient the API sent as null (Ruling M1) stays null;
/// - nothing logged in the range gives null for every nutrient;
/// - an `incomplete` total of exactly 0 is unknown (the only logged values
///   were missing), never a known 0.
num? _shown(num? total, {required bool incomplete, required bool logged}) {
  if (!logged || total == null) return null;
  if (incomplete && total == 0) return null;
  return total;
}

SummaryTotals _totals(
  Totals t,
  IncompleteNutrients inc, {
  required bool logged,
}) {
  // `_shown` takes `num?`: the API is moving these to `number|null`.
  return SummaryTotals(
    sugars: _shown(t.sugarsG, incomplete: inc.sugarsG, logged: logged),
    salt: _shown(t.saltG, incomplete: inc.saltG, logged: logged),
    protein: _shown(t.proteinG, incomplete: inc.proteinG, logged: logged),
    kcal: _shown(t.energyKcal, incomplete: inc.energyKcal, logged: logged),
  );
}

PerNutrient<bool> _incomplete(IncompleteNutrients i) => PerNutrient(
  sugars: i.sugarsG,
  salt: i.saltG,
  protein: i.proteinG,
  kcal: i.energyKcal,
);

PerNutrient<Band> _bands(NutrientBands b) => PerNutrient(
  sugars: Band.fromApi(b.sugarG),
  salt: Band.fromApi(b.saltG),
  protein: Band.fromApi(b.proteinG),
  kcal: Band.fromApi(b.kcal),
);

/// One IST day of a summary.
class SummaryDay {
  const SummaryDay({
    required this.date,
    required this.items,
    required this.totals,
    required this.incomplete,
    required this.bands,
  });

  final DateTime date;
  final int items;
  final SummaryTotals totals;
  final PerNutrient<bool> incomplete;
  final PerNutrient<Band> bands;
}

/// `GET /v1/meals/summary` for display. Bands and limits are the API's; the
/// app never computes a band, a limit or a total.
class MealSummary {
  const MealSummary({
    required this.memberId,
    required this.period,
    required this.start,
    required this.end,
    required this.totals,
    required this.incomplete,
    required this.limits,
    required this.bands,
    required this.days,
    required this.pendingClinicianReview,
    this.proteinLeftG,
    this.proteinGPerKg,
    this.energyHidden = false,
    this.macrosHidden = false,
    this.proteinBasis,
    this.proteinTargetStatus,
  });

  factory MealSummary.fromApi(Summary s) {
    final days = [
      for (final d in s.days)
        SummaryDay(
          date: d.date,
          items: d.items,
          totals: _totals(d.totals, d.incomplete, logged: d.items > 0),
          incomplete: _incomplete(d.incomplete),
          bands: _bands(d.bands),
        ),
    ];
    return MealSummary(
      memberId: s.memberId,
      period: s.period,
      start: s.start,
      end: s.end,
      totals: _totals(
        s.totals,
        s.incomplete,
        logged: days.any((d) => d.items > 0),
      ),
      incomplete: _incomplete(s.incomplete),
      limits: PerNutrient(
        sugars: s.limits.sugarG,
        salt: s.limits.saltG,
        protein: s.limits.proteinTargetG,
        kcal: s.limits.kcal,
      ),
      bands: _bands(s.bands),
      days: days,
      pendingClinicianReview: s.pendingClinicianReview,
      proteinLeftG: s.proteinLeftG,
      proteinGPerKg: s.limits.proteinGPerKg,
      energyHidden: s.numbersHidden?.energy ?? false,
      macrosHidden: s.numbersHidden?.macros ?? false,
      proteinBasis: s.limits.proteinBasis,
      proteinTargetStatus: s.limits.proteinTargetStatus,
    );
  }

  final String memberId;
  final SummaryPeriod period;
  final DateTime start;
  final DateTime end;
  final SummaryTotals totals;
  final PerNutrient<bool> incomplete;

  /// Daily limits (sugar, salt), the protein target and kcal (always null in
  /// v1). Null means no limit for this member.
  final PerNutrient<num?> limits;
  final PerNutrient<Band> bands;
  final List<SummaryDay> days;
  final bool pendingClinicianReview;

  /// `period=day` only: how far today's protein is below the target, as the
  /// API calculated it; null without a target (or for a week).
  final num? proteinLeftG;

  /// The g per kg the API computed the protein target with (its YAML
  /// value), for the guide sentence; null whenever there is no target.
  /// Display only: never derived on the device.
  final num? proteinGPerKg;

  /// The API hid every energy number (`numbers_hidden.energy`): a null
  /// energy total is hidden, not unknown.
  final bool energyHidden;

  /// The API hid the macro, sugar and salt numbers and the protein target
  /// (`numbers_hidden.macros`).
  final bool macrosHidden;

  /// Which weight the protein target is based on (lean mass, adjusted
  /// weight, actual weight); null without a target.
  final DailyLimitsOutProteinBasis? proteinBasis;

  /// Why there is no protein target (`paused_pregnancy`, ...), null when
  /// the legacy rule applies or a target exists.
  final DailyLimitsOutProteinTargetStatus? proteinTargetStatus;

  /// Whether the API hid [n]'s numbers.
  bool isHidden(SummaryNutrient n) =>
      n == SummaryNutrient.kcal ? energyHidden : macrosHidden;

  /// Any nutrient on any day is missing from a logged label.
  bool get anyIncomplete => [
    incomplete,
    for (final d in days) d.incomplete,
  ].any((i) => SummaryNutrient.values.any((n) => i[n]));

  /// At least one item was logged in the range.
  bool get anyLogged => days.any((d) => d.items > 0);
}
