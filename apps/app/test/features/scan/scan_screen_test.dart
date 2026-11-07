import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/analysis/data/analysis_repository.dart';
import 'package:smartnutri_ai/features/analysis/presentation/result_screen.dart';
import 'package:smartnutri_ai/features/scan/data/barcode_source.dart';
import 'package:smartnutri_ai/features/scan/presentation/manual_barcode_field.dart';
import 'package:smartnutri_ai/features/scan/presentation/scan_screen.dart';
import 'package:smartnutri_ai/core/network/api_client.dart';
import 'package:smartnutri_ai/features/diary/presentation/diary_providers.dart';
import 'package:smartnutri_ai/features/foods/presentation/portion_picker_sheet.dart';
import 'package:smartnutri_api/src/export.dart';
import 'package:smartnutri_ai/core/platform/app_settings.dart';
import '../../support/fake_app_settings.dart';
import '../../support/fake_foods.dart';
import '../../support/fake_meals.dart';
import '../../support/fake_user_types.dart';

class FakeBarcodeSource implements BarcodeSource {
  FakeBarcodeSource([this.status = BarcodeSourceStatus.ready]);
  final BarcodeSourceStatus status;
  final _c = StreamController<String>.broadcast();
  bool disposed = false;

  void emit(String v) => _c.add(v);

  @override
  Stream<String> get codes => _c.stream;
  @override
  Future<BarcodeSourceStatus> start() async => status;
  @override
  Widget buildPreview(BuildContext context) =>
      const SizedBox(key: Key('preview'));
  @override
  Future<void> dispose() async => disposed = true;
}

/// Like the real scanner: start() only succeeds once the preview was built.
class _AttachingSource extends FakeBarcodeSource {
  final _attached = Completer<void>();

  @override
  Future<BarcodeSourceStatus> start() async {
    await _attached.future.timeout(
      const Duration(milliseconds: 500),
      onTimeout: () => throw StateError('controllerNotAttached'),
    );
    return BarcodeSourceStatus.ready;
  }

  @override
  Widget buildPreview(BuildContext context) {
    if (!_attached.isCompleted) _attached.complete();
    return const SizedBox(key: Key('preview'));
  }
}

/// Never answers, so the result screen stays in its loading state.
class _PendingRepo implements AnalysisRepository {
  @override
  Future<AnalyzeOut> analyzeBarcode(String barcode, {String language = 'en'}) =>
      Completer<AnalyzeOut>().future;

  @override
  Future<AnalyzeOut> analyzeProduct(
    String productId, {
    String language = 'en',
  }) => Completer<AnalyzeOut>().future;
}

Widget _app(
  FakeBarcodeSource src,
  List<String> visited, {
  AppSettings? settings,
}) {
  final router = GoRouter(
    initialLocation: '/scan',
    routes: [
      GoRoute(path: '/scan', builder: (_, _) => const ScanScreen()),
      GoRoute(
        path: '/result',
        builder: (_, s) {
          visited.add(s.uri.queryParameters['barcode']!);
          return ResultScreen(barcode: s.uri.queryParameters['barcode']!);
        },
      ),
    ],
  );
  return ProviderScope(
    overrides: [
      ...mealTestOverrides(),
      if (settings != null) appSettingsProvider.overrideWithValue(settings),
      barcodeSourceFactoryProvider.overrideWithValue(() => src),
      analysisRepositoryProvider.overrideWithValue(_PendingRepo()),
    ],
    child: MaterialApp.router(
      routerConfig: router,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
    ),
  );
}

Widget _diaryApp(
  FakeBarcodeSource src,
  List<String> visited,
  FakeFoodsClient foods,
  List<MealIn> logged,
) {
  final router = GoRouter(
    initialLocation: '/scan',
    routes: [
      GoRoute(path: '/scan', builder: (_, _) => const ScanScreen()),
      GoRoute(
        path: '/result',
        builder: (_, s) {
          visited.add(s.uri.queryParameters['barcode']!);
          return const Scaffold(body: Text('result'));
        },
      ),
    ],
  );
  return ProviderScope(
    overrides: [
      ...mealTestOverrides(client: _LoggingMeals(logged)),
      barcodeSourceFactoryProvider.overrideWithValue(() => src),
      apiClientProvider.overrideWithValue(FakeUserTypesApi(foods: foods)),
      diaryAddContextProvider.overrideWith(
        () => _FixedAddContext(
          const DiaryAddContext(method: 'barcode', memberId: 'm1'),
        ),
      ),
    ],
    child: MaterialApp.router(
      routerConfig: router,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
    ),
  );
}

class _FixedAddContext extends DiaryAddContextNotifier {
  _FixedAddContext(this._value);
  final DiaryAddContext _value;

  @override
  DiaryAddContext? build() => _value;
}

class _LoggingMeals extends FakeMealsClient {
  _LoggingMeals(this.sink);
  final List<MealIn> sink;

  @override
  Future<MealOut> mealsLog({required MealIn body}) {
    sink.add(body);
    return super.mealsLog(body: body);
  }
}

