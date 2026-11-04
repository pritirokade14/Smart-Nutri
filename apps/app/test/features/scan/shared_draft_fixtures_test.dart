// AGENTS.md rule 11 / Ruling R21: the confirm screen is driven through every
// scripted save in packages/test-fixtures/drafts/expected.json, and the body it
// would send must equal the expected `ProductCreate` body exactly. The files
// are read from the repo; nothing is copied.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/scan/domain/number_text.dart';
import 'package:smartnutri_ai/features/scan/presentation/draft_form.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';

const _scanId = 'scan-fixture';

Finder _input(String field) => find.descendant(
  of: find.byKey(ValueKey('field:$field')),
  matching: find.byType(EditableText),
);

Finder _box(String field) => find.descendant(
  of: find.byKey(ValueKey('confirm:$field')),
  matching: find.byType(Checkbox),
);

/// The keys of every confirm box on screen (`confirm:<field>`), as fields.
Set<String> _shownBoxes(WidgetTester t) => {
  for (final w in t.widgetList<CheckboxListTile>(find.byType(CheckboxListTile)))
    if (w.key case ValueKey<String>(
      :final value,
    ) when value.startsWith('confirm:'))
      value.substring('confirm:'.length),
};

/// The body as JSON, without what the client adds (`scan_id`) or what the
/// fixtures leave out (`barcode`).
Map<String, Object?> _json(ProductCreate body) {
  final json = jsonDecode(jsonEncode(body.toJson())) as Map<String, Object?>
    ..remove('scan_id')
    ..remove('barcode');
  return json;
}

void main() {
  final file = draftExpectationsFile();
  final cases = (file['cases']! as Map).cast<String, Map<String, Object?>>();

  test('expected.json is format 1 and covers every draft file', () {
    expect(file['format_version'], 1);
    expect(cases.keys.toList()..sort(), draftFixtureNames());
    for (final c in cases.entries) {
      expect(c.value['draft'], '${c.key}.json');
      expect((c.value['saves']! as List), isNotEmpty, reason: c.key);
    }
  });

  for (final MapEntry(key: name, value: spec) in cases.entries) {
    final saves = (spec['saves']! as List).cast<Map<String, Object?>>();
    for (final (i, save) in saves.indexed) {
      final actions = (save['actions']! as Map).cast<String, Object?>();
      final fixtureBody = (save['body']! as Map).cast<String, Object?>();

      testWidgets('$name #$i ${jsonEncode(actions)}', (t) async {
        t.view.physicalSize = const Size(1000, 12000);
        t.view.devicePixelRatio = 1;
        addTearDown(t.view.reset);
        final draft = draftFixture(name);
        final body = fixtureBody;
        final blocked = save['client_blocks'] == true;
        final sent = <ProductCreate>[];
        await t.pumpWidget(
          MaterialApp(
            locale: const Locale('en'),
            localizationsDelegates: AppLocalizations.localizationsDelegates,
            supportedLocales: AppLocalizations.supportedLocales,
            home: Scaffold(
              body: DraftForm(draft: draft, scanId: _scanId, onSave: sent.add),
            ),
          ),
        );
        await t.pumpAndSettle();

        // P9 S5: the API's category hint shows next to the picker, only
        // when set, and never preselects a category.
        final en = lookupAppLocalizations(const Locale('en'));
        final suggested = draft.confirm.categorySuggestion == 'supplement';
        expect(
          find.text(en.confirmCategorySuggestionSupplement),
          suggested ? findsOneWidget : findsNothing,
          reason: '$name category_suggestion',
        );

        Future<void> tap(String key) async {
          final f = find.byKey(ValueKey(key));
          expect(f, findsOneWidget, reason: '$key is offered');
          await t.tap(f);
          await t.pump();
        }

        if (actions['pick_basis'] case final String b) await tap('basis:$b');
        if (actions['pick_category'] case final String c) {
          await tap('category:$c');
        }

        // Nothing is ever ticked on the user's behalf, and the boxes are
        // exactly the chosen column's confirm_fields.
        for (final b in t.widgetList<Checkbox>(
          find.descendant(
            of: find.byType(CheckboxListTile),
            matching: find.byType(Checkbox),
          ),
        )) {
          expect(b.value, isFalse, reason: 'no box is pre-ticked');
        }
        final basis = (body['basis'] as String?) ?? '';
        final column = switch (basis) {
          'per_100g' => draft.confirm.columns.per100g,
          'per_serving' => draft.confirm.columns.perServing,
          _ => null,
        };
        if (column != null) {
          expect(_shownBoxes(t), {
            for (final f in column.confirmFields) f.json!,
          });
        }

        if (actions['sodium_unit'] case final String u) {
          await tap('sodium_unit:$u');
        }
        if (actions['edit'] case final Map<String, Object?> edits) {
          for (final MapEntry(:key, :value) in edits.entries) {
            await t.enterText(
              _input(key),
              value == null ? '' : formatForDisplay(value as num),
            );
            await t.pump();
          }
        }
        if (actions['tick'] case final List<Object?> ticks) {
          for (final f in ticks.cast<String>()) {
            expect(_box(f), findsOneWidget, reason: 'box for $f');
            if (t.widget<Checkbox>(_box(f)).value != true) {
              await tap('confirm:$f');
            }
          }
        }

        // Blocked vs sent is decided ONLY by client_blocks (R24).
        final button = t.widget<FilledButton>(find.byKey(const Key('save')));
        expect(
          button.onPressed != null,
          !blocked,
          reason: blocked ? 'save must stay disabled' : 'save must be enabled',
        );
        if (blocked) {
          expect(sent, isEmpty, reason: 'a blocked save sends no body');
          return;
        }
        await t.tap(find.byKey(const Key('save')));
        await t.pump();
        final out = sent.single;
        expect(out.scanId, _scanId);
        expect(_json(out), body);
      });
    }
  }
}
