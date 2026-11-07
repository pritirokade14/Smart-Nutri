import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/foods/domain/portion_preview.dart';

void main() {
  test('matches units/conversions.json', () {
    final file = File('../../packages/test-fixtures/units/conversions.json');
    final cases =
        (jsonDecode(file.readAsStringSync()) as Map<String, dynamic>)['cases']
            as List<dynamic>;
    var checked = 0;
    for (final raw in cases) {
      final c = raw as Map<String, dynamic>;
      final expected = c['expected'] as Map<String, dynamic>;
      final want = expected['preview'] as Map<String, dynamic>?;
      if (want == null) continue;
      final per100 = {
        for (final e in (c['per_100'] as Map<String, dynamic>).entries)
          e.key: e.value as num?,
      };
      final got = previewPortion(
        per100,
        c['quantity'] as num,
        expected['grams_per_unit'] as num,
      );
      for (final e in want.entries) {
        final v = got[e.key];
        if (e.value == null) {
          expect(v, isNull, reason: '${c['case']} ${e.key}');
        } else {
          expect(
            double.parse(v!),
            (e.value as num).toDouble(),
            reason: '${c['case']} ${e.key}',
          );
        }
      }
      checked++;
    }
    expect(checked, greaterThan(10));
  });

  test('1.15 rounds half-up to 1.2 and null stays null', () {
    final r = previewPortion({'fibre_g': 1.15, 'fat_g': null}, 100, 1);
    expect(r['fibre_g'], '1.2');
    expect(r['fat_g'], isNull);
    expect(previewPortion({'a': 0.04}, 1, 1)['a'], '0.0');
    expect(previewPortion({'a': 1e-7}, 1, 1)['a'], '0.0');
  });
}
