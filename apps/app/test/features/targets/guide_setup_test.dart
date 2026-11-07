import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/theme/verdict_colors.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/features/home/presentation/home_screen.dart';
import 'package:smartnutri_ai/features/members/presentation/consent_sheet.dart';
import 'package:smartnutri_ai/features/members/presentation/member_form_screen.dart';
import 'package:smartnutri_ai/features/targets/presentation/about_you_step.dart';
import 'package:smartnutri_ai/features/targets/presentation/activity_step.dart';
import 'package:smartnutri_ai/features/targets/presentation/flag_notes.dart';
import 'package:smartnutri_ai/features/targets/presentation/goal_step.dart';
import 'package:smartnutri_ai/features/targets/presentation/guide_result_step.dart';
import 'package:smartnutri_ai/features/targets/presentation/guide_setup_screen.dart';
import 'package:smartnutri_ai/features/targets/presentation/numbers_choice.dart';
import 'package:smartnutri_ai/features/targets/presentation/targets_explanation.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart' show apiError;
import '../../support/fake_members.dart';
import '../../support/fake_targets.dart';
import '../../support/fake_user_types.dart';
import '../../support/fixtures.dart';
import '../user_types/user_types_harness.dart';

MemberOut _primary({num? bodyFat, MemberOutGoal? goal}) => memberOut(
  id: 'p1',
  name: 'Ravi',
  relation: MemberOutRelation.self,
  birthYear: 1997,
  sex: MemberOutSex.male,
  heightCm: 175,
  weightKg: 70,
  bodyFatPct: bodyFat,
  goal: goal,
  diet: MemberOutDiet.nonVeg,
  isPrimary: true,
);

class _Setup {
  _Setup(this.h, this.targets, this.members, this.consents);
  final AppHarness h;
  final FakeTargetsClient targets;
  final FakeMembersClient members;
  final FakeConsentsClient consents;
}

Future<_Setup> _open(
  WidgetTester t, {
  FakeTargetsClient? targets,
  MemberOut? member,
  FakeConsentsClient? consents,
  String initial = '/guide/setup',
}) async {
  final fakeTargets = targets ?? FakeTargetsClient(today: 'g1_build_muscle');
  final fakeMembers = FakeMembersClient([member ?? _primary()]);
  final fakeConsents =
      consents ?? FakeConsentsClient(granted: {'terms', 'health_data'});
  final h = await pumpApp(
    t,
    FakeUserTypesApi(
      me: FakeUserTypesMe(userTypesOut(types: ['gym'])),
      members: fakeMembers,
      consents: fakeConsents,
      targets: fakeTargets,
    ),
    initial: initial,
  );
  return _Setup(h, fakeTargets, fakeMembers, fakeConsents);
}

Future<void> _tap(WidgetTester t, Key key) async {
  await t.ensureVisible(find.byKey(key));
  await t.pumpAndSettle();
  await t.tap(find.byKey(key));
  await t.pumpAndSettle();
}

Future<void> _next(WidgetTester t) => _tap(t, GuideSetupScreen.nextKey);

/// Taps without settling: an open consent sheet keeps the busy spinner
/// of the screen under it running.
Future<void> _tapAndPump(WidgetTester t, Key key) async {
  await t.ensureVisible(find.byKey(key));
  await t.pump();
  await t.tap(find.byKey(key));
  await t.pump(const Duration(seconds: 1));
}

/// Intro, about you, activity, goal, then the guide step.
Future<void> _toGuide(WidgetTester t) async {
  await _next(t);
  await _next(t);
  await _tap(t, ActivityStep.levelKey('light'));
  await _next(t);
  await _next(t);
}

Future<void> _agree(WidgetTester t) async {
  await t.pump(const Duration(seconds: 1)); // the sheet finishes sliding up
  await t.ensureVisible(find.byKey(ConsentSheet.agreeKey));
  await t.pump();
  await t.tap(find.byKey(ConsentSheet.agreeKey));
  await t.pumpAndSettle();
}

