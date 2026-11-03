import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/tokens.g.dart';
import 'package:smartnutri_ai/features/scan/presentation/draft_form.dart';
import 'package:smartnutri_ai/features/scan/presentation/warning_banner.dart';
import 'package:smartnutri_api/src/export.dart';

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

void main() {
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
    await _pump(t, implausibleDraft());
    expect(find.text(en.warningImplausibleValue), findsOneWidget);
    expect(
      find.descendant(
        of: find.byType(WarningBanner),
        matching: find.text(en.confirmFieldSugarsG),
      ),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('highlight:sugars_g')), findsOneWidget);
    expect(find.byKey(const ValueKey('highlight:protein_g')), findsNothing);
  });

  testWidgets('per_100g_missing warning shown for per-serving label without '
      'serving size', (t) async {
    await _pump(t, per100gMissingDraft());
    expect(find.text(en.warningPer100gMissing), findsOneWidget);
    expect(find.text(en.warningPerServingIgnored), findsOneWidget);
  });

  testWidgets('a code:path warning renders its key and the field label, and '
      'highlights the field', (t) async {
    await _pump(t, withheldProteinDraft());
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

  group('withheld protein', () {
    testWidgets('unticked: sent, but not in confirmed_fields', (t) async {
      final h = await _pump(t, withheldProteinDraft());
      expect(find.text(en.confirmWithheldHint), findsOneWidget);
      final box = t.widget<Checkbox>(
        find.descendant(
          of: find.byKey(const ValueKey('confirm:protein_g')),
          matching: find.byType(Checkbox),
        ),
      );
      expect(box.value, isFalse);
      await _save(t);
      expect(h.last.nutrients.proteinG, 0.5);
      expect(_confirmed(h.last), isNot(contains('protein_g')));
    });

    testWidgets('ticking adds it', (t) async {
      final h = await _pump(t, withheldProteinDraft());
      await _tap(t, 'confirm:protein_g');
      await _save(t);
      expect(_confirmed(h.last), contains('protein_g'));
    });

    testWidgets('editing adds it', (t) async {
      final h = await _pump(t, withheldProteinDraft());
      await _enter(t, 'protein_g', '0.4');
      await _save(t);
      expect(h.last.nutrients.proteinG, 0.4);
      expect(_confirmed(h.last), contains('protein_g'));
    });
  });

  testWidgets('basis_mismatch: save disabled until a basis is chosen; numbers '
      'sent as printed', (t) async {
    final h = await _pump(t, basisMismatchDraft());
    expect(find.text(en.warningBasisMismatch), findsOneWidget);
    expect(_saveEnabled(t), isFalse);
    expect(find.text(en.confirmChooseRequired), findsOneWidget);
    await _tap(t, 'basis:per_100g');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.basis, ProductCreateBasis.per100g);
    expect(h.last.nutrients.proteinG, 7.5);
    expect(h.last.nutrients.energyKcal, 451.37);

    // Per serving: the printed numbers stay as they are, and a serving size
    // must be entered (typing it confirms it) before saving.
    await _tap(t, 'basis:per_serving');
    expect(_text(t, 'protein_g'), '7.5');
    expect(_saveEnabled(t), isFalse);
    await _enter(t, 'serving_size_g', '30');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.basis, ProductCreateBasis.perServing);
    expect(h.last.nutrients.proteinG, 7.5);
    expect(h.last.nutrients.energyKcal, 451.37);
    expect(h.last.nutrients.sodiumMg, 360);
    expect(h.last.servingSizeG, 30);
    expect(_confirmed(h.last), contains('serving_size_g'));
  });

  testWidgets('unit_unconfirmed sodium: save disabled until mg or g; 0.4 '
      'stays 0.4', (t) async {
    final h = await _pump(t, sodiumUnitDraft());
    expect(find.text(en.warningUnitUnconfirmed), findsOneWidget);
    expect(find.byKey(const ValueKey('highlight:sodium_mg')), findsOneWidget);
    expect(_saveEnabled(t), isFalse);
    expect(_text(t, 'sodium_mg'), '0.4');
    await _tap(t, 'sodium_unit:g');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.sodiumUnit, ProductCreateSodiumUnit.g);
    expect(h.last.nutrients.sodiumMg, 0.4);
  });

  testWidgets('R19: the unit picker shows for a unit-less sodium on either '
      'column, whichever basis is chosen, and the unit sits beside the input', (
    t,
  ) async {
    final j = baseDraftJson();
    j['per_serving'] = column(energyKcal: 90, sodiumMg: 0.1);
    j['serving_size_g'] = 20;
    j['warnings'] = ['unit_unconfirmed:per_serving.sodium_mg'];
    final h = await _pump(t, draftFrom(j));
    // Basis is per 100 g (mg printed there), yet the per-serving column's
    // sodium had no unit: the choice is still required.
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
    expect(h.last.nutrients.sodiumMg, 360);
  });

  testWidgets('R19: confirming sodium never replaces the unit choice', (
    t,
  ) async {
    await _pump(t, sodiumUnitDraft());
    expect(find.byKey(const ValueKey('confirm:sodium_mg')), findsNothing);
    await _enter(t, 'sodium_mg', '0.5');
    expect(_saveEnabled(t), isFalse);
  });

  testWidgets('no unit picker without a unit_unconfirmed warning; mg shown '
      'beside sodium', (t) async {
    final h = await _pump(t, baseDraft());
    expect(find.byKey(const ValueKey('sodium_unit:mg')), findsNothing);
    final suffix = find.byKey(const ValueKey('sodium_unit_suffix'));
    expect(
      find.descendant(
        of: suffix,
        matching: find.text(en.confirmSodiumUnitOptionMg),
      ),
      findsOneWidget,
    );
    await _save(t);
    expect(h.last.sodiumUnit, isNull);
  });

  group('derived_from_serving', () {
    testWidgets('shows the printed per-serving column and the serving size; '
        'sends per_serving, never the derived per-100 g (R19)', (t) async {
      final h = await _pump(t, derivedDraft());
      expect(find.text(en.confirmDerivedPerServing('30')), findsOneWidget);
      expect(_text(t, 'serving_size_g'), '30');
      expect(_text(t, 'protein_g'), '2');
      expect(_text(t, 'energy_kcal'), '120');
      final basis = t.widget<ChoiceChip>(
        find.byKey(const ValueKey('basis:per_serving')),
      );
      expect(basis.selected, isTrue);
      await _tap(t, 'confirm:serving_size_g');
      await _save(t);
      expect(h.last.basis, ProductCreateBasis.perServing);
      expect(h.last.nutrients.proteinG, 2);
      expect(h.last.nutrients.energyKcal, 120);
      expect(h.last.servingSizeG, 30);
    });

    testWidgets('R19: save needs the serving-size tick; serving_size_g is '
        'confirmed only after a tick', (t) async {
      final h = await _pump(t, derivedDraft());
      final box = t.widget<Checkbox>(
        find.descendant(
          of: find.byKey(const ValueKey('confirm:serving_size_g')),
          matching: find.byType(Checkbox),
        ),
      );
      expect(box.value, isFalse);
      expect(_saveEnabled(t), isFalse);
      await _tap(t, 'confirm:serving_size_g');
      expect(_saveEnabled(t), isTrue);
      await _save(t);
      expect(_confirmed(h.last), contains('serving_size_g'));
    });

    testWidgets('editing the serving size confirms it', (t) async {
      final h = await _pump(t, derivedDraft());
      await _enter(t, 'serving_size_g', '25');
      expect(_saveEnabled(t), isTrue);
      await _save(t);
      expect(h.last.servingSizeG, 25);
      expect(_confirmed(h.last), contains('serving_size_g'));
    });

    testWidgets('R19: the tick is required even with basis_mismatch', (
      t,
    ) async {
      final j = derivedDraftJson();
      j['warnings'] = ['derived_from_serving', 'basis_mismatch'];
      final h = await _pump(t, draftFrom(j));
      expect(_text(t, 'protein_g'), '2');
      expect(_saveEnabled(t), isFalse);
      await _tap(t, 'confirm:serving_size_g');
      expect(_saveEnabled(t), isTrue);
      await _save(t);
      expect(h.last.basis, ProductCreateBasis.perServing);
      expect(h.last.nutrients.proteinG, 2);
      expect(_confirmed(h.last), contains('serving_size_g'));
    });
  });

  testWidgets('a draft serving size is shown with an unticked confirm box', (
    t,
  ) async {
    final j = baseDraftJson();
    j['serving_size_g'] = 300;
    final h = await _pump(t, draftFrom(j));
    expect(_text(t, 'serving_size_g'), '300');
    await _save(t);
    expect(h.last.servingSizeG, 300);
    expect(_confirmed(h.last), isNot(contains('serving_size_g')));
  });

  testWidgets('category_check keeps save disabled until a category is chosen', (
    t,
  ) async {
    final h = await _pump(t, categoryCheckDraft());
    expect(find.text(en.warningCategoryCheck), findsOneWidget);
    for (final c in ProductCreateCategory.$valuesDefined) {
      final chip = t.widget<ChoiceChip>(
        find.byKey(ValueKey('category:${c.json}')),
      );
      expect(chip.selected, isFalse, reason: c.json);
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

  testWidgets('manual entry: empty form, needs name and category, no scan_id', (
    t,
  ) async {
    final h = await _pump(t, null);
    expect(_text(t, 'name'), isEmpty);
    expect(_text(t, 'protein_g'), isEmpty);
    expect(find.byType(WarningBanner), findsNothing);
    expect(_saveEnabled(t), isFalse);
    await _enter(t, 'name', 'Home Namkeen');
    expect(_saveEnabled(t), isFalse);
    await _tap(t, 'category:general');
    expect(_saveEnabled(t), isTrue);
    await _enter(t, 'sugars_g', '4.25');
    await _save(t);
    expect(h.last.scanId, isNull);
    expect(h.last.name, 'Home Namkeen');
    expect(h.last.nutrients.sugarsG, 4.25);
    expect(h.last.nutrients.proteinG, isNull);
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

  testWidgets('a scan saved per serving needs the serving-size tick', (
    t,
  ) async {
    final j = baseDraftJson();
    j['per_serving'] = column(energyKcal: 135, proteinG: 2.3, sodiumMg: 108);
    j['serving_size_g'] = 30;
    final h = await _pump(t, draftFrom(j));
    expect(_saveEnabled(t), isTrue, reason: 'per 100 g needs no tick');
    await _tap(t, 'basis:per_serving');
    // The printed per-serving column, not the per-100 g one.
    expect(_text(t, 'protein_g'), '2.3');
    expect(_text(t, 'energy_kcal'), '135');
    expect(_saveEnabled(t), isFalse);
    await _tap(t, 'confirm:serving_size_g');
    expect(_saveEnabled(t), isTrue);
    await _save(t);
    expect(h.last.basis, ProductCreateBasis.perServing);
    expect(h.last.nutrients.proteinG, 2.3);
    expect(h.last.nutrients.carbsG, isNull);
    expect(h.last.servingSizeG, 30);
    expect(_confirmed(h.last), contains('serving_size_g'));
  });

  testWidgets('with a sodium-unit warning the sodium label has no unit', (
    t,
  ) async {
    await _pump(t, sodiumUnitDraft());
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

  testWidgets('without a sodium-unit warning the label is "Sodium (mg)"', (
    t,
  ) async {
    await _pump(t, baseDraft());
    final field = find.byKey(const ValueKey('field:sodium_mg'));
    expect(
      find.descendant(of: field, matching: find.text(en.confirmFieldSodiumMg)),
      findsOneWidget,
    );
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
