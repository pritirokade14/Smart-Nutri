import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/settings/presentation/profile_screen.dart';
import 'package:smartnutri_ai/features/targets/presentation/guide_settings_screen.dart';
import 'package:smartnutri_ai/features/targets/presentation/guide_setup_screen.dart';
import 'package:smartnutri_ai/features/targets/presentation/numbers_choice.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart' show apiError;
import '../../support/fake_members.dart';
import '../../support/fake_targets.dart';
import '../../support/fake_user_types.dart';
import '../../support/fixtures.dart';
import '../user_types/user_types_harness.dart';

MemberOut _primary() => memberOut(
  id: 'p1',
  name: 'Ravi',
  relation: MemberOutRelation.self,
  birthYear: 1997,
  sex: MemberOutSex.male,
  heightCm: 175,
  weightKg: 70,
  diet: MemberOutDiet.nonVeg,
  isPrimary: true,
);

Future<(AppHarness, FakeTargetsClient)> _open(
  WidgetTester t,
  FakeTargetsClient targets, {
  String initial = '/profile/guide',
}) async {
  final h = await pumpApp(
    t,
    FakeUserTypesApi(
      me: FakeUserTypesMe(userTypesOut(types: ['gym'])),
      members: FakeMembersClient([_primary()]),
      consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
      targets: targets,
    ),
    initial: initial,
  );
  return (h, targets);
}

Future<void> _tap(WidgetTester t, Key key) async {
  await t.ensureVisible(find.byKey(key));
  await t.pumpAndSettle();
  await t.tap(find.byKey(key));
  await t.pumpAndSettle();
}

void main() {
  testWidgets('profile lists Diary and daily guide', (t) async {
    final (_, _) = await _open(t, FakeTargetsClient(), initial: '/profile');
    await _tap(t, ProfileScreen.guideKey);
    expect(find.text(en.settingsDiaryTitle), findsWidgets);
    expect(find.byKey(GuideSettingsScreen.setupKey), findsOneWidget);
  });

  testWidgets('numbers choice sends the display only', (t) async {
    final (_, targets) = await _open(
      t,
      FakeTargetsClient(
        today: 'g1_build_muscle',
        settings: goalSettingsOut(activity: 'moderate'),
      ),
    );
    await _tap(t, NumbersChoice.optionKey('hide_all'));
    expect(
      targets.displays.single.numbersDisplay,
      DisplayInNumbersDisplay.hideAll,
    );
    expect(targets.puts, isEmpty);
  });

  testWidgets('reset confirms then deletes the settings', (t) async {
    final (_, targets) = await _open(
      t,
      FakeTargetsClient(
        today: 'g1_build_muscle',
        settings: goalSettingsOut(activity: 'moderate'),
      ),
    );
    await _tap(t, GuideSettingsScreen.resetKey);
    expect(find.text(en.settingsDiaryResetConfirm), findsOneWidget);
    await _tap(t, GuideSettingsScreen.resetConfirmKey);
    expect(targets.resets, hasLength(1));
    expect(targets.settings, isNull);
  });

  testWidgets('consent_required shows an inline card, not a redirect', (
    t,
  ) async {
    final targets = FakeTargetsClient(today: 'g1_build_muscle')
      ..settingsGetError = apiError(403, 'consent_required');
    final (h, _) = await _open(t, targets);
    expect(find.byKey(GuideSettingsScreen.consentKey), findsOneWidget);
    expect(find.text(en.diaryTargetsConsent), findsOneWidget);
    expect(
      h.router.routerDelegate.currentConfiguration.uri.path,
      '/profile/guide',
    );
  });

  testWidgets('saving settings sends the settings put', (t) async {
    final (_, targets) = await _open(
      t,
      FakeTargetsClient(
        today: 'g1_build_muscle',
        settings: goalSettingsOut(activity: 'moderate'),
      )..previewResult = targetsFixture('g1_build_muscle'),
    );
    await _tap(t, GuideSettingsScreen.saveKey);
    expect(
      targets.puts.single.activityLevel,
      GoalSettingsInActivityLevel.moderate,
    );
    expect(find.byType(GuideSetupScreen), findsNothing);
  });
}
