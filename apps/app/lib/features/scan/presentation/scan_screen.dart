import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';
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

  @override
  void initState() {
    super.initState();
    _source = ref.read(barcodeSourceFactoryProvider)();
    _sub = _source.codes.listen(_onRaw);
    _source.start().then((s) {
      if (mounted) setState(() => _status = s);
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
    final Widget camera = switch (_status) {
      null => const Center(child: CircularProgressIndicator()),
      BarcodeSourceStatus.ready => Stack(
        fit: StackFit.expand,
        children: [
          _source.buildPreview(context),
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              width: double.infinity,
              color: theme.colorScheme.surface.withValues(alpha: 0.8),
              padding: const EdgeInsets.all(SnTokens.space2),
              child: Text(l10n.scanScanning, textAlign: TextAlign.center),
            ),
          ),
        ],
      ),
      BarcodeSourceStatus.permissionDenied => Center(
        child: Text(l10n.scanCameraDenied, textAlign: TextAlign.center),
      ),
      BarcodeSourceStatus.unavailable => Center(
        child: Text(l10n.scanCameraUnavailable, textAlign: TextAlign.center),
      ),
    };
    return Scaffold(
      appBar: AppBar(title: Text(l10n.scanTitle)),
      body: Column(
        children: [
          Expanded(child: camera),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(SnTokens.space4),
              child: ManualBarcodeField(onSubmit: _go),
            ),
          ),
        ],
      ),
    );
  }
}
