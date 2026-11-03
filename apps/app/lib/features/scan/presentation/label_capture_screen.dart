import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
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
      ref.read(labelScanControllerProvider.notifier).recoverLost();
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
          extra: ConfirmArgs(
            scan: next.out,
            // A recovered photo may be of another product (R24).
            barcode: next.recovered ? null : _code,
          ),
        );
      }
    });
    final state = ref.watch(labelScanControllerProvider);
    final controller = ref.read(labelScanControllerProvider.notifier);

    final c = SnColors.of(context);
    final Widget body = switch (state) {
      LabelScanBusy(:final phase) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _LabelHero(
            icon: phase == LabelPhase.uploading
                ? Icons.cloud_upload_outlined
                : Icons.document_scanner_outlined,
          ),
          const SizedBox(height: SnTokens.space5),
          const SizedBox(
            width: SnTokens.space8 * 3,
            child: LinearProgressIndicator(),
          ),
          const SizedBox(height: SnTokens.space3),
          Text(
            phase == LabelPhase.uploading
                ? l10n.labelUploading
                : l10n.labelReading,
            textAlign: TextAlign.center,
            style: theme.textTheme.titleMedium,
          ),
        ],
      ),
      LabelScanFailed(:final failure) => ErrorState(
        message: _failureText(l10n, failure.code),
        icon: failure.code == cameraPermissionDenied
            ? Icons.no_photography_outlined
            : Icons.error_outline_rounded,
        actions: [
          PrimaryButton(
            label: l10n.labelRetake,
            icon: Icons.photo_camera_outlined,
            onPressed: controller.reset,
          ),
          SecondaryButton(
            label: l10n.labelEnterManually,
            icon: Icons.edit_note_rounded,
            onPressed: () => _enterManually(context),
          ),
        ],
      ),
      // Drafted navigates away (listener above); idle offers the choices.
      LabelScanIdle() || LabelScanDrafted() => Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const _LabelHero(icon: Icons.document_scanner_outlined),
          const SizedBox(height: SnTokens.space5),
          // F15: an unknown barcode led here.
          if (_code != null) ...[
            Text(
              l10n.notfoundGoToLabel,
              textAlign: TextAlign.center,
              style: theme.textTheme.titleMedium,
            ),
          ] else
            Text(
              l10n.homeLabelBody,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: c.textSecondary,
              ),
            ),
          const SizedBox(height: SnTokens.space5),
          PrimaryButton(
            label: l10n.labelTakePhoto,
            icon: Icons.photo_camera_outlined,
            onPressed: () =>
                controller.capture(ImageSource.camera, barcode: _code),
          ),
          const SizedBox(height: SnTokens.space3),
          SecondaryButton(
            label: l10n.labelChooseFile,
            icon: Icons.photo_library_outlined,
            onPressed: () =>
                controller.capture(ImageSource.gallery, barcode: _code),
          ),
          const SizedBox(height: SnTokens.space2),
          TextButton.icon(
            onPressed: () => _enterManually(context),
            icon: const Icon(Icons.edit_note_rounded),
            label: Text(l10n.labelEnterManually),
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

/// A soft brand circle with a large icon, for the capture states.
class _LabelHero extends StatelessWidget {
  const _LabelHero({required this.icon});

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    return Center(
      child: Container(
        width: SnTokens.space8 * 2,
        height: SnTokens.space8 * 2,
        decoration: BoxDecoration(color: c.brandSoft, shape: BoxShape.circle),
        child: Icon(icon, size: SnTokens.space8, color: c.brand),
      ),
    );
  }
}
