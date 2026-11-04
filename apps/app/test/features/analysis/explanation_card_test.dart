import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/features/analysis/domain/explanation_text.dart';
import 'package:smartnutri_ai/features/analysis/presentation/explanation_card.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';

final en = lookupAppLocalizations(const Locale('en'));

Widget wrap(Widget child, {String locale = 'en'}) => MaterialApp(
  theme: buildAppTheme(),
  locale: Locale(locale),
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(body: SingleChildScrollView(child: child)),
);

VerdictOut verdict(String id, String name, {bool primary = false}) =>
    VerdictOut.fromJson({
      'member_id': id,
      'member_name': name,
      'is_primary': primary,
      'relation': primary ? 'self' : 'child',
      'profile_set_up': true,
      'status': 'caution',
      'reasons': <Object>[],
    });

ExplanationOut explanation({
  String source = 'llm',
  String? text,
  List<String> tips = const [],
  Map<String, String> refs = const {},
}) => ExplanationOut.fromJson({
  'language': 'en',
  'member_refs': refs,
  'prompt_version': 'explanation_v1',
  'source': source,
  'text': text,
  'tips': tips,
});

void main() {
  // member_1 .. member_10, so member_10 must not be read as member_1 + "0".
  final verdicts = [for (var i = 1; i <= 10; i++) verdict('id$i', 'Name$i')];
  final refs = {for (var i = 1; i <= 10; i++) 'member_$i': 'id$i'};
  final names = {for (final v in verdicts) v.memberId: v.memberName};

  group('substituteMemberTokens', () {
    test('replaces member_10 before member_1', () {
      expect(
        substituteMemberTokens('member_10 and member_1.', refs, names),
        'Name10 and Name1.',
      );
    });

    test('a token with no member is not shown (null)', () {
      expect(substituteMemberTokens('member_11 too', refs, names), isNull);
      expect(
        substituteMemberTokens('member_2', {'member_2': 'gone'}, names),
        isNull,
      );
    });

    test('text without tokens is unchanged', () {
      expect(substituteMemberTokens('Plain text.', refs, names), 'Plain text.');
    });
  });

  testWidgets('hidden when the explanation is unavailable', (t) async {
    // Every shared fixture has source "unavailable".
    final out = analyzeFixture('sf_biscuit');
    expect(out.explanation.source, ExplanationOutSource.unavailable);
    await t.pumpWidget(
      wrap(
        ExplanationCard(explanation: out.explanation, verdicts: out.verdicts),
      ),
    );
    expect(find.text(en.explanationTitle), findsNothing);
    expect(find.text(en.explanationAiNote), findsNothing);
  });

  testWidgets('hidden when a token cannot be resolved', (t) async {
    await t.pumpWidget(
      wrap(
        ExplanationCard(
          explanation: explanation(text: 'member_3 should check.', refs: refs),
          verdicts: verdicts.take(2).toList(),
        ),
      ),
    );
    expect(find.text(en.explanationTitle), findsNothing);
  });

  for (final locale in ['en', 'hi', 'mr']) {
    testWidgets('shows names, tips and the AI note [$locale]', (t) async {
      final l = lookupAppLocalizations(Locale(locale));
      await t.pumpWidget(
        wrap(
          ExplanationCard(
            explanation: explanation(
              text: 'member_10 and member_1 differ.',
              tips: ['Check member_1 portions.', 'Read the label.'],
              refs: refs,
            ),
            verdicts: verdicts,
          ),
          locale: locale,
        ),
      );
      expect(find.text(l.explanationTitle), findsOneWidget);
      expect(find.text(l.explanationAiNote), findsOneWidget);
      expect(find.text('Name10 and Name1 differ.'), findsOneWidget);
      expect(find.text(l.explanationTipsTitle), findsOneWidget);
      expect(find.text('Check Name1 portions.'), findsOneWidget);
      expect(find.text('Read the label.'), findsOneWidget);
      expect(find.textContaining('member_'), findsNothing);
    });
  }

  testWidgets('the primary with no name is "you"', (t) async {
    await t.pumpWidget(
      wrap(
        ExplanationCard(
          explanation: explanation(
            text: 'Fine for member_1.',
            refs: {'member_1': 'p'},
          ),
          verdicts: [verdict('p', '', primary: true)],
        ),
      ),
    );
    expect(find.text('Fine for ${en.resultYou}.'), findsOneWidget);
  });

  testWidgets('the account holder is "you" even with a name (as web)', (
    t,
  ) async {
    await t.pumpWidget(
      wrap(
        ExplanationCard(
          explanation: explanation(
            text: 'Fine for member_1 and member_2.',
            refs: {'member_1': 'p', 'member_2': 'c'},
          ),
          verdicts: [verdict('p', 'Ravi', primary: true), verdict('c', 'Asha')],
        ),
      ),
    );
    expect(find.text('Fine for ${en.resultYou} and Asha.'), findsOneWidget);
  });
}
