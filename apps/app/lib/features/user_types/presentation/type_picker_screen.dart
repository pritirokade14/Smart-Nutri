import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../domain/user_types.dart';
import 'user_type_labels.dart';
import 'user_types_flow.dart';
import 'user_types_providers.dart';

/// "What brings you to SmartNutri?": up to 3 of the 6 user types, right
/// after the terms (and from Profile with [edit]). The types only arrange
/// the app; scanning and results stay the same.
class TypePickerScreen extends ConsumerStatefulWidget {
  const TypePickerScreen({super.key, this.edit = false});

  /// Opened from Profile: prefilled with the stored answers, no "Skip".
  final bool edit;

  static Key tileKey(String type) => Key('user-type-$type');
  static const continueKey = Key('user-types-continue');
  static const skipKey = Key('user-types-skip');
  static const consentNoteKey = Key('user-types-consent-note');

  @override
  ConsumerState<TypePickerScreen> createState() => _TypePickerScreenState();
}

class _TypePickerScreenState extends ConsumerState<TypePickerScreen> {
  bool _busy = false;

  /// The draft is (re)started after the first frame: a provider cannot
  /// change while the tree builds.
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      ref
          .read(userTypesDraftProvider.notifier)
          .start(widget.edit ? ref.read(userTypesProvider).value : null);
      setState(() => _ready = true);
    });
  }

  void _toggle(String type) {
    final ok = ref.read(userTypesDraftProvider.notifier).toggle(type);
    if (!ok) {
      ScaffoldMessenger.maybeOf(context)
        ?..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(context).userTypesMaxReached),
          ),
        );
    }
  }

  Future<void> _continue() async {
    setState(() => _busy = true);
    try {
      if (consentMissingFor(ref) && !await askHealthConsent(context, ref)) {
        return; // nothing left: stay here with the note
      }
      if (!mounted) return;
      final types = ref.read(userTypesDraftProvider).types;
      if (followUpTypes(types).isNotEmpty) {
        await context.push('/welcome/follow-up${editQuery(widget.edit)}');
      } else {
        await saveUserTypes(context, ref, edit: widget.edit);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _skip() async {
    setState(() => _busy = true);
    await skipUserTypes(context, ref);
    if (mounted) setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final watched = ref.watch(userTypesDraftProvider);
    final draft = _ready ? watched : const UserTypesDraft();
    return Scaffold(
      appBar: widget.edit ? AppBar(title: Text(l10n.userTypesEdit)) : null,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(SnTokens.space4),
          children: [
            Text(l10n.userTypesTitle, style: theme.textTheme.headlineSmall),
            const SizedBox(height: SnTokens.space2),
            Text(
              l10n.userTypesSubtitle,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: c.textSecondary,
              ),
            ),
            const SizedBox(height: SnTokens.space3),
            Text(l10n.userTypesPickUpTo, style: theme.textTheme.titleSmall),
            const SizedBox(height: SnTokens.space2),
            for (final type in userTypeKeys)
              _TypeTile(
                key: TypePickerScreen.tileKey(type),
                type: type,
                selected: draft.types.contains(type),
                onTap: _busy ? null : () => _toggle(type),
              ),
            if (draft.consentDeclined) ...[
              const SizedBox(height: SnTokens.space2),
              Container(
                key: TypePickerScreen.consentNoteKey,
                padding: const EdgeInsets.all(SnTokens.space3),
                decoration: BoxDecoration(
                  color: c.muted,
                  borderRadius: BorderRadius.circular(SnTokens.radiusMd),
                  border: Border.all(color: c.border),
                ),
                child: Row(
                  children: [
                    Icon(Icons.shield_outlined, color: c.brand),
                    const SizedBox(width: SnTokens.space2),
                    Expanded(child: Text(l10n.userTypesConsentNeeded)),
                  ],
                ),
              ),
            ],
            const SizedBox(height: SnTokens.space3),
            Text(
              l10n.userTypesConsentNote,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
            const SizedBox(height: SnTokens.space4),
            PrimaryButton(
              buttonKey: TypePickerScreen.continueKey,
              label: l10n.userTypesContinue,
              // Disabled, not spinning: a consent sheet may be open.
              onPressed: _busy || (draft.types.isEmpty && !widget.edit)
                  ? null
                  : _continue,
            ),
            if (!widget.edit) ...[
              const SizedBox(height: SnTokens.space2),
              TextButton(
                key: TypePickerScreen.skipKey,
                onPressed: _busy ? null : _skip,
                child: Text(l10n.userTypesSkip),
              ),
            ],
            const SizedBox(height: SnTokens.space2),
            Text(
              l10n.userTypesChangeLater,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TypeTile extends StatelessWidget {
  const _TypeTile({
    super.key,
    required this.type,
    required this.selected,
    required this.onTap,
  });

  final String type;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: SnTokens.space2),
      child: Semantics(
        selected: selected,
        button: true,
        child: Material(
          color: selected ? c.brandSoft : c.surface,
          borderRadius: BorderRadius.circular(SnTokens.radiusLg),
          clipBehavior: Clip.antiAlias,
          child: InkWell(
            onTap: onTap,
            child: Container(
              padding: const EdgeInsets.all(SnTokens.space3),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(SnTokens.radiusLg),
                border: Border.all(
                  color: selected ? c.brand : c.border,
                  width: selected ? 2 : 1,
                ),
              ),
              child: Row(
                children: [
                  Icon(userTypeIcon(type), color: c.brandStrong),
                  const SizedBox(width: SnTokens.space3),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          userTypeTitle(l10n, type),
                          style: theme.textTheme.titleMedium,
                        ),
                        Text(
                          userTypeSubtitle(l10n, type),
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: c.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    selected
                        ? Icons.check_circle_rounded
                        : Icons.radio_button_unchecked_rounded,
                    color: selected ? c.brand : c.textSecondary,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
