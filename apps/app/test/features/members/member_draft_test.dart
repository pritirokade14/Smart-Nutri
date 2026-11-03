import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/members/domain/member.dart';
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_members.dart';

void main() {
  group('values this app version does not know', () {
    test('an unknown condition leaves the conditions unchanged (null)', () {
      final stored = memberOut(
        conditions: [
          MemberOutConditions.diabetes,
          MemberOutConditions.$unknown,
        ],
      );
      final patch = MemberDraft.fromMember(stored).toMemberPatch();
      expect(patch.conditions, isNull);
    });

    test('an unknown alert leaves the custom alerts unchanged (null)', () {
      final stored = memberOut(
        customAlerts: [
          MemberOutCustomAlerts.palmOil,
          MemberOutCustomAlerts.$unknown,
        ],
      );
      final patch = MemberDraft.fromMember(stored).toMemberPatch();
      expect(patch.customAlerts, isNull);
    });

    test('an unknown diet is never coerced to non_veg', () {
      final stored = memberOut(diet: MemberOutDiet.$unknown);
      final draft = MemberDraft.fromMember(stored);
      expect(draft.diet, isNull);
      expect(draft.toMemberPatch().diet, isNull);
    });

    test('known values are still sent in full', () {
      final stored = memberOut(
        diet: MemberOutDiet.vegan,
        conditions: [MemberOutConditions.diabetes],
        customAlerts: [MemberOutCustomAlerts.palmOil],
      );
      final patch = MemberDraft.fromMember(stored).toMemberPatch();
      expect(patch.diet, MemberPatchDiet.vegan);
      expect(patch.conditions, [MemberPatchConditions.diabetes]);
      expect(patch.customAlerts, [MemberPatchCustomAlerts.palmOil]);
    });
  });
}
