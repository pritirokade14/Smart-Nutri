import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/diary/domain/slot_label.dart';

void main() {
  const typed = 'Evening chai ☕';
  for (final code in ['en', 'hi', 'mr']) {
    test('custom label renders exactly as typed in $code', () {
      final l10n = lookupAppLocalizations(Locale(code));
      expect(slotLabel(l10n, customLabel: typed), typed);
      // Even when a default key is present, the user's text wins.
      expect(
        slotLabel(l10n, labelKey: 'diary.slot.lunch', customLabel: typed),
        typed,
      );
    });
  }

  test('default key translated', () {
    final en = lookupAppLocalizations(const Locale('en'));
    final hi = lookupAppLocalizations(const Locale('hi'));
    expect(
      slotLabel(en, labelKey: 'diary.slot.breakfast'),
      en.diarySlotBreakfast,
    );
    expect(slotLabel(hi, labelKey: 'diary.slot.dinner'), hi.diarySlotDinner);
    expect(hi.diarySlotDinner, isNot(en.diarySlotDinner));
  });

  test('a blank custom label falls back to the default', () {
    final en = lookupAppLocalizations(const Locale('en'));
    expect(
      slotLabel(en, labelKey: 'diary.slot.snack', customLabel: '  '),
      en.diarySlotSnack,
    );
  });
}
