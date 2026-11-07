import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/network/api_client.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_foods.dart';
import '../../support/fake_meals.dart' show mealTestOverrides;
import '../../support/fake_user_types.dart';

final en = lookupAppLocalizations(const Locale('en'));

/// Pumps [child] over a fake API with [foods], in [locale].
Future<void> pumpOver(
  WidgetTester t,
  FakeFoodsClient foods,
  Widget child, {
  String locale = 'en',
}) async {
  t.view.physicalSize = const Size(900, 3600);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        apiClientProvider.overrideWithValue(FakeUserTypesApi(foods: foods)),
      ],
      child: MaterialApp(
        theme: buildAppTheme(),
        locale: Locale(locale),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Scaffold(body: child),
      ),
    ),
  );
  await t.pumpAndSettle();
}

List<String> shownTexts(WidgetTester t) => [
  for (final w in t.widgetList<Text>(find.byType(Text)))
    w.data ?? w.textSpan?.toPlainText() ?? '',
];

const noFood = FoodKindPath.food;

/// Pumps [screen] as a pushed page (so it can pop) over [api].
Future<void> pumpScreen(
  WidgetTester t,
  FakeUserTypesApi api,
  Widget screen, {
  String locale = 'en',
}) async {
  t.view.physicalSize = const Size(900, 3600);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  await t.pumpWidget(const SizedBox());
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        apiClientProvider.overrideWithValue(api),
        ...mealTestOverrides(),
      ],
      child: MaterialApp(
        theme: buildAppTheme(),
        locale: Locale(locale),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Builder(
          builder: (context) => TextButton(
            key: const Key('open'),
            onPressed: () => Navigator.of(
              context,
            ).push(MaterialPageRoute<void>(builder: (_) => screen)),
            child: const Text('open'),
          ),
        ),
      ),
    ),
  );
  await t.tap(find.byKey(const Key('open')));
  await t.pumpAndSettle();
}
