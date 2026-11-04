import 'dart:convert';
import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/observability/analytics.dart';
import 'package:smartnutri_ai/features/voice/data/voice_device.dart';
import 'package:smartnutri_ai/features/voice/data/voice_repository.dart';
import 'package:smartnutri_ai/features/voice/domain/voice_state.dart';
import 'package:smartnutri_ai/features/voice/presentation/voice_controller.dart';
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';
import '../members/members_harness.dart' show apiError;
import 'voice_fakes.dart';

const _target = VoiceTarget(memberId: 'm1', productId: 'p1', language: 'hi');

class _Harness {
  _Harness({bool granted = true}) : mic = FakeMic(granted: granted);
  final FakeMic mic;
  final recorder = FakeRecorder();
  final player = FakePlayer();
  final repo = FakeVoiceRepository(() => voiceAnswerFixture('answer_avoid'));
  final events = <(String, Map<String, Object>)>[];

  late final container = ProviderContainer(
    overrides: [
      micPermissionProvider.overrideWithValue(mic),
      voiceRecorderProvider.overrideWith((ref) => recorder),
      voicePlayerProvider.overrideWith((ref) => player),
      voiceRepositoryProvider.overrideWithValue(repo),
      recordingPathProvider.overrideWithValue(tempRecordingPath),
      analyticsProvider.overrideWithValue(
        Analytics((e, p) async => events.add((e, p))),
      ),
    ],
  );

  VoiceController get controller =>
      container.read(voiceControllerProvider('m1').notifier);
  VoiceState get state => container.read(voiceControllerProvider('m1'));

  void keepAlive() {
    final sub = container.listen(voiceControllerProvider('m1'), (_, _) {});
    addTearDown(sub.close);
    addTearDown(container.dispose);
  }
}

