import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/observability/analytics.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/share/share_text.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../../diary/presentation/diary_providers.dart';
import '../../scan/domain/number_text.dart';
import '../data/meals_repository.dart';
import '../domain/meal_draft.dart';
import 'meals_providers.dart';

/// The product being logged. Exactly one of [productId] (our product) and
/// [barcode] (Open Food Facts) is set.
class LogMealProduct {
  const LogMealProduct({
    required this.productId,
    required this.barcode,
    required this.name,
    required this.servingSizeG,
  });

  final String? productId;
  final String? barcode;
  final String name;

  /// From the API; servings are offered only when it is known.
  final num? servingSizeG;
}

/// The member as the family list shows them: "You" for the account holder,
/// their name, or the relation when the name is blank. Never a status or a
/// condition.
String memberLabel(AppLocalizations l10n, VerdictOut v) {
  if (v.isPrimary) return l10n.resultYou;
  final name = v.memberName.trim();
  if (name.isNotEmpty) return name;
  return shareRelation(l10n, v.relation.json);
}

/// Opens the "I ate this" sheet for [product], preselecting [memberId].
/// Returns what happened, or null when dismissed.
Future<MealLogResult?> showLogMealSheet(
  BuildContext context, {
  required LogMealProduct product,
  required List<VerdictOut> verdicts,
  required String memberId,
}) => showModalBottomSheet<MealLogResult>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  builder: (_) =>
      LogMealSheet(product: product, verdicts: verdicts, memberId: memberId),
);

enum _Portion { servings, grams }

/// "I ate this": who ate it and how much (servings when the product has a
/// serving size, else grams). Shows names only, never verdicts.
class LogMealSheet extends ConsumerStatefulWidget {
  const LogMealSheet({
    super.key,
    required this.product,
    required this.verdicts,
    required this.memberId,
  });

  final LogMealProduct product;
  final List<VerdictOut> verdicts;
  final String memberId;

  static const saveKey = Key('log-meal-save');
  static const amountKey = Key('log-meal-amount');

  /// Same bounds as the API (`MealIn`).
  static const maxGrams = 5000;
  static const maxServings = 200;

  @override
  ConsumerState<LogMealSheet> createState() => _LogMealSheetState();
}

class _LogMealSheetState extends ConsumerState<LogMealSheet> {
  late String _memberId = widget.memberId;
  late _Portion _portion = widget.product.servingSizeG == null
      ? _Portion.grams
      : _Portion.servings;
  late final _amount = TextEditingController(
    text: _portion == _Portion.servings ? '1' : '',
  );
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _amount.dispose();
    super.dispose();
  }

  num? get _value {
    final parsed = parseNumber(_amount.text);
    final v = parsed.value;
    if (!parsed.ok || v == null || v <= 0) return null;
    final max = _portion == _Portion.grams
        ? LogMealSheet.maxGrams
        : LogMealSheet.maxServings;
    return v > max ? null : v;
  }

  Future<void> _save() async {
    final value = _value;
    if (value == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    final diaryContext = ref.read(diaryAddContextProvider);
    final draft = MealDraft(
      memberId: _memberId,
      productId: widget.product.productId,
      barcode: widget.product.productId == null ? widget.product.barcode : null,
      grams: _portion == _Portion.grams ? value : null,
      servings: _portion == _Portion.servings ? value : null,
      eatenAt: DateTime.now().toUtc(),
      // From the Diary's add-food flow: its slot and day (else the API picks).
      mealSlotId: diaryContext?.slotId,
      localDate: diaryContext?.localDate,
      displayName: widget.product.name,
    );
    try {
      final result = await ref.read(mealsRepositoryProvider).log(draft);
      ref.read(mealsRevisionProvider.notifier).bump();
      // Event name only: no product, member or portion.
      await ref
          .read(analyticsProvider)
          .track(result is MealLogged ? 'meal_logged' : 'meal_queued');
      if (diaryContext != null) {
        // The method only (search, barcode or label).
        await ref.read(analyticsProvider).track('diary_entry_added', {
          'method': diaryContext.method,
        });
      }
      if (mounted) Navigator.of(context).pop(result);
    } on MealsFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(AppLocalizations.of(context), e.code);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final serving = widget.product.servingSizeG;
    final error = _error;
    return Padding(
      padding: EdgeInsets.only(
        left: SnTokens.space4,
        right: SnTokens.space4,
        bottom: MediaQuery.viewInsetsOf(context).bottom + SnTokens.space4,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.mealsLogTitle, style: theme.textTheme.titleLarge),
            const SizedBox(height: SnTokens.space1),
            Text(
              widget.product.name,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: c.textSecondary,
              ),
            ),
            const SizedBox(height: SnTokens.space4),
            Text(l10n.mealsLogMember, style: theme.textTheme.titleSmall),
            const SizedBox(height: SnTokens.space2),
            Wrap(
              spacing: SnTokens.space2,
              runSpacing: SnTokens.space2,
              children: [
                for (final v in widget.verdicts)
                  ChoiceChip(
                    label: Text(memberLabel(l10n, v)),
                    selected: v.memberId == _memberId,
                    onSelected: _busy
                        ? null
                        : (_) => setState(() => _memberId = v.memberId),
                  ),
              ],
            ),
            const SizedBox(height: SnTokens.space4),
            if (serving != null) ...[
              SegmentedButton<_Portion>(
                segments: [
                  ButtonSegment(
                    value: _Portion.servings,
                    label: Text(l10n.mealsLogServings),
                  ),
                  ButtonSegment(
                    value: _Portion.grams,
                    label: Text(l10n.mealsLogGrams),
                  ),
                ],
                selected: {_portion},
                onSelectionChanged: _busy
                    ? null
                    : (s) => setState(() {
                        _portion = s.single;
                        _amount.text = _portion == _Portion.servings ? '1' : '';
                      }),
              ),
              const SizedBox(height: SnTokens.space3),
            ],
            TextField(
              key: LogMealSheet.amountKey,
              controller: _amount,
              enabled: !_busy,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              onChanged: (_) => setState(() {}),
              decoration: InputDecoration(
                labelText: _portion == _Portion.servings
                    ? l10n.mealsLogAmountServings
                    : l10n.mealsLogAmountGrams,
                helperText: serving != null && _portion == _Portion.servings
                    ? l10n.mealsLogServingSize(formatForDisplay(serving))
                    : null,
              ),
            ),
            const SizedBox(height: SnTokens.space3),
            Row(
              children: [
                Icon(
                  Icons.schedule_rounded,
                  size: SnTokens.fontSizeMd,
                  color: c.textSecondary,
                ),
                const SizedBox(width: SnTokens.space2),
                Text(
                  '${l10n.mealsLogEatenAt}: ${l10n.mealsLogNow}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: c.textSecondary,
                  ),
                ),
              ],
            ),
            if (error != null) ...[
              const SizedBox(height: SnTokens.space3),
              InlineErrorBanner(message: error),
            ],
            const SizedBox(height: SnTokens.space4),
            PrimaryButton(
              buttonKey: LogMealSheet.saveKey,
              label: l10n.mealsLogSave,
              icon: Icons.check_rounded,
              busy: _busy,
              onPressed: _value == null ? null : _save,
            ),
          ],
        ),
      ),
    );
  }
}
