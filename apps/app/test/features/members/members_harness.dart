import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/features/members/data/members_repository.dart';

import '../../support/fake_members.dart';

/// Pumps [child] with real repositories over fake generated clients, on a
/// tall surface so the whole form is built.
Future<void> pumpMembers(
  WidgetTester t,
  Widget child, {
  required FakeMembersClient members,
  required FakeConsentsClient consents,
  String locale = 'en',
  bool settle = true,
}) async {
  t.view.physicalSize = const Size(900, 4200);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        membersRepositoryProvider.overrideWithValue(MembersRepository(members)),
        consentsRepositoryProvider.overrideWithValue(
          ConsentsRepository(consents),
        ),
      ],
      child: MaterialApp(
        theme: buildAppTheme(),
        locale: Locale(locale),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: child,
      ),
    ),
  );
  if (settle) await t.pumpAndSettle();
}

AppLocalizations l10nFor(String locale) =>
    lookupAppLocalizations(Locale(locale));

/// A DioException carrying the API error envelope.
DioException apiError(int status, String code) {
  final ro = RequestOptions(path: '/v1/members');
  return DioException(
    requestOptions: ro,
    response: Response(
      requestOptions: ro,
      statusCode: status,
      data: {
        'error': {'code': code, 'message_key': 'error.$code'},
      },
    ),
  );
}
