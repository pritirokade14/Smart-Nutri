import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';
import 'package:smartnutri_ai/features/history/presentation/day_summary_card.dart';
import 'package:smartnutri_ai/features/history/presentation/history_screen.dart';
import 'package:smartnutri_ai/features/history/presentation/weekly_dashboard.dart';
import 'package:smartnutri_ai/features/members/data/members_repository.dart';
import 'package:smartnutri_ai/shared/share/share_sheet.dart';
import 'package:smartnutri_ai/shared/widgets/off_attribution.dart';
import 'package:smartnutri_ai/shared/widgets/states.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';
import '../../support/fake_members.dart';
import '../../support/test_config.dart';

final en = lookupAppLocalizations(const Locale('en'));

Map<String, Object?> _weekJson() =>
    jsonDecode(
          File(
            '../../packages/test-fixtures/meals/expected/'
            'week_family.dad_diabetic.json',
          ).readAsStringSync(),
        )
        as Map<String, Object?>;

Summary _summary(String memberId, SummaryPeriod? period) {
  final json = _weekJson()..['member_id'] = memberId;
  if (period == SummaryPeriod.day) {
    final last = (json['days']! as List).last as Map<String, Object?>;
    json
      ..['period'] = 'day'
      ..['start'] = last['date']
      ..['totals'] = last['totals']
      ..['incomplete'] = last['incomplete']
      ..['bands'] = last['bands']
      ..['days'] = [last];
  }
  return Summary.fromJson(json);
}

final _dad = memberOut(
  id: 'dad',
  name: 'Ravi Patil',
  relation: MemberOutRelation.parent,
  birthYear: 1960,
);

class _H {
  final meals = FakeMealsClient();
  final queue = MemoryMealQueue();
  final shared = <String>[];
}

Future<_H> _pump(
  WidgetTester t, {
  void Function(_H h)? setUp,
  List<MemberOut>? members,
}) async {
  final h = _H();
  h.meals
    ..summary = _summary
    ..meals = [
      mealOut(
        id: 'm-a',
        memberId: 'p1',
        productName: 'Masala Oats',
        eatenAt: DateTime.now().toUtc(),
        grams: 40,
      ),
      mealOut(
        id: 'm-b',
        memberId: 'p1',
        productName: 'Cola',
        barcode: '8901',
        attribution: 'attribution.off',
        grade: NutriScoreGrade.e,
        eatenAt: DateTime.now().toUtc().subtract(const Duration(days: 2)),
        grams: 250,
      ),
    ];
  setUp?.call(h);
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        testConfigOverride(),
        ...mealTestOverrides(queue: h.queue, client: h.meals),
        membersRepositoryProvider.overrideWithValue(
          MembersRepository(
            FakeMembersClient(members ?? [primaryMember(), _dad]),
          ),
        ),
        shareLauncherProvider.overrideWithValue((text) async {
          h.shared.add(text);
        }),
      ],
      child: MaterialApp(
        locale: const Locale('en'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: const HistoryScreen(),
      ),
    ),
  );
  await t.pumpAndSettle();
  return h;
}

Future<void> _scrollTo(WidgetTester t, Finder f) async {
  await t.scrollUntilVisible(f, 200, scrollable: find.byType(Scrollable).first);
  await t.pumpAndSettle();
}

