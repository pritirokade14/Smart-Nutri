import 'dart:convert';
import 'dart:io';
import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/analysis/domain/reasons.dart';
import 'package:smartnutri_ai/features/analysis/presentation/reason_line.dart';
import 'package:smartnutri_api/src/export.dart';

/// Parity oracle: the exact strings both clients must show
/// (`packages/test-fixtures/reason-text/`).
void main() {
  for (final locale in ['en', 'hi', 'mr']) {
    final entries =
        (jsonDecode(
                  File(
                    '../../packages/test-fixtures/reason-text/$locale.json',
                  ).readAsStringSync(),
                )
                as List)
            .cast<Map<String, Object?>>();
    final l10n = lookupAppLocalizations(Locale(locale));

    group('reason-text fixture [$locale]', () {
      test('has entries', () => expect(entries, isNotEmpty));
      for (final e in entries) {
        final r = e['reason']! as Map<String, Object?>;
        test('${e['key']} (${e['product']}/${e['member']})', () {
          final reason = ReasonOut(
            code: r['code']! as String,
            params: r['params'],
            severity: ReasonOutSeverity.fromJson(r['severity']! as String),
          );
          expect(reasonMessageKey(reason), e['key']);
          expect(reasonText(l10n, reason), e['text']);
        });
      }
    });
  }
}
