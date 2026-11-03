import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/members/presentation/consent_sheet.dart';
import 'package:smartnutri_ai/features/settings/presentation/consents_section.dart';

import '../../support/fake_members.dart';
import 'members_harness.dart';

/// A button that opens the sheet and keeps its result.
class _Opener extends StatefulWidget {
  const _Opener();

  @override
  State<_Opener> createState() => _OpenerState();
}

bool? sheetResult;

class _OpenerState extends State<_Opener> {
  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: TextButton(
        onPressed: () async => sheetResult = await showConsentSheet(context),
        child: const Text('open'),
      ),
    ),
  );
}

Future<FakeConsentsClient> openSheet(
  WidgetTester t, {
  Set<String> granted = const {},
  String locale = 'en',
}) async {
  sheetResult = null;
  final consents = FakeConsentsClient(granted: granted);
  await pumpMembers(
    t,
    const _Opener(),
    members: FakeMembersClient(),
    consents: consents,
    locale: locale,
  );
  await t.tap(find.text('open'));
  await t.pumpAndSettle();
  return consents;
}

void main() {
  for (final locale in ['en', 'hi', 'mr']) {
    testWidgets('records both purposes [$locale]', (t) async {
      final l = l10nFor(locale);
      final consents = await openSheet(t, locale: locale);
      expect(find.text(l.consentHealthDataBody), findsOneWidget);
      expect(find.text(l.consentAiProcessingBody), findsOneWidget);
      expect(find.text(l.consentOptionalAiNote), findsOneWidget);

      await t.tap(find.byKey(ConsentSheet.aiCheckboxKey));
      await t.pump();
      await t.tap(find.byKey(ConsentSheet.agreeKey));
      await t.pumpAndSettle();

      expect(
        [
          for (final r in consents.recorded)
            (r.purpose.json, r.granted, r.version),
        ],
        [
          ('health_data', true, consentVersions['health_data']),
          ('ai_processing', true, consentVersions['ai_processing']),
        ],
      );
      expect(sheetResult, isTrue);
      expect(find.byType(ConsentSheet), findsNothing);
    });
  }

  testWidgets('AI consent is optional and unticked by default', (t) async {
    final consents = await openSheet(t);
    await t.tap(find.byKey(ConsentSheet.agreeKey));
    await t.pumpAndSettle();
    expect(consents.recorded.map((r) => r.purpose.json), ['health_data']);
    expect(sheetResult, isTrue);
  });

  testWidgets('declining records nothing and returns false', (t) async {
    final consents = await openSheet(t);
    await t.tap(find.byKey(ConsentSheet.declineKey));
    await t.pumpAndSettle();
    expect(consents.recorded, isEmpty);
    expect(sheetResult, isFalse);
  });

  testWidgets('AI choice is hidden when already agreed', (t) async {
    await openSheet(t, granted: {'ai_processing'});
    expect(find.byKey(ConsentSheet.aiCheckboxKey), findsNothing);
  });

  testWidgets('Profile shows consents and withdraws or grants them', (t) async {
    final l = l10nFor('en');
    final consents = FakeConsentsClient(granted: {'health_data'});
    await pumpMembers(
      t,
      const Scaffold(body: SingleChildScrollView(child: ConsentsSection())),
      members: FakeMembersClient(),
      consents: consents,
    );
    expect(find.text(l.consentHealthDataTitle), findsOneWidget);
    expect(find.text(l.consentAiProcessingTitle), findsOneWidget);
    expect(find.text(l.consentGranted), findsOneWidget);
    expect(find.text(l.consentNotGranted), findsOneWidget);

    await t.tap(find.byKey(ConsentsSection.actionKey('health_data')));
    await t.pumpAndSettle();
    await t.tap(find.byKey(ConsentsSection.actionKey('ai_processing')));
    await t.pumpAndSettle();
    expect(
      [for (final r in consents.recorded) (r.purpose.json, r.granted)],
      [('health_data', false), ('ai_processing', true)],
    );
    expect(find.text(l.consentGranted), findsOneWidget);
    expect(find.text(l.consentWithdraw), findsOneWidget);
  });
}
