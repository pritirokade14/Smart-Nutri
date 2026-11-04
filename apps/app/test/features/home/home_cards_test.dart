import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/features/history/presentation/summary_display.dart';
import 'package:smartnutri_ai/features/home/presentation/cards/home_cards.dart';
import 'package:smartnutri_ai/features/meals/domain/meal_summary.dart';
import 'package:smartnutri_ai/features/modes/mode_layouts.dart';
import 'package:smartnutri_ai/features/protein/presentation/protein_progress.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';
import '../../support/fake_members.dart';
import '../../support/fake_user_types.dart';
import '../user_types/user_types_harness.dart';

/// A `period=day` summary for [memberId]. Null totals are "not on a label".
Summary daySummary(
  String memberId, {
  int items = 1,
  num? sugars = 10,
  num? salt = 1,
  num? protein = 20,
  num? kcal = 300,
  String sugarBand = 'ok',
  String saltBand = 'ok',
  String proteinBand = 'near',
  num? proteinTarget = 56,
  num? proteinLeft = 36,
}) {
  final totals = {
    'energy_kcal': kcal,
    'protein_g': protein,
    'salt_g': salt,
    'sugars_g': sugars,
  };
  final incomplete = {
    'energy_kcal': kcal == null,
    'protein_g': protein == null,
    'salt_g': salt == null,
    'sugars_g': sugars == null,
  };
  final bands = {
    'kcal': 'unknown',
    'protein_g': proteinBand,
    'salt_g': saltBand,
    'sugar_g': sugarBand,
  };
  return Summary.fromJson({
    'bands': bands,
    'days': [
      {
        'bands': bands,
        'date': '2026-11-04',
        'incomplete': incomplete,
        'items': items,
        'totals': totals,
      },
    ],
    'end': '2026-11-04',
    'incomplete': incomplete,
    'limits': {
      'kcal': null,
      'protein_target_g': proteinTarget,
      'salt_g': 5.0,
      'sugar_g': 25.0,
    },
    'member_id': memberId,
    'pending_clinician_review': true,
    'period': 'day',
    'protein_left_g': proteinLeft,
    'start': '2026-11-04',
    'totals': totals,
  });
}

MemberOut _primary({List<String> allergens = const []}) => memberOut(
  id: 'p1',
  name: 'Ravi',
  relation: MemberOutRelation.self,
  birthYear: 1985,
  allergens: allergens,
  weightKg: 70,
  isPrimary: true,
);

Future<AppHarness> _pumpHome(
  WidgetTester t,
  String mode, {
  List<MemberOut>? members,
  Summary Function(String id)? summary,
}) => pumpApp(
  t,
  FakeUserTypesApi(
    me: FakeUserTypesMe(userTypesOut(types: [mode])),
    members: FakeMembersClient(members ?? [_primary()]),
  ),
  meals: FakeMealsClient()
    ..summary = (id, _) => (summary ?? (id) => daySummary(id))(id),
);

List<String> _shownCards(WidgetTester t, String mode, bool allergens) {
  final cards = homeCardsFor(mode, anyMemberHasAllergens: allergens);
  final positions = {
    for (final c in cards) c: t.getTopLeft(find.byKey(HomeCards.cardKey(c))).dy,
  };
  return [...cards]..sort((a, b) => positions[a]!.compareTo(positions[b]!));
}

void main() {
  for (final mode in kModeLayouts.keys) {
    testWidgets('home cards follow layout order: $mode', (t) async {
      await _pumpHome(t, mode);
      expect(_shownCards(t, mode, false), kModeLayouts[mode]!.homeCards);
    });

    testWidgets('allergy_check first in every mode when a member has '
        'allergens: $mode', (t) async {
      await _pumpHome(
        t,
        mode,
        members: [
          _primary(),
          memberOut(id: 'k1', name: 'Asha', allergens: ['peanut']),
        ],
      );
      final shown = _shownCards(t, mode, true);
      expect(shown.first, 'allergy_check');
      expect(
        find.text(
          en.homeCardsAllergyCheckMemberLine(en.allergenPeanut, 'Asha'),
        ),
        findsOneWidget,
      );
      expect(find.text(en.homeCardsAllergyCheckUnknownNote), findsOneWidget);
    });
  }

  testWidgets('no allergy card without allergens outside allergy mode', (
    t,
  ) async {
    await _pumpHome(t, 'gym');
    expect(find.byKey(HomeCards.cardKey('allergy_check')), findsNothing);
  });

  testWidgets('allergy mode offers to add allergies when none are set', (
    t,
  ) async {
    await _pumpHome(t, 'allergy_diet');
    expect(find.text(en.homeCardsAllergyCheckNone), findsOneWidget);
    expect(find.text(en.homeCardsAllergyCheckAddCta), findsOneWidget);
  });

  testWidgets('today protein shows the API total, target and protein left', (
    t,
  ) async {
    await _pumpHome(t, 'gym');
    expect(find.text(en.proteinProgress('56', '20')), findsOneWidget);
    expect(find.text(en.proteinLeftToday('36')), findsOneWidget);
    expect(find.text(en.summaryKcalTotal('300')), findsOneWidget);
  });

  testWidgets('no protein target shows the note', (t) async {
    await _pumpHome(
      t,
      'gym',
      summary: (id) => daySummary(id, proteinTarget: null, proteinLeft: null),
    );
    expect(find.byKey(ProteinProgress.noTargetKey), findsOneWidget);
    expect(find.text(en.proteinNoTarget), findsOneWidget);
  });

  testWidgets('unknown protein band is never green', (t) async {
    await _pumpHome(
      t,
      'gym',
      summary: (id) => daySummary(
        id,
        protein: null,
        proteinBand: 'unknown',
        proteinLeft: null,
      ),
    );
    final card = find.byKey(HomeCards.cardKey('today_protein'));
    final chip = find.descendant(of: card, matching: find.byType(BandChip));
    expect(chip, findsOneWidget);
    expect(t.widget<BandChip>(chip).band, Band.unknown);
    final colors = SnColors.of(t.element(chip));
    final box = t.widget<Container>(
      find.descendant(of: chip, matching: find.byType(Container)).first,
    );
    final color = (box.decoration! as BoxDecoration).color;
    expect(color, isNot(colors.verdictOk));
    expect(color, bandTone(colors, Band.unknown).color);
  });

  testWidgets('today sugar and salt use the API bands', (t) async {
    await _pumpHome(
      t,
      'health_condition',
      summary: (id) => daySummary(id, sugarBand: 'over', saltBand: 'near'),
    );
    final card = find.byKey(HomeCards.cardKey('today_sugar_salt'));
    final bands = [
      for (final e
          in find
              .descendant(of: card, matching: find.byType(BandChip))
              .evaluate())
        (e.widget as BandChip).band,
    ];
    expect(bands, [Band.over, Band.near]);
  });
}
