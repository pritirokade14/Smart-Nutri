import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/platform/app_settings.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../shared/widgets/open_settings_button.dart';
import '../../../core/theme/tokens.g.dart';
import '../data/barcode_source.dart';
import '../domain/barcode.dart';
import 'manual_barcode_field.dart';

class ScanScreen extends ConsumerStatefulWidget {
  const ScanScreen({super.key});

  @override
  ConsumerState<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends ConsumerState<ScanScreen> {
  late final BarcodeSource _source;
  StreamSubscription<String>? _sub;
  BarcodeSourceStatus? _status;
  bool _handled = false;
  bool _permanentlyDenied = false;

  @override
  void initState() {
    super.initState();
    _source = ref.read(barcodeSourceFactoryProvider)();
    _sub = _source.codes.listen(_onRaw);
    _source.start().then((s) async {
      if (!mounted) return;
      setState(() => _status = s);
      if (s == BarcodeSourceStatus.permissionDenied) {
        final permanent = await ref
            .read(appSettingsProvider)
            .noteDenied(cameraPermission);
        if (mounted) setState(() => _permanentlyDenied = permanent);
      }
    });
  }

  void _onRaw(String raw) {
    final code = normalizeBarcode(raw);
    if (code == null) return;
    _go(code);
  }

  void _go(String code) {
    if (_handled) return;
    _handled = true;
    _sub?.cancel();
    context.pushReplacement('/result?barcode=$code');
  }

  @override
  void dispose() {
    _sub?.cancel();
    _source.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final Widget camera = switch (_status) {
      // Starting: the preview must be in the tree so the scanner controller
      // can attach and start() can request the camera permission.
      null => Stack(
        fit: StackFit.expand,
        children: [
          _source.buildPreview(context),
          const Center(child: CircularProgressIndicator()),
        ],
      ),
      BarcodeSourceStatus.ready => Stack(
        fit: StackFit.expand,
        children: [
          _source.buildPreview(context),
          const IgnorePointer(child: _ScanFrame()),
          Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.all(SnTokens.space4),
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: SnTokens.space4,
                  vertical: SnTokens.space2,
                ),
                decoration: BoxDecoration(
                  color: c.surface.withValues(alpha: 0.92),
                  borderRadius: BorderRadius.circular(SnTokens.radiusFull),
                ),
                child: Text(
                  l10n.scanScanning,
                  textAlign: TextAlign.center,
                  style: theme.textTheme.labelLarge,
                ),
              ),
            ),
          ),
        ],
      ),
      BarcodeSourceStatus.permissionDenied => _CameraMessage(
        icon: Icons.no_photography_outlined,
        text: l10n.scanCameraDenied,
        action: _permanentlyDenied ? const OpenSettingsButton() : null,
      ),
      BarcodeSourceStatus.unavailable => _CameraMessage(
        icon: Icons.videocam_off_outlined,
        text: l10n.scanCameraUnavailable,
      ),
    };
    return Scaffold(
      appBar: AppBar(title: Text(l10n.scanTitle)),
      body: Column(
        children: [
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(
                SnTokens.space4,
                SnTokens.space2,
                SnTokens.space4,
                SnTokens.space4,
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(SnTokens.radiusXl),
                child: ColoredBox(color: c.muted, child: camera),
              ),
            ),
          ),
          Container(
            decoration: BoxDecoration(
              color: c.surface,
              borderRadius: const BorderRadius.vertical(
                top: Radius.circular(SnTokens.radiusXl),
              ),
              border: Border(top: BorderSide(color: c.border)),
            ),
            child: SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.all(SnTokens.space4),
                child: ManualBarcodeField(onSubmit: _go),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// A clear window with white corners over a soft scrim, so the user knows
/// where to hold the barcode. Drawn over the camera, so the same in both
/// themes.
class _ScanFrame extends StatelessWidget {
  const _ScanFrame();

  @override
  Widget build(BuildContext context) => CustomPaint(
    painter: _ScanFramePainter(
      scrim: SnTokens.textPrimary.withValues(alpha: 0.4),
      corner: SnTokens.textInverse,
    ),
  );
}

class _ScanFramePainter extends CustomPainter {
  _ScanFramePainter({required this.scrim, required this.corner});

  final Color scrim;
  final Color corner;

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width * 0.78;
    final h = w * 0.5;
    final window = RRect.fromRectAndRadius(
      Rect.fromCenter(center: size.center(Offset.zero), width: w, height: h),
      const Radius.circular(SnTokens.radiusLg),
    );
    canvas.drawPath(
      Path.combine(
        PathOperation.difference,
        Path()..addRect(Offset.zero & size),
        Path()..addRRect(window),
      ),
      Paint()..color = scrim,
    );
    final pen = Paint()
      ..color = corner
      ..style = PaintingStyle.stroke
      ..strokeWidth = SnTokens.space1
      ..strokeCap = StrokeCap.round;
    const arm = SnTokens.space5;
    final r = window.outerRect;
    for (final (o, dx, dy) in [
      (r.topLeft, 1.0, 1.0),
      (r.topRight, -1.0, 1.0),
      (r.bottomLeft, 1.0, -1.0),
      (r.bottomRight, -1.0, -1.0),
    ]) {
      canvas
        ..drawLine(o, o + Offset(arm * dx, 0), pen)
        ..drawLine(o, o + Offset(0, arm * dy), pen);
    }
  }

  @override
  bool shouldRepaint(_ScanFramePainter old) =>
      old.scrim != scrim || old.corner != corner;
}

class _CameraMessage extends StatelessWidget {
  const _CameraMessage({required this.icon, required this.text, this.action});

  final IconData icon;
  final String text;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(SnTokens.space5),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: SnTokens.space7, color: c.textSecondary),
            const SizedBox(height: SnTokens.space3),
            Text(
              text,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            if (action != null) ...[
              const SizedBox(height: SnTokens.space3),
              action!,
            ],
          ],
        ),
      ),
    );
  }
}
