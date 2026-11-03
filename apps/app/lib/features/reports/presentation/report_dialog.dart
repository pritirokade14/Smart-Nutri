import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/observability/analytics.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/states.dart';
import '../data/reports_repository.dart';

/// Opens "Report a problem" (F14) for one of our own products. Shows a thank
/// you snack bar once the report is sent.
Future<void> showReportDialog(
  BuildContext context, {
  required String productId,
}) async {
  final messenger = ScaffoldMessenger.maybeOf(context);
  final l10n = AppLocalizations.of(context);
  final sent = await showDialog<bool>(
    context: context,
    builder: (_) => ReportDialog(productId: productId),
  );
  if (sent ?? false) {
    messenger?.showSnackBar(SnackBar(content: Text(l10n.reportThanks)));
  }
}

String reportReasonLabel(AppLocalizations l10n, ReportCreateReason reason) =>
    switch (reason) {
      ReportCreateReason.wrongValues => l10n.reportReasonWrongValues,
      ReportCreateReason.wrongIngredients => l10n.reportReasonWrongIngredients,
      ReportCreateReason.wrongProduct => l10n.reportReasonWrongProduct,
      _ => l10n.reportReasonOther,
    };

/// A reason (required) and an optional note of up to 500 characters.
class ReportDialog extends ConsumerStatefulWidget {
  const ReportDialog({super.key, required this.productId});

  final String productId;

  static const noteKey = Key('report-note');
  static const submitKey = Key('report-submit');

  @override
  ConsumerState<ReportDialog> createState() => _ReportDialogState();
}

class _ReportDialogState extends ConsumerState<ReportDialog> {
  final _note = TextEditingController();
  ReportCreateReason? _reason;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _note.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final reason = _reason;
    if (reason == null) return;
    final l10n = AppLocalizations.of(context);
    final navigator = Navigator.of(context);
    final analytics = ref.read(analyticsProvider);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref
          .read(reportsRepositoryProvider)
          .submit(widget.productId, reason: reason, note: _note.text);
    } on ReportFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(l10n, e.code);
      });
      return;
    }
    try {
      // Only the reason enum, never the note.
      await analytics.track('report_submitted', {'reason': reason.json});
    } on Object {
      // Analytics never blocks the report.
    }
    navigator.pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AlertDialog(
      title: Text(l10n.reportTitle),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            RadioGroup<ReportCreateReason>(
              groupValue: _reason,
              onChanged: (r) {
                if (!_busy) setState(() => _reason = r);
              },
              child: Column(
                children: [
                  for (final reason in reportReasons)
                    RadioListTile<ReportCreateReason>(
                      value: reason,
                      contentPadding: EdgeInsets.zero,
                      title: Text(reportReasonLabel(l10n, reason)),
                    ),
                ],
              ),
            ),
            const SizedBox(height: SnTokens.space2),
            TextField(
              key: ReportDialog.noteKey,
              controller: _note,
              enabled: !_busy,
              maxLength: reportNoteMaxLength,
              minLines: 2,
              maxLines: 4,
              decoration: InputDecoration(labelText: l10n.reportNoteLabel),
            ),
            if (_error case final message?) ...[
              const SizedBox(height: SnTokens.space2),
              InlineErrorBanner(message: message),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.of(context).pop(false),
          child: Text(l10n.commonCancel),
        ),
        FilledButton(
          key: ReportDialog.submitKey,
          onPressed: _busy || _reason == null ? null : _submit,
          child: _busy
              ? const SizedBox.square(
                  dimension: SnTokens.space4,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(l10n.reportSubmit),
        ),
      ],
    );
  }
}
