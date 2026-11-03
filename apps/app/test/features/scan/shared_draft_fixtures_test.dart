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

/// Brief §1: saves the form never lets through. The fixture still records
/// what the server would do with them.
bool _blockedByClient(
  Map<String, Object?> body,
  Map<String, Object?> result,
  ProductDraft draft,
) {
  if (!body.containsKey('basis') || !body.containsKey('category')) return true;
  final error = result['error'] as Map<String, Object?>?;
  final fields = (error?['fields'] as List?)?.cast<String>() ?? const [];
  if (fields.contains('body.sodium_unit')) return true;
  if (body['basis'] == 'per_serving') {
    final col = draft.confirm.columns.perServing;
    final needsServing = (col?.confirmFields ?? const []).contains(
      ColumnConfirmConfirmFields.servingSizeG,
    );
    final confirmed = (body['confirmed_fields']! as List).cast<String>();
    if (needsServing && !confirmed.contains('serving_size_g')) return true;
  }
  return false;
}

const _contractOrder = [
  'energy_kcal',
  'protein_g',
  'carbs_g',
  'sugars_g',
  'fat_g',
  'sat_fat_g',
  'fiber_g',
  'salt_g',
  'sodium_mg',
  'serving_size_g',
];

/// The fixture builds `confirmed_fields` from ticks only (README step 4).
/// The round-B brief §1 adds that an edit confirms too: an edited field of
/// the chosen column's `confirm_fields`, and an edited serving size even when
/// not listed. The body the client must send therefore lists those as well.
Map<String, Object?> _clientBody(
  Map<String, Object?> body,
  Map<String, Object?> actions,
  ProductDraft draft,
) {
  final edits = (actions['edit'] as Map?)?.cast<String, Object?>();
  final basis = body['basis'] as String?;
  if (edits == null || basis == null) return body;
  final column = basis == 'per_100g'
      ? draft.confirm.columns.per100g
      : draft.confirm.columns.perServing;
  final listed = {for (final f in column?.confirmFields ?? const []) f.json};
  final shown = basis == 'per_100g' ? draft.per100g : draft.perServing;
  num? original(String f) =>
      f == 'serving_size_g' ? draft.servingSizeG : shown?.toJson()[f] as num?;
  final confirmed = {...(body['confirmed_fields']! as List).cast<String>()};
  for (final MapEntry(:key, :value) in edits.entries) {
    if (value == original(key)) continue; // not an edit
    if (key == 'serving_size_g' || listed.contains(key)) confirmed.add(key);
  }
  return {
    ...body,
    'confirmed_fields': [
      for (final f in _contractOrder)
        if (confirmed.contains(f)) f,
    ],
  };
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
      final result = (save['result']! as Map).cast<String, Object?>();

      testWidgets('$name #$i ${jsonEncode(actions)}', (t) async {
        t.view.physicalSize = const Size(1000, 12000);
        t.view.devicePixelRatio = 1;
        addTearDown(t.view.reset);
        final draft = draftFixture(name);
        final body = _clientBody(fixtureBody, actions, draft);
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

        final blocked = _blockedByClient(body, result, draft);
        final save = t.widget<FilledButton>(find.byKey(const Key('save')));
        expect(
          save.onPressed != null,
          !blocked,
          reason: blocked ? 'save must stay disabled' : 'save must be enabled',
        );

        final state = t.state<DraftFormState>(find.byType(DraftForm));
        if (!body.containsKey('basis') || !body.containsKey('category')) {
          expect(state.previewBody, isNull);
          return;
        }
        final ProductCreate out;
        if (blocked) {
          out = state.previewBody!;
        } else {
          await t.tap(find.byKey(const Key('save')));
          await t.pump();
          out = sent.single;
        }
        expect(out.scanId, _scanId);
        expect(_json(out), body);
      });
    }
  }
}