void main() {
  testWidgets(
    'diary barcode: your own custom food goes to the portion picker',
    (tester) async {
      final src = FakeBarcodeSource();
      final visited = <String>[];
      final logged = <MealIn>[];
      final foods = FakeFoodsClient(
        details: {
          'c1': foodDetail(
            id: 'c1',
            name: 'Homemade ladoo',
            kind: FoodDetailOutKind.customFood,
            defaultUnit: 'g',
            attributions: const [],
            units: [unitOut('g', 1, kind: FoodUnitOutKind.mass)],
          ),
        },
      );
      tester.view.physicalSize = const Size(900, 3600);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(_diaryApp(src, visited, foods, logged));
      await tester.pumpAndSettle();
      src.emit('8901063201089');
      await tester.pumpAndSettle();
      // The portion picker, not the verdict screen.
      expect(find.byType(PortionPickerSheet), findsOneWidget);
      expect(visited, isEmpty);
      await tester.tap(find.byKey(PortionPickerSheet.saveKey));
      await tester.pumpAndSettle();
      expect(logged.single.customFoodId, 'c1');
      expect(logged.single.productId, isNull);
    },
  );

  testWidgets('diary barcode: a product keeps the usual result screen', (
    tester,
  ) async {
    final src = FakeBarcodeSource();
    final visited = <String>[];
    final foods = FakeFoodsClient(
      details: {'p1': foodDetail(id: 'p1', kind: FoodDetailOutKind.product)},
    );
    await tester.pumpWidget(_diaryApp(src, visited, foods, []));
    await tester.pumpAndSettle();
    src.emit('8901063201089');
    await tester.pumpAndSettle();
    expect(find.byType(PortionPickerSheet), findsNothing);
    expect(visited, ['8901063201089']);
  });

  testWidgets('first valid code navigates once; invalid and later ignored', (
    tester,
  ) async {
    final src = FakeBarcodeSource();
    final visited = <String>[];
    await tester.pumpWidget(_app(src, visited));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('preview')), findsOneWidget);
    expect(find.byType(ManualBarcodeField), findsOneWidget);

    src.emit('abc');
    src.emit('12345');
    await tester.pumpAndSettle();
    expect(visited, isEmpty);

    src.emit('8901 0632 0108 9');
    src.emit('012345678905');
    // The result screen keeps a spinner running, so pump a fixed time instead
    // of settling.
    for (var i = 0; i < 3; i++) {
      await tester.pump(const Duration(milliseconds: 500));
    }
    expect(visited, ['8901063201089']);
    expect(find.byType(ResultScreen), findsOneWidget);
  });

  testWidgets('preview is attached while starting, so start() can succeed', (
    tester,
  ) async {
    final src = _AttachingSource();
    await tester.pumpWidget(_app(src, []));
    await tester.pumpAndSettle();
    final l10n = AppLocalizations.of(tester.element(find.byType(ScanScreen)));
    expect(find.text(l10n.scanCameraUnavailable), findsNothing);
    expect(find.text(l10n.scanScanning), findsOneWidget);
  });

  testWidgets('permission denied shows message and manual field', (
    tester,
  ) async {
    final src = FakeBarcodeSource(BarcodeSourceStatus.permissionDenied);
    await tester.pumpWidget(_app(src, []));
    await tester.pumpAndSettle();
    final l10n = AppLocalizations.of(tester.element(find.byType(ScanScreen)));
    expect(find.text(l10n.scanCameraDenied), findsOneWidget);
    expect(find.byType(ManualBarcodeField), findsOneWidget);
    expect(find.byKey(const Key('preview')), findsNothing);
  });

  testWidgets('permanently denied camera offers Open settings', (tester) async {
    final settings = FakeAppSettings();
    final src = FakeBarcodeSource(BarcodeSourceStatus.permissionDenied);
    await tester.pumpWidget(_app(src, [], settings: settings));
    await tester.pumpAndSettle();
    final l10n = AppLocalizations.of(tester.element(find.byType(ScanScreen)));
    expect(settings.denied, [cameraPermission]);
    await tester.tap(find.text(l10n.commonOpenSettings));
    expect(settings.opened, 1);
  });

  testWidgets(
    'a camera denial that can be asked again has no settings button',
    (tester) async {
      final src = FakeBarcodeSource(BarcodeSourceStatus.permissionDenied);
      await tester.pumpWidget(
        _app(src, [], settings: FakeAppSettings(permanent: false)),
      );
      await tester.pumpAndSettle();
      final l10n = AppLocalizations.of(tester.element(find.byType(ScanScreen)));
      expect(find.text(l10n.commonOpenSettings), findsNothing);
    },
  );

  testWidgets('no camera shows unavailable message', (tester) async {
    final src = FakeBarcodeSource(BarcodeSourceStatus.unavailable);
    await tester.pumpWidget(_app(src, []));
    await tester.pumpAndSettle();
    final l10n = AppLocalizations.of(tester.element(find.byType(ScanScreen)));
    expect(find.text(l10n.scanCameraUnavailable), findsOneWidget);
    expect(find.byType(ManualBarcodeField), findsOneWidget);
  });

  testWidgets('manual entry navigates to result', (tester) async {
    final src = FakeBarcodeSource(BarcodeSourceStatus.permissionDenied);
    final visited = <String>[];
    await tester.pumpWidget(_app(src, visited));
    await tester.pumpAndSettle();
    final l10n = AppLocalizations.of(tester.element(find.byType(ScanScreen)));
    await tester.enterText(find.byType(TextField), '8901-0632-0108-9');
    await tester.tap(find.text(l10n.scanSubmit));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(visited, ['8901063201089']);
  });

  testWidgets('manual field: invalid shows error, valid calls onSubmit', (
    tester,
  ) async {
    final got = <String>[];
    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Scaffold(body: ManualBarcodeField(onSubmit: got.add)),
      ),
    );
    final l10n = AppLocalizations.of(
      tester.element(find.byType(ManualBarcodeField)),
    );
    await tester.enterText(find.byType(TextField), '1234567');
    await tester.tap(find.text(l10n.scanSubmit));
    await tester.pump();
    expect(find.text(l10n.scanInvalid), findsOneWidget);
    expect(got, isEmpty);

    await tester.enterText(find.byType(TextField), '8901 0632 0108 9');
    await tester.tap(find.text(l10n.scanSubmit));
    await tester.pump();
    expect(find.text(l10n.scanInvalid), findsNothing);
    expect(got, ['8901063201089']);
  });
}
