import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/observability/analytics.dart';
import 'package:smartnutri_ai/features/analysis/data/analysis_repository.dart';
import 'package:smartnutri_ai/features/analysis/presentation/result_screen.dart';
import 'package:smartnutri_ai/features/analysis/presentation/verdict_card.dart';
import 'package:smartnutri_ai/features/scan/data/label_repository.dart';
import 'package:smartnutri_ai/features/scan/presentation/confirm_screen.dart';
import 'package:smartnutri_ai/features/scan/presentation/draft_form.dart';
import 'package:smartnutri_ai/features/scan/presentation/label_capture_screen.dart';
import 'package:smartnutri_ai/features/scan/presentation/label_providers.dart';
import 'package:smartnutri_ai/features/scan/presentation/warning_banner.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';
import 'draft_fixtures.dart';
import '../../support/fake_meals.dart';

final en = lookupAppLocalizations(const Locale('en'));

class FakeLabelRepository implements LabelRepository {
  FakeLabelRepository({this.scan, this.save});

  final FutureOr<ScanDraftOut> Function()? scan;
  final FutureOr<ProductOut> Function()? save;
  final scanBarcodes = <String?>[];
  final saved = <ProductCreate>[];

  @override
  Future<ScanDraftOut> scanLabel(
    XFile photo, {
    String? barcode,
    void Function(LabelPhase)? onPhase,
  }) async {
    scanBarcodes.add(barcode);
    onPhase?.call(LabelPhase.uploading);
    onPhase?.call(LabelPhase.reading);
    return scan!();
  }

  @override
  Future<ProductOut> saveDraft(ProductCreate body) async {
    saved.add(body);
    return save!();
  }
}

class FakeAnalysisRepository implements AnalysisRepository {
  FakeAnalysisRepository(this.respond);
  final FutureOr<AnalyzeOut> Function() respond;
  final barcodes = <String>[];
  final productIds = <String>[];

  @override
  Future<AnalyzeOut> analyzeBarcode(
    String barcode, {
    String language = 'en',
  }) async {
    barcodes.add(barcode);
    return respond();
  }

  @override
  Future<AnalyzeOut> analyzeProduct(
    String productId, {
    String language = 'en',
  }) async {
    productIds.add(productId);
    return respond();
  }
}

LabelFailure _failure(
  String code, {
  List<String> fields = const [],
  String? id,
}) => LabelFailure(code, fields: fields, productId: id);

ProductOut _savedProduct(String id) {
  final json = analyzeJson('sf_biscuit');
  final product = Map<String, Object?>.from(json['product']! as Map)
    ..['product_id'] = id;
  return ProductOut.fromJson(product);
}

class _Visits {
  final locations = <String>[];
}

Future<_Visits> _pumpFlow(
  WidgetTester t, {
  required String initial,
  Object? extra,
  FakeLabelRepository? labels,
  FakeAnalysisRepository? analysis,
  List<String>? events,
  LabelPhotoPicker? picker,
  LabelLostPhoto? lostPhoto,
}) async {
  t.view.physicalSize = const Size(1000, 9000);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  final visits = _Visits();
  final router = GoRouter(
    initialLocation: initial,
    initialExtra: extra,
    redirect: (_, s) {
      visits.locations.add(s.uri.toString());
      return null;
    },
    routes: [
      GoRoute(path: '/scan', builder: (_, _) => const Text('scan-screen')),
      GoRoute(
        path: '/scan/label',
        builder: (_, s) =>
            LabelCaptureScreen(barcode: s.uri.queryParameters['barcode']),
      ),
      GoRoute(
        path: '/scan/confirm',
        builder: (_, s) => ConfirmScreen(args: s.extra as ConfirmArgs?),
      ),
      GoRoute(
        path: '/result',
        builder: (_, s) => ResultScreen(
          barcode: s.uri.queryParameters['barcode'],
          productId: s.uri.queryParameters['product_id'],
        ),
      ),
    ],
  );
  addTearDown(router.dispose);
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        ...mealTestOverrides(),
        labelRepositoryProvider.overrideWithValue(
          labels ?? FakeLabelRepository(),
        ),
        analysisRepositoryProvider.overrideWithValue(
          analysis ?? FakeAnalysisRepository(() => analyzeFixture('water')),
        ),
        labelPhotoPickerProvider.overrideWithValue(
          picker ?? (_) async => XFile.fromData(Uint8List.fromList([1, 2, 3])),
        ),
        labelLostPhotoProvider.overrideWithValue(lostPhoto ?? () async => null),
        analyticsProvider.overrideWithValue(
          Analytics((event, props) async {
            // Recorded as `event:method`; only allow-listed, valueless props.
            events?.add('$event:${props['method']}');
            expect(
              props.keys.toSet().difference({'method', 'found'}),
              isEmpty,
              reason: 'no values in label events',
            );
          }),
        ),
      ],
      child: MaterialApp.router(
        locale: const Locale('en'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        routerConfig: router,
      ),
    ),
  );
  await t.pumpAndSettle();
  return visits;
}

