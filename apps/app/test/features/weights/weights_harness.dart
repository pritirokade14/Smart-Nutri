import 'package:flutter/widgets.dart' show Size;
import 'package:flutter_test/flutter_test.dart';

import '../../support/fake_diary.dart';
import '../../support/fake_meals.dart';
import '../../support/fake_members.dart';
import '../../support/fake_targets.dart';
import '../../support/fake_user_types.dart';
import '../../support/fake_weights.dart';
import '../diary/diary_harness.dart';

export '../diary/diary_harness.dart' show AppHarness, en, pumpApp, texts;

class WeightsEnv {
  WeightsEnv({
    String trend = 'weekly_rate_loss',
    String targets = 'g1_build_muscle',
    Set<String> consents = const {'terms', 'health_data'},
    FakeWeightsClient? weights,
  }) : weights = weights ?? FakeWeightsClient(trend: trend),
       consents = FakeConsentsClient(granted: consents),
       targets = FakeTargetsClient(
         today: targets,
         settings: goalSettingsOut(activity: 'moderate'),
       );

  final FakeWeightsClient weights;
  final FakeConsentsClient consents;
  final FakeTargetsClient targets;
  final queue = MemoryMealQueue();

  FakeUserTypesApi get api => FakeUserTypesApi(
    me: FakeUserTypesMe(userTypesOut(types: ['gym'])),
    members: FakeMembersClient([diaryPrimary()]),
    consents: consents,
    targets: targets,
    diary: FakeDiaryClient(),
    weights: weights,
  );
}

/// The Weight screen (Profile, "Weight").
Future<AppHarness> pumpWeights(WidgetTester t, WeightsEnv env) => pumpApp(
  t,
  env.api,
  queue: env.queue,
  initial: '/diary/weight',
  size: const Size(900, 3600),
);
