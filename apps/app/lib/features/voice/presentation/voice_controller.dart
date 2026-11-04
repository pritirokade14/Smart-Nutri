import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/observability/analytics.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../data/voice_device.dart';
import '../data/voice_repository.dart';
import '../domain/voice_state.dart';

/// Push-to-talk for one member (F10): ask for the mic, record up to 30 s,
/// send, then show and play the API's answer. The recording is deleted as
/// soon as it is sent or cancelled; the transcript is never stored. The
/// answer mp3 comes inline (base64) and is never stored either (ADR 0020):
/// it is played from memory, staged only while playing, and dropped when the
/// answer is closed. With no audio (`audio_base64` null) only the text shows.
class VoiceController extends Notifier<VoiceState> {
  VoiceController(this.memberId);

  final String memberId;

  Timer? _ticker;
  VoiceTarget? _target;
  String? _path;
  bool _starting = false;
  bool _releasedWhileStarting = false;
  bool _sending = false;

  VoiceRecorder get _recorder => ref.read(voiceRecorderProvider);
  VoicePlayer get _player => ref.read(voicePlayerProvider);

  @override
  VoiceState build() {
    // Keep the device handles alive as long as this controller.
    ref.watch(voiceRecorderProvider);
    ref.watch(voicePlayerProvider);
    ref.onDispose(() {
      _ticker?.cancel();
      _deleteRecording();
    });
    return const VoiceIdle();
  }

  /// Press: asks for the microphone, then starts recording.
  Future<void> start(VoiceTarget target) async {
    if (_starting || _sending || state is VoiceRecording) return;
    _starting = true;
    _releasedWhileStarting = false;
    _target = target;
    try {
      await _player.stop();
      final granted = await ref.read(micPermissionProvider).request();
      if (!ref.mounted) return;
      if (!granted) {
        state = const VoiceError('voice.mic_denied');
        return;
      }
      final path = await ref.read(recordingPathProvider)();
      await _recorder.start(path);
      _path = path;
      if (!ref.mounted) return;
      if (_releasedWhileStarting) {
        // Let go before recording began: too short to be a question.
        await _discard();
        return;
      }
      state = const VoiceRecording(Duration.zero);
      _ticker = Timer.periodic(const Duration(seconds: 1), (timer) {
        final elapsed = Duration(seconds: timer.tick);
        if (elapsed >= voiceMaxDuration) {
          unawaited(stopAndSend());
        } else {
          state = VoiceRecording(elapsed);
        }
      });
    } on Object {
      if (ref.mounted) state = const VoiceError('error');
      _deleteRecording();
    } finally {
      _starting = false;
    }
  }

  /// Release: stops recording and asks the API.
  Future<void> stopAndSend() async {
    if (_starting) {
      _releasedWhileStarting = true;
      return;
    }
    final target = _target;
    if (state is! VoiceRecording || _sending || target == null) return;
    _sending = true;
    _ticker?.cancel();
    try {
      final path = await _recorder.stop() ?? _path;
      if (!ref.mounted) return;
      if (path == null) {
        state = const VoiceError('error');
        return;
      }
      state = const VoiceUploading();
      unawaited(
        ref.read(analyticsProvider).track('voice_asked', {
          'language': target.language,
        }),
      );
      final answer = await ref
          .read(voiceRepositoryProvider)
          .ask(
            audio: File(path),
            memberId: target.memberId,
            productId: target.productId,
            barcode: target.barcode,
            language: target.language,
          );
      if (!ref.mounted) return;
      state = VoicePlaying(answer);
      await _play(answer);
    } on VoiceFailure catch (e) {
      if (ref.mounted) {
        state = VoiceError(voiceErrorKey(e.code), code: e.code);
      }
    } on Object {
      if (ref.mounted) state = const VoiceError('error');
    } finally {
      _sending = false;
      _deleteRecording();
    }
  }

  /// Slide away: drop the recording, send nothing.
  Future<void> cancel() async {
    if (_starting) {
      _releasedWhileStarting = true;
      return;
    }
    if (state is! VoiceRecording) return;
    await _discard();
  }

  /// Close the answer or the error.
  Future<void> dismiss() async {
    try {
      await _player.stop();
    } on Object {
      // Nothing playing.
    }
    if (ref.mounted && !_sending) state = const VoiceIdle();
  }

  /// Play the answer again (while it is open).
  Future<void> replay() async {
    if (state case VoicePlaying(:final answer)) await _play(answer);
  }

  Future<void> _play(VoiceAnswer answer) async {
    final audio = answer.audioBase64;
    if (audio == null) return; // Text only: over the inline audio cap.
    try {
      await _player.playMp3(base64Decode(audio));
    } on Object {
      // The text is on screen; audio is a bonus.
    }
  }

  Future<void> _discard() async {
    _ticker?.cancel();
    try {
      await _recorder.cancel();
    } on Object {
      // Already stopped.
    }
    _deleteRecording();
    if (ref.mounted) state = const VoiceIdle();
  }

  void _deleteRecording() {
    final path = _path;
    _path = null;
    if (path == null) return;
    try {
      final file = File(path);
      if (file.existsSync()) file.deleteSync();
    } on Object {
      // The OS clears the cache directory eventually.
    }
  }
}

final voiceControllerProvider = NotifierProvider.autoDispose
    .family<VoiceController, VoiceState, String>(VoiceController.new);
