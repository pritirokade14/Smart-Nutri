import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

/// Asks for the microphone at the moment of use.
abstract interface class MicPermission {
  /// True once granted; false when denied (or permanently denied).
  Future<bool> request();
}

/// RECORD_AUDIO through the `record` plugin, which shows the system prompt
/// when needed. (`permission_handler` 13 needs compileSdk 37; the app stays
/// on 36.)
class SystemMicPermission implements MicPermission {
  @override
  Future<bool> request() async {
    final recorder = AudioRecorder();
    try {
      return await recorder.hasPermission();
    } finally {
      await recorder.dispose();
    }
  }
}

/// Records one question to a file.
abstract interface class VoiceRecorder {
  Future<void> start(String path);

  /// The recorded file's path.
  Future<String?> stop();
  Future<void> cancel();
  Future<void> dispose();
}

/// AAC-LC in an m4a, 16 kHz mono (Plan 7 Task 8).
class RecordVoiceRecorder implements VoiceRecorder {
  final _recorder = AudioRecorder();

  @override
  Future<void> start(String path) => _recorder.start(
    const RecordConfig(
      encoder: AudioEncoder.aacLc,
      sampleRate: 16000,
      numChannels: 1,
    ),
    path: path,
  );

  @override
  Future<String?> stop() => _recorder.stop();

  @override
  Future<void> cancel() => _recorder.cancel();

  @override
  Future<void> dispose() => _recorder.dispose();
}

/// Plays the answer's signed mp3 URL.
abstract interface class VoicePlayer {
  Future<void> play(String url);
  Future<void> stop();
}

class JustAudioVoicePlayer implements VoicePlayer {
  final _player = AudioPlayer();

  @override
  Future<void> play(String url) async {
    await _player.setUrl(url);
    // play() completes only when playback ends; don't wait for it.
    unawaited(_player.play());
  }

  @override
  Future<void> stop() => _player.stop();

  Future<void> dispose() => _player.dispose();
}

final micPermissionProvider = Provider<MicPermission>(
  (ref) => SystemMicPermission(),
);

final voiceRecorderProvider = Provider.autoDispose<VoiceRecorder>((ref) {
  final recorder = RecordVoiceRecorder();
  ref.onDispose(recorder.dispose);
  return recorder;
});

final voicePlayerProvider = Provider.autoDispose<VoicePlayer>((ref) {
  final player = JustAudioVoicePlayer();
  ref.onDispose(player.dispose);
  return player;
});

/// A new file path in the app's cache for one recording. The file is
/// deleted as soon as the question is sent or cancelled.
final recordingPathProvider = Provider<Future<String> Function()>(
  (ref) => () async {
    final dir = await getTemporaryDirectory();
    return '${dir.path}/voice_${DateTime.now().microsecondsSinceEpoch}.m4a';
  },
);
