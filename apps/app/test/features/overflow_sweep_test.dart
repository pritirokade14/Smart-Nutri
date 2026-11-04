import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/analysis/data/analysis_repository.dart';
import 'package:smartnutri_ai/features/analysis/presentation/analysis_providers.dart';
import 'package:smartnutri_ai/features/methodology/data/methodology_repository.dart';
import 'package:smartnutri_ai/features/methodology/presentation/methodology_providers.dart';
import 'package:smartnutri_ai/features/modes/mode_layouts.dart';
import 'package:smartnutri_ai/features/product/data/product_discovery_repository.dart';
import 'package:smartnutri_ai/features/product/presentation/product_discovery_providers.dart';
import 'package:smartnutri_api/src/export.dart';

import '../support/fake_members.dart';
import '../support/fake_products.dart';
import '../support/fake_user_types.dart';
import '../support/fixtures.dart';
import 'user_types/user_types_harness.dart';

class _Analysis implements AnalysisRepository {
  @override
  Future<AnalyzeOut> analyzeBarcode(String b, {String language = 'en'}) async =>
      analyzeFixture('sf_biscuit');
  @override
  Future<AnalyzeOut> analyzeProduct(
    String id, {
    String language = 'en',
  }) async => analyzeFixture('sf_biscuit');
}

class _Methodology implements MethodologyClient {
  @override
  Future<Methodology> methodologyGet({
    MethodologyLanguage? language = MethodologyLanguage.en,
  }) async => methodologyFixture();
}

/// Every main screen at 360x640 in every locale: no RenderFlex overflow.
void main() {
  const size = Size(360, 640);

  // Real glyph widths: flutter test would otherwise use the Ahem font.
  setUpAll(() async {
    final loader = FontLoader('Mukta');
    for (final w in ['Regular', 'Medium', 'SemiBold', 'Bold']) {
      final bytes = File('assets/fonts/mukta/Mukta-$w.ttf').readAsBytesSync();
      loader.addFont(Future.value(ByteData.sublistView(bytes)));
    }
    await loader.load();
  });

  for (final locale in ['en', 'hi', 'mr']) {
    final routes = <String, (String, String)>{
      for (final mode in kModeLayouts.keys) 'home-$mode': (mode, '/home'),
      'result': ('family', '/result?barcode=8901063201089'),
      'family': ('family', '/family'),
      'search': ('family', '/search'),
      'how-we-score': ('family', '/methodology'),
      'protein': ('gym', '/protein'),
    };
    for (final e in routes.entries) {
      testWidgets('no overflow: ${e.key} $locale', (t) async {
        await pumpApp(
          t,
          FakeUserTypesApi(
            me: FakeUserTypesMe(userTypesOut(types: [e.value.$1])),
            members: FakeMembersClient([primaryMember()]),
            consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
          ),
          locale: locale,
          size: size,
          overrides: [
            analysisRepositoryProvider.overrideWithValue(_Analysis()),
            methodologyRepositoryProvider.overrideWithValue(
              MethodologyRepository(_Methodology()),
            ),
            productDiscoveryRepositoryProvider.overrideWithValue(
              ProductDiscoveryRepository(FakeProductsClient()),
            ),
          ],
          initial: e.value.$2,
        );
        await t.pump(const Duration(seconds: 1));
        expect(t.takeException(), isNull);
      });
    }
  }
}
