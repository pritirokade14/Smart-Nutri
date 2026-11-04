import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/modes/mode_layouts.dart';

Map<String, Object?> _fixture() =>
    jsonDecode(
          File(
            '../../packages/test-fixtures/modes/layouts.json',
          ).readAsStringSync(),
        )
        as Map<String, Object?>;

List<String> _strings(Object? v) => [for (final e in v! as List) e as String];

void main() {
  test('layouts match shared fixture', () {
    final f = _fixture();
    expect(kTypePriority, _strings(f['priority']));
    expect(kDefaultType, f['default_type']);
    expect(kDestinations, _strings(f['destinations']));
    expect(
      kAlwaysFirstCardWithAllergens,
      f['always_first_card_when_any_member_has_allergens'],
    );
    final modes = (f['modes']! as Map).cast<String, Object?>();
    expect(kModeLayouts.keys.toSet(), modes.keys.toSet());
    for (final MapEntry(key: mode, value: raw) in modes.entries) {
      final m = (raw! as Map).cast<String, Object?>();
      expect(kModeLayouts[mode]!.tabs, _strings(m['tabs']), reason: mode);
      expect(
        kModeLayouts[mode]!.homeCards,
        _strings(m['home_cards']),
        reason: mode,
      );
    }
  });

  for (final mode in kModeLayouts.keys) {
    test('$mode: five tabs, home first, scan second, profile last; '
        'More holds the rest', () {
      final tabs = kModeLayouts[mode]!.tabs;
      expect(tabs, hasLength(5));
      expect(tabs.first, 'home');
      expect(tabs[1], 'scan');
      expect(tabs.last, 'profile');
      final more = moreDestinations(mode);
      expect({...tabs, ...more}, kDestinations.toSet());
      expect(more.toSet().intersection(tabs.toSet()), isEmpty);
      expect(more, contains('how_we_score'));
      expect(kModeLayouts[mode]!.homeCards.last, 'recent_scans');
    });

    test('$mode: allergy_check first when a member has allergens', () {
      final cards = homeCardsFor(mode, anyMemberHasAllergens: true);
      expect(cards.first, 'allergy_check');
      expect(cards.where((c) => c == 'allergy_check'), hasLength(1));
      final none = homeCardsFor(mode, anyMemberHasAllergens: false);
      expect(none, kModeLayouts[mode]!.homeCards);
    });
  }
}
