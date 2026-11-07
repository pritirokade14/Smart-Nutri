import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/core/theme/verdict_colors.dart';
import 'package:smartnutri_ai/features/home/presentation/cards/home_cards.dart';
import 'package:smartnutri_ai/features/members/presentation/consent_sheet.dart';
import 'package:smartnutri_ai/features/targets/presentation/eye_toggle.dart';
import 'package:smartnutri_ai/features/targets/presentation/targets_explanation.dart';
import 'package:smartnutri_ai/features/targets/presentation/today_targets_card.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';
import '../../support/fake_diary.dart';
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
  weightKg: 70,
  isPrimary: true,
);

Future<AppHarness> _home(
  WidgetTester t,
  FakeTargetsClient targets, {
  String mode = 'gym',
  FakeConsentsClient? consents,
  String day = 'day_complete_under',
  DiaryDayOut Function(DateTime? date)? dayFor,
}) => pumpApp(
  t,
  FakeUserTypesApi(
    me: FakeUserTypesMe(userTypesOut(types: [mode])),
    members: FakeMembersClient([_primary()]),
    consents: consents ?? FakeConsentsClient(granted: {'terms', 'health_data'}),
    targets: targets,
    diary: FakeDiaryClient(day: day)..dayFor = dayFor,
  ),
  meals: FakeMealsClient(),
);

Finder get _card => find.byKey(HomeCards.cardKey('today_targets'));

Finder _in(Finder f) => find.descendant(of: _card, matching: f);

Finder get _digits => _in(find.textContaining(RegExp(r'\d')));

Future<void> _tap(WidgetTester t, Key key) async {
  await t.ensureVisible(find.byKey(key));
  await t.pumpAndSettle();
  await t.tap(find.byKey(key));
  await t.pumpAndSettle();
}

