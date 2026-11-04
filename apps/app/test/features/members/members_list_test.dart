import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/members/presentation/members_list_screen.dart';
import 'package:smartnutri_ai/shared/widgets/states.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_members.dart';
import 'members_harness.dart';

class _SlowMembers extends FakeMembersClient {
  final completer = Completer<List<MemberOut>>();
  @override
  Future<List<MemberOut>> membersList() => completer.future;
}

class _FailingMembers extends FakeMembersClient {
  int listCalls = 0;
  @override
  Future<List<MemberOut>> membersList() async {
    listCalls++;
    if (listCalls == 1) throw apiError(500, 'internal_error');
    return super.membersList();
  }
}

void main() {
  testWidgets('loading state', (t) async {
    final members = _SlowMembers();
    await pumpMembers(
      t,
      const MembersListScreen(),
      members: members,
      consents: FakeConsentsClient(),
      settle: false,
    );
    await t.pump();
    expect(find.byType(LoadingSkeleton), findsOneWidget);
    members.completer.complete([primaryMember()]);
    await t.pumpAndSettle();
    expect(find.text('Ravi'), findsOneWidget);
  });

  testWidgets('error state with retry', (t) async {
    final l = l10nFor('en');
    final members = _FailingMembers();
    await pumpMembers(
      t,
      const MembersListScreen(),
      members: members,
      consents: FakeConsentsClient(),
    );
    expect(find.text(l.errorInternalError), findsOneWidget);
    await t.tap(find.text(l.commonRetry));
    await t.pumpAndSettle();
    expect(find.text('Ravi'), findsOneWidget);
  });

  testWidgets('lists members in API order, primary marked "You"', (t) async {
    final l = l10nFor('hi');
    await pumpMembers(
      t,
      const MembersListScreen(),
      members: FakeMembersClient([
        primaryMember(),
        memberOut(
          name: 'Asha',
          allergens: ['peanut', 'Kiwi'],
          conditions: [MemberOutConditions.diabetes],
        ),
      ]),
      consents: FakeConsentsClient(),
      locale: 'hi',
    );
    expect(
      t.getTopLeft(find.text('Ravi')).dy,
      lessThan(t.getTopLeft(find.text('Asha')).dy),
    );
    expect(find.text(l.membersYouBadge), findsOneWidget);
    expect(
      find.text('${l.allergenPeanut}, Kiwi, ${l.conditionDiabetes}'),
      findsOneWidget,
    );
    expect(find.byKey(MembersListScreen.addKey), findsOneWidget);
  });

  testWidgets('primary member named "You" shows it once', (t) async {
    final l = l10nFor('en');
    await pumpMembers(
      t,
      const MembersListScreen(),
      members: FakeMembersClient([primaryMember(name: l.membersYouBadge)]),
      consents: FakeConsentsClient(),
    );
    expect(find.text(l.membersYouBadge), findsOneWidget);
  });

  testWidgets('at the member limit the add button becomes a note', (t) async {
    final l = l10nFor('en');
    await pumpMembers(
      t,
      const MembersListScreen(),
      members: FakeMembersClient([
        primaryMember(),
        for (var i = 0; i < maxMembers - 1; i++)
          memberOut(id: 'm$i', name: 'M$i'),
      ]),
      consents: FakeConsentsClient(),
    );
    expect(find.byKey(MembersListScreen.addKey), findsNothing);
    expect(find.text(l.errorMemberLimit), findsOneWidget);
  });

  testWidgets('withdrawn health consent shows the notice', (t) async {
    final l = l10nFor('en');
    await pumpMembers(
      t,
      const MembersListScreen(),
      members: FakeMembersClient(),
      consents: FakeConsentsClient(withdrawn: {'health_data'}),
    );
    expect(find.text(l.membersConsentWithdrawnNotice), findsOneWidget);
  });
}
