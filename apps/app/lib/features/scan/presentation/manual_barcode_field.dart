import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../domain/barcode.dart';

class ManualBarcodeField extends StatefulWidget {
  const ManualBarcodeField({super.key, required this.onSubmit});

  final void Function(String barcode) onSubmit;

  @override
  State<ManualBarcodeField> createState() => _ManualBarcodeFieldState();
}

class _ManualBarcodeFieldState extends State<ManualBarcodeField> {
  final _controller = TextEditingController();
  bool _invalid = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final code = normalizeBarcode(_controller.text);
    setState(() => _invalid = code == null);
    if (code != null) widget.onSubmit(code);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          l10n.scanManualEntry,
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: SnTokens.space2),
        TextField(
          controller: _controller,
          keyboardType: TextInputType.number,
          inputFormatters: [
            FilteringTextInputFormatter.allow(RegExp(r'[0-9\s-]')),
          ],
          decoration: InputDecoration(
            hintText: l10n.scanManualPlaceholder,
            errorText: _invalid ? l10n.scanInvalid : null,
            prefixIcon: const Icon(Icons.dialpad_rounded),
          ),
          onSubmitted: (_) => _submit(),
        ),
        const SizedBox(height: SnTokens.space3),
        PrimaryButton(
          label: l10n.scanSubmit,
          icon: Icons.search_rounded,
          onPressed: _submit,
        ),
      ],
    );
  }
}
