import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/tokens.g.dart';
import '../data/label_repository.dart';
import '../domain/barcode.dart';
import 'confirm_screen.dart';
import 'label_providers.dart';

/// Photograph (or choose) a label photo; the extracted draft opens the
/// confirm screen. Every error offers Retake and Enter manually.
class LabelCaptureScreen extends ConsumerStatefulWidget {
  const LabelCaptureScreen({super.key, this.barcode});

  /// The unknown barcode that led here (F15), carried to the scan and save.
  final String? barcode;

  @override
  ConsumerState<LabelCaptureScreen> createState() => _LabelCaptureScreenState();
}

class _LabelCaptureScreenState extends ConsumerState<LabelCaptureScreen> {
  String? get _code {
    final code = widget.barcode;
    return code == null ? null : normalizeBarcode(code);
  }

  @override
  void initState() {
    super.initState();
    // A photo Android kept after killing the app mid-capture continues the
    // flow (ImagePicker.retrieveLostData).
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      ref
          .read(labelScanControllerProvider.notifier)
          .recoverLost(barcode: _code);
    });
  }

  void _enterManually(BuildContext context) => context.pushReplacement(
    '/scan/confirm',
    extra: ConfirmArgs(barcode: _code),
  );

  static String _failureText(AppLocalizations l10n, String code) =>
      code == cameraPermissionDenied
      ? l10n.labelCameraPermissionDenied
      : localizedErrorCode(l10n, code);

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    ref.listen(labelScanControllerProvider, (_, next) {
      if (next is LabelScanDrafted) {
        context.pushReplacement(
          '/scan/confirm',
          extra: ConfirmArgs(scan: next.out, barcode: _code),
        );
      }
    });
    final state = ref.watch(labelScanControllerProvider);
    final controller = ref.read(labelScanControllerProvider.notifier);

    final Widget body = switch (state) {
      LabelScanBusy(:final phase) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: SnTokens.space3),
          Text(
            phase == LabelPhase.uploading
                ? l10n.labelUploading
                : l10n.labelReading,
            textAlign: TextAlign.center,
          ),
        ],
      ),
      LabelScanFailed(:final failure) => Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            _failureText(l10n, failure.code),
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyLarge,
          ),
          const SizedBox(height: SnTokens.space4),
          FilledButton(
            onPressed: controller.reset,
            child: Text(l10n.labelRetake),
          ),
          const SizedBox(height: SnTokens.space2),
          OutlinedButton(
            onPressed: () => _enterManually(context),
            child: Text(l10n.labelEnterManually),
          ),
        ],
      ),
      // Drafted navigates away (listener above); idle offers the choices.
      LabelScanIdle() || LabelScanDrafted() => Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // F15: an unknown barcode led here.
          if (_code != null) ...[
            Text(
              l10n.notfoundGoToLabel,
              textAlign: TextAlign.center,
              style: theme.textTheme.titleMedium,
            ),
            const SizedBox(height: SnTokens.space4),
          ],
          Icon(
            Icons.document_scanner_outlined,
            size: 64,
            color: theme.colorScheme.onSurfaceVariant,
          ),
          const SizedBox(height: SnTokens.space4),
          FilledButton.icon(
            onPressed: () =>
                controller.capture(ImageSource.camera, barcode: _code),
            icon: const Icon(Icons.photo_camera_outlined),
            label: Text(l10n.labelTakePhoto),
          ),
          const SizedBox(height: SnTokens.space2),
          OutlinedButton.icon(
            onPressed: () =>
                controller.capture(ImageSource.gallery, barcode: _code),
            icon: const Icon(Icons.photo_library_outlined),
            label: Text(l10n.labelChooseFile),
          ),
          const SizedBox(height: SnTokens.space2),
          TextButton(
            onPressed: () => _enterManually(context),
            child: Text(l10n.labelEnterManually),
          ),
        ],
      ),
    };

    return Scaffold(
      appBar: AppBar(title: Text(l10n.labelTitle)),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(SnTokens.space5),
          child: body,
        ),
      ),
    );
  }
}
