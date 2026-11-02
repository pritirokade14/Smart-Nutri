import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

enum BarcodeSourceStatus { ready, permissionDenied, unavailable }

/// Abstraction over the camera scanner so widgets can be tested without one.
abstract class BarcodeSource {
  /// Raw decoded values.
  Stream<String> get codes;
  Future<BarcodeSourceStatus> start();
  Widget buildPreview(BuildContext context);
  Future<void> dispose();
}

class MobileBarcodeSource implements BarcodeSource {
  MobileBarcodeSource()
    : _controller = MobileScannerController(
        autoStart: false,
        formats: const [
          BarcodeFormat.ean13,
          BarcodeFormat.ean8,
          BarcodeFormat.upcA,
          BarcodeFormat.upcE,
        ],
      );

  final MobileScannerController _controller;

  @override
  Stream<String> get codes => _controller.barcodes
      .expand((c) => c.barcodes)
      .map((b) => b.rawValue)
      .where((v) => v != null)
      .cast<String>();

  @override
  Future<BarcodeSourceStatus> start() async {
    try {
      await _controller.start();
      return BarcodeSourceStatus.ready;
    } on MobileScannerException catch (e) {
      return e.errorCode == MobileScannerErrorCode.permissionDenied
          ? BarcodeSourceStatus.permissionDenied
          : BarcodeSourceStatus.unavailable;
    } catch (_) {
      return BarcodeSourceStatus.unavailable;
    }
  }

  @override
  Widget buildPreview(BuildContext context) =>
      MobileScanner(controller: _controller);

  @override
  Future<void> dispose() => _controller.dispose();
}

/// Creates a fresh source per scan screen; overridden in tests.
final barcodeSourceFactoryProvider = Provider<BarcodeSource Function()>(
  (ref) =>
      () => MobileBarcodeSource(),
);
