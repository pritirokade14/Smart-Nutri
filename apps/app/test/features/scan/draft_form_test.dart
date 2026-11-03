import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/tokens.g.dart';
import 'package:smartnutri_ai/features/scan/presentation/draft_form.dart';
import 'package:smartnutri_ai/features/scan/presentation/warning_banner.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';
import 'draft_fixtures.dart';

final en = lookupAppLocalizations(const Locale('en'));

class _Harness {
  final saved = <ProductCreate>[];
  ProductCreate get last => saved.last;
}

Future<_Harness> _pump(
  WidgetTester t,
  ProductDraft? draft, {
  String? scanId = 'scan-1',
  String? barcode,
  Map<String, String> fieldErrors = const {},
}) async {
  t.view.physicalSize = const Size(1000, 9000);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  final h = _Harness();
  await t.pumpWidget(
    MaterialApp(
      locale: const Locale('en'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(
        body: DraftForm(
          draft: draft,
          scanId: draft == null ? null : scanId,
          barcode: barcode,
          fieldErrors: fieldErrors,
          onSave: h.saved.add,
        ),
      ),
    ),
  );
  await t.pumpAndSettle();
  return h;
}

Finder _field(String name) => find.descendant(
  of: find.byKey(ValueKey('field:$name')),
  matching: find.byType(EditableText),
);

String _text(WidgetTester t, String name) =>
    t.widget<EditableText>(_field(name)).controller.text;

Future<void> _enter(WidgetTester t, String name, String text) async {
  await t.enterText(_field(name), text);
  await t.pump();
}

bool _saveEnabled(WidgetTester t) =>
    t.widget<FilledButton>(find.byKey(const Key('save'))).onPressed != null;

Future<void> _save(WidgetTester t) async {
  await t.tap(find.byKey(const Key('save')));
  await t.pump();
}

Future<void> _tap(WidgetTester t, String key) async {
  await t.tap(find.byKey(ValueKey(key)));
  await t.pump();
}

List<String?> _confirmed(ProductCreate b) =>
    b.confirmedFields.map((f) => f.json).toList();

bool _chipSelected(WidgetTester t, String key) =>
    t.widget<ChoiceChip>(find.byKey(ValueKey(key))).selected;

bool? _boxValue(WidgetTester t, String field) => t
    .widget<Checkbox>(
      find.descendant(
        of: find.byKey(ValueKey('confirm:$field')),
        matching: find.byType(Checkbox),
      ),
    )
    .value;

void main() {
  group('safety review regressions (R21)', () {
    testWidgets('B1: two printed columns, per_serving picked: the per-serving '
        'numbers are shown and sent, never the per-100 g ones', (t) async {
      final h = await _pump(t, draftFixture('basis_mismatch_both_columns'));
      await _tap(t, 'basis:per_serving');
      expect(_text(t, 'energy_kcal'), '45');
      expect(_text(t, 'sugars_g'), '3');
      await _tap(t, 'confirm:serving_size_g');
      await _save(t);
      expect(h.last.basis, ProductCreateBasis.perServing);
      expect(h.last.nutrients.energyKcal, 45);
      expect(h.last.nutrients.sugarsG, 3);
      expect(h.last.nutrients.sodiumMg, 60);
      expect(h.last.servingSizeG, 30);
      expect(_confirmed(h.last), ['serving_size_g']);

      // Switching back sends the per-100 g column unchanged.
      await _tap(t, 'basis:per_100g');
      expect(_text(t, 'energy_kcal'), '150');
      await _save(t);
      expect(h.last.basis, ProductCreateBasis.per100g);
      expect(h.last.nutrients.energyKcal, 150);
      expect(h.last.nutrients.sugarsG, 10);
    });

    testWidgets('B2: derived + basis_mismatch: no basis is preselected, save '
        'is disabled, and the derived per-100 g values are never shown', (
      t,
    ) async {
      final h = await _pump(t, draftFixture('derived_basis_mismatch'));
      expect(_chipSelected(t, 'basis:per_100g'), isFalse);
      expect(_chipSelected(t, 'basis:per_serving'), isFalse);
      expect(_saveEnabled(t), isFalse);
      expect(find.text(en.confirmChooseRequired), findsOneWidget);
      // The printed (shared) per-serving column, not the derived 150 kcal.
      expect(_text(t, 'energy_kcal'), '45');
      await _tap(t, 'basis:per_100g');
      expect(_text(t, 'energy_kcal'), '45');
      await _tap(t, 'confirm:serving_size_g');
      await _save(t);
      expect(h.last.basis, ProductCreateBasis.per100g);
      expect(h.last.nutrients.energyKcal, 45);
      expect(_confirmed(h.last), ['serving_size_g']);
    });
  });

  testWidgets('draft blanks stay blank and are sent as null', (t) async {
    final h = await _pump(t, baseDraft());
    expect(_text(t, 'fiber_g'), isEmpty);
    expect(_text(t, 'added_sugars_g'), isEmpty);
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    final n = h.last.nutrients;
    expect(n.fiberG, isNull);
    expect(n.addedSugarsG, isNull);
    expect(n.transFatG, isNull);
    // The input shows the exact printed value; the body carries it unchanged.
    expect(_text(t, 'energy_kcal'), '451.37');
    expect(n.energyKcal, 451.37);
    expect(n.proteinG, 7.5);
    expect(h.last.basis, ProductCreateBasis.per100g);
    expect(h.last.category, ProductCreateCategory.general);
    expect(h.last.sodiumUnit, isNull);
    expect(h.last.scanId, 'scan-1');
  });

  testWidgets('clearing a value sends null, never 0', (t) async {
    final h = await _pump(t, baseDraft());
    await _enter(t, 'protein_g', '');
    await _save(t);
    expect(h.last.nutrients.proteinG, isNull);
  });

  testWidgets('implausible field highlighted and warning shown', (t) async {
    await _pump(t, draftFixture('implausible_value'));
    expect(find.text(en.warningImplausibleValue), findsNWidgets(2));
    expect(
      find.descendant(
        of: find.byType(WarningBanner),
        matching: find.text(en.confirmFieldSugarsG),
      ),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('highlight:sugars_g')), findsOneWidget);
    expect(find.byKey(const ValueKey('highlight:carbs_g')), findsOneWidget);
    expect(find.byKey(const ValueKey('highlight:protein_g')), findsNothing);
  });

  testWidgets('per_100g_missing warning shown for per-serving label without '
      'serving size', (t) async {
    await _pump(t, draftFixture('per_serving_only_no_serving'));
    expect(find.text(en.warningPer100gMissing), findsOneWidget);
    expect(find.text(en.warningPerServingIgnored), findsOneWidget);
  });

  testWidgets('a code:path warning renders its key and the field label, and '
      'highlights the field', (t) async {
    await _pump(t, draftFixture('upper_bound_protein_per_100g'));
    final banner = find.byType(WarningBanner);
    expect(
      find.descendant(of: banner, matching: find.text(en.warningUpperBound)),
      findsOneWidget,
    );
    expect(
      find.descendant(of: banner, matching: find.text(en.confirmFieldProteinG)),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('highlight:protein_g')), findsOneWidget);
  });

  testWidgets('warning banners are never green', (t) async {
    await _pump(t, lowConfidenceDraft());
    expect(find.text(en.warningLowConfidence), findsOneWidget);
    expect(find.text(en.warningUnreadableField), findsOneWidget);
    expect(find.byKey(const ValueKey('highlight:fiber_g')), findsOneWidget);
    for (final b in t.widgetList<WarningBanner>(find.byType(WarningBanner))) {
      expect(b.color, isNot(SnTokens.verdictOk));
    }
  });

  group('withheld protein (confirm_fields)', () {
    testWidgets('unticked: sent, but not in confirmed_fields', (t) async {
      final h = await _pump(t, draftFixture('upper_bound_protein_per_100g'));
      expect(find.text(en.confirmWithheldHint), findsOneWidget);
      expect(_boxValue(t, 'protein_g'), isFalse);
      await _save(t);
      expect(h.last.nutrients.proteinG, 0.5);
      expect(_confirmed(h.last), isNot(contains('protein_g')));
    });

    testWidgets('ticking adds it', (t) async {
      final h = await _pump(t, draftFixture('upper_bound_protein_per_100g'));
      await _tap(t, 'confirm:protein_g');
      await _save(t);
      expect(_confirmed(h.last), ['protein_g']);
    });

    testWidgets('editing adds it', (t) async {
      final h = await _pump(t, draftFixture('upper_bound_protein_per_100g'));
      await _enter(t, 'protein_g', '0.4');
      expect(_boxValue(t, 'protein_g'), isTrue);
      await _save(t);
      expect(h.last.nutrients.proteinG, 0.4);
      expect(_confirmed(h.last), ['protein_g']);
    });

    testWidgets('editing a field not in confirm_fields never lists it', (
      t,
    ) async {
      final h = await _pump(t, draftFixture('upper_bound_protein_per_100g'));
      expect(find.byKey(const ValueKey('confirm:sugars_g')), findsNothing);
      await _enter(t, 'sugars_g', '9');
      await _save(t);
      expect(h.last.nutrients.sugarsG, 9);
      expect(_confirmed(h.last), isEmpty);
    });
  });

  testWidgets('basis_required with one printed column: save disabled until a '
      'basis is chosen; the shared numbers are sent as printed for either '
      'basis, with the chosen basis shown beside them', (t) async {
    final h = await _pump(t, draftFixture('basis_mismatch_one_column'));
    expect(find.text(en.warningBasisMismatch), findsOneWidget);
    expect(_chipSelected(t, 'basis:per_100g'), isFalse);
    expect(_chipSelected(t, 'basis:per_serving'), isFalse);
    expect(_saveEnabled(t), isFalse);
    expect(find.text(en.confirmChooseRequired), findsOneWidget);
    expect(find.byKey(const ValueKey('shared_basis')), findsNothing);
    await _tap(t, 'basis:per_100g');
    expect(_saveEnabled(t), isTrue);
    final label = find.byKey(const ValueKey('shared_basis'));
    expect(
      find.descendant(
        of: label,
        matching: find.text(en.confirmBasisOptionPer100g),
      ),
      findsOneWidget,
    );
    await _save(t);
    expect(h.last.basis, ProductCreateBasis.per100g);
    expect(h.last.nutrients.proteinG, 3);
    expect(h.last.nutrients.energyKcal, 150);

    // Per serving: the same printed numbers, and the serving size must be
    // confirmed before saving.
    await _tap(t, 'basis:per_serving');
    expect(
      find.descendant(
        of: label,
        matching: find.text(en.confirmBasisOptionPerServing),
      ),
      findsOneWidget,
    );
    expect(_text(t, 'protein_g'), '3');
    expect(_saveEnabled(t), isFalse);
    await _tap(t, 'confirm:serving_size_g');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.basis, ProductCreateBasis.perServing);
    expect(h.last.nutrients.proteinG, 3);
    expect(h.last.nutrients.sodiumMg, 200);
    expect(h.last.servingSizeG, 30);
    expect(_confirmed(h.last), ['serving_size_g']);
  });

  testWidgets('two printed columns: no shared-basis label; the column follows '
      'the basis', (t) async {
    await _pump(t, draftFixture('basis_mismatch_both_columns'));
    await _tap(t, 'basis:per_serving');
    expect(find.byKey(const ValueKey('shared_basis')), findsNothing);
    expect(_text(t, 'energy_kcal'), '45');
  });

  testWidgets('a lone offered basis is selected and the other is hidden', (
    t,
  ) async {
    await _pump(t, draftFixture('derived_from_serving'));
    expect(_chipSelected(t, 'basis:per_serving'), isTrue);
    expect(find.byKey(const ValueKey('basis:per_100g')), findsNothing);
  });

  testWidgets('a lone per-100 g basis is selected; two offered without '
      'basis_required preselect per 100 g (R22)', (t) async {
    await _pump(t, draftFixture('clean'));
    expect(_chipSelected(t, 'basis:per_100g'), isTrue);
    expect(find.byKey(const ValueKey('basis:per_serving')), findsNothing);
  });

  testWidgets('two offered bases without basis_required: per 100 g is '
      'preselected and the user can switch (R22)', (t) async {
    final h = await _pump(t, draftFixture('upper_bound_protein_per_serving'));
    expect(_chipSelected(t, 'basis:per_100g'), isTrue);
    expect(_chipSelected(t, 'basis:per_serving'), isFalse);
    await _tap(t, 'basis:per_serving');
    await _tap(t, 'confirm:serving_size_g');
    await _save(t);
    expect(h.last.basis, ProductCreateBasis.perServing);
    expect(h.last.nutrients.sodiumMg, 60);
  });

  testWidgets('per_100g not offered: only per serving is shown, and a '
      'serving typed where none was read is confirmed by typing', (t) async {
    final h = await _pump(t, draftFixture('per_serving_only_no_serving'));
    expect(find.byKey(const ValueKey('basis:per_100g')), findsNothing);
    expect(_chipSelected(t, 'basis:per_serving'), isTrue);
    expect(_saveEnabled(t), isFalse);
    await _enter(t, 'serving_size_g', '30');
    expect(_boxValue(t, 'serving_size_g'), isTrue);
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.servingSizeG, 30);
    expect(_confirmed(h.last), ['serving_size_g']);
  });

  testWidgets('sodium_unit_required: save disabled until mg or g; 0.4 stays '
      '0.4; picking the unit confirms sodium without a box', (t) async {
    final h = await _pump(t, draftFixture('unit_unconfirmed_sodium_per_100g'));
    expect(find.text(en.warningUnitUnconfirmed), findsOneWidget);
    expect(find.byKey(const ValueKey('highlight:sodium_mg')), findsOneWidget);
    expect(find.byKey(const ValueKey('confirm:sodium_mg')), findsNothing);
    expect(_saveEnabled(t), isFalse);
    expect(_text(t, 'sodium_mg'), '0.4');
    await _tap(t, 'sodium_unit:g');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.sodiumUnit, ProductCreateSodiumUnit.g);
    expect(h.last.nutrients.sodiumMg, 0.4);
    expect(_confirmed(h.last), isEmpty);
  });

  testWidgets('R24: a picked sodium unit is cleared when the shown column '
      'changes; save is blocked until it is picked again', (t) async {
    final h = await _pump(
      t,
      draftFixture('unit_unconfirmed_sodium_per_serving'),
    );
    await _tap(t, 'sodium_unit:g');
    expect(_saveEnabled(t), isTrue);
    await _tap(t, 'basis:per_serving');
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('sodium_unit_suffix')),
        matching: find.text(en.confirmSodiumUnitOptionG),
      ),
      findsNothing,
    );
    await _tap(t, 'confirm:serving_size_g');
    expect(_saveEnabled(t), isFalse, reason: 'unit is unset again');
    await _tap(t, 'sodium_unit:mg');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.sodiumUnit, ProductCreateSodiumUnit.mg);
  });

  group('R24 confirmed = ticked or changed', () {
    testWidgets('edit then revert a confirm field: unconfirmed', (t) async {
      final h = await _pump(t, draftFixture('upper_bound_protein_per_100g'));
      await _enter(t, 'protein_g', '0.4');
      expect(_boxValue(t, 'protein_g'), isTrue);
      await _enter(t, 'protein_g', '0.5');
      expect(_boxValue(t, 'protein_g'), isFalse);
      await _save(t);
      expect(_confirmed(h.last), isEmpty);
    });

    testWidgets('typing the same number confirms nothing', (t) async {
      final h = await _pump(t, draftFixture('upper_bound_protein_per_100g'));
      await _enter(t, 'protein_g', '0.50');
      expect(_boxValue(t, 'protein_g'), isFalse);
      await _save(t);
      expect(_confirmed(h.last), isEmpty);
    });

    testWidgets('serving_size_g: edit then revert is unconfirmed and blocks '
        'save when required', (t) async {
      final h = await _pump(t, draftFixture('derived_from_serving'));
      await _enter(t, 'serving_size_g', '25');
      expect(_saveEnabled(t), isTrue);
      await _enter(t, 'serving_size_g', '30');
      expect(_boxValue(t, 'serving_size_g'), isFalse);
      expect(_saveEnabled(t), isFalse);
      await _tap(t, 'confirm:serving_size_g');
      await _save(t);
      expect(_confirmed(h.last), ['serving_size_g']);
    });
  });

  testWidgets('R24: no confirm boxes until a basis is chosen', (t) async {
    await _pump(t, draftFixture('basis_mismatch_both_columns'));
    expect(find.byType(CheckboxListTile), findsNothing);
    await _tap(t, 'basis:per_serving');
    expect(
      find.byKey(const ValueKey('confirm:serving_size_g')),
      findsOneWidget,
    );
  });

  testWidgets('sodium_unit_required from the other column: the picker shows '
      'and the picked unit sits beside the input', (t) async {
    final h = await _pump(
      t,
      draftFixture('unit_unconfirmed_sodium_per_serving'),
    );
    expect(find.byKey(const ValueKey('sodium_unit:mg')), findsOneWidget);
    expect(_saveEnabled(t), isFalse);
    await _tap(t, 'sodium_unit:mg');
    final suffix = find.byKey(const ValueKey('sodium_unit_suffix'));
    expect(
      find.descendant(
        of: suffix,
        matching: find.text(en.confirmSodiumUnitOptionMg),
      ),
      findsOneWidget,
    );
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.sodiumUnit, ProductCreateSodiumUnit.mg);
    expect(h.last.nutrients.sodiumMg, 200);
  });

  testWidgets('a blank sodium needs no unit; editing sodium never replaces '
      'the unit choice', (t) async {
    final h = await _pump(t, draftFixture('unit_unconfirmed_sodium_per_100g'));
    await _enter(t, 'sodium_mg', '0.5');
    expect(_saveEnabled(t), isFalse);
    await _enter(t, 'sodium_mg', '');
    expect(find.byKey(const ValueKey('sodium_unit:mg')), findsNothing);
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.nutrients.sodiumMg, isNull);
    expect(h.last.sodiumUnit, isNull);
  });

  testWidgets('no unit picker without sodium_unit_required; the label says mg '
      'and there is no duplicate suffix', (t) async {
    final h = await _pump(t, draftFixture('clean'));
    expect(find.byKey(const ValueKey('sodium_unit:mg')), findsNothing);
    expect(find.byKey(const ValueKey('sodium_unit_suffix')), findsNothing);
    final field = find.byKey(const ValueKey('field:sodium_mg'));
    expect(
      find.descendant(of: field, matching: find.text(en.confirmFieldSodiumMg)),
      findsOneWidget,
    );
    await _save(t);
    expect(h.last.sodiumUnit, isNull);
  });

  testWidgets('with the picker the sodium label has no unit', (t) async {
    await _pump(t, draftFixture('unit_unconfirmed_sodium_per_100g'));
    final field = find.byKey(const ValueKey('field:sodium_mg'));
    expect(
      find.descendant(of: field, matching: find.text(en.confirmSodium)),
      findsOneWidget,
    );
    expect(
      find.descendant(of: field, matching: find.text(en.confirmFieldSodiumMg)),
      findsNothing,
    );
  });

  group('derived_from_serving', () {
    testWidgets('shows the printed per-serving column and the serving size; '
        'sends per_serving, never the derived per-100 g', (t) async {
      final h = await _pump(t, draftFixture('derived_from_serving'));
      expect(find.text(en.confirmDerivedPerServing('30')), findsOneWidget);
      expect(_text(t, 'serving_size_g'), '30');
      expect(_text(t, 'protein_g'), '0.9');
      expect(_text(t, 'energy_kcal'), '45');
      await _tap(t, 'confirm:serving_size_g');
      await _save(t);
      expect(h.last.basis, ProductCreateBasis.perServing);
      expect(h.last.nutrients.proteinG, 0.9);
      expect(h.last.nutrients.energyKcal, 45);
      expect(h.last.servingSizeG, 30);
    });

    testWidgets('save needs the serving-size tick; serving_size_g is '
        'confirmed only after a tick', (t) async {
      final h = await _pump(t, draftFixture('derived_from_serving'));
      expect(_boxValue(t, 'serving_size_g'), isFalse);
      expect(_saveEnabled(t), isFalse);
      await _tap(t, 'confirm:serving_size_g');
      expect(_saveEnabled(t), isTrue);
      await _save(t);
      expect(_confirmed(h.last), ['serving_size_g']);
    });

    testWidgets('editing the serving size confirms it, and the derived line '
        'shows the edited serving', (t) async {
      final h = await _pump(t, draftFixture('derived_from_serving'));
      await _enter(t, 'serving_size_g', '25');
      expect(find.text(en.confirmDerivedPerServing('25')), findsOneWidget);
      expect(find.text(en.confirmDerivedPerServing('30')), findsNothing);
      expect(_saveEnabled(t), isTrue);
      await _save(t);
      expect(h.last.servingSizeG, 25);
      expect(_confirmed(h.last), ['serving_size_g']);
    });

    testWidgets('derived_basis_mismatch saved per 100 g needs a confirmed '
        'serving (server serving_required)', (t) async {
      await _pump(t, draftFixture('derived_basis_mismatch'));
      await _tap(t, 'basis:per_100g');
      expect(_saveEnabled(t), isFalse);
      await _tap(t, 'confirm:serving_size_g');
      expect(_saveEnabled(t), isTrue);
    });

    testWidgets('with basis_required the tick is still needed per serving', (
      t,
    ) async {
      final h = await _pump(t, draftFixture('derived_basis_mismatch'));
      await _tap(t, 'basis:per_serving');
      expect(_text(t, 'protein_g'), '0.9');
      expect(_saveEnabled(t), isFalse);
      await _tap(t, 'confirm:serving_size_g');
      expect(_saveEnabled(t), isTrue);
      await _save(t);
      expect(h.last.basis, ProductCreateBasis.perServing);
      expect(h.last.nutrients.proteinG, 0.9);
      expect(_confirmed(h.last), ['serving_size_g']);
    });
  });

  testWidgets('a draft serving size is shown with an unticked confirm box', (
    t,
  ) async {
    final h = await _pump(t, draftFixture('upper_bound_protein_per_serving'));
    expect(_text(t, 'serving_size_g'), '30');
    expect(_boxValue(t, 'serving_size_g'), isFalse);
    await _save(t);
    expect(h.last.servingSizeG, 30);
    expect(_confirmed(h.last), isEmpty);
  });

  testWidgets('a serving typed where the draft had none is confirmed by the '
      'typing', (t) async {
    final h = await _pump(t, draftFixture('clean'));
    expect(_text(t, 'serving_size_g'), isEmpty);
    expect(find.byKey(const ValueKey('confirm:serving_size_g')), findsNothing);
    await _enter(t, 'serving_size_g', '25');
    await _save(t);
    expect(h.last.servingSizeG, 25);
    expect(_confirmed(h.last), ['serving_size_g']);
  });

  testWidgets('category_required keeps save disabled until a category is '
      'chosen', (t) async {
    final h = await _pump(t, draftFixture('category_check'));
    expect(find.text(en.warningCategoryCheck), findsOneWidget);
    for (final c in ProductCreateCategory.$valuesDefined) {
      expect(_chipSelected(t, 'category:${c.json}'), isFalse, reason: c.json);
    }
    expect(_saveEnabled(t), isFalse);
    await _tap(t, 'category:beverage');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.category, ProductCreateCategory.beverage);
  });

  testWidgets('Devanagari ingredients round-trip unchanged', (t) async {
    final j = baseDraftJson();
    j['ingredients'] = ['गेहूं का आटा', 'चीनी (शक्कर)'];
    final h = await _pump(t, draftFrom(j));
    expect(find.text('गेहूं का आटा'), findsOneWidget);
    await t.tap(find.text(en.confirmAddIngredient));
    await t.pump();
    await t.enterText(_field('ingredient:2'), 'मूंगफली तेल');
    await t.pump();
    await _save(t);
    expect(h.last.ingredients, ['गेहूं का आटा', 'चीनी (शक्कर)', 'मूंगफली तेल']);
  });

  testWidgets('allergen statements shown in full; clearing one needs a '
      'deliberate confirmation', (t) async {
    final h = await _pump(t, baseDraft());
    expect(_text(t, 'allergen_statement'), 'Contains wheat (gluten).');
    expect(_text(t, 'may_contain_statement'), 'May contain milk.');
    await _enter(t, 'may_contain_statement', '');
    expect(_saveEnabled(t), isFalse);
    expect(find.text(en.confirmClearStatementConfirm), findsOneWidget);
    await _tap(t, 'blank:may_contain_statement');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.mayContainStatement, isNull);
    expect(h.last.allergenStatement, 'Contains wheat (gluten).');
  });

  testWidgets('manual entry: empty form, needs name, category and basis, no '
      'scan_id', (t) async {
    final h = await _pump(t, null);
    expect(_text(t, 'name'), isEmpty);
    expect(_text(t, 'protein_g'), isEmpty);
    expect(_text(t, 'serving_size_g'), isEmpty);
    expect(find.byType(WarningBanner), findsNothing);
    expect(find.byType(CheckboxListTile), findsNothing);
    expect(_chipSelected(t, 'basis:per_100g'), isFalse);
    expect(_chipSelected(t, 'basis:per_serving'), isFalse);
    expect(_saveEnabled(t), isFalse);
    await _enter(t, 'name', 'Home Namkeen');
    expect(_saveEnabled(t), isFalse);
    await _tap(t, 'category:general');
    expect(_saveEnabled(t), isFalse, reason: 'basis is a forced choice');
    await _tap(t, 'basis:per_100g');
    expect(_saveEnabled(t), isTrue);
    await _enter(t, 'sugars_g', '4.25');
    await _enter(t, 'sodium_mg', '120');
    expect(find.byKey(const ValueKey('sodium_unit:mg')), findsNothing);
    await _save(t);
    expect(h.last.scanId, isNull);
    expect(h.last.name, 'Home Namkeen');
    expect(h.last.basis, ProductCreateBasis.per100g);
    expect(h.last.nutrients.sugarsG, 4.25);
    expect(h.last.nutrients.proteinG, isNull);
    expect(h.last.sodiumUnit, isNull);
    expect(h.last.confirmedFields, isEmpty);

    // Per serving needs a serving size; no confirm box for typed values.
    await _tap(t, 'basis:per_serving');
    expect(_saveEnabled(t), isFalse);
    await _enter(t, 'serving_size_g', '30');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.basis, ProductCreateBasis.perServing);
    expect(h.last.nutrients.sugarsG, 4.25);
    expect(h.last.servingSizeG, 30);
    expect(h.last.confirmedFields, isEmpty);
  });

  testWidgets('server field errors show next to the field', (t) async {
    await _pump(
      t,
      baseDraft(),
      fieldErrors: {'protein_g': en.errorImplausibleValue},
    );
    expect(find.byKey(const ValueKey('highlight:protein_g')), findsOneWidget);
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('field:protein_g')),
        matching: find.text(en.errorImplausibleValue),
      ),
      findsOneWidget,
    );
  });

  testWidgets('malformed numbers are rejected, never guessed', (t) async {
    await _pump(t, baseDraft());
    for (final bad in ['1,5', '-1', 'abc', '1.2.3', '1e3', '५']) {
      await _enter(t, 'fat_g', bad);
      expect(_saveEnabled(t), isFalse, reason: bad);
      expect(
        find.descendant(
          of: find.byKey(const ValueKey('field:fat_g')),
          matching: find.text(en.errorValidationError),
        ),
        findsOneWidget,
        reason: bad,
      );
    }
    await _enter(t, 'fat_g', '1.5');
    expect(_saveEnabled(t), isTrue);
  });

  testWidgets('small printed values show exactly (0.04 is not 0) and are '
      'sent unchanged', (t) async {
    final j = baseDraftJson();
    final col = j['per_100g']! as Map<String, Object?>;
    col['trans_fat_g'] = 0.04;
    col['sat_fat_g'] = 6.25;
    final h = await _pump(t, draftFrom(j));
    expect(_text(t, 'trans_fat_g'), '0.04');
    expect(_text(t, 'sat_fat_g'), '6.25');
    expect(_text(t, 'sodium_mg'), '360');
    await _save(t);
    expect(h.last.nutrients.transFatG, 0.04);
    expect(h.last.nutrients.satFatG, 6.25);
  });

  testWidgets('a blank input sends null', (t) async {
    final h = await _pump(t, baseDraft());
    await _enter(t, 'sugars_g', '   ');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.nutrients.sugarsG, isNull);
  });

  testWidgets('claims: one per line; ingredients removed only by the user', (
    t,
  ) async {
    final j = baseDraftJson();
    j['claims'] = ['No added sugar', 'High fibre'];
    final h = await _pump(t, draftFrom(j));
    expect(_text(t, 'claims'), 'No added sugar\nHigh fibre');
    await _enter(t, 'claims', 'No added sugar\n\nHigh fibre\nSugar free');
    await t.tap(find.byKey(const ValueKey('remove:ingredient:1')));
    await t.pumpAndSettle();
    expect(find.text(en.confirmVegMarkTitle), findsOneWidget);
    await _save(t);
    expect(h.last.claims, ['No added sugar', 'High fibre', 'Sugar free']);
    expect(h.last.ingredients, ['Wheat flour', 'Palm oil']);
  });
}
