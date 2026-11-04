import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/voice/data/voice_device.dart';

/// The answer mp3 arrives inline (base64) and is never stored (ADR 0020). The
/// player stages it in a private cache file only while it is playing.
void main() {
  late Directory dir;
  late StagedMp3 staged;

  setUp(() {
    dir = Directory.systemTemp.createTempSync('staged_mp3_test');
    staged = StagedMp3(() async => dir);
  });

  tearDown(() => dir.deleteSync(recursive: true));

  List<FileSystemEntity> files() => dir.listSync();

  test('write stages the bytes in one file', () async {
    final bytes = Uint8List.fromList([1, 2, 3]);
    final path = await staged.write(bytes);
    expect(File(path).readAsBytesSync(), bytes);
    expect(files(), hasLength(1));
  });

  test('a new answer replaces the previous file', () async {
    final first = await staged.write(Uint8List.fromList([1]));
    final second = await staged.write(Uint8List.fromList([2]));
    expect(File(first).existsSync(), isFalse);
    expect(File(second).readAsBytesSync(), [2]);
    expect(files(), hasLength(1));
  });

  test('delete removes the staged file and is safe to repeat', () async {
    await staged.write(Uint8List.fromList([1, 2]));
    staged.delete();
    staged.delete();
    expect(files(), isEmpty);
  });
}