void main() {
  testWidgets('no longer a "coming soon" placeholder', (t) async {
    await _pump(t);
    expect(find.text(en.historyComingSoonTitle), findsNothing);
    expect(find.text(en.historyTitle), findsOneWidget);
  });

  testWidgets('today and the week for the account holder by default', (
    t,
  ) async {
    final h = await _pump(t);
    expect(h.meals.summaries.map((s) => (s.$1, s.$2)).toSet(), {
      ('p1', SummaryPeriod.day),
      ('p1', SummaryPeriod.week),
    });
    expect(find.byType(DaySummaryCard), findsOneWidget);
    await _scrollTo(t, find.byType(WeeklyDashboard));
    expect(find.byType(WeeklyDashboard), findsOneWidget);
  });

  testWidgets('logged items, with OFF credit; remove asks first', (t) async {
    final h = await _pump(t);
    await _scrollTo(t, find.text('Cola'));
    expect(find.text('Masala Oats'), findsOneWidget);
    expect(find.textContaining(en.historyItemAmount('250')), findsOneWidget);
    expect(find.byType(OffAttribution), findsOneWidget);
    expect(find.text(en.historyToday), findsOneWidget);

    await t.tap(find.byKey(const Key('meal-remove-m-b')));
    await t.pumpAndSettle();
    expect(find.text(en.historyRemoveConfirm), findsOneWidget);
    await t.tap(find.widgetWithText(TextButton, en.historyRemove));
    await t.pumpAndSettle();
    expect(h.meals.deleted, ['m-b']);
    expect(find.text('Cola'), findsNothing);
  });

  testWidgets('switching member reloads for that member', (t) async {
    final h = await _pump(t);
    await t.tap(find.text('Ravi Patil'));
    await t.pumpAndSettle();
    expect(h.meals.summaries.map((s) => s.$1), contains('dad'));
  });

  testWidgets('summary error shows retry', (t) async {
    final h = await _pump(
      t,
      setUp: (h) => h.meals.summaryError = networkError(),
    );
    expect(find.text(en.errorNetwork), findsWidgets);
    h.meals.summaryError = null;
    await t.tap(find.text(en.commonRetry).first);
    await t.pumpAndSettle();
    expect(find.byType(DaySummaryCard), findsOneWidget);
  });

  testWidgets('loading state', (t) async {
    final gate = Completer<List<MemberOut>>();
    await t.pumpWidget(
      ProviderScope(
        overrides: [
          ...mealTestOverrides(client: FakeMealsClient()),
          membersRepositoryProvider.overrideWithValue(_SlowMembers(gate)),
        ],
        child: MaterialApp(
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          home: const HistoryScreen(),
        ),
      ),
    );
    expect(find.byType(LoadingSkeleton), findsWidgets);
    gate.complete([primaryMember()]);
    await t.pumpAndSettle();
  });

  testWidgets('items waiting offline and refused items are announced', (
    t,
  ) async {
    await _pump(
      t,
      setUp: (h) {
        h.queue.rows['c1'] = PendingMeal(
          clientId: 'c1',
          memberId: 'p1',
          productId: 'x',
          eatenAt: DateTime.utc(2026, 11, 3),
          attempts: 1,
        );
        h.queue.rows['c2'] = PendingMeal(
          clientId: 'c2',
          memberId: 'p1',
          productId: 'x',
          eatenAt: DateTime.utc(2026, 11, 3),
          attempts: 1,
          lastError: 'eaten_at_out_of_range',
        );
      },
    );
    expect(find.text(en.mealsQueuedOffline), findsOneWidget);
    expect(find.text(en.mealsSyncFailed), findsOneWidget);
  });

  testWidgets('share our week: counts only, after the privacy note', (t) async {
    final h = await _pump(t);
    final button = find.text(en.shareWeeklyButton);
    await _scrollTo(t, button);
    await t.tap(button);
    await t.pumpAndSettle();
    expect(find.text(en.sharePrivacyNote), findsOneWidget);
    await t.tap(find.byKey(ShareSheet.shareKey));
    await t.pumpAndSettle();
    expect(h.shared, [
      'Our week on SmartNutri — products checked: 12, items logged: 10. '
          'Checked with SmartNutri: https://site.example/en',
    ]);
  });
}

class _SlowMembers implements MembersRepository {
  _SlowMembers(this.gate);
  final Completer<List<MemberOut>> gate;
  @override
  Future<List<MemberOut>> list() => gate.future;
  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}
