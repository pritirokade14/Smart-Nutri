import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/observability/analytics.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/states.dart';
import '../../auth/data/auth_repository.dart';
import '../../meals/presentation/meals_providers.dart';
import '../data/account_repository.dart';

Future<void> showDeleteAccountDialog(BuildContext context) => showDialog<void>(
  context: context,
  barrierDismissible: false,
  builder: (_) => const DeleteAccountDialog(),
);

/// Deletes the account (F11) after the user types the confirmation word
/// (`settings.delete_confirm_word`). On success it signs out at once, which
/// drops every account-scoped provider, and shows the goodbye screen. A
/// failure (503 `deletion_incomplete` included) keeps the dialog open with a
/// retry; `DELETE /v1/me` is idempotent.
class DeleteAccountDialog extends ConsumerStatefulWidget {
  const DeleteAccountDialog({super.key});

  static const inputKey = Key('delete-account-input');
  static const confirmKey = Key('delete-account-confirm');

  @override
  ConsumerState<DeleteAccountDialog> createState() =>
      _DeleteAccountDialogState();
}

class _DeleteAccountDialogState extends ConsumerState<DeleteAccountDialog> {
  final _input = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  bool _typed(AppLocalizations l10n) =>
      _input.text.trim().toUpperCase() ==
      l10n.settingsDeleteConfirmWord.toUpperCase();

  Future<void> _delete() async {
    final l10n = AppLocalizations.of(context);
    final router = GoRouter.of(context);
    final navigator = Navigator.of(context);
    final analytics = ref.read(analyticsProvider);
    final auth = ref.read(authRepositoryProvider);
    final queue = ref.read(mealQueueProvider);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(accountRepositoryProvider).deleteAccount();
    } on AccountFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(l10n, e.code);
      });
      return;
    }
    try {
      await analytics.track('account_deleted');
    } on Object {
      // Analytics never blocks the sign-out.
    }
    navigator.pop();
    try {
      await signOutClearingQueue(auth, queue);
    } on Object {
      // The auth user is already deleted server-side; the local session is
      // cleared before the sign-out call can fail.
    }
    router.go('/goodbye');
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final error = theme.colorScheme.error;
    return PopScope(
      canPop: !_busy,
      child: AlertDialog(
        title: Text(l10n.settingsDeleteDialogTitle),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(l10n.settingsDeleteBody),
              const SizedBox(height: SnTokens.space4),
              TextField(
                key: DeleteAccountDialog.inputKey,
                controller: _input,
                enabled: !_busy,
                autocorrect: false,
                enableSuggestions: false,
                textCapitalization: TextCapitalization.characters,
                decoration: InputDecoration(
                  labelText: l10n.settingsDeleteConfirmLabel(
                    l10n.settingsDeleteConfirmWord,
                  ),
                ),
                onChanged: (_) => setState(() {}),
              ),
              if (_error case final message?) ...[
                const SizedBox(height: SnTokens.space3),
                InlineErrorBanner(message: message),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: _busy ? null : () => Navigator.of(context).pop(),
            child: Text(l10n.commonCancel),
          ),
          FilledButton(
            key: DeleteAccountDialog.confirmKey,
            style: FilledButton.styleFrom(
              backgroundColor: error,
              foregroundColor: theme.colorScheme.onError,
            ),
            onPressed: !_busy && _typed(l10n) ? _delete : null,
            child: _busy
                ? SizedBox.square(
                    dimension: SnTokens.space4,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: theme.colorScheme.onError,
                    ),
                  )
                : Text(
                    _error == null
                        ? l10n.settingsDeleteConfirm
                        : l10n.commonRetry,
                  ),
          ),
        ],
      ),
    );
  }
}
