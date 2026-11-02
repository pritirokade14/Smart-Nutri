import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../auth/data/auth_repository.dart';

final meProvider = FutureProvider.autoDispose<MeOut>(
  (ref) => ref.watch(apiClientProvider).me.meGet(),
  // Show API errors immediately; the user retries with the button.
  retry: (_, _) => null,
);

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final me = ref.watch(meProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.appName),
        actions: [
          TextButton(
            onPressed: () => ref.read(authRepositoryProvider).signOut(),
            child: Text(l10n.authSignOut),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: Center(
                child: me.when(
                  loading: () => Text(l10n.commonLoading),
                  error: (e, _) => Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(localizedApiError(l10n, e)),
                      TextButton(
                        onPressed: () => ref.invalidate(meProvider),
                        child: Text(l10n.commonRetry),
                      ),
                    ],
                  ),
                  data: (m) => Text(
                    l10n.homeWelcome(m.displayName ?? m.email ?? ''),
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                ),
              ),
            ),
            Text(l10n.commonDisclaimer, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
