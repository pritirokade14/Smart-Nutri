import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

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

/// Plays the answer's mp3, which arrives inline in the API response and is
/// never stored (ADR 0020).
abstract interface class VoicePlayer {
  /// Plays [mp3] from the start.
  Future<void> playMp3(Uint8List mp3);

  /// Stops playback and deletes any staged audio.
  Future<void> stop();
}

/// Holds at most one answer mp3 in a private file in the app's cache, only
/// while it plays. ExoPlayer needs a file or URL source, and an in-memory
/// `StreamAudioSource` would need a cleartext localhost proxy, which the app
/// does not allow. A new answer replaces the file; [delete] removes it.
class StagedMp3 {
  StagedMp3(this._dir);

  final Future<Directory> Function() _dir;
  File? _file;

  Future<String> write(Uint8List mp3) async {
    delete();
    final dir = await _dir();
    final file = File(
      '${dir.path}/voice_answer_${DateTime.now().microsecondsSinceEpoch}.mp3',
    );
    _file = file;
    await file.writeAsBytes(mp3, flush: true);
    return file.path;
  }

  void delete() {
    final file = _file;
    _file = null;
    if (file == null) return;
    try {
      if (file.existsSync()) file.deleteSync();
    } on Object {
      // The OS clears the cache directory eventually.
    }
  }
}

class JustAudioVoicePlayer implements VoicePlayer {
  final _player = AudioPlayer();
  final _staged = StagedMp3(getTemporaryDirectory);

  @override
  Future<void> playMp3(Uint8List mp3) async {
    await _player.stop();
    final path = await _staged.write(mp3);
    await _player.setFilePath(path);
    // play() completes only when playback ends; don't wait for it.
    unawaited(_player.play());
  }

  @override
  Future<void> stop() async {
    try {
      await _player.stop();
    } finally {
      _staged.delete();
    }
  }

  Future<void> dispose() async {
    _staged.delete();
    await _player.dispose();
  }
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
