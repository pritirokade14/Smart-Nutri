import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/observability/analytics.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/features/reports/data/reports_repository.dart';
import 'package:smartnutri_ai/features/reports/presentation/report_dialog.dart';
import 'package:smartnutri_api/src/export.dart';

import '../members/members_harness.dart' show apiError;

class _FakeReports implements ReportsClient {
  final sent = <(String, ReportCreate)>[];
  Object? error;

  @override
  Future<ReportOut> reportsCreate({
    required String productId,
    required ReportCreate body,
  }) async {
    sent.add((productId, body));
    if (error case final e?) throw e;
    return ReportOut(
      createdAt: DateTime(2026),
      id: 'r1',
      productId: productId,
      reason: ReportOutReason.fromJson(body.reason.json!),
      status: ReportOutStatus.open,
    );
  }
}

AppLocalizations get _l => lookupAppLocalizations(const Locale('en'));

Future<List<(String, Map<String, Object>)>> _open(
  WidgetTester t,
  _FakeReports client,
) async {
  final events = <(String, Map<String, Object>)>[];
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        reportsRepositoryProvider.overrideWithValue(ReportsRepository(client)),
        analyticsProvider.overrideWithValue(
          Analytics((e, p) async => events.add((e, p))),
        ),
      ],
      child: MaterialApp(
        theme: buildAppTheme(),
        locale: const Locale('en'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Scaffold(
          body: Builder(
            builder: (context) => TextButton(
              onPressed: () => showReportDialog(context, productId: 'p1'),
              child: const Text('open'),
            ),
          ),
        ),
      ),
    ),
  );
  await t.tap(find.text('open'));
  await t.pumpAndSettle();
  expect(find.text(_l.reportTitle), findsOneWidget);
  return events;
}

void main() {
  testWidgets('report_dialog_submits_selected_reason_and_note', (t) async {
    final client = _FakeReports();
    final events = await _open(t, client);
    // Nothing is sent until a reason is chosen.
    expect(
      t.widget<FilledButton>(find.byKey(ReportDialog.submitKey)).enabled,
      isFalse,
    );
    await t.tap(find.text(_l.reportReasonWrongIngredients));
    await t.enterText(find.byKey(ReportDialog.noteKey), '  Peanuts missing  ');
    await t.pump();
    await t.tap(find.byKey(ReportDialog.submitKey));
    await t.pumpAndSettle();
    expect(client.sent.single.$1, 'p1');
    expect(client.sent.single.$2.reason, ReportCreateReason.wrongIngredients);
    expect(client.sent.single.$2.note, 'Peanuts missing');
    expect(find.text(_l.reportTitle), findsNothing);
    expect(find.text(_l.reportThanks), findsOneWidget);
    expect(events.single.$1, 'report_submitted');
    expect(events.single.$2, {'reason': 'wrong_ingredients'});
  });

  testWidgets('a blank note is sent as null', (t) async {
    final client = _FakeReports();
    await _open(t, client);
    await t.tap(find.text(_l.reportReasonOther));
    await t.enterText(find.byKey(ReportDialog.noteKey), '   ');
    await t.tap(find.byKey(ReportDialog.submitKey));
    await t.pumpAndSettle();
    expect(client.sent.single.$2.note, isNull);
  });

  testWidgets('report_dialog_429_shows_rate_limited', (t) async {
    final client = _FakeReports()..error = apiError(429, 'rate_limited');
    final events = await _open(t, client);
    await t.tap(find.text(_l.reportReasonWrongValues));
    await t.pump();
    await t.tap(find.byKey(ReportDialog.submitKey));
    await t.pumpAndSettle();
    expect(find.text(_l.errorRateLimited), findsOneWidget);
    expect(find.text(_l.reportTitle), findsOneWidget);
    expect(events, isEmpty);
  });
}
