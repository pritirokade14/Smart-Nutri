import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/consent/presentation/consent_screen.dart';
import 'package:smartnutri_ai/features/home/presentation/home_screen.dart';
import 'package:smartnutri_ai/features/members/presentation/consent_sheet.dart';
import 'package:smartnutri_ai/features/members/presentation/members_providers.dart';
import 'package:smartnutri_ai/features/settings/presentation/profile_screen.dart';
import 'package:smartnutri_ai/features/user_types/presentation/follow_up_screen.dart';
import 'package:smartnutri_ai/features/user_types/presentation/prefill_review_screen.dart';
import 'package:smartnutri_ai/features/user_types/presentation/type_picker_screen.dart';
import 'package:smartnutri_ai/features/user_types/presentation/user_types_providers.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart' show apiError;
import '../../support/fake_members.dart';
import '../../support/fake_user_types.dart';
import 'user_types_harness.dart';

Future<void> _tapKey(WidgetTester t, Key key) async {
  await t.ensureVisible(find.byKey(key));
  await t.pumpAndSettle();
  await t.tap(find.byKey(key));
  await t.pumpAndSettle();
}

Future<void> _pick(WidgetTester t, String type) =>
    _tapKey(t, TypePickerScreen.tileKey(type));

bool _checked(WidgetTester t, Key key) =>
    t.widget<CheckboxListTile>(find.byKey(key)).value ?? false;

