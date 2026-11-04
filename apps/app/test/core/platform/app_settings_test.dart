import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/platform/app_settings.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel(AppSettings.channelName);
  final calls = <MethodCall>[];

  void mock({required bool rationale}) {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          calls.add(call);
          return call.method == 'shouldShowRationale' ? rationale : null;
        });
  }

  setUp(calls.clear);
  tearDown(
    () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null),
  );

  test('one denial with a rationale to show is not permanent', () async {
    mock(rationale: true);
    expect(await AppSettings().noteDenied(cameraPermission), isFalse);
  });

  test('one denial and no rationale (don\'t ask again) is permanent', () async {
    mock(rationale: false);
    expect(await AppSettings().noteDenied(cameraPermission), isTrue);
    expect(calls.single.arguments, {'permission': cameraPermission});
  });

  test('denied twice is permanent even if a rationale shows', () async {
    mock(rationale: true);
    final s = AppSettings();
    expect(await s.noteDenied(microphonePermission), isFalse);
    expect(await s.noteDenied(microphonePermission), isTrue);
    // Another permission is counted separately.
    expect(await s.noteDenied(cameraPermission), isFalse);
  });

  test('open calls openAppSettings on the channel', () async {
    mock(rationale: true);
    await AppSettings().open();
    expect(calls.single.method, 'openAppSettings');
  });

  test(
    'without a platform side it can still ask and open is a no-op',
    () async {
      final s = AppSettings();
      expect(await s.noteDenied(cameraPermission), isFalse);
      await s.open();
    },
  );
}
