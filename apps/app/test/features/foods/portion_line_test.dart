import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/foods/domain/portion_line.dart';

import 'foods_harness.dart';

void main() {
  test('only portion and density are approximate', () {
    expect(isApproxUnitSource('portion'), isTrue);
    expect(isApproxUnitSource('density'), isTrue);
    expect(isApproxUnitSource('grams'), isFalse);
    expect(isApproxUnitSource(null), isFalse);
  });

  test('grams, millilitres and approx', () {
    expect(portionLine(en, amount: 40, ml: false), '40 g');
    expect(portionLine(en, amount: 200, ml: true), '200 ml');
    expect(
      portionLine(en, amount: 136, ml: false, quantity: 2, unit: 'roti'),
      '2 rotis · 136 g',
    );
    expect(
      portionLine(
        en,
        amount: 310,
        ml: true,
        quantity: 2,
        unit: 'glass',
        approx: true,
      ),
      '2 glasses · ≈ 310 ml',
    );
    // ml of an ml food is exact and plain.
    expect(
      portionLine(en, amount: 200, ml: true, quantity: 200, unit: 'ml'),
      '200 ml',
    );
  });
}