void main() {
  testWidgets('terms then picker redirect', (t) async {
    final consents = FakeConsentsClient();
    final api = FakeUserTypesApi(consents: consents);
    final h = await pumpApp(t, api);
    // Terms first: no picker before the terms are agreed.
    expect(find.byType(ConsentScreen), findsOneWidget);
    expect(find.byType(TypePickerScreen), findsNothing);
    consents.granted.add('terms');
    h.container.invalidate(consentStateProvider);
    await t.pumpAndSettle();
    expect(find.byType(TypePickerScreen), findsOneWidget);
    // Other routes lead back to the picker until it is answered.
    h.router.go('/history');
    await t.pumpAndSettle();
    expect(find.byType(TypePickerScreen), findsOneWidget);
  });

  testWidgets('no picker once answered', (t) async {
    final api = FakeUserTypesApi(
      me: FakeUserTypesMe(userTypesOut(types: ['gym'])),
    );
    final h = await pumpApp(t, api);
    expect(find.byType(HomeScreen), findsOneWidget);
    h.router.go('/welcome');
    await t.pumpAndSettle();
    expect(find.byType(TypePickerScreen), findsNothing);
    expect(find.byType(HomeScreen), findsOneWidget);
  });

  testWidgets('a failed user-types load lets the app go on', (t) async {
    final me = FakeUserTypesMe()..getError = StateError('offline');
    await pumpApp(t, FakeUserTypesApi(me: me));
    expect(find.byType(HomeScreen), findsOneWidget);
  });

  testWidgets('max three selections', (t) async {
    final h = await pumpApp(t, FakeUserTypesApi());
    for (final type in ['health_condition', 'family', 'gym']) {
      await _pick(t, type);
    }
    await _pick(t, 'eat_better');
    expect(find.text(en.userTypesMaxReached), findsOneWidget);
    final selected = h.container.read(userTypesDraftProvider).types;
    expect(selected, ['health_condition', 'family', 'gym']);
  });

  testWidgets('skip stores empty types and lands on home', (t) async {
    final api = FakeUserTypesApi();
    await pumpApp(t, api);
    await _tapKey(t, TypePickerScreen.skipKey);
    expect(api.me.puts.single.types, isEmpty);
    expect(
      api.me.puts.single.followUps?.toJson().values.whereType<Object>(),
      isEmpty,
    );
    expect(find.byType(HomeScreen), findsOneWidget);
    expect(api.members.patched, isEmpty);
  });

  testWidgets('health tile without consent opens consent sheet; declined '
      'drops it with note', (t) async {
    final api = FakeUserTypesApi(
      consents: FakeConsentsClient(granted: {'terms'}),
    );
    await pumpApp(t, api);
    await _pick(t, 'health_condition');
    await _pick(t, 'family');
    await _tapKey(t, TypePickerScreen.continueKey);
    expect(find.byType(ConsentSheet), findsOneWidget);
    expect(api.me.puts, isEmpty, reason: 'consent is asked before the PUT');
    await t.tap(find.byKey(ConsentSheet.declineKey));
    await t.pumpAndSettle();
    expect(find.text(en.userTypesConsentNeeded), findsWidgets);
    // The rest goes on: the family follow-up, then the save.
    expect(find.byType(FollowUpScreen), findsOneWidget);
    await _tapKey(t, FollowUpScreen.chipKey('family', 'children'));
    await _tapKey(t, FollowUpScreen.nextKey);
    final put = api.me.puts.single;
    expect([for (final x in put.types) x.json], ['family']);
    expect(put.followUps?.conditions, isNull);
    expect([for (final f in put.followUps!.familyWith!) f.json], ['children']);
    expect(find.byType(HomeScreen), findsOneWidget);
  });

  testWidgets('a health tile with consent saves its follow-up', (t) async {
    final api = FakeUserTypesApi(
      consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
    );
    await pumpApp(t, api);
    await _pick(t, 'health_condition');
    await _tapKey(t, TypePickerScreen.continueKey);
    expect(find.byType(ConsentSheet), findsNothing);
    await _tapKey(t, FollowUpScreen.chipKey('conditions', 'diabetes'));
    await _tapKey(t, FollowUpScreen.nextKey);
    final put = api.me.puts.single;
    expect([for (final c in put.followUps!.conditions!) c.json], ['diabetes']);
  });

  testWidgets('a 403 on the save opens the consent sheet and retries', (
    t,
  ) async {
    final api = FakeUserTypesApi(
      consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
    );
    api.me.putErrors.add(apiError(403, 'consent_required'));
    await pumpApp(t, api);
    await _pick(t, 'weight_loss');
    await _tapKey(t, TypePickerScreen.continueKey);
    expect(find.byType(ConsentSheet), findsOneWidget);
    await t.tap(find.byKey(ConsentSheet.agreeKey));
    await t.pumpAndSettle();
    expect(api.me.puts, hasLength(2));
    expect(find.byType(HomeScreen), findsOneWidget);
  });

  testWidgets('defaults are not saved until confirmed', (t) async {
    final api = FakeUserTypesApi(
      consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
    );
    api.me.prefillAfterPut = (_) => prefillSuggestion(
      changes: [
        prefillChange(
          'custom_alerts',
          current: <String>[],
          value: ['palm_oil'],
          added: ['palm_oil'],
        ),
      ],
    );
    await pumpApp(t, api);
    await _pick(t, 'eat_better');
    await _tapKey(t, TypePickerScreen.continueKey);
    await _tapKey(t, FollowUpScreen.chipKey('alerts', 'palm_oil'));
    await _tapKey(t, FollowUpScreen.nextKey);
    expect(find.byType(PrefillReviewScreen), findsOneWidget);
    expect(api.members.patched, isEmpty);
    expect(_checked(t, PrefillReviewScreen.changeKey('custom_alerts')), isTrue);
    await _tapKey(t, PrefillReviewScreen.applyKey);
    expect(api.members.patched, hasLength(1));
    final (id, body) = api.members.patched.single;
    expect(id, 'p1');
    expect([for (final a in body.customAlerts!) a.json], ['palm_oil']);
    expect(find.byType(HomeScreen), findsOneWidget);
  });

  testWidgets('not now sends nothing', (t) async {
    final api = FakeUserTypesApi();
    api.me.prefillAfterPut = (_) => prefillSuggestion(
      changes: [
        prefillChange(
          'custom_alerts',
          current: <String>[],
          value: ['msg'],
          added: ['msg'],
        ),
      ],
    );
    await pumpApp(t, api);
    await _pick(t, 'eat_better');
    await _tapKey(t, TypePickerScreen.continueKey);
    await _tapKey(t, FollowUpScreen.nextKey);
    await _tapKey(t, PrefillReviewScreen.notNowKey);
    expect(api.members.patched, isEmpty);
    expect(find.byType(HomeScreen), findsOneWidget);
  });

  testWidgets('only ticked changes are sent', (t) async {
    final members = FakeMembersClient([
      memberOut(
        id: 'p1',
        name: 'Ravi',
        relation: MemberOutRelation.self,
        birthYear: 1985,
        diet: MemberOutDiet.nonVeg,
        weightKg: 70,
        isPrimary: true,
      ),
    ]);
    final api = FakeUserTypesApi(
      members: members,
      consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
    );
    api.me.prefillAfterPut = (_) => prefillSuggestion(
      changes: [
        prefillChange(
          'conditions',
          current: <String>[],
          value: ['diabetes'],
          added: ['diabetes'],
          reason: 'health_condition',
        ),
        prefillChange('goal', value: 'weight_loss', reason: 'weight_loss'),
      ],
    );
    await pumpApp(t, api);
    await _pick(t, 'health_condition');
    await _pick(t, 'weight_loss');
    await _tapKey(t, TypePickerScreen.continueKey);
    await _tapKey(t, FollowUpScreen.chipKey('conditions', 'diabetes'));
    await _tapKey(t, FollowUpScreen.nextKey);
    // The follow-up chose the condition; the goal comes from the type only.
    expect(_checked(t, PrefillReviewScreen.changeKey('conditions')), isTrue);
    expect(_checked(t, PrefillReviewScreen.changeKey('goal')), isFalse);
    // Untick the condition, tick the goal.
    await _tapKey(t, PrefillReviewScreen.changeKey('conditions'));
    await _tapKey(t, PrefillReviewScreen.changeKey('goal'));
    await _tapKey(t, PrefillReviewScreen.applyKey);
    final (_, body) = members.patched.single;
    expect(body.conditions, isEmpty);
    expect(body.goal?.json, 'weight_loss');
    // Everything else is the member as stored.
    expect(body.diet?.json, 'non_veg');
    expect(body.weightKg, 70);
    expect(body.birthYear, 1985);
  });

  testWidgets('goal conflict defaults to neither', (t) async {
    final api = FakeUserTypesApi(
      consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
    );
    api.me.prefillAfterPut = (_) =>
        prefillSuggestion(goalChoice: ['weight_loss', 'build_muscle']);
    await pumpApp(t, api);
    await _pick(t, 'weight_loss');
    await _pick(t, 'gym');
    await _tapKey(t, TypePickerScreen.continueKey);
    await _tapKey(t, FollowUpScreen.chipKey('gym', 'build_muscle'));
    await _tapKey(t, FollowUpScreen.nextKey);
    expect(find.text(en.userTypesPrefillGoalConflict), findsOneWidget);
    final neither = t.widget<RadioGroup<String>>(
      find.byType(RadioGroup<String>),
    );
    expect(neither.groupValue, '');
    expect(find.text(en.userTypesPrefillGoalNeither), findsOneWidget);
    await _tapKey(t, PrefillReviewScreen.applyKey);
    expect(api.members.patched, isEmpty, reason: 'neither: nothing to send');
  });

  testWidgets('a picked conflict goal is sent', (t) async {
    final api = FakeUserTypesApi(
      consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
    );
    api.me.prefillAfterPut = (_) =>
        prefillSuggestion(goalChoice: ['weight_loss', 'build_muscle']);
    await pumpApp(t, api);
    await _pick(t, 'weight_loss');
    await _pick(t, 'gym');
    await _tapKey(t, TypePickerScreen.continueKey);
    await _tapKey(t, FollowUpScreen.nextKey);
    await _tapKey(t, PrefillReviewScreen.goalKey('build_muscle'));
    await _tapKey(t, PrefillReviewScreen.applyKey);
    expect(api.members.patched.single.$2.goal?.json, 'build_muscle');
  });

  testWidgets('editing types in profile never sends a members PATCH by '
      'itself', (t) async {
    final api = FakeUserTypesApi(
      me: FakeUserTypesMe(userTypesOut(types: ['family'])),
    );
    api.me.prefillAfterPut = (_) => prefillSuggestion(
      changes: [
        prefillChange(
          'custom_alerts',
          current: <String>[],
          value: ['maida'],
          added: ['maida'],
        ),
      ],
    );
    final h = await pumpApp(t, api, initial: '/profile');
    expect(find.byType(ProfileScreen), findsOneWidget);
    await _tapKey(t, ProfileScreen.userTypesKey);
    expect(find.byType(TypePickerScreen), findsOneWidget);
    // Prefilled with the stored types; no "Skip" when editing.
    expect(find.byKey(TypePickerScreen.skipKey), findsNothing);
    await _pick(t, 'eat_better');
    await _tapKey(t, TypePickerScreen.continueKey);
    await _tapKey(t, FollowUpScreen.nextKey); // family
    await _tapKey(t, FollowUpScreen.nextKey); // eat better
    expect(
      [for (final x in api.me.puts.single.types) x.json],
      ['family', 'eat_better'],
    );
    expect(find.byType(PrefillReviewScreen), findsOneWidget);
    await _tapKey(t, PrefillReviewScreen.notNowKey);
    expect(api.members.patched, isEmpty);
    expect(api.members.calls.where((c) => c == 'update'), isEmpty);
    expect(find.byType(ProfileScreen), findsOneWidget);
    expect(h.router.routerDelegate.currentConfiguration.uri.path, '/profile');
  });

  testWidgets('no analytics events', (t) async {
    final api = FakeUserTypesApi(
      consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
    );
    api.me.prefillAfterPut = (_) => prefillSuggestion(
      changes: [prefillChange('goal', value: 'build_muscle', reason: 'gym')],
    );
    final h = await pumpApp(t, api);
    await _pick(t, 'gym');
    await _pick(t, 'allergy_diet');
    await _tapKey(t, TypePickerScreen.continueKey);
    await _tapKey(t, FollowUpScreen.chipKey('allergens', 'peanut'));
    await _tapKey(t, FollowUpScreen.nextKey);
    await _tapKey(t, FollowUpScreen.chipKey('gym', 'build_muscle'));
    await _tapKey(t, FollowUpScreen.nextKey);
    expect(_checked(t, PrefillReviewScreen.changeKey('goal')), isTrue);
    await _tapKey(t, PrefillReviewScreen.applyKey);
    expect(api.members.patched, hasLength(1));
    expect(h.events, isEmpty);
  });

  test('all copy from l10n', () {
    final literal = RegExp(
      r'''(Text|labelText:|hintText:|tooltip:|semanticsLabel:)\s*\(?\s*['"]''',
    );
    final dir = Directory('lib/features/user_types');
    final offenders = <String>[];
    for (final f in dir.listSync(recursive: true).whereType<File>()) {
      if (!f.path.endsWith('.dart')) continue;
      final lines = f.readAsLinesSync();
      for (final (i, line) in lines.indexed) {
        if (literal.hasMatch(line)) offenders.add('${f.path}:${i + 1}');
      }
    }
    expect(offenders, isEmpty);
  });
}
