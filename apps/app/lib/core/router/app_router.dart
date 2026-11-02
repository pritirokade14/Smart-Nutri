import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/data/auth_repository.dart';
import '../../features/auth/presentation/email_otp_screen.dart';
import '../../features/auth/presentation/phone_otp_screen.dart';
import '../../features/auth/presentation/sign_in_screen.dart';
import '../../features/home/presentation/home_screen.dart';
import '../../features/result/presentation/result_placeholder_screen.dart';
import '../../features/scan/presentation/scan_screen.dart';
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
          GoRoute(path: 'email', builder: (_, _) => const EmailOtpScreen()),
          if (config.featurePhoneOtp)
            GoRoute(path: 'phone', builder: (_, _) => const PhoneOtpScreen()),
        ],
      ),
      GoRoute(path: '/home', builder: (_, _) => const HomeScreen()),
      GoRoute(path: '/scan', builder: (_, _) => const ScanScreen()),
      GoRoute(
        path: '/result',
        builder: (_, state) => ResultPlaceholderScreen(
          barcode: state.uri.queryParameters['barcode'] ?? '',
        ),
      ),
    ],
  );
  ref.onDispose(router.dispose);
  return router;
});
