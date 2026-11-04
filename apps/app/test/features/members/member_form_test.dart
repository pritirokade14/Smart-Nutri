import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/members/presentation/consent_sheet.dart';
import 'package:smartnutri_ai/features/members/presentation/member_form_screen.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_members.dart';
import 'members_harness.dart';

Future<void> fillNew(
  WidgetTester t,
  String locale, {
  String name = 'Asha',
  String year = '2015',
}) async {
  final l = l10nFor(locale);
  await t.enterText(find.byKey(MemberFormScreen.nameKey), name);
  await t.tap(find.text(l.membersRelationChild));
  await t.enterText(find.byKey(MemberFormScreen.birthYearKey), year);
  await t.pump();
}

Finder inDialog(String text) =>
    find.descendant(of: find.byType(AlertDialog), matching: find.text(text));

Future<void> save(WidgetTester t) async {
  await t.tap(find.byKey(MemberFormScreen.saveKey));
  await t.pumpAndSettle();
}

void main() {
  for (final locale in ['en', 'hi']) {
    testWidgets('saves member with other allergen [$locale]', (t) async {
      final members = FakeMembersClient();
      await pumpMembers(
        t,
        const MemberFormScreen(),
        members: members,
        consents: FakeConsentsClient(granted: {'health_data'}),
        locale: locale,
      );
      await fillNew(t, locale);
      await t.enterText(find.byKey(MemberFormScreen.otherAllergenKey), 'Kiwi');
      await t.tap(find.byKey(MemberFormScreen.addAllergenKey));
      await t.pump();
      expect(find.text('Kiwi'), findsOneWidget); // now a chip
      await save(t);

      final body = members.created.single;
      expect(body.allergens, ['Kiwi']);
      expect(body.name, 'Asha');
      expect(body.relation, MemberInRelation.child);
      expect(body.birthYear, 2015);
    });

    testWidgets('shows consent sheet before saving conditions [$locale]', (
      t,
    ) async {
      final l = l10nFor(locale);
      final members = FakeMembersClient();
      await pumpMembers(
        t,
        const MemberFormScreen(),
        members: members,
        consents: FakeConsentsClient(),
        locale: locale,
      );
      await fillNew(t, locale);
      await t.tap(find.text(l.conditionDiabetes));
      await t.pump();
      await save(t);

      expect(find.byType(ConsentSheet), findsOneWidget);
      expect(find.text(l.consentHealthDataBody), findsOneWidget);
      expect(members.calls.where((c) => c != 'list'), isEmpty);

      // Declining leaves the form unsaved.
      await t.tap(find.byKey(ConsentSheet.declineKey));
      await t.pumpAndSettle();
      expect(find.byType(ConsentSheet), findsNothing);
      expect(members.created, isEmpty);
    });
  }

  testWidgets('agreeing in the sheet records consent, then saves', (t) async {
    final members = FakeMembersClient();
    final consents = FakeConsentsClient();
    await pumpMembers(
      t,
      const MemberFormScreen(),
      members: members,
      consents: consents,
    );
    await fillNew(t, 'en');
    await t.tap(find.text(l10nFor('en').conditionDiabetes));
    await save(t);
    await t.tap(find.byKey(ConsentSheet.agreeKey));
    await t.pumpAndSettle();
    expect(consents.recorded.map((r) => r.purpose.json), ['health_data']);
    expect(members.created.single.conditions, [MemberInConditions.diabetes]);
  });

  testWidgets('no consent sheet when nothing health-related is saved', (
    t,
  ) async {
    final members = FakeMembersClient();
    await pumpMembers(
      t,
      const MemberFormScreen(),
      members: members,
      consents: FakeConsentsClient(),
    );
    await fillNew(t, 'en');
    await save(t);
    expect(find.byType(ConsentSheet), findsNothing);
    expect(members.created, hasLength(1));
  });

  testWidgets('API consent_required opens the sheet, then retries', (t) async {
    final members = FakeMembersClient()
      ..error = apiError(403, 'consent_required');
    final consents = FakeConsentsClient(granted: {'health_data'});
    await pumpMembers(
      t,
      const MemberFormScreen(),
      members: members,
      consents: consents,
    );
    await fillNew(t, 'en');
    await t.tap(find.text(l10nFor('en').conditionPcos));
    await save(t);
    // Never a raw error: the sheet.
    expect(find.byType(ConsentSheet), findsOneWidget);
    expect(find.text(l10nFor('en').errorConsentRequired), findsNothing);
    await t.tap(find.byKey(ConsentSheet.agreeKey));
    await t.pumpAndSettle();
    expect(members.created, hasLength(2));
    expect(members.members.last.conditions, [MemberOutConditions.pcos]);
  });

  testWidgets('member_limit maps to its i18n message', (t) async {
    final members = FakeMembersClient()..error = apiError(422, 'member_limit');
    await pumpMembers(
      t,
      const MemberFormScreen(),
      members: members,
      consents: FakeConsentsClient(granted: {'health_data'}),
    );
    await fillNew(t, 'en');
    await save(t);
    expect(find.text(l10nFor('en').errorMemberLimit), findsOneWidget);
  });

  testWidgets('relation picker never offers self; birth year is required', (
    t,
  ) async {
    final l = l10nFor('en');
    final members = FakeMembersClient();
    await pumpMembers(
      t,
      const MemberFormScreen(),
      members: members,
      consents: FakeConsentsClient(),
    );
    for (final r in [
      l.membersRelationChild,
      l.membersRelationParent,
      l.membersRelationSpouse,
    ]) {
      expect(find.widgetWithText(ChoiceChip, r), findsOneWidget);
    }
    // "Other" is both a relation and a sex.
    expect(
      find.widgetWithText(ChoiceChip, l.membersRelationOther),
      findsWidgets,
    );
    expect(
      find.widgetWithText(ChoiceChip, l.membersRelationSelf),
      findsNothing,
    );

    await t.enterText(find.byKey(MemberFormScreen.nameKey), 'Asha');
    await t.tap(find.text(l.membersRelationChild));
    await save(t);
    expect(
      find.text(l.membersFormBirthYearInvalid('${DateTime.now().year}')),
      findsOneWidget,
    );
    expect(members.created, isEmpty);

    await t.enterText(find.byKey(MemberFormScreen.birthYearKey), '1800');
    await save(t);
    expect(members.created, isEmpty);
  });

  testWidgets('edit sends the full form state, so nothing is cleared', (
    t,
  ) async {
    final members = FakeMembersClient([
      primaryMember(),
      memberOut(
        id: 'm1',
        name: 'Asha',
        sex: MemberOutSex.female,
        heightCm: 120,
        weightKg: 25.5,
        goal: MemberOutGoal.healthyEating,
        allergens: ['milk', 'Kiwi'],
        conditions: [MemberOutConditions.diabetes],
        customAlerts: [MemberOutCustomAlerts.palmOil],
      ),
    ]);
    await pumpMembers(
      t,
      const MemberFormScreen(memberId: 'm1'),
      members: members,
      // Withdrawn: re-sending stored health data must not need consent.
      consents: FakeConsentsClient(withdrawn: {'health_data'}),
    );
    await t.enterText(find.byKey(MemberFormScreen.nameKey), 'Asha R');
    await save(t);

    expect(find.byType(ConsentSheet), findsNothing);
    final (id, patch) = members.patched.single;
    expect(id, 'm1');
    expect(patch.toJson(), {
      'name': 'Asha R',
      'relation': 'child',
      'birth_year': 2015,
      'sex': 'female',
      'height_cm': 120,
      'weight_kg': 25.5,
      'diet': 'veg',
      'allergens': ['milk', 'Kiwi'],
      'conditions': ['diabetes'],
      'custom_alerts': ['palm_oil'],
      'goal': 'healthy_eating',
    });
  });

  testWidgets('clearing an optional field sends null for it only', (t) async {
    final members = FakeMembersClient([
      memberOut(id: 'm1', heightCm: 120, sex: MemberOutSex.male),
    ]);
    await pumpMembers(
      t,
      const MemberFormScreen(memberId: 'm1'),
      members: members,
      consents: FakeConsentsClient(granted: {'health_data'}),
    );
    await t.enterText(find.byKey(MemberFormScreen.heightKey), '');
    await save(t);
    final json = members.patched.single.$2.toJson();
    expect(json['height_cm'], isNull);
    expect(json['sex'], 'male');
  });

  testWidgets('removing an allergy asks first; cancel keeps it', (t) async {
    final l = l10nFor('en');
    final members = FakeMembersClient([
      memberOut(id: 'm1', name: 'Asha', allergens: ['milk', 'peanut']),
    ]);
    await pumpMembers(
      t,
      const MemberFormScreen(memberId: 'm1'),
      members: members,
      consents: FakeConsentsClient(),
    );
    await t.tap(find.widgetWithText(FilterChip, l.allergenMilk));
    await t.pumpAndSettle();
    expect(
      find.text(l.membersFormRemoveAllergyConfirm(l.allergenMilk, 'Asha')),
      findsOneWidget,
    );
    await t.tap(find.text(l.membersFormCancel));
    await t.pumpAndSettle();
    expect(
      t
          .widget<FilterChip>(find.widgetWithText(FilterChip, l.allergenMilk))
          .selected,
      isTrue,
    );

    await t.tap(find.widgetWithText(FilterChip, l.allergenMilk));
    await t.pumpAndSettle();
    await t.tap(inDialog(l.membersRemove));
    await t.pumpAndSettle();

    // The last one uses the "remove every allergy" wording.
    await t.tap(find.widgetWithText(FilterChip, l.allergenPeanut));
    await t.pumpAndSettle();
    expect(
      find.text(l.membersFormClearAllergiesConfirm('Asha')),
      findsOneWidget,
    );
    await t.tap(inDialog(l.membersRemove));
    await t.pumpAndSettle();

    // A pure removal needs no consent (P8.1).
    await save(t);
    expect(find.byType(ConsentSheet), findsNothing);
    expect(members.patched.single.$2.allergens, isEmpty);
  });

  testWidgets('typing a listed allergy picks the listed chip', (t) async {
    final l = l10nFor('en');
    final members = FakeMembersClient();
    await pumpMembers(
      t,
      const MemberFormScreen(),
      members: members,
      consents: FakeConsentsClient(granted: {'health_data'}),
    );
    await fillNew(t, 'en');
    await t.enterText(find.byKey(MemberFormScreen.otherAllergenKey), 'Peanut ');
    await t.tap(find.byKey(MemberFormScreen.addAllergenKey));
    await t.pump();
    await t.enterText(find.byKey(MemberFormScreen.otherAllergenKey), 'x');
    await t.tap(find.byKey(MemberFormScreen.addAllergenKey));
    await t.pump();
    expect(find.text(l.membersFormAllergenLength), findsOneWidget);
    await save(t);
    expect(members.created.single.allergens, ['peanut']);
  });

  testWidgets('custom alerts are labelled from alert.* and saved by key', (
    t,
  ) async {
    final members = FakeMembersClient();
    await pumpMembers(
      t,
      const MemberFormScreen(),
      members: members,
      consents: FakeConsentsClient(),
    );
    await fillNew(t, 'en');
    // Alerts are not health fields: no consent needed.
    await t.tap(find.text('Maida (refined wheat flour)'));
    await t.tap(find.text('MSG (monosodium glutamate)'));
    await save(t);
    expect(find.byType(ConsentSheet), findsNothing);
    expect(members.created.single.customAlerts, [
      MemberInCustomAlerts.maida,
      MemberInCustomAlerts.msg,
    ]);
  });

  testWidgets('remove a member after confirming', (t) async {
    final l = l10nFor('en');
    final members = FakeMembersClient([primaryMember(), memberOut(id: 'm1')]);
    await pumpMembers(
      t,
      const MemberFormScreen(memberId: 'm1'),
      members: members,
      consents: FakeConsentsClient(),
    );
    await t.tap(find.byKey(MemberFormScreen.removeKey));
    await t.pumpAndSettle();
    expect(find.text(l.membersRemoveConfirm('Asha')), findsOneWidget);
    await t.tap(inDialog(l.membersRemove));
    await t.pumpAndSettle();
    expect(members.deleted, ['m1']);
  });

  testWidgets('the primary has no remove button and no relation picker', (
    t,
  ) async {
    final l = l10nFor('en');
    await pumpMembers(
      t,
      const MemberFormScreen(memberId: 'p1'),
      members: FakeMembersClient(),
      consents: FakeConsentsClient(),
    );
    expect(find.byKey(MemberFormScreen.removeKey), findsNothing);
    expect(find.text(l.membersRelationSelf), findsWidgets);
  });
}
