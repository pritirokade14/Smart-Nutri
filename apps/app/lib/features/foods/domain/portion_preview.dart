/// The portion preview (Plan 12, G14): `quantity x gramsPerUnit x per100 /
/// 100`, rounded half-up to 1 decimal. This is the app's only nutrient
/// arithmetic and it is an estimate: the saved values come from the API.
///
/// The maths is exact decimal (BigInt mantissa and scale from each number's
/// `toString()`), so `1.15` rounds to `1.2` and never `1.1`.
library;

/// One 1-dp string per nutrient key; null stays null (never 0).
typedef NutrientPreview = Map<String, String?>;

class _Dec {
  const _Dec(this.mantissa, this.scale);

  final BigInt mantissa;
  final int scale;

  /// Parses `toString()` of a finite number ("12", "0.04", "1.5e-7").
  factory _Dec.of(num value) {
    var s = value.toString().toLowerCase();
    var exp = 0;
    final e = s.indexOf('e');
    if (e >= 0) {
      exp = int.parse(s.substring(e + 1));
      s = s.substring(0, e);
    }
    final dot = s.indexOf('.');
    final digits = dot < 0 ? s : s.replaceFirst('.', '');
    final frac = dot < 0 ? 0 : s.length - dot - 1;
    return _Dec(BigInt.parse(digits), frac - exp);
  }
}

/// [per100] values scaled to `quantity x gramsPerUnit`, to 1 dp.
NutrientPreview previewPortion(
  Map<String, num?> per100,
  num quantity,
  num gramsPerUnit,
) {
  final q = _Dec.of(quantity);
  final g = _Dec.of(gramsPerUnit);
  return {
    for (final entry in per100.entries)
      entry.key: entry.value == null ? null : _scale(entry.value!, q, g),
  };
}

String _scale(num per100, _Dec q, _Dec g) {
  final p = _Dec.of(per100);
  final negative = p.mantissa.isNegative;
  final mantissa = q.mantissa * g.mantissa * p.mantissa.abs();
  // / 100 adds two to the scale.
  final scale = q.scale + g.scale + p.scale + 2;
  final BigInt tenths;
  if (scale <= 1) {
    tenths = mantissa * BigInt.from(10).pow(1 - scale);
  } else {
    final div = BigInt.from(10).pow(scale - 1);
    // Half-up: floor((2m + d) / 2d).
    tenths = (mantissa * BigInt.two + div) ~/ (div * BigInt.two);
  }
  final whole = tenths ~/ BigInt.from(10);
  final dec = (tenths % BigInt.from(10)).toInt();
  return '${negative && tenths != BigInt.zero ? '-' : ''}$whole.$dec';
}
