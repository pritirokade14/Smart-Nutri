import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/config/app_config.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/features/analysis/data/analysis_repository.dart';
import 'package:smartnutri_ai/features/analysis/presentation/result_screen.dart';
import 'package:smartnutri_ai/features/meals/presentation/log_meal_sheet.dart'
    show memberLabel;
import 'package:smartnutri_ai/features/voice/data/voice_device.dart';
import 'package:smartnutri_ai/features/voice/data/voice_repository.dart';
import 'package:smartnutri_ai/features/voice/domain/voice_state.dart';
import 'package:smartnutri_ai/features/voice/presentation/push_to_talk_button.dart';
import 'package:smartnutri_ai/features/voice/presentation/voice_answer_sheet.dart';
import 'package:smartnutri_ai/shared/widgets/verdict_badge.dart';
import 'package:smartnutri_api/src/export.dart';

import 'package:smartnutri_ai/core/platform/app_settings.dart';
import '../../support/fake_app_settings.dart';
import '../../support/fixtures.dart';
import '../analysis/result_screen_test.dart' show FakeAnalysisRepository;
import 'voice_fakes.dart';

AppLocalizations get _l => lookupAppLocalizations(const Locale('en'));

AppConfig _config({required bool voice}) => AppConfig(
  environment: 'test',
  apiBaseUrl: 'http://x',
  supabaseUrl: 'http://s',
  supabasePublishableKey: 'k',
  googleWebClientId: 'g',
  sentryDsn: '',
  posthogKey: '',
  featurePhoneOtp: false,
  featureVoice: voice,
);

