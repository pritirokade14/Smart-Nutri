import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/observability/analytics.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/states.dart';
import '../data/label_repository.dart';
import 'draft_form.dart';

/// What the confirm screen edits: a label scan's draft, or nothing (manual
/// entry, an empty form with no scan_id).
class ConfirmArgs {
  const ConfirmArgs({this.scan, this.barcode});

  final ScanDraftOut? scan;
  final String? barcode;
}

/// The editable confirm screen. Saving calls `products_create`, then the
/// result view analyses the saved product (`/result?product_id=`). No verdict
/// colour is shown here.
class ConfirmScreen extends ConsumerStatefulWidget {
  const ConfirmScreen({super.key, this.args});

  final ConfirmArgs? args;

  @override
  ConsumerState<ConfirmScreen> createState() => _ConfirmScreenState();
}

class _ConfirmScreenState extends ConsumerState<ConfirmScreen> {
  bool _saving = false;
  LabelFailure? _failure;

  ScanDraftOut? get _scan => widget.args?.scan;
  String? get _barcode => widget.args?.barcode;

  void _retake() {
    final code = _barcode;
    context.pushReplacement(
      code == null ? '/scan/label' : '/scan/label?barcode=$code',
    );
  }

  /// Always an EMPTY form: a scan draft is never re-posted as manual entry.
  void _enterManually() => context.pushReplacement(
    '/scan/confirm',
    extra: ConfirmArgs(barcode: _barcode),
  );

  void _openProduct(String id) => context.pushReplacement(
    '/result?product_id=${Uri.encodeQueryComponent(id)}',
  );

  Future<void> _save(ProductCreate body) async {
    setState(() {
      _saving = true;
      _failure = null;
    });
    final analytics = ref.read(analyticsProvider);
    try {
      final out = await ref.read(labelRepositoryProvider).saveDraft(body);
      if (!mounted) return;
      final id = out.productId;
      if (id == null) {
        setState(() {
          _saving = false;
          _failure = const LabelFailure('internal_error');
        });
        return;
      }
      unawaited(
        analytics.track(
          body.scanId == null ? 'manual_product_saved' : 'label_scan_saved',
        ),
      );
      _openProduct(id);
    } on LabelFailure catch (f) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _failure = f;
      });
    } on Object {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _failure = const LabelFailure('internal_error');
      });
    }
  }

  Map<String, String> _fieldErrors(AppLocalizations l10n) {
    final f = _failure;
    if (f == null) return const {};
    final message = switch (f.code) {
      'implausible_value' => l10n.errorImplausibleValue,
      'validation_error' => l10n.errorValidationError,
      _ => null,
    };
    if (message == null) return const {};
    return {for (final field in f.fields) field: message};
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final failure = _failure;
    final scan = _scan;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.confirmTitle)),
      body: DraftForm(
        key: ValueKey(scan?.scanId ?? 'manual'),
        draft: scan?.draft,
        scanId: scan?.scanId,
        barcode: _barcode,
        saving: _saving,
        fieldErrors: _fieldErrors(l10n),
        onSave: _save,
        header: [
          Container(
            padding: const EdgeInsets.all(SnTokens.space3),
            decoration: BoxDecoration(
              color: c.brandSoft,
              borderRadius: BorderRadius.circular(SnTokens.radiusLg),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.fact_check_outlined, color: c.brandStrong),
                const SizedBox(width: SnTokens.space3),
                Expanded(
                  child: Text(
                    l10n.confirmSubtitle,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: c.brandStrong,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: SnTokens.space2),
          Wrap(
            spacing: SnTokens.space2,
            runSpacing: SnTokens.space1,
            children: [
              OutlinedButton.icon(
                onPressed: _retake,
                icon: const Icon(Icons.photo_camera_outlined),
                label: Text(l10n.labelRetake),
              ),
              TextButton.icon(
                onPressed: _enterManually,
                icon: const Icon(Icons.edit_note_rounded),
                label: Text(l10n.labelEnterManually),
              ),
            ],
          ),
          const SizedBox(height: SnTokens.space2),
          if (failure != null)
            Padding(
              padding: const EdgeInsets.only(bottom: SnTokens.space2),
              child: InlineErrorBanner(
                message: localizedErrorCode(l10n, failure.code),
                action: failure.code == 'product_exists'
                    ? switch (failure.productId) {
                        final id? => TextButton(
                          onPressed: () => _openProduct(id),
                          child: Text(l10n.confirmOpenExisting),
                        ),
                        null => null,
                      }
                    : null,
              ),
            ),
        ],
        footer: [
          const SizedBox(height: SnTokens.space2),
          DisclaimerFooter(text: l10n.confirmNotMedicalAdvice),
        ],
      ),
    );
  }
}