String _fieldText(WidgetTester t, String name) => t
    .widget<EditableText>(
      find.descendant(
        of: find.byKey(ValueKey('field:$name')),
        matching: find.byType(EditableText),
      ),
    )
    .controller
    .text;

void main() {
  group('label capture', () {
    testWidgets('photo → confirm screen with the draft; barcode travels', (
      t,
    ) async {
      final labels = FakeLabelRepository(scan: () => scanOut(baseDraft()));
      final events = <String>[];
      await _pumpFlow(
        t,
        initial: '/scan/label?barcode=8901063201089',
        labels: labels,
        events: events,
      );
      expect(find.text(en.labelTitle), findsWidgets);
      await t.tap(find.text(en.labelTakePhoto));
      await t.pumpAndSettle();
      expect(labels.scanBarcodes.single, '8901063201089');
      expect(find.byType(ConfirmScreen), findsOneWidget);
      expect(_fieldText(t, 'name'), 'Marie Biscuit');
      expect(events, contains('scan_started:label'));
    });

    testWidgets('extraction_failed shows retake + enter manually; no form '
        'prefilled', (t) async {
      final labels = FakeLabelRepository(
        scan: () => throw _failure('extraction_failed'),
      );
      final events = <String>[];
      await _pumpFlow(
        t,
        initial: '/scan/label',
        labels: labels,
        events: events,
      );
      await t.tap(find.text(en.labelChooseFile));
      await t.pumpAndSettle();
      expect(events, ['scan_started:label']);
      expect(find.text(en.errorExtractionFailed), findsOneWidget);
      expect(find.text(en.labelRetake), findsOneWidget);
      expect(find.text(en.labelEnterManually), findsOneWidget);
      expect(find.byType(DraftForm), findsNothing);

      await t.tap(find.text(en.labelEnterManually));
      await t.pumpAndSettle();
      expect(find.byType(DraftForm), findsOneWidget);
      expect(_fieldText(t, 'name'), isEmpty);
      expect(_fieldText(t, 'protein_g'), isEmpty);

      await t.tap(find.text(en.labelRetake));
      await t.pumpAndSettle();
      expect(find.byType(LabelCaptureScreen), findsOneWidget);
      expect(find.text(en.labelTakePhoto), findsOneWidget);
    });

    testWidgets('every capture error offers retake and enter manually', (
      t,
    ) async {
      for (final (code, text) in [
        ('image_too_large', en.errorImageTooLarge),
        ('unsupported_image', en.errorUnsupportedImage),
        ('rate_limited_scans', en.errorRateLimitedScans),
        ('extraction_unavailable', en.errorExtractionUnavailable),
        ('storage_unavailable', en.errorStorageUnavailable),
        ('scan_image_not_found', en.errorScanImageNotFound),
        ('network', en.errorNetwork),
      ]) {
        await _pumpFlow(
          t,
          initial: '/scan/label',
          labels: FakeLabelRepository(scan: () => throw _failure(code)),
        );
        await t.tap(find.text(en.labelTakePhoto));
        await t.pumpAndSettle();
        expect(find.text(text), findsOneWidget, reason: code);
        expect(find.text(en.labelRetake), findsOneWidget, reason: code);
        expect(find.text(en.labelEnterManually), findsOneWidget, reason: code);
        await t.pumpWidget(const SizedBox());
      }
    });
  });

  group('capture parity', () {
    testWidgets('with a barcode, the capture screen says why (F15)', (t) async {
      await _pumpFlow(t, initial: '/scan/label?barcode=8901063201089');
      expect(find.text(en.notfoundGoToLabel), findsOneWidget);
      await t.pumpWidget(const SizedBox());
      await _pumpFlow(t, initial: '/scan/label');
      expect(find.text(en.notfoundGoToLabel), findsNothing);
    });

    testWidgets('a denied camera permission shows the permission message', (
      t,
    ) async {
      final events = <String>[];
      await _pumpFlow(
        t,
        initial: '/scan/label',
        events: events,
        picker: (_) async =>
            throw PlatformException(code: 'camera_access_denied'),
      );
      await t.tap(find.text(en.labelTakePhoto));
      await t.pumpAndSettle();
      expect(find.text(en.labelCameraPermissionDenied), findsOneWidget);
      expect(find.text(en.errorUnsupportedImage), findsNothing);
      expect(find.text(en.labelRetake), findsOneWidget);
      expect(find.text(en.labelEnterManually), findsOneWidget);
    });

    testWidgets('a photo lost when Android killed the app is recovered on '
        'start and the flow continues', (t) async {
      final labels = FakeLabelRepository(scan: () => scanOut(baseDraft()));
      final events = <String>[];
      await _pumpFlow(
        t,
        initial: '/scan/label?barcode=8901063201089',
        labels: labels,
        events: events,
        lostPhoto: () async => XFile.fromData(Uint8List.fromList([4, 5, 6])),
      );
      // R24: a recovered photo can be of another product; no barcode.
      expect(labels.scanBarcodes, [null]);
      expect(find.byType(ConfirmScreen), findsOneWidget);
      expect(events, contains('scan_started:label'));
    });

    testWidgets('R24: opened with ?barcode=B, a recovered photo is saved with '
        'no barcode', (t) async {
      final labels = FakeLabelRepository(
        scan: () => scanOut(baseDraft()),
        save: () => _savedProduct('p-9'),
      );
      await _pumpFlow(
        t,
        initial: '/scan/label?barcode=B',
        labels: labels,
        analysis: FakeAnalysisRepository(() => analyzeFixture('sf_biscuit')),
        lostPhoto: () async => XFile.fromData(Uint8List.fromList([4, 5, 6])),
      );
      expect(labels.scanBarcodes, [null]);
      expect(find.byType(ConfirmScreen), findsOneWidget);
      await t.tap(find.byKey(const Key('save')));
      await t.pumpAndSettle();
      expect(labels.saved.single.scanId, 'scan-1');
      expect(labels.saved.single.barcode, isNull);
    });

    testWidgets('no lost photo: the capture screen waits for the user', (
      t,
    ) async {
      final labels = FakeLabelRepository(scan: () => scanOut(baseDraft()));
      await _pumpFlow(t, initial: '/scan/label', labels: labels);
      expect(labels.scanBarcodes, isEmpty);
      expect(find.text(en.labelTakePhoto), findsOneWidget);
    });
  });

  group('confirm screen', () {
    testWidgets('shows not-medical-advice, retake and enter manually', (
      t,
    ) async {
      await _pumpFlow(
        t,
        initial: '/scan/confirm',
        extra: ConfirmArgs(scan: scanOut(baseDraft())),
      );
      expect(find.text(en.confirmNotMedicalAdvice), findsOneWidget);
      expect(find.text(en.labelRetake), findsOneWidget);
      expect(find.text(en.labelEnterManually), findsOneWidget);
    });

    testWidgets('save → analyze → result screen shows verdict', (t) async {
      final labels = FakeLabelRepository(save: () => _savedProduct('p-1'));
      final body = analyzeFixture('sf_biscuit');
      final analysis = FakeAnalysisRepository(() => body);
      final events = <String>[];
      await _pumpFlow(
        t,
        initial: '/scan/confirm',
        extra: ConfirmArgs(
          scan: scanOut(baseDraft()),
          barcode: '8901063201089',
        ),
        labels: labels,
        analysis: analysis,
        events: events,
      );
      await t.tap(find.byKey(const Key('save')));
      await t.pumpAndSettle();
      expect(labels.saved.single.scanId, 'scan-1');
      expect(labels.saved.single.barcode, '8901063201089');
      expect(analysis.productIds, ['p-1']);
      expect(analysis.barcodes, isEmpty);
      expect(find.byType(ResultScreen), findsOneWidget);
      expect(find.byType(VerdictCard), findsNWidgets(body.verdicts.length));
      expect(find.text(en.commonDisclaimer), findsOneWidget);
      expect(events, contains('scan_completed:label'));
    });

    testWidgets('low_confidence offers retake and saves with the scan_id', (
      t,
    ) async {
      final labels = FakeLabelRepository(save: () => _savedProduct('p-2'));
      await _pumpFlow(
        t,
        initial: '/scan/confirm',
        extra: ConfirmArgs(scan: scanOut(lowConfidenceDraft())),
        labels: labels,
      );
      expect(find.text(en.warningLowConfidence), findsOneWidget);
      expect(find.text(en.labelRetake), findsOneWidget);
      await t.tap(find.byKey(const Key('save')));
      await t.pumpAndSettle();
      // Never re-posted as a manual entry.
      expect(labels.saved.single.scanId, 'scan-1');
    });

    testWidgets('enter manually starts an empty form with no scan_id', (
      t,
    ) async {
      final labels = FakeLabelRepository(save: () => _savedProduct('p-3'));
      final events = <String>[];
      await _pumpFlow(
        t,
        initial: '/scan/confirm',
        extra: ConfirmArgs(
          scan: scanOut(lowConfidenceDraft()),
          barcode: '12345670',
        ),
        labels: labels,
        events: events,
      );
      await t.tap(find.text(en.labelEnterManually));
      await t.pumpAndSettle();
      expect(_fieldText(t, 'name'), isEmpty);
      expect(_fieldText(t, 'energy_kcal'), isEmpty);
      expect(find.byType(WarningBanner), findsNothing);
      await t.enterText(
        find.descendant(
          of: find.byKey(const ValueKey('field:name')),
          matching: find.byType(EditableText),
        ),
        'Typed',
      );
      await t.tap(find.byKey(const ValueKey('category:general')));
      await t.tap(find.byKey(const ValueKey('basis:per_100g')));
      await t.pump();
      await t.tap(find.byKey(const Key('save')));
      await t.pumpAndSettle();
      expect(labels.saved.single.scanId, isNull);
      expect(labels.saved.single.barcode, '12345670');
      expect(events, ['scan_completed:manual']);
      expect(labels.saved.single.nutrients.energyKcal, isNull);
    });

    testWidgets('product_exists with a product_id offers to open it', (
      t,
    ) async {
      final labels = FakeLabelRepository(
        save: () => throw _failure('product_exists', id: 'p-9'),
      );
      final analysis = FakeAnalysisRepository(() => analyzeFixture('curd'));
      await _pumpFlow(
        t,
        initial: '/scan/confirm',
        extra: ConfirmArgs(scan: scanOut(baseDraft())),
        labels: labels,
        analysis: analysis,
      );
      await t.tap(find.byKey(const Key('save')));
      await t.pumpAndSettle();
      expect(find.text(en.errorProductExists), findsOneWidget);
      await t.tap(find.text(en.confirmOpenExisting));
      await t.pumpAndSettle();
      expect(analysis.productIds, ['p-9']);
      expect(find.byType(ResultScreen), findsOneWidget);
    });

    testWidgets(
      'implausible_value from the server is shown next to the field',
      (t) async {
        final labels = FakeLabelRepository(
          save: () =>
              throw _failure('implausible_value', fields: ['protein_g']),
        );
        await _pumpFlow(
          t,
          initial: '/scan/confirm',
          extra: ConfirmArgs(scan: scanOut(baseDraft())),
          labels: labels,
        );
        await t.tap(find.byKey(const Key('save')));
        await t.pumpAndSettle();
        expect(find.byType(ConfirmScreen), findsOneWidget);
        expect(
          find.byKey(const ValueKey('highlight:protein_g')),
          findsOneWidget,
        );
        expect(
          find.descendant(
            of: find.byKey(const ValueKey('field:protein_g')),
            matching: find.text(en.errorImplausibleValue),
          ),
          findsOneWidget,
        );
      },
    );

    testWidgets('a 422 on an ingredient highlights the ingredients field', (
      t,
    ) async {
      final labels = FakeLabelRepository(
        save: () => throw _failure('validation_error', fields: ['ingredients']),
      );
      await _pumpFlow(
        t,
        initial: '/scan/confirm',
        extra: ConfirmArgs(scan: scanOut(baseDraft())),
        labels: labels,
      );
      await t.tap(find.byKey(const Key('save')));
      await t.pumpAndSettle();
      expect(
        find.byKey(const ValueKey('highlight:ingredients')),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: find.byKey(const ValueKey('list:ingredients')),
          matching: find.text(en.errorValidationError),
        ),
        findsOneWidget,
      );
      // Items are never dropped automatically.
      expect(_fieldText(t, 'ingredient:2'), 'Palm oil');
    });

    testWidgets('scan_not_found on save offers retake', (t) async {
      final labels = FakeLabelRepository(
        save: () => throw _failure('scan_not_found'),
      );
      await _pumpFlow(
        t,
        initial: '/scan/confirm',
        extra: ConfirmArgs(scan: scanOut(baseDraft())),
        labels: labels,
      );
      await t.tap(find.byKey(const Key('save')));
      await t.pumpAndSettle();
      expect(find.text(en.errorScanNotFound), findsOneWidget);
      expect(find.text(en.labelRetake), findsOneWidget);
    });
  });

  testWidgets('404 on barcode result navigates to label capture with barcode', (
    t,
  ) async {
    final analysis = FakeAnalysisRepository(
      () => throw const AnalysisNotFound(),
    );
    final visits = await _pumpFlow(
      t,
      initial: '/result?barcode=8901063201089',
      analysis: analysis,
    );
    // F15: straight to label capture, as on the web; no tap needed.
    expect(find.byType(ResultScreen), findsNothing);
    expect(find.byType(LabelCaptureScreen), findsOneWidget);
    expect(visits.locations.last, '/scan/label?barcode=8901063201089');
    expect(find.text(en.notfoundGoToLabel), findsOneWidget);
    expect(analysis.barcodes, ['8901063201089']);
  });
}
