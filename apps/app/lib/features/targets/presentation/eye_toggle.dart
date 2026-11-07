import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../data/targets_repository.dart';
import 'targets_providers.dart';

/// One tap hides or shows every number: `show` goes to `hide_all`, anything
/// else goes to `show`. Only `targets_display_put` is called (it needs just
/// the terms), then the targets and summaries reload from the API.
class EyeToggle extends ConsumerStatefulWidget {
  const EyeToggle({super.key, this.settings});

  /// The stored settings, or null when they cannot be read (health data
  /// withdrawn). The toggle still works then: the first tap hides.
  final GoalSettingsOut? settings;

  static const buttonKey = Key('eye-toggle');

  @override
  ConsumerState<EyeToggle> createState() => _EyeToggleState();
}

class _EyeToggleState extends ConsumerState<EyeToggle> {
  bool _busy = false;

  /// Last value set here; used when the stored settings cannot be read.
  String? _local;

  bool get _showing {
    final s = widget.settings;
    if (s == null) return (_local ?? 'show') == 'show';
    return s.numbersDisplay == GoalSettingsOutNumbersDisplay.valueShow;
  }

  Future<void> _toggle() async {
    final l10n = AppLocalizations.of(context);
    final showing = _showing;
    setState(() => _busy = true);
    try {
      await ref
          .read(targetsRepositoryProvider)
          .setDisplay(
            DisplayIn(
              numbersDisplay: showing
                  ? DisplayInNumbersDisplay.hideAll
                  : DisplayInNumbersDisplay.valueShow,
            ),
          );
      if (mounted) {
        setState(() => _local = showing ? 'hide_all' : 'show');
        refreshTargets(ref);
      }
    } on TargetsFailure catch (e) {
      if (mounted) {
        ScaffoldMessenger.maybeOf(context)?.showSnackBar(
          SnackBar(
            content: Text(
              e.isNotFound
                  ? l10n.targetsIntroBody
                  : localizedErrorCode(l10n, e.code),
            ),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final showing = _showing;
    return IconButton(
      key: EyeToggle.buttonKey,
      tooltip: showing ? l10n.diaryEyeHide : l10n.diaryEyeShow,
      icon: Icon(
        showing ? Icons.visibility_outlined : Icons.visibility_off_outlined,
      ),
      onPressed: _busy ? null : _toggle,
    );
  }
}
