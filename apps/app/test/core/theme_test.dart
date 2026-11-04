import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/core/theme/verdict_colors.dart';

bool greenish(Color c) {
  final hsv = HSVColor.fromColor(c);
  return hsv.hue >= 70 && hsv.hue <= 185 && hsv.saturation >= 0.08;
}

void main() {
  test('theme ColorScheme is not green-tinted (light and dark)', () {
    for (final theme in [buildAppTheme(), buildDarkAppTheme()]) {
      final s = theme.colorScheme;
      expect(greenish(s.primary), isFalse);
      expect(greenish(s.secondary), isFalse);
      expect(greenish(s.tertiary), isFalse);
      expect(greenish(s.surfaceTint), isFalse);
      expect(greenish(s.primaryContainer), isFalse);
    }
  });

  test('both themes are Material 3, use the Devanagari-capable font and '
      'carry their palette', () {
    final light = buildAppTheme();
    final dark = buildDarkAppTheme();
    expect(light.useMaterial3 && dark.useMaterial3, isTrue);
    expect(light.brightness, Brightness.light);
    expect(dark.brightness, Brightness.dark);
    expect(light.textTheme.bodyMedium!.fontFamily, 'Mukta');
    expect(dark.textTheme.bodyMedium!.fontFamily, 'Mukta');
    expect(light.extension<SnColors>(), SnColors.light);
    expect(dark.extension<SnColors>(), SnColors.dark);
  });

  test('verdict tones: unknown is grey in both palettes; unrecognised '
      'statuses are shown as unknown', () {
    for (final p in [SnColors.light, SnColors.dark]) {
      final unknown = verdictTone(p, 'unknown');
      expect(greenish(unknown.color), isFalse);
      expect(greenish(unknown.surface), isFalse);
      expect(unknown.color, isNot(verdictTone(p, 'ok').color));
    }
    expect(verdictTone(SnColors.light, 'ok').color, verdictColor('ok'));
    expect(safeVerdictStatus('green'), 'unknown');
    expect(safeVerdictStatus('avoid'), 'avoid');
    expect(() => verdictTone(SnColors.light, 'green'), throwsArgumentError);
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
