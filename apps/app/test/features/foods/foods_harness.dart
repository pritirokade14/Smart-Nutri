import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/network/api_client.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_foods.dart';
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
