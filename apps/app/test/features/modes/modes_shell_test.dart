import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/history/presentation/history_screen.dart';
import 'package:smartnutri_ai/features/home/presentation/home_screen.dart';
import 'package:smartnutri_ai/features/members/presentation/members_list_screen.dart';
import 'package:smartnutri_ai/features/methodology/presentation/methodology_screen.dart';
import 'package:smartnutri_ai/features/modes/mode_layouts.dart';
import 'package:smartnutri_ai/features/modes/presentation/destinations.dart';
import 'package:smartnutri_ai/features/modes/presentation/mode_switcher.dart';
import 'package:smartnutri_ai/features/modes/presentation/more_menu.dart';
import 'package:smartnutri_ai/features/product/presentation/compare_screen.dart';
import 'package:smartnutri_ai/features/product/presentation/search_screen.dart';
import 'package:smartnutri_ai/features/protein/presentation/protein_screen.dart';
import 'package:smartnutri_ai/features/scan/presentation/scan_screen.dart';
import 'package:smartnutri_ai/features/settings/presentation/profile_screen.dart';

import '../../support/fake_meals.dart' show apiError;
import '../../support/fake_user_types.dart';
import '../user_types/user_types_harness.dart';

const _screens = <String, Type>{
  'home': HomeScreen,
  'scan': ScanScreen,
  'history': HistoryScreen,
  'family': MembersListScreen,
  'protein': ProteinScreen,
  'compare': CompareScreen,
  'search': SearchScreen,
  'profile': ProfileScreen,
  'how_we_score': MethodologyScreen,
};

List<String> _barLabels(WidgetTester t) => [
  for (final d
      in t
          .widget<NavigationBar>(find.byType(NavigationBar))
          .destinations
          .cast<NavigationDestination>())
    d.label,
];

Future<AppHarness> _pumpMode(WidgetTester t, String mode) => pumpApp(
  t,
  FakeUserTypesApi(me: FakeUserTypesMe(userTypesOut(types: [mode]))),
);

/// Settles, tolerating the scanner (whose camera never settles in tests).
Future<void> _settle(WidgetTester t) async {
  await t.pump();
  await t.pump(const Duration(seconds: 1));
}

void main() {
  for (final mode in kModeLayouts.keys) {
    testWidgets('each mode shows its five tabs with scan second: $mode', (
      t,
    ) async {
      await _pumpMode(t, mode);
      final tabs = kModeLayouts[mode]!.tabs;
      expect(_barLabels(t), [for (final k in tabs) destinationLabel(en, k)]);
      expect(_barLabels(t)[1], en.navScan);
      expect(
        t.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex,
        0,
      );
    });

    testWidgets('more lists every destination not in the bar: $mode', (
      t,
    ) async {
      await _pumpMode(t, mode);
      await t.tap(find.byKey(HomeScreen.moreKey));
      await t.pumpAndSettle();
      final expected = moreDestinations(mode);
      for (final d in kDestinations) {
        expect(
          find.byKey(MoreList.itemKey(d)),
          expected.contains(d) ? findsOneWidget : findsNothing,
          reason: '$mode $d',
        );
      }
    });

    testWidgets('every destination reachable in every mode: $mode', (t) async {
      final h = await _pumpMode(t, mode);
      final tabs = kModeLayouts[mode]!.tabs;
      for (final d in kDestinations) {
        h.router.go('/home');
        await t.pumpAndSettle();
        if (tabs.contains(d)) {
          await t.tap(
            find.descendant(
              of: find.byType(NavigationBar),
              matching: find.text(destinationLabel(en, d)),
            ),
          );
        } else {
          await t.tap(find.byKey(HomeScreen.moreKey));
          await t.pumpAndSettle();
          await t.tap(find.byKey(MoreList.itemKey(d)));
        }
        await _settle(t);
        expect(find.byType(_screens[d]!), findsOneWidget, reason: '$mode $d');
      }
    });
  }

  testWidgets('a branch outside the bar shows the bar with Home selected', (
    t,
  ) async {
    final h = await _pumpMode(t, 'gym');
    h.router.go('/family');
    await t.pumpAndSettle();
    expect(find.byType(MembersListScreen), findsOneWidget);
    expect(
      t.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex,
      0,
    );
  });

  testWidgets('switcher hidden with one type', (t) async {
    await _pumpMode(t, 'gym');
    expect(find.byKey(ModeSwitcher.switcherKey), findsNothing);
  });

  testWidgets('switcher shown with two, calls set_active', (t) async {
    final me = FakeUserTypesMe(userTypesOut(types: ['gym', 'family']));
    await pumpApp(t, FakeUserTypesApi(me: me));
    expect(find.byKey(ModeSwitcher.switcherKey), findsOneWidget);
    // family has the higher priority, so it is the default mode.
    expect(_barLabels(t), [
      for (final k in kModeLayouts['family']!.tabs) destinationLabel(en, k),
    ]);
    await t.tap(find.byKey(ModeSwitcher.segmentKey('gym')));
    await t.pumpAndSettle();
    expect(me.actives, ['gym']);
    expect(_barLabels(t), [
      for (final k in kModeLayouts['gym']!.tabs) destinationLabel(en, k),
    ]);
  });

  testWidgets('switcher rolls back when the API refuses', (t) async {
    final me = FakeUserTypesMe(userTypesOut(types: ['gym', 'family']))
      ..activeErrors.add(apiError(422, 'user_type_not_selected'));
    await pumpApp(t, FakeUserTypesApi(me: me));
    await t.tap(find.byKey(ModeSwitcher.segmentKey('gym')));
    await t.pumpAndSettle();
    expect(me.actives, ['gym']);
    expect(_barLabels(t), [
      for (final k in kModeLayouts['family']!.tabs) destinationLabel(en, k),
    ]);
    expect(find.text(en.errorUserTypeNotSelected), findsOneWidget);
  });

  testWidgets('profile lists More first and the switcher', (t) async {
    final me = FakeUserTypesMe(userTypesOut(types: ['gym', 'eat_better']));
    await pumpApp(t, FakeUserTypesApi(me: me), initial: '/profile');
    expect(find.byType(ProfileScreen), findsOneWidget);
    for (final d in moreDestinations('gym')) {
      expect(find.byKey(MoreList.itemKey(d)), findsOneWidget, reason: d);
    }
    expect(find.byKey(ModeSwitcher.switcherKey), findsOneWidget);
    expect(find.text(en.modesSameChecks), findsOneWidget);
  });
}
