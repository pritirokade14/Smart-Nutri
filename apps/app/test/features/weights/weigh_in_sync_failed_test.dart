import 'package:flutter/widgets.dart' show Size;
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';
import 'package:smartnutri_ai/features/weights/data/weight_sync.dart';

import '../../support/fake_meals.dart';
import 'weights_harness.dart';

PendingWeighIn _row(String id) => PendingWeighIn(
  clientId: id,
  localDate: '2026-11-07',
  weightKg: 71.5,
  confirmUnusual: false,
  status: WeighInStatus.pending,
  attempts: 0,
);

void main() {
  for (final (status, code, copy) in [
    (422, 'date_in_future', en.errorDateInFuture),
    (403, 'consent_required', en.errorConsentRequired),
  ]) {
    testWidgets('$code refusal shows in the sync notice, then is cleared', (
      t,
    ) async {
      final env = WeightsEnv();
      await pumpApp(
        t,
        env.api,
        queue: env.queue,
        initial: '/diary',
        size: const Size(900, 3600),
      );
      await env.queue.addWeighIn(_row('w1'));
      env.weights.putErrors.add(apiError(status, code));
      await t.runAsync(() => WeighInSync(env.weights, env.queue).flush());
      await t.pumpAndSettle();
      expect(env.queue.weighIns['w1']!.status, WeighInStatus.failed);
      expect(find.text(copy), findsOneWidget);

      await t.tap(find.text('OK'));
      await t.pumpAndSettle();
      expect(env.queue.weighIns, isEmpty);
      expect(find.text(copy), findsNothing);
    });
  }
}
