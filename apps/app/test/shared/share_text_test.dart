import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/shared/share/share_text.dart';
import 'package:smartnutri_api/src/export.dart';

import '../support/fixtures.dart';

Map<String, Object?> _share(String name) =>
    jsonDecode(
          File(
            '../../packages/test-fixtures/share/$name.json',
          ).readAsStringSync(),
        )
        as Map<String, Object?>;

/// The sf_biscuit analyze response with the share fixture's members, each
/// carrying the full engine reasons of its fixture member (so a leak of a
/// condition or reason would show).
AnalyzeOut _response(Map<String, Object?> input) {
  final json = analyzeJson('sf_biscuit');
  final names = memberNamesById();
  final byFixture = {
    for (final v in (json['verdicts']! as List).cast<Map<String, Object?>>())
      names[v['member_id']]: v,
  };
  json['verdicts'] = [
    for (final m in (input['verdicts']! as List).cast<Map<String, Object?>>())
      {
        ...byFixture[m['fixture_member']]!,
        'member_id': m['member_id'],
        'member_name': m['name'],
        'relation': m['relation'],
        'status': m['status'],
        'is_primary': false,
      },
  ];
  (json['product']! as Map)['name'] = input['product'];
  return AnalyzeOut.fromJson(json);
}

void main() {
  final result = _share('share_result.sf_biscuit');
  final input = result['input']! as Map<String, Object?>;
  final expected = (result['expected']! as Map).cast<String, String>();
  final forbidden = (result['forbidden_substrings']! as Map).map(
    (k, v) => MapEntry(k as String, (v as List).cast<String>()),
  );
  final urls = (input['urls']! as Map).cast<String, String>();

  for (final locale in ['en', 'hi', 'mr']) {
    test('share text has no conditions ($locale)', () {
      final l = lookupAppLocalizations(Locale(locale));
      final r = _response(input);
      final text = shareResultText(
        l,
        r,
        input['product']! as String,
        urls[locale]!,
      );
      expect(text, expected[locale]);

      final lower = text.toLowerCase();
      for (final word in forbidden[locale]!) {
        expect(lower.contains(word.toLowerCase()), isFalse, reason: word);
      }
      for (final word in ['diabetes', 'diabetic', 'milk', 'allergy']) {
        expect(lower.contains(word), isFalse, reason: word);
      }
      for (final v in r.verdicts) {
        for (final reason in v.reasons) {
          expect(text.contains(reason.code), isFalse, reason: reason.code);
        }
      }
    });
  }

  test('only the members the user picked are shared', () {
    final l = lookupAppLocalizations(const Locale('en'));
    final r = _response(input);
    final text = shareResultText(
      l,
      r,
      'Sugar Free Biscuit',
      'https://x/en',
      memberIds: {r.verdicts[1].memberId},
    );
    expect(
      text,
      'Sugar Free Biscuit — Nutri-Score D (calculated by SmartNutri). '
      'Riya: Avoid. Checked with SmartNutri: https://x/en',
    );
  });

  test('an ungraded product uses the ungraded template', () {
    final l = lookupAppLocalizations(const Locale('en'));
    final json = analyzeJson('sf_biscuit');
    (json['report']! as Map)['nutriscore'] = {'grade': null};
    final r = AnalyzeOut.fromJson(json);
    final text = shareResultText(l, r, 'Biscuit', 'https://x/en');
    expect(text, startsWith('Biscuit — '));
    expect(text, contains('not enough label data'));
  });

  final weekly = _share('share_weekly.week_family');
  final wInput = weekly['input']! as Map<String, Object?>;
  final wExpected = (weekly['expected']! as Map).cast<String, String>();
  for (final locale in ['en', 'hi', 'mr']) {
    test('weekly share matches fixture ($locale)', () {
      final l = lookupAppLocalizations(Locale(locale));
      expect(
        shareWeeklyText(
          l,
          wInput['scans']! as int,
          wInput['logged']! as int,
          (wInput['urls']! as Map)[locale]! as String,
        ),
        wExpected[locale],
      );
    });
  }

  test('share URL: public product page for a barcode, else the home page', () {
    expect(
      shareUrl('https://smartnutri.app', 'hi', barcode: '8901063201089'),
      'https://smartnutri.app/hi/p/8901063201089',
    );
    expect(
      shareUrl('https://smartnutri.app/', 'en'),
      'https://smartnutri.app/en',
    );
  });
}
