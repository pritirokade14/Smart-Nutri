import 'dart:async';
import 'dart:io';

import 'package:smartnutri_ai/features/voice/data/voice_device.dart';
import 'package:smartnutri_ai/features/voice/data/voice_repository.dart';
import 'package:smartnutri_api/src/export.dart';

class FakeMic implements MicPermission {
  FakeMic({this.granted = true});
  bool granted;
  int requests = 0;

  @override
  Future<bool> request() async {
    requests++;
    return granted;
  }
}

/// Creates the file on start (so deletion can be checked); stop returns it.
class FakeRecorder implements VoiceRecorder {
  final started = <String>[];
  int stops = 0;
  int cancels = 0;
  String? _path;

  @override
  Future<void> start(String path) async {
    started.add(path);
    File(path).writeAsBytesSync([1, 2, 3]);
    _path = path;
  }

  @override
  Future<String?> stop() async {
    stops++;
    return _path;
  }

  @override
  Future<void> cancel() async => cancels++;

  @override
  Future<void> dispose() async {}
}

class FakePlayer implements VoicePlayer {
  final played = <String>[];
  int stops = 0;

  @override
  Future<void> play(String url) async => played.add(url);

  @override
  Future<void> stop() async => stops++;
}

class FakeVoiceRepository implements VoiceRepository {
  FakeVoiceRepository(this.result);
  FutureOr<VoiceAnswer> Function() result;
  final asks = <Map<String, Object?>>[];

  @override
  Future<VoiceAnswer> ask({
    required File audio,
    required String memberId,
    required String language,
    String? productId,
    String? barcode,
  }) async {
    asks.add({
      'exists': audio.existsSync(),
      'member_id': memberId,
      'language': language,
      'product_id': productId,
      'barcode': barcode,
    });
    return result();
  }
}

var _n = 0;

/// A fresh temp path per recording.
Future<String> tempRecordingPath() async =>
    '${Directory.systemTemp.path}/voice_test_${pid}_${_n++}.m4a';
