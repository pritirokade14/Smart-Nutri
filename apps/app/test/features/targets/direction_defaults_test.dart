import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/targets/domain/direction_defaults.dart';

import '../../support/fixtures.dart';

void main() {
  test('kDirectionForGoal equals the shared fixture', () {
    expect(kDirectionForGoal, directionDefaultsFixture());
  });

  test('an unknown goal defaults to maintain', () {
    expect(directionForGoal(null), 'maintain');
    expect(directionForGoal('mystery'), 'maintain');
  });
}
