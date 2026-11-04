import 'package:flutter/material.dart';

import '../../core/theme/tokens.g.dart';

/// The main action on a screen: a full-width filled button in the brand
/// colour. While [busy] it is disabled and shows a small spinner.
class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.busy = false,
    this.buttonKey,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool busy;

  /// Key for the underlying [FilledButton].
  final Key? buttonKey;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: double.infinity,
    child: FilledButton(
      key: buttonKey,
      onPressed: busy ? null : onPressed,
      child: _ButtonContent(label: label, icon: icon, busy: busy),
    ),
  );
}

/// A secondary action: a full-width outlined button.
class SecondaryButton extends StatelessWidget {
  const SecondaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.busy = false,
    this.buttonKey,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool busy;
  final Key? buttonKey;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: double.infinity,
    child: OutlinedButton(
      key: buttonKey,
      onPressed: busy ? null : onPressed,
      child: _ButtonContent(label: label, icon: icon, busy: busy),
    ),
  );
}

class _ButtonContent extends StatelessWidget {
  const _ButtonContent({required this.label, this.icon, this.busy = false});

  final String label;
  final IconData? icon;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final icon = this.icon;
    final Widget? lead = busy
        ? const SizedBox.square(
            dimension: SnTokens.fontSizeLg,
            child: CircularProgressIndicator(strokeWidth: 2),
          )
        : icon == null
        ? null
        : Icon(icon, size: SnTokens.fontSizeLg);
    return Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (lead != null) ...[lead, const SizedBox(width: SnTokens.space2)],
        Flexible(child: Text(label, textAlign: TextAlign.center)),
      ],
    );
  }
}
