import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../scan/domain/number_text.dart';

/// What the quick-add form hands back. A blank optional field is null,
/// never 0.
class QuickAddValues {
  const QuickAddValues({
    required this.energyKcal,
    this.name,
    this.proteinG,
    this.fatG,
    this.carbsG,
    this.fibreG,
  });

  final String? name;
  final num energyKcal;
  final num? proteinG;
  final num? fatG;
  final num? carbsG;
  final num? fibreG;
}

/// Name (optional), calories (required) and optional protein, fat, carbs
/// and fibre. The API checks the bounds; the form only requires calories.
class QuickAddForm extends StatefulWidget {
  const QuickAddForm({
    super.key,
    required this.onSubmit,
    this.busy = false,
    this.error,
  });

  final void Function(QuickAddValues values) onSubmit;
  final bool busy;
  final String? error;

  static const nameKey = Key('quick-name');
  static const energyKey = Key('quick-energy');
  static const proteinKey = Key('quick-protein');
  static const fatKey = Key('quick-fat');
  static const carbsKey = Key('quick-carbs');
  static const fibreKey = Key('quick-fibre');
  static const saveKey = Key('quick-save');
  static const energyErrorKey = Key('quick-energy-error');

  @override
  State<QuickAddForm> createState() => _QuickAddFormState();
}

class _QuickAddFormState extends State<QuickAddForm> {
  final _name = TextEditingController();
  final _energy = TextEditingController();
  final _protein = TextEditingController();
  final _fat = TextEditingController();
  final _carbs = TextEditingController();
  final _fibre = TextEditingController();
  bool _energyMissing = false;

  @override
  void dispose() {
    for (final c in [_name, _energy, _protein, _fat, _carbs, _fibre]) {
      c.dispose();
    }
    super.dispose();
  }

  num? _n(TextEditingController c) => parseNumber(c.text).value;

  void _submit() {
    final e = _n(_energy);
    if (e == null || e <= 0) {
      setState(() => _energyMissing = true);
      return;
    }
    setState(() => _energyMissing = false);
    final name = _name.text.trim();
    widget.onSubmit(
      QuickAddValues(
        name: name.isEmpty ? null : name,
        energyKcal: e,
        proteinG: _n(_protein),
        fatG: _n(_fat),
        carbsG: _n(_carbs),
        fibreG: _n(_fibre),
      ),
    );
  }

  Widget _num(Key key, TextEditingController c, String label, {String? err}) =>
      Padding(
        padding: const EdgeInsets.only(bottom: SnTokens.space2),
        child: TextField(
          key: key,
          controller: c,
          enabled: !widget.busy,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(labelText: label, errorText: err),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: SnTokens.space2),
          child: TextField(
            key: QuickAddForm.nameKey,
            controller: _name,
            enabled: !widget.busy,
            maxLength: 60,
            decoration: InputDecoration(labelText: l10n.diaryQuickAddNameLabel),
          ),
        ),
        _num(
          QuickAddForm.energyKey,
          _energy,
          l10n.diaryQuickAddEnergy,
          err: _energyMissing ? l10n.errorQuickAddEnergyRequired : null,
        ),
        _num(QuickAddForm.proteinKey, _protein, l10n.diaryQuickAddProtein),
        _num(QuickAddForm.fatKey, _fat, l10n.diaryQuickAddFat),
        _num(QuickAddForm.carbsKey, _carbs, l10n.diaryQuickAddCarbs),
        _num(QuickAddForm.fibreKey, _fibre, l10n.diaryQuickAddFibre),
        Text(
          l10n.foodsBlankIsUnknown,
          style: Theme.of(context).textTheme.bodySmall,
        ),
        if (widget.error != null) ...[
          const SizedBox(height: SnTokens.space2),
          Text(widget.error!),
        ],
        const SizedBox(height: SnTokens.space3),
        PrimaryButton(
          buttonKey: QuickAddForm.saveKey,
          label: l10n.mealsLogSave,
          icon: Icons.check_rounded,
          busy: widget.busy,
          onPressed: _submit,
        ),
      ],
    );
  }
}