TargetsOut _withUnusual(String stem, List<String> fields) =>
    TargetsOut.fromJson({...targetsJson(stem), 'unusual_fields': fields});

Color? _textColor(WidgetTester t, Finder f) =>
    t.widget<Text>(f).style?.color ??
    DefaultTextStyle.of(t.element(f)).style.color;

void main() {
  testWidgets('onboarding preselects show numbers', (t) async {
    await _open(t);
    final group = t.widget<RadioGroup<String>>(find.byType(RadioGroup<String>));
    expect(group.groupValue, 'show');
    expect(find.byKey(NumbersChoice.optionKey('hide_all')), findsOneWidget);
    expect(find.text(en.targetsSkip), findsOneWidget);
  });

  testWidgets('body fat field shows the hint', (t) async {
    await _open(t);
    await _next(t);
    expect(find.byKey(AboutYouStep.bodyFatKey), findsOneWidget);
    expect(find.text(en.targetsBodyFatHint), findsOneWidget);
  });

  testWidgets('blank body fat is saved as unknown', (t) async {
    final s = await _open(t);
    await _toGuide(t);
    await _tap(t, GuideSetupScreen.saveKey);
    final patch = s.members.patched.single.$2;
    expect(patch.bodyFatPct, isNull);
    expect(patch.clearBodyFatPct, isFalse);
    expect(s.targets.puts, hasLength(1));
  });

  testWidgets('clearing a stored body fat sends clear flag', (t) async {
    final s = await _open(t, member: _primary(bodyFat: 15));
    await _next(t);
    expect(find.text('15'), findsOneWidget);
    await t.enterText(find.byKey(AboutYouStep.bodyFatKey), '');
    await _next(t);
    await _tap(t, ActivityStep.levelKey('light'));
    await _next(t);
    await _next(t);
    await _tap(t, GuideSetupScreen.saveKey);
    final patch = s.members.patched.single.$2;
    expect(patch.clearBodyFatPct, isTrue);
    expect(patch.bodyFatPct, isNull);
  });

  testWidgets('member save keeps body fat', (t) async {
    final s = await _open(
      t,
      member: _primary(bodyFat: 15),
      initial: '/family/p1',
    );
    await _tap(t, MemberFormScreen.saveKey);
    final patch = s.members.patched.single.$2;
    expect(patch.clearBodyFatPct, isFalse);
    expect(patch.bodyFatPct, isNull);
    expect(s.members.members.single.bodyFatPct, 15);
  });

  testWidgets('out-of-range body fat shows the API message', (t) async {
    final s = await _open(t);
    s.targets.previewErrors.add(
      apiError(422, 'body_fat_out_of_range', details: {'min': 3, 'max': 70}),
    );
    await _next(t);
    await t.enterText(find.byKey(AboutYouStep.bodyFatKey), '2.9');
    await _next(t);
    await _tap(t, ActivityStep.levelKey('light'));
    await _next(t);
    expect(
      find.text('Please enter a number between 3 and 70.'),
      findsOneWidget,
    );
    expect(find.byKey(AboutYouStep.bodyFatKey), findsOneWidget);
  });

  testWidgets('guide step renders g2_lose_adjusted', (t) async {
    final s = await _open(t);
    s.targets.previewResult = targetsFixture('g2_lose_adjusted');
    await _toGuide(t);
    expect(find.textContaining('1,540'), findsOneWidget);
    expect(find.text('71 g'), findsOneWidget);
    expect(find.text('43 g'), findsOneWidget);
    expect(find.text('217 g'), findsOneWidget);
    await _tap(t, TargetsExplanationTile.tileKey);
    expect(
      find.text(en.targetsHowProteinAdjusted('1.2', '59.3')),
      findsOneWidget,
    );
    expect(find.textContaining('59.3'), findsOneWidget);
    expect(find.text(en.proteinKidneyNote), findsOneWidget);
    expect(find.text(en.targetsPendingReview), findsOneWidget);
    expect(find.text(en.diaryDisclaimer), findsOneWidget);
  });

  testWidgets('guide step shows lean basis for g11_lean_mass', (t) async {
    final s = await _open(t);
    s.targets.previewResult = targetsFixture('g11_lean_mass');
    await _toGuide(t);
    await _tap(t, TargetsExplanationTile.tileKey);
    final e = targetsFixture('g11_lean_mass').explanation!;
    expect(e.proteinReferenceWeightKg, 59.5);
    expect(find.text(en.targetsHowProteinLean('2', '59.5')), findsOneWidget);
  });

  testWidgets('floor note renders for g4_floor in a neutral style', (t) async {
    final s = await _open(t);
    s.targets.previewResult = targetsFixture('g4_floor');
    await _toGuide(t);
    final note = find.byKey(FlagNotes.noteKey('floor_applied'));
    expect(note, findsOneWidget);
    final text = find.descendant(of: note, matching: find.byType(Text));
    expect((t.widget<Text>(text).data ?? ''), contains('1,200'));
    final c = SnColors.of(t.element(text));
    final danger = verdictTone(c, 'avoid').color;
    expect(_textColor(t, text), isNot(danger));
    final box = t.widget<Container>(note);
    expect((box.decoration! as BoxDecoration).color, isNot(danger));
  });

  testWidgets('hidden floor note for g4_hide_all has no digits', (t) async {
    final s = await _open(t);
    s.targets.previewResult = targetsFixture('g4_hide_all');
    await _toGuide(t);
    final note = find.byKey(FlagNotes.noteKey('floor_applied'));
    final text = t.widget<Text>(
      find.descendant(of: note, matching: find.byType(Text)),
    );
    expect(text.data, en.targetsFlagFloorAppliedHidden);
    expect(text.data, isNot(contains(RegExp(r'\d'))));
  });

  testWidgets('minor shows adults-only message', (t) async {
    final s = await _open(t);
    s.targets.previewResult = targetsFixture('g6_minor');
    await _toGuide(t);
    expect(find.text(en.targetsMinor), findsOneWidget);
    expect(find.byKey(TargetRows.rowKey('energy')), findsNothing);
  });

  testWidgets('pregnancy shows paused message', (t) async {
    final s = await _open(t);
    s.targets.previewResult = targetsFixture('pregnancy');
    await _toGuide(t);
    expect(find.text(en.targetsPregnancyPaused), findsOneWidget);
  });

  testWidgets('underweight lose offers maintenance', (t) async {
    final s = await _open(t, member: _primary(goal: MemberOutGoal.weightLoss));
    s.targets.previewErrors.add(apiError(422, 'goal_not_allowed_underweight'));
    await _next(t);
    await _next(t);
    await _tap(t, ActivityStep.levelKey('light'));
    await _next(t);
    expect(find.text(en.targetsUnderweight), findsOneWidget);
    final chip = t.widget<ChoiceChip>(
      find.byKey(GoalStep.directionKey('maintain')),
    );
    expect(chip.selected, isTrue);
    expect(
      s.targets.previews.last.direction,
      TargetsPreviewInDirection.maintain,
    );
  });

  testWidgets('needs_height_cm highlights height', (t) async {
    final s = await _open(t);
    s.targets.previewResult = targetsFixture('needs_height_cm');
    await _toGuide(t);
    expect(
      find.text(en.targetsNeedsBodyData(en.membersFormHeightCm)),
      findsOneWidget,
    );
    await _tap(t, GuideSetupScreen.editAnswersKey);
    expect(find.byKey(AboutYouStep.heightKey), findsOneWidget);
    expect(
      find.text(en.targetsNeedsBodyData(en.membersFormHeightCm)),
      findsOneWidget,
    );
  });

  testWidgets('rate chips show kg from rate_options', (t) async {
    final json = targetsJson('g2_lose_adjusted');
    final options = [
      for (final o in json['rate_options']! as List)
        Map<String, Object?>.from(o as Map),
    ];
    options.first['kg_per_week'] = 0.37;
    final s = await _open(t, member: _primary(goal: MemberOutGoal.weightLoss));
    s.targets.previewResult = TargetsOut.fromJson({
      ...json,
      'rate_options': options,
    });
    await _next(t);
    await _next(t);
    await _tap(t, ActivityStep.levelKey('light'));
    await _next(t);
    final chip = find.byKey(GoalStep.rateKey(0));
    expect(chip, findsOneWidget);
    expect(
      find.descendant(of: chip, matching: find.textContaining('0.37')),
      findsOneWidget,
    );
    await _tap(t, GoalStep.rateKey(1));
    expect(s.targets.previews.last.ratePctBwPerWeek, 0.5);
  });

  testWidgets('g1_hide_all preview shows no digits for energy and macros', (
    t,
  ) async {
    final s = await _open(t);
    s.targets.previewResult = targetsFixture('g1_hide_all');
    await _toGuide(t);
    for (final row in ['energy', 'protein', 'fat', 'carbs']) {
      expect(find.byKey(TargetRows.rowKey(row)), findsNothing);
    }
    expect(find.byKey(TargetRows.hiddenKey), findsOneWidget);
    await _tap(t, TargetsExplanationTile.tileKey);
    expect(
      find.descendant(
        of: find.byKey(TargetsExplanationTile.tileKey),
        matching: find.textContaining(RegExp(r'\d')),
      ),
      findsNothing,
    );
  });

  testWidgets('missing consent opens the health-data sheet before save', (
    t,
  ) async {
    final consents = FakeConsentsClient(granted: {'terms'});
    final s = await _open(t, consents: consents);
    s.targets.previewResult = targetsFixture('g1_build_muscle');
    await _next(t);
    await _next(t);
    await _tap(t, ActivityStep.levelKey('light'));
    await _tapAndPump(t, GuideSetupScreen.nextKey);
    expect(find.byKey(ConsentSheet.agreeKey), findsOneWidget);
    expect(s.targets.puts, isEmpty);
    await _agree(t);
    expect(
      consents.recorded.map((c) => c.purpose.json),
      contains('health_data'),
    );
  });

  testWidgets('consent_required on save asks then retries', (t) async {
    final s = await _open(t);
    s.targets.previewResult = targetsFixture('g1_build_muscle');
    await _toGuide(t);
    s.targets.putErrors.add(apiError(403, 'consent_required'));
    s.consents.granted.remove('health_data');
    await _tapAndPump(t, GuideSetupScreen.saveKey);
    expect(find.byKey(ConsentSheet.agreeKey), findsOneWidget);
    await _agree(t);
    expect(s.targets.puts, hasLength(2));
    expect(find.byType(HomeScreen), findsOneWidget);
  });

  testWidgets('unusual height asks for confirmation', (t) async {
    final s = await _open(t);
    s.targets.previewResult = _withUnusual('g1_build_muscle', ['height_cm']);
    await _toGuide(t);
    expect(
      find.text(en.targetsUnusualConfirm(en.membersFormHeightCm)),
      findsOneWidget,
    );
    FilledButton save() =>
        t.widget<FilledButton>(find.byKey(GuideSetupScreen.saveKey));
    expect(save().onPressed, isNull);
    await _tap(t, GuideSetupScreen.unusualKey);
    expect(save().onPressed, isNotNull);
  });

  testWidgets('skip goes home without saving', (t) async {
    final s = await _open(t);
    await _tap(t, GuideSetupScreen.skipKey);
    expect(find.byType(HomeScreen), findsOneWidget);
    expect(s.targets.puts, isEmpty);
    expect(s.members.patched, isEmpty);
  });

  testWidgets('pregnancy prefer-not is sent as true', (t) async {
    final s = await _open(t);
    s.targets.previewResult = targetsFixture('g1_build_muscle');
    await _next(t);
    await _next(t);
    await _tap(t, ActivityStep.levelKey('light'));
    await _next(t);
    await _tap(t, GoalStep.pregnancyKey('prefer_not'));
    expect(s.targets.previews.last.pregnantOrBreastfeeding, isTrue);
  });
}
