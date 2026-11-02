import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/core/theme/verdict_colors.dart';

bool greenish(Color c) {
  final hsv = HSVColor.fromColor(c);
  return hsv.hue >= 70 && hsv.hue <= 185 && hsv.saturation >= 0.08;
}

void main() {
  test('theme ColorScheme is not green-tinted', () {
    final s = buildAppTheme().colorScheme;
    expect(greenish(s.primary), isFalse);
    expect(greenish(s.secondary), isFalse);
    expect(greenish(s.tertiary), isFalse);
    expect(greenish(s.surfaceTint), isFalse);
  });

  test('unknown is not green and differs from ok', () {
    expect(greenish(verdictColor('unknown')), isFalse);
    expect(verdictColor('unknown'), isNot(verdictColor('ok')));
  });

  test('every status maps; unknown string throws', () {
    for (final s in ['ok', 'caution', 'unknown', 'avoid']) {
      verdictColor(s);
    }
    expect(() => verdictColor('green'), throwsArgumentError);
  });
}
