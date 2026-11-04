import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/analysis/data/analysis_repository.dart';
import 'package:smartnutri_ai/features/analysis/presentation/result_screen.dart';
import 'package:smartnutri_ai/features/analysis/presentation/verdict_card.dart';
import 'package:smartnutri_ai/features/modes/mode_layouts.dart';
import 'package:smartnutri_ai/features/product/data/product_discovery_repository.dart';
import 'package:smartnutri_ai/shared/widgets/disclaimer_footer.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_products.dart';
import '../../support/fake_user_types.dart';
import '../../support/fixtures.dart';
import '../user_types/user_types_harness.dart';

class _Analysis implements AnalysisRepository {
  _Analysis(this.out);
  final AnalyzeOut out;

  @override
  Future<AnalyzeOut> analyzeBarcode(
    String barcode, {
    String language = 'en',
  }) async => out;

  @override
  Future<AnalyzeOut> analyzeProduct(
    String productId, {
    String language = 'en',
  }) async => out;
}

/// Every label, value and flag in the semantics subtree of [node].
List<String> _semantics(SemanticsNode node) {
  final out = <String>[];
  void visit(SemanticsNode n) {
    final d = n.getSemanticsData();
    final text = [
      d.label,
      d.value,
      d.hint,
      d.tooltip,
    ].where((s) => s.isNotEmpty).join('|');
    if (text.isNotEmpty) out.add(text);
    n.visitChildren((c) {
      visit(c);
      return true;
    });
  }

  visit(node);
  return out;
}

/// The verdict section: every member's card (status, reasons, allergen
/// rows) and the disclaimer.
Future<List<String>> _verdictSection(
  WidgetTester t,
  String mode,
  AnalyzeOut out,
) async {
  final h = await pumpApp(
    t,
    FakeUserTypesApi(me: FakeUserTypesMe(userTypesOut(types: [mode]))),
    overrides: [
      analysisRepositoryProvider.overrideWithValue(_Analysis(out)),
      productDiscoveryRepositoryProvider.overrideWithValue(
        ProductDiscoveryRepository(FakeProductsClient()),
      ),
    ],
  );
  h.router.push('/result?product_id=p-fixture');
  await t.pumpAndSettle();
  expect(find.byType(ResultScreen), findsOneWidget);
  final cards = find.byType(VerdictCard);
  expect(cards, findsWidgets);
  return [
    for (final e in cards.evaluate())
      ..._semantics(t.getSemantics(find.byWidget(e.widget))),
    ..._semantics(t.getSemantics(find.byType(DisclaimerFooter).first)),
  ];
}

void main() {
  for (final product in ['cola', 'sf_biscuit']) {
    testWidgets('result screen identical in every mode: $product', (t) async {
      final handle = t.ensureSemantics();
      final out = analyzeFixture(product);
      final byMode = <String, List<String>>{};
      for (final mode in kModeLayouts.keys) {
        byMode[mode] = await _verdictSection(t, mode, out);
      }
      final reference = byMode[kDefaultType]!;
      expect(reference, isNotEmpty);
      for (final MapEntry(key: mode, value: section) in byMode.entries) {
        expect(section, reference, reason: mode);
      }
      handle.dispose();
    });
  }
}
