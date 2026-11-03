import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/observability/analytics.dart';
import '../data/label_repository.dart';

/// Picks one label photo from the camera or the gallery (null if cancelled).
typedef LabelPhotoPicker = Future<XFile?> Function(ImageSource source);

final labelPhotoPickerProvider = Provider<LabelPhotoPicker>((ref) {
  final picker = ImagePicker();
  // The picker downsizes on the device; compressForUpload is the hard limit.
  return (source) => picker.pickImage(
    source: source,
    maxWidth: maxUploadSide.toDouble(),
    maxHeight: maxUploadSide.toDouble(),
    imageQuality: 85,
  );
});

/// The label capture flow: idle → uploading → reading → drafted | failed.
sealed class LabelScanState {
  const LabelScanState();
}

class LabelScanIdle extends LabelScanState {
  const LabelScanIdle();
}

class LabelScanBusy extends LabelScanState {
  const LabelScanBusy(this.phase);
  final LabelPhase phase;
}

class LabelScanFailed extends LabelScanState {
  const LabelScanFailed(this.failure);
  final LabelFailure failure;
}

class LabelScanDrafted extends LabelScanState {
  const LabelScanDrafted(this.out);
  final ScanDraftOut out;
}

class LabelScanController extends Notifier<LabelScanState> {
  @override
  LabelScanState build() => const LabelScanIdle();

  /// Picks a photo and extracts a draft. Analytics events carry no values.
  Future<void> capture(ImageSource source, {String? barcode}) async {
    if (state is LabelScanBusy) return;
    final XFile? photo;
    try {
      photo = await ref.read(labelPhotoPickerProvider)(source);
    } on Object {
      state = const LabelScanFailed(LabelFailure('unsupported_image'));
      return;
    }
    if (photo == null) return; // cancelled
    final analytics = ref.read(analyticsProvider);
    unawaited(analytics.track('label_scan_started'));
    state = const LabelScanBusy(LabelPhase.uploading);
    try {
      final out = await ref
          .read(labelRepositoryProvider)
          .scanLabel(
            photo,
            barcode: barcode,
            onPhase: (p) {
              if (ref.mounted) state = LabelScanBusy(p);
            },
          );
      if (!ref.mounted) return;
      state = LabelScanDrafted(out);
    } on LabelFailure catch (f) {
      if (!ref.mounted) return;
      unawaited(analytics.track('label_scan_failed'));
      state = LabelScanFailed(f);
    } on Object {
      if (!ref.mounted) return;
      unawaited(analytics.track('label_scan_failed'));
      state = const LabelScanFailed(LabelFailure('internal_error'));
    }
  }

  /// Retake: back to the photo choice.
  void reset() => state = const LabelScanIdle();
}

final labelScanControllerProvider =
    NotifierProvider.autoDispose<LabelScanController, LabelScanState>(
      LabelScanController.new,
    );