Widget _wrap(Widget home, List<Object> overrides) => ProviderScope(
  overrides: overrides.cast(),
  child: MaterialApp(
    theme: buildAppTheme(),
    locale: const Locale('en'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: home,
  ),
);

void main() {
  testWidgets('answer_sheet_shows_verdict_colour_disclaimer_and_text', (
    t,
  ) async {
    final answer = voiceAnswerFixture('answer_avoid');
    await t.pumpWidget(
      _wrap(
        Scaffold(
          body: VoiceAnswerSheet(answer: answer, onReplay: () {}),
        ),
        [],
      ),
    );
    await t.pumpAndSettle();
    expect(find.text(answer.answer), findsOneWidget);
    expect(find.text(_l.commonDisclaimer), findsOneWidget);
    final badge = t.widget<VerdictBadge>(find.byType(VerdictBadge));
    expect(badge.status, 'avoid');
    final surface = t.widget<Container>(
      find.byKey(VoiceAnswerSheet.badgeSurfaceKey),
    );
    final colors = SnColors.of(t.element(find.byType(VoiceAnswerSheet)));
    expect((surface.decoration! as BoxDecoration).color, colors.verdictAvoid);
    // The question is shown back (never stored), and an LLM answer carries
    // no fallback note.
    expect(find.text(_l.voiceYouAsked(answer.question)), findsOneWidget);
    expect(find.text(_l.explanationSourceFallbackNote), findsNothing);
  });

  testWidgets('a rules-only (fallback) answer says so', (t) async {
    final answer = voiceAnswerFixture('answer_avoid_fallback');
    expect(answer.source, VoiceAnswerSource.fallback);
    await t.pumpWidget(
      _wrap(
        Scaffold(
          body: VoiceAnswerSheet(answer: answer, onReplay: () {}),
        ),
        [],
      ),
    );
    await t.pumpAndSettle();
    expect(find.text(_l.explanationSourceFallbackNote), findsOneWidget);
    expect(find.text(_l.voiceYouAsked(answer.question)), findsOneWidget);
    expect(find.text(_l.commonDisclaimer), findsOneWidget);
  });

  testWidgets('a text-only answer has no replay control', (t) async {
    final answer = voiceAnswerFixture('answer_avoid_text_only');
    await t.pumpWidget(
      _wrap(
        Scaffold(
          body: VoiceAnswerSheet(answer: answer, onReplay: () {}),
        ),
        [],
      ),
    );
    await t.pumpAndSettle();
    expect(find.text(answer.answer), findsOneWidget);
    expect(find.text(_l.commonDisclaimer), findsOneWidget);
    expect(find.text(_l.voiceReplay), findsNothing);
    expect(find.text(_l.voicePlaying), findsNothing);
  });

  testWidgets('an answer with audio offers replay', (t) async {
    var replays = 0;
    await t.pumpWidget(
      _wrap(
        Scaffold(
          body: VoiceAnswerSheet(
            answer: voiceAnswerFixture('answer_avoid'),
            onReplay: () => replays++,
          ),
        ),
        [],
      ),
    );
    await t.pumpAndSettle();
    await t.tap(find.text(_l.voiceReplay));
    expect(replays, 1);
  });

  test('an unknown status from a newer API never shows as ok', () {
    final json = voiceAnswerFixture('answer_avoid').toJson()
      ..['verdict_status'] = 'something_new';
    final answer = VoiceAnswer.fromJson(json);
    expect(VoiceAnswerSheet.statusOf(answer.verdictStatus), 'unknown');
  });

  testWidgets('voice button hidden unless FEATURE_VOICE is on', (t) async {
    final body = analyzeFixture('sf_biscuit');
    await t.pumpWidget(
      _wrap(const ResultScreen(barcode: '8901063201089'), [
        appConfigProvider.overrideWithValue(_config(voice: false)),
        analysisRepositoryProvider.overrideWithValue(
          FakeAnalysisRepository([() => body]),
        ),
      ]),
    );
    await t.pumpAndSettle();
    expect(find.byType(PushToTalkButton), findsNothing);

    await t.pumpWidget(const SizedBox());
    await t.pumpWidget(
      _wrap(const ResultScreen(barcode: '8901063201089'), [
        appConfigProvider.overrideWithValue(_config(voice: true)),
        analysisRepositoryProvider.overrideWithValue(
          FakeAnalysisRepository([() => body]),
        ),
      ]),
    );
    await t.pumpAndSettle();
    expect(find.byType(PushToTalkButton), findsNWidgets(body.verdicts.length));
  });

  testWidgets('voice button has a per-member semantics label', (t) async {
    final h = t.ensureSemantics();
    final body = analyzeFixture('sf_biscuit');
    await t.pumpWidget(
      _wrap(const ResultScreen(barcode: '8901063201089'), [
        appConfigProvider.overrideWithValue(_config(voice: true)),
        analysisRepositoryProvider.overrideWithValue(
          FakeAnalysisRepository([() => body]),
        ),
      ]),
    );
    await t.pumpAndSettle();
    for (final v in body.verdicts.take(2)) {
      final name = memberLabel(_l, v);
      expect(
        find.bySemanticsLabel(_l.voiceButtonHoldFor(name)),
        findsOneWidget,
      );
    }
    h.dispose();
  });

  testWidgets('hold to record shows the timer; release shows the answer', (
    t,
  ) async {
    final recorder = FakeRecorder();
    final player = FakePlayer();
    final repo = FakeVoiceRepository(() => voiceAnswerFixture('answer_avoid'));
    await t.pumpWidget(
      _wrap(
        const Scaffold(
          body: Center(
            child: PushToTalkButton(
              target: VoiceTarget(
                memberId: 'm1',
                productId: 'p1',
                language: 'en',
              ),
            ),
          ),
        ),
        [
          micPermissionProvider.overrideWithValue(FakeMic()),
          voiceRecorderProvider.overrideWith((ref) => recorder),
          voicePlayerProvider.overrideWith((ref) => player),
          voiceRepositoryProvider.overrideWithValue(repo),
          recordingPathProvider.overrideWithValue(tempRecordingPath),
        ],
      ),
    );
    expect(find.text(_l.voiceButtonHold), findsOneWidget);
    final gesture = await t.startGesture(
      t.getCenter(find.byType(PushToTalkButton)),
    );
    await t.pump(const Duration(milliseconds: 600)); // long press
    await t.pump();
    expect(find.text(_l.voiceRecording), findsOneWidget);
    await t.pump(const Duration(seconds: 2));
    expect(find.text('0:02'), findsOneWidget);
    await gesture.up();
    await t.pumpAndSettle();
    expect(repo.asks, hasLength(1));
    expect(find.byType(VoiceAnswerSheet), findsOneWidget);
    expect(find.text(_l.commonDisclaimer), findsOneWidget);
  });

  testWidgets('sliding away cancels the recording', (t) async {
    final recorder = FakeRecorder();
    final repo = FakeVoiceRepository(() => voiceAnswerFixture('answer_avoid'));
    await t.pumpWidget(
      _wrap(
        const Scaffold(
          body: Center(
            child: PushToTalkButton(
              target: VoiceTarget(
                memberId: 'm1',
                productId: 'p1',
                language: 'en',
              ),
            ),
          ),
        ),
        [
          micPermissionProvider.overrideWithValue(FakeMic()),
          voiceRecorderProvider.overrideWith((ref) => recorder),
          voicePlayerProvider.overrideWith((ref) => FakePlayer()),
          voiceRepositoryProvider.overrideWithValue(repo),
          recordingPathProvider.overrideWithValue(tempRecordingPath),
        ],
      ),
    );
    final gesture = await t.startGesture(
      t.getCenter(find.byType(PushToTalkButton)),
    );
    await t.pump(const Duration(milliseconds: 600));
    await t.pump();
    await gesture.moveBy(const Offset(0, -200));
    await t.pump();
    await gesture.up();
    await t.pumpAndSettle();
    expect(recorder.cancels, 1);
    expect(repo.asks, isEmpty);
    expect(find.text(_l.voiceButtonHold), findsOneWidget);
  });

  testWidgets('mic denied shows the message', (t) async {
    await t.pumpWidget(
      _wrap(
        const Scaffold(
          body: Center(
            child: PushToTalkButton(
              target: VoiceTarget(
                memberId: 'm1',
                productId: 'p1',
                language: 'en',
              ),
            ),
          ),
        ),
        [
          micPermissionProvider.overrideWithValue(FakeMic(granted: false)),
          voiceRecorderProvider.overrideWith((ref) => FakeRecorder()),
          voicePlayerProvider.overrideWith((ref) => FakePlayer()),
          voiceRepositoryProvider.overrideWithValue(
            FakeVoiceRepository(() => voiceAnswerFixture('answer_avoid')),
          ),
          recordingPathProvider.overrideWithValue(tempRecordingPath),
        ],
      ),
    );
    await t.longPress(find.byType(PushToTalkButton));
    await t.pumpAndSettle();
    expect(find.text(_l.voiceMicDenied), findsOneWidget);
    expect(find.text(_l.commonOpenSettings), findsNothing);
  });

  for (final permanent in [true, false]) {
    testWidgets('mic denied: Open settings only when permanent ($permanent)', (
      t,
    ) async {
      final settings = FakeAppSettings(permanent: permanent);
      await t.pumpWidget(
        _wrap(
          const Scaffold(
            body: Center(
              child: PushToTalkButton(
                target: VoiceTarget(
                  memberId: 'm1',
                  productId: 'p1',
                  language: 'en',
                ),
              ),
            ),
          ),
          [
            appSettingsProvider.overrideWithValue(settings),
            micPermissionProvider.overrideWithValue(FakeMic(granted: false)),
            voiceRecorderProvider.overrideWith((ref) => FakeRecorder()),
            voicePlayerProvider.overrideWith((ref) => FakePlayer()),
            voiceRepositoryProvider.overrideWithValue(
              FakeVoiceRepository(() => voiceAnswerFixture('answer_avoid')),
            ),
            recordingPathProvider.overrideWithValue(tempRecordingPath),
          ],
        ),
      );
      await t.longPress(find.byType(PushToTalkButton));
      await t.pumpAndSettle();
      expect(settings.denied, [microphonePermission]);
      if (permanent) {
        await t.tap(find.text(_l.commonOpenSettings));
        expect(settings.opened, 1);
      } else {
        expect(find.text(_l.commonOpenSettings), findsNothing);
      }
    });
  }
}
