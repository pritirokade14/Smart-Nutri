import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/analysis/presentation/result_screen.dart';
import '../../features/auth/data/auth_repository.dart';
import '../../features/auth/presentation/email_otp_screen.dart';
import '../../features/auth/presentation/phone_otp_screen.dart';
import '../../features/auth/presentation/sign_in_screen.dart';
import '../../features/history/presentation/history_screen.dart';
import '../../features/home/presentation/home_screen.dart';
import '../../features/meals/presentation/meals_providers.dart';
import '../../features/members/presentation/member_form_screen.dart';
import '../../features/members/presentation/members_list_screen.dart';
import '../../features/product/presentation/compare_screen.dart';
import '../../features/product/presentation/discovery_routes.dart';
import '../../features/product/presentation/search_screen.dart';
import '../../features/scan/presentation/confirm_screen.dart';
import '../../features/scan/presentation/label_capture_screen.dart';
import '../../features/scan/presentation/scan_screen.dart';
import '../../features/settings/presentation/profile_screen.dart';
import '../../shared/widgets/app_shell.dart';
import '../config/app_config.dart';

class _AuthRefresh extends ChangeNotifier {
  _AuthRefresh(Stream<bool> stream) {
    _sub = stream.listen((_) => notifyListeners());
  }
  late final StreamSubscription<bool> _sub;

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }
}

final routerProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authRepositoryProvider);
  final config = ref.watch(appConfigProvider);
  final refresh = _AuthRefresh(auth.authStateChanges());
  ref.onDispose(refresh.dispose);

  final router = GoRouter(
    initialLocation: '/home',
    refreshListenable: refresh,
    redirect: (context, state) {
      final onSignIn = state.matchedLocation.startsWith('/sign-in');
      if (!auth.isSignedIn) return onSignIn ? null : '/sign-in';
      if (onSignIn) return '/home';
      return null;
    },
    routes: [
      GoRoute(
        path: '/sign-in',
        builder: (_, _) => const SignInScreen(),
        routes: [
          if (config.featureEmailOtp)
            GoRoute(path: 'email', builder: (_, _) => const EmailOtpScreen()),
          if (config.featurePhoneOtp)
            GoRoute(path: 'phone', builder: (_, _) => const PhoneOtpScreen()),
        ],
      ),
      // The signed-in tabs. Scan, label capture, confirm and result are
      // full-screen routes above the shell (see AppShell).
      StatefulShellRoute.indexedStack(
        // The offline log syncs while signed in (start, resume, back online).
        builder: (_, _, shell) => MealSyncScope(child: AppShell(shell: shell)),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(path: '/home', builder: (_, _) => const HomeScreen()),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/history',
                builder: (_, _) => const HistoryScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/family',
                builder: (_, _) => const MembersListScreen(),
                routes: [
                  GoRoute(
                    path: 'new',
                    builder: (_, _) => const MemberFormScreen(),
                  ),
                  GoRoute(
                    path: ':id',
                    builder: (_, state) =>
                        MemberFormScreen(memberId: state.pathParameters['id']),
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/profile',
                builder: (_, _) => const ProfileScreen(),
              ),
            ],
          ),
        ],
      ),
      GoRoute(path: '/scan', builder: (_, _) => const ScanScreen()),
      GoRoute(
        path: '/scan/label',
        builder: (_, state) =>
            LabelCaptureScreen(barcode: state.uri.queryParameters['barcode']),
      ),
      GoRoute(
        path: '/scan/confirm',
        // The draft travels in memory only; a deep link opens an empty
        // manual-entry form.
        builder: (_, state) => ConfirmScreen(
          args: state.extra is ConfirmArgs ? state.extra! as ConfirmArgs : null,
        ),
      ),
      GoRoute(
        path: '/search',
        builder: (_, state) {
          final q = discoveryQuery(state.uri.queryParameters);
          return SearchScreen(compareWith: q.a, memberId: q.memberId);
        },
      ),
      GoRoute(
        path: '/compare',
        builder: (_, state) {
          final q = discoveryQuery(state.uri.queryParameters);
          return CompareScreen(a: q.a, b: q.b, memberId: q.memberId);
        },
      ),
      GoRoute(
        path: '/result',
        builder: (_, state) => ResultScreen(
          barcode: state.uri.queryParameters['barcode'],
          productId: state.uri.queryParameters['product_id'],
        ),
      ),
    ],
  );
  ref.onDispose(router.dispose);
  return router;
});