void main() {
  testWidgets(
    'start_when_permission_denied_sets_mic_denied_and_never_records',
    (t) async {
      final h = _Harness(granted: false)..keepAlive();
      await h.controller.start(_target);
      expect(h.mic.requests, 1);
      expect(h.recorder.started, isEmpty);
      expect(h.state, isA<VoiceError>());
      expect((h.state as VoiceError).messageKey, 'voice.mic_denied');
      expect(h.repo.asks, isEmpty);
    },
  );

  testWidgets('recording counts up, then auto_stops_at_30_seconds and sends', (
    t,
  ) async {
    final h = _Harness()..keepAlive();
    await h.controller.start(_target);
    expect(h.state, const VoiceRecording(Duration.zero));
    await t.pump(const Duration(seconds: 3));
    expect(h.state, const VoiceRecording(Duration(seconds: 3)));
    await t.pump(const Duration(seconds: 27));
    await t.pump();
    expect(h.recorder.stops, 1);
    expect(h.repo.asks, hasLength(1));
    expect(h.state, isA<VoicePlaying>());
  });

  testWidgets('stop_and_send_plays_answer_audio', (t) async {
    final h = _Harness()..keepAlive();
    await h.controller.start(_target);
    final path = h.recorder.started.single;
    await h.controller.stopAndSend();
    final answer = voiceAnswerFixture('answer_avoid');
    expect(h.repo.asks.single, {
      'exists': true,
      'member_id': 'm1',
      'language': 'hi',
      'product_id': 'p1',
      'barcode': null,
    });
    // The inline mp3 (base64 in the response) is decoded and played from memory.
    expect(h.player.played, [base64Decode(answer.audioBase64!)]);
    final state = h.state as VoicePlaying;
    expect(state.answer.answer, answer.answer);
    expect(state.answer.verdictStatus, answer.verdictStatus);
    // The recording is not kept on the device.
    expect(File(path).existsSync(), isFalse);
    expect(h.events.single.$1, 'voice_asked');
    expect(h.events.single.$2, {'language': 'hi'});
  });

  testWidgets(
    'a text_only answer (audio null) shows the text and plays nothing',
    (t) async {
      final h = _Harness()..keepAlive();
      h.repo.result = () => voiceAnswerFixture('answer_avoid_text_only');
      await h.controller.start(_target);
      await h.controller.stopAndSend();
      final state = h.state as VoicePlaying;
      expect(state.answer.audioBase64, isNull);
      expect(state.answer.answer, isNotEmpty);
      expect(h.player.played, isEmpty);
      await h.controller.replay();
      expect(h.player.played, isEmpty);
    },
  );

  testWidgets('malformed audio is skipped; the text answer stays', (t) async {
    final h = _Harness()..keepAlive();
    final json = voiceAnswerFixture('answer_avoid').toJson()
      ..['audio_base64'] = 'not base64 !!';
    h.repo.result = () => VoiceAnswer.fromJson(json);
    await h.controller.start(_target);
    await h.controller.stopAndSend();
    expect(h.state, isA<VoicePlaying>());
    expect(h.player.played, isEmpty);
  });

  testWidgets('replay plays the same answer again while it is open', (t) async {
    final h = _Harness()..keepAlive();
    await h.controller.start(_target);
    await h.controller.stopAndSend();
    await h.controller.replay();
    final bytes = base64Decode(voiceAnswerFixture('answer_avoid').audioBase64!);
    expect(h.player.played, [bytes, bytes]);
    await h.controller.dismiss();
    await h.controller.replay();
    expect(h.player.played, hasLength(2));
  });

  testWidgets('429_maps_to_rate_limited_message', (t) async {
    final h = _Harness()..keepAlive();
    h.repo.result = () => throw VoiceFailure(
      apiError(429, 'rate_limited_voice').response!.data['error']['code']
          as String,
    );
    await h.controller.start(_target);
    final path = h.recorder.started.single;
    await h.controller.stopAndSend();
    expect((h.state as VoiceError).messageKey, 'voice.rate_limited');
    expect(h.player.played, isEmpty);
    expect(File(path).existsSync(), isFalse);
  });

  test('error codes map to voice messages', () {
    expect(voiceErrorKey('rate_limited_voice'), 'voice.rate_limited');
    expect(voiceErrorKey('audio_too_long'), 'voice.too_long');
    expect(voiceErrorKey('voice_not_understood'), 'voice.not_understood');
    expect(voiceErrorKey('ai_unavailable'), 'voice.ai_unavailable');
    expect(voiceErrorKey('consent_required'), 'consent.required_to_continue');
    expect(voiceErrorKey('product_not_found'), 'error');
  });

  testWidgets('cancel_discards_recording_and_sends_nothing', (t) async {
    final h = _Harness()..keepAlive();
    await h.controller.start(_target);
    final path = h.recorder.started.single;
    await h.controller.cancel();
    expect(h.recorder.cancels, 1);
    expect(h.repo.asks, isEmpty);
    expect(h.state, const VoiceIdle());
    expect(File(path).existsSync(), isFalse);
    await t.pump(const Duration(seconds: 31));
    expect(h.repo.asks, isEmpty);
  });

  testWidgets('release before recording starts sends nothing', (t) async {
    final h = _Harness()..keepAlive();
    final starting = h.controller.start(_target);
    await h.controller.stopAndSend();
    await starting;
    expect(h.repo.asks, isEmpty);
    expect(h.state, const VoiceIdle());
  });

  testWidgets('dismiss stops playback and returns to idle', (t) async {
    final h = _Harness()..keepAlive();
    await h.controller.start(_target);
    await h.controller.stopAndSend();
    await h.controller.dismiss();
    expect(h.player.stops, greaterThan(0));
    expect(h.state, const VoiceIdle());
  });

  test('voice target needs a product id or a barcode', () {
    expect(
      VoiceTarget.forProduct(
        memberId: 'm',
        productId: null,
        barcode: null,
        language: 'en',
      ),
      isNull,
    );
    final off = VoiceTarget.forProduct(
      memberId: 'm',
      productId: null,
      barcode: '8901063201089',
      language: 'en',
    )!;
    expect((off.productId, off.barcode), (null, '8901063201089'));
    final own = VoiceTarget.forProduct(
      memberId: 'm',
      productId: 'p',
      barcode: '8901063201089',
      language: 'en',
    )!;
    expect((own.productId, own.barcode), ('p', null));
  });
}