void main() {
  testWidgets('renders golden g1_build_muscle targets', (t) async {
    await _home(
      t,
      FakeTargetsClient(
        today: 'g1_build_muscle',
        settings: goalSettingsOut(activity: 'moderate'),
      ),
    );
    // Energy and protein read "{eaten} of {target}" and the API's remaining
    // ("diary_day_get"); fat and carbs, the target.
    expect(_in(find.textContaining('2,760')), findsWidgets);
    expect(_in(find.text('77 g')), findsOneWidget);
    expect(_in(find.text('405 g')), findsOneWidget);
    expect(
      _in(find.text(en.diaryOfTarget('1,501 kcal', '2,760 kcal'))),
      findsOneWidget,
    );
    expect(_in(find.text(en.diaryOfTarget('44.7 g', '112 g'))), findsOneWidget);
    expect(_in(find.text(en.diaryLeft('1,259 kcal'))), findsOneWidget);
    expect(_in(find.text(en.diaryLeft('67.4 g'))), findsOneWidget);
  });

  testWidgets('status none shows setup CTA and skip', (t) async {
    await _home(t, FakeTargetsClient());
    expect(find.byKey(TodayTargetsCard.setupKey), findsOneWidget);
    expect(find.text(en.targetsSetupCta), findsOneWidget);
    await _tap(t, TodayTargetsCard.skipKey);
    expect(find.byKey(TodayTargetsCard.setupKey), findsNothing);
  });

  testWidgets('consent_required shows the consent card, not a redirect', (
    t,
  ) async {
    final targets = FakeTargetsClient(today: 'g1_build_muscle')
      ..getError = apiError(403, 'consent_required')
      ..settingsGetError = apiError(403, 'consent_required');
    final h = await _home(
      t,
      targets,
      consents: FakeConsentsClient(granted: {'terms'}),
    );
    expect(find.byKey(TodayTargetsCard.consentKey), findsOneWidget);
    expect(find.text(en.diaryTargetsConsent), findsOneWidget);
    expect(h.router.routerDelegate.currentConfiguration.uri.path, '/home');
    // The rest of Home still works.
    expect(find.byKey(HomeCards.cardKey('today_protein')), findsOneWidget);
    await _tap(t, TodayTargetsCard.consentButtonKey);
    expect(find.byKey(ConsentSheet.agreeKey), findsOneWidget);
  });

  testWidgets('eye toggle stays and works after health_data is withdrawn', (
    t,
  ) async {
    final targets = FakeTargetsClient(today: 'g1_build_muscle')
      ..getError = apiError(403, 'consent_required')
      ..settingsGetError = apiError(403, 'consent_required');
    await _home(t, targets, consents: FakeConsentsClient(granted: {'terms'}));
    expect(find.byKey(TodayTargetsCard.consentKey), findsOneWidget);
    await _tap(t, EyeToggle.buttonKey);
    expect(
      targets.displays.single.numbersDisplay,
      DisplayInNumbersDisplay.hideAll,
    );
    await _tap(t, EyeToggle.buttonKey);
    expect(
      targets.displays.last.numbersDisplay,
      DisplayInNumbersDisplay.valueShow,
    );
  });

  testWidgets('eye toggle 404 shows neutral copy, no crash', (t) async {
    final targets = FakeTargetsClient(today: 'g1_build_muscle')
      ..getError = apiError(403, 'consent_required')
      ..settingsGetError = apiError(403, 'consent_required')
      ..displayError = apiError(404, 'not_found');
    await _home(t, targets, consents: FakeConsentsClient(granted: {'terms'}));
    await _tap(t, EyeToggle.buttonKey);
    expect(find.text(en.targetsIntroBody), findsOneWidget);
    expect(t.takeException(), isNull);
  });

  testWidgets('eye toggle hides every number in one tap', (t) async {
    final targets =
        FakeTargetsClient(
            today: 'g1_build_muscle',
            settings: goalSettingsOut(activity: 'moderate'),
          )
          ..todayForDisplay = (d) => targetsFixture(
            d == 'hide_all' ? 'g1_hide_all' : 'g1_build_muscle',
          );
    await _home(
      t,
      targets,
      dayFor: (_) => diaryFixture(
        targets.settings?.numbersDisplay.json == 'hide_all'
            ? 'day_hide_all'
            : 'day_complete_under',
      ),
    );
    expect(_digits, findsWidgets);
    await _tap(t, EyeToggle.buttonKey);
    expect(
      targets.displays.single.numbersDisplay,
      DisplayInNumbersDisplay.hideAll,
    );
    expect(_digits, findsNothing);
    expect(_in(find.text(en.diaryHiddenNumbers)), findsOneWidget);
    // And back with another tap.
    await _tap(t, EyeToggle.buttonKey);
    expect(
      targets.displays.last.numbersDisplay,
      DisplayInNumbersDisplay.valueShow,
    );
    expect(_in(find.textContaining('2,760')), findsOneWidget);
  });

  testWidgets('un-hiding a rate-limited toggle shows the standard error', (
    t,
  ) async {
    final targets = FakeTargetsClient(
      today: 'g1_hide_all',
      settings: goalSettingsOut(
        activity: 'moderate',
        numbersDisplay: 'hide_all',
      ),
    )..displayError = apiError(429, 'rate_limited');
    await _home(t, targets, day: 'day_hide_all');
    await _tap(t, EyeToggle.buttonKey);
    expect(find.text(en.errorRateLimited), findsOneWidget);
    expect(_digits, findsNothing);
  });

  testWidgets('hide_energy shows macros but no kcal', (t) async {
    await _home(
      t,
      FakeTargetsClient(
        today: 'g1_hide_energy',
        settings: goalSettingsOut(
          activity: 'moderate',
          numbersDisplay: 'hide_energy',
        ),
      ),
      day: 'day_hide_energy',
    );
    expect(find.byKey(TodayTargetsCard.rowKey('energy')), findsNothing);
    expect(_in(find.textContaining('kcal')), findsNothing);
    expect(_in(find.textContaining('112 g')), findsOneWidget);
    expect(_in(find.text('77 g')), findsOneWidget);
  });

  testWidgets('incomplete energy shows the grey chip', (t) async {
    await _home(
      t,
      FakeTargetsClient(today: 'g1_build_muscle'),
      day: 'day_incomplete_energy',
    );
    expect(find.byKey(TodayTargetsCard.incompleteKey), findsOneWidget);
    expect(_in(find.text(en.diaryIncomplete)), findsOneWidget);
    // No eaten number and no "left" for the incomplete total: the target only.
    expect(_in(find.text('2,760 kcal')), findsOneWidget);
    expect(find.byKey(const Key('today-remaining-energy')), findsNothing);
  });

  testWidgets('over target uses the neutral tone', (t) async {
    await _home(
      t,
      FakeTargetsClient(today: 'g1_build_muscle'),
      day: 'day_over_energy',
    );
    // The API's remaining is -250.4: "250 kcal over", in a neutral colour.
    final line = find.text(en.diaryOver('250 kcal'));
    expect(line, findsOneWidget);
    final c = SnColors.of(t.element(line));
    final color = t.widget<Text>(line).style?.color;
    expect(color, c.textSecondary);
    expect(color, isNot(verdictTone(c, 'avoid').color));
    expect(color, isNot(Theme.of(t.element(line)).colorScheme.error));
  });

  testWidgets('disclaimer and pending review shown', (t) async {
    await _home(t, FakeTargetsClient(today: 'g1_build_muscle'));
    expect(_in(find.text(en.diaryDisclaimer)), findsOneWidget);
    expect(find.byKey(PendingReviewNote.noteKey), findsOneWidget);
    expect(find.text(en.targetsPendingReview), findsOneWidget);
  });

  testWidgets('minor and pregnancy statuses show their message', (t) async {
    await _home(t, FakeTargetsClient(today: 'g6_minor'));
    expect(_in(find.text(en.targetsMinor)), findsOneWidget);
  });

  testWidgets('weight_loss mode shows today_targets first', (t) async {
    await _home(
      t,
      FakeTargetsClient(today: 'g1_build_muscle'),
      mode: 'weight_loss',
    );
    final ys = {
      for (final c in ['today_targets', 'today_sugar_salt', 'recent_scans'])
        c: t.getTopLeft(find.byKey(HomeCards.cardKey(c))).dy,
    };
    expect(ys['today_targets']!, lessThan(ys['today_sugar_salt']!));
  });
}
