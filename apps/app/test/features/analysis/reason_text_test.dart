import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/analysis/domain/reasons.dart';
import 'package:smartnutri_ai/features/analysis/presentation/reason_line.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';

ReasonOut _r(
  String code,
  Map<String, Object?> params, [
  String sev = 'caution',
]) => ReasonOut(
  code: code,
  params: params,
  severity: ReasonOutSeverity.fromJson(sev),
);

void main() {
  final en = lookupAppLocalizations(const Locale('en'));
  final locales = [
    for (final l in ['en', 'hi', 'mr']) lookupAppLocalizations(Locale(l)),
  ];

  group('reasonMessageKey (reason_variant rules)', () {
    test('diet_violation with ingredients uses reason.diet_violation', () {
      expect(
        reasonMessageKey(
          _r('diet_violation', {
            'diet': 'jain',
            'ingredients': ['onion'],
          }),
        ),
        'reason.diet_violation',
      );
    });
    test('diet_violation with empty ingredients is the mark-only variant', () {
      expect(
        reasonMessageKey(
          _r('diet_violation', {'diet': 'veg', 'ingredients': <String>[]}),
        ),
        'reason_variant.diet_violation_mark_only',
      );
      expect(
        reasonText(
          en,
          _r('diet_violation', {'diet': 'veg', 'ingredients': <String>[]}),
        ),
        en.reasonVariantDietViolationMarkOnly(en.dietVeg),
      );
    });
    test('nutrient_missing with reason=low_confidence is the variant', () {
      final r = _r('nutrient_missing', {
        'nutrient': 'sugars_g',
        'rule': 'blood_sugar',
        'reason': 'low_confidence',
      }, 'unknown');
      expect(
        reasonMessageKey(r),
        'reason_variant.nutrient_missing_low_confidence',
      );
      expect(
        reasonText(en, r),
        en.reasonVariantNutrientMissingLowConfidence(en.nutrientSugarsG),
      );
    });
    test('plain nutrient_missing uses reason.nutrient_missing', () {
      final r = _r('nutrient_missing', {
        'nutrient': 'salt',
        'rule': 'hypertension',
      }, 'unknown');
      expect(reasonMessageKey(r), 'reason.nutrient_missing');
      expect(reasonText(en, r), en.reasonNutrientMissing(en.nutrientSalt));
    });
  });

  group('displayReasons', () {
    test(
      'collapses duplicate nutrient_missing lines by nutrient, API order kept',
      () {
        final reasons = [
          _r('nutrient_missing', {
            'nutrient': 'salt',
            'rule': 'hypertension',
          }, 'unknown'),
          _r('sugar_high', {'sugars_g': 30}, 'avoid'),
          _r('nutrient_missing', {
            'nutrient': 'salt',
            'rule': 'child',
          }, 'unknown'),
          _r('nutrient_missing', {
            'nutrient': 'sugars_g',
            'rule': 'child',
          }, 'unknown'),
        ];
        final shown = displayReasons(reasons);
        expect(shown.map((r) => r.code).toList(), [
          'nutrient_missing',
          'sugar_high',
          'nutrient_missing',
        ]);
        expect((shown[0].params as Map)['nutrient'], 'salt');
        expect((shown[2].params as Map)['nutrient'], 'sugars_g');
      },
    );
    test('other codes are never collapsed or re-ordered', () {
      final reasons = [
        _r('diet_unknown', {'diet': 'veg'}, 'unknown'),
        _r('sugar_moderate', {'sugars_g': 10}),
        _r('diet_unknown', {'diet': 'veg'}, 'unknown'),
      ];
      expect(displayReasons(reasons), reasons);
    });
  });

  group('param localisation', () {
    test('claim code maps through claim.*', () {
      expect(
        reasonText(en, _r('misleading_sugar_claim', {'claim': 'sugar_free'})),
        en.reasonMisleadingSugarClaim(en.claimSugarFree),
      );
    });
    test('high_in list maps through nutrient.* and joins', () {
      expect(
        reasonText(
          en,
          _r('cardio_risk_high_in', {
            'high_in': ['sat_fat', 'salt'],
          }),
        ),
        en.reasonCardioRiskHighIn('saturated fat, salt'),
      );
    });
    test('ingredients list is joined, diet mapped', () {
      expect(
        reasonText(
          en,
          _r('diet_violation', {
            'diet': 'jain',
            'ingredients': ['garlic powder', 'onion powder'],
          }),
        ),
        'May not match the Jain diet: garlic powder, onion powder.',
      );
    });
    test('known allergen is localized, unrecognised one shown as-is', () {
      expect(
        reasonText(en, _r('allergen_contains', {'allergen': 'tree_nut'})),
        en.reasonAllergenContains(en.allergenTreeNut),
      );
      expect(
        reasonText(
          en,
          _r('allergen_unrecognised', {'allergen': 'kiwi'}, 'unknown'),
        ),
        en.reasonAllergenUnrecognised('kiwi'),
      );
    });
    test('condition is shown as-is', () {
      expect(
        reasonText(
          en,
          _r('condition_unrecognised', {'condition': 'gout'}, 'unknown'),
        ),
        en.reasonConditionUnrecognised('gout'),
      );
    });
    test('numbers are formatted for the locale, basis is an ICU select', () {
      expect(
        reasonText(
          en,
          _r('child_sugar_high', {
            'basis': 'per_serving',
            'limit_g': 24.0,
            'pct': 132.5,
          }, 'avoid'),
        ),
        "One serving gives 132.5% of a child's daily sugar limit "
        '(about 24 g a day). That is high for a child.',
      );
      expect(
        reasonText(
          en,
          _r('carbs_per_serving_high', {'basis': 'per_100g', 'carbs_g': 60.0}),
        ),
        en.reasonCarbsPerServingHigh('per_100g', '60'),
      );
    });
  });

  group('robustness', () {
    test('unknown reason code falls back to generic text, never throws', () {
      for (final l10n in locales) {
        final text = reasonText(l10n, _r('brand_new_code', {'x': 1}, 'avoid'));
        expect(text, isNotEmpty);
        expect(text, reasonFallbackText(l10n));
      }
    });
    test('missing or wrongly typed params fall back, never throw', () {
      for (final l10n in locales) {
        expect(
          reasonText(l10n, _r('sugar_high', const {}, 'avoid')),
          reasonFallbackText(l10n),
        );
        expect(
          reasonText(l10n, _r('diet_violation', const {'diet': 3})),
          reasonFallbackText(l10n),
        );
        expect(
          reasonText(
            l10n,
            const ReasonOut(
              code: 'sugar_high',
              params: null,
              severity: ReasonOutSeverity.avoid,
            ),
          ),
          reasonFallbackText(l10n),
        );
      }
    });
  });

  group('R22 rules', () {
    test(
      'diet_violation with missing ingredients is the mark-only variant',
      () {
        final r = _r('diet_violation', {'diet': 'veg'});
        expect(reasonMessageKey(r), 'reason_variant.diet_violation_mark_only');
        expect(
          reasonText(en, r),
          en.reasonVariantDietViolationMarkOnly(en.dietVeg),
        );
      },
    );
    test('nutrient_missing dedupe keeps a variant and a plain line', () {
      final plain = _r('nutrient_missing', {
        'nutrient': 'salt',
        'rule': 'a',
      }, 'unknown');
      final lowConf = _r('nutrient_missing', {
        'nutrient': 'salt',
        'rule': 'b',
        'reason': 'low_confidence',
      }, 'unknown');
      final dupPlain = _r('nutrient_missing', {
        'nutrient': 'salt',
        'rule': 'c',
      }, 'unknown');
      expect(displayReasons([plain, lowConf, dupPlain]), [plain, lowConf]);
    });
    test('numbers use Latin digits in every locale', () {
      final mr = lookupAppLocalizations(const Locale('mr'));
      final hi = lookupAppLocalizations(const Locale('hi'));
      for (final l10n in [mr, hi]) {
        final text = reasonText(
          l10n,
          _r('sugar_high', {'sugars_g': 2.5}, 'avoid'),
        );
        expect(text, contains('2.5'));
        expect(text, isNot(matches(RegExp(r'[\u0966-\u096F]'))));
      }
    });
    test('fallback is verdictReasonUnavailable', () {
      expect(reasonFallbackText(en), en.verdictReasonUnavailable);
    });
    test('splitReasons keeps API order within each group', () {
      final a = _r('allergen_contains', {'allergen': 'milk'}, 'avoid');
      final b = _r('energy_dense', {'energy_kcal': 500});
      final c = _r('sugar_high', {'sugars_g': 30}, 'avoid');
      final d = _r('nutriscore_low', {'grade': 'D'});
      final g = splitReasons([b, a, d, c]);
      expect(g.visible, [a, c]);
      expect(g.collapsed, [b, d]);
    });
  });

  test('every reason in every golden file renders in en, hi and mr', () {
    var count = 0;
    for (final c in sharedFixtureCases()) {
      for (final r in c.verdict.reasons) {
        for (final l10n in locales) {
          final text = reasonText(l10n, r);
          expect(
            text,
            isNotEmpty,
            reason: '${c.product}.${c.member} ${r.code}',
          );
          expect(
            text,
            isNot(reasonFallbackText(l10n)),
            reason: '${c.product}.${c.member} ${r.code} (${l10n.localeName})',
          );
          expect(text, isNot(contains('{')));
          count++;
        }
      }
    }
    expect(count, greaterThan(0));
  });
}
