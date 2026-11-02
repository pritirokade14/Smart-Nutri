
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/main.dart';

void main() {
  testWidgets('Nutrition profile screen smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const NutritionApp());

    // Verify that the profile setup screen title appears.
    expect(find.text('Setup Nutrition Profile'), findsOneWidget);
  });
}