import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/user_types/data/user_types_repository.dart';
import 'package:smartnutri_ai/features/user_types/domain/user_types.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_members.dart';
import '../../support/fake_user_types.dart';

void main() {
  test('follow-ups in priority order; weight loss has none', () {
    expect(followUpTypes(['eat_better', 'weight_loss', 'gym', 'family']), [
      'family',
      'gym',
      'eat_better',
    ]);
    expect(followUpTypes(['weight_loss']), isEmpty);
  });

  test('only the chosen types\' answers are sent; empty is null', () {
    const a = FollowUpAnswers(
      conditions: ['diabetes'],
      familyWith: ['children'],
      allergens: [],
      diet: 'veg',
      alerts: ['msg'],
    );
    final sent = a.toApi(['family', 'eat_better']);
    expect(sent.conditions, isNull);
    expect(sent.diet, isNull);
    expect(sent.allergens, isNull);
    expect([for (final f in sent.familyWith!) f.json], ['children']);
    expect([for (final x in sent.alerts!) x.json], ['msg']);
  });

  test('health consent: health types or health follow-ups', () {
    const none = FollowUpAnswers();
    expect(
      typesNeedHealthConsent(['family', 'gym', 'eat_better'], none),
      isFalse,
    );
    for (final t in ['health_condition', 'weight_loss', 'allergy_diet']) {
      expect(typesNeedHealthConsent([t], none), isTrue, reason: t);
    }
  });

  test('ticked by default only for the user\'s own follow-up answers', () {
    expect(
      tickedByDefault(
        prefillChange(
          'conditions',
          value: ['pcos'],
          reason: 'health_condition',
        ),
      ),
      isTrue,
    );
    expect(
      tickedByDefault(
        prefillChange('goal', value: 'build_muscle', reason: 'gym'),
      ),
      isTrue,
    );
    expect(
      tickedByDefault(
        prefillChange('goal', value: 'weight_loss', reason: 'weight_loss'),
      ),
      isFalse,
    );
    expect(
      tickedByDefault(
        prefillChange('goal', value: 'healthy_eating', reason: 'eat_better'),
      ),
      isFalse,
    );
  });

  test('applyPrefill only adds the confirmed values and keeps the rest', () {
    final primary = memberOut(
      id: 'p1',
      relation: MemberOutRelation.self,
      birthYear: 1990,
      allergens: ['peanut'],
      conditions: [MemberOutConditions.pcos],
      weightKg: 60,
      isPrimary: true,
    );
    final draft = applyPrefill(primary, [
      prefillChange(
        'allergens',
        current: ['peanut'],
        value: ['peanut', 'milk'],
        added: ['milk'],
      ),
    ], goal: 'build_muscle');
    expect(draft.allergens, ['peanut', 'milk']);
    expect(draft.conditions, ['pcos']);
    expect(draft.goal, 'build_muscle');
    expect(draft.weightKg, 60);
    expect(draft.diet, 'veg');
  });

  test('repository maps API errors to UserTypesFailure', () async {
    final me = FakeUserTypesMe()..getError = StateError('x');
    final repo = UserTypesRepository(me);
    await expectLater(repo.get(), throwsA(isA<UserTypesFailure>()));
    final out = await UserTypesRepository(
      FakeUserTypesMe(),
    ).save(['gym'], const FollowUps(gymGoal: FollowUpsGymGoal.stayFit));
    expect(out.answered, isTrue);
  });
}
