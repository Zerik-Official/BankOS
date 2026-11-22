import 'package:bankos_mobile/app/main_shell.dart';
import 'package:bankos_mobile/features/deposit/deposit_page.dart';
import 'package:bankos_mobile/features/home/home_page.dart';
import 'package:bankos_mobile/features/login/login_page.dart';
import 'package:bankos_mobile/features/notices/notices_page.dart';
import 'package:bankos_mobile/features/profile/profile_page.dart';
import 'package:bankos_mobile/features/transactions/transactions_page.dart';
import 'package:bankos_mobile/features/transfer/transfer_page.dart';
import 'package:bankos_mobile/features/withdraw/withdraw_page.dart';
import 'package:bankos_mobile/providers/session_provider.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Path of the login screen.
const String loginPath = '/login';

/// Provides the navigation configuration of the app.
final Provider<GoRouter> routerProvider = Provider<GoRouter>((Ref ref) {
  return GoRouter(
    initialLocation: loginPath,
    redirect: (BuildContext context, GoRouterState state) {
      final bool signedIn = ref.read(sessionProvider) != null;
      final bool onLogin = state.matchedLocation == loginPath;
      if (!signedIn && !onLogin) {
        return loginPath;
      }
      if (signedIn && onLogin) {
        return '/';
      }
      return null;
    },
    routes: <RouteBase>[
      GoRoute(
        path: loginPath,
        builder: (BuildContext context, GoRouterState state) =>
            const LoginPage(),
      ),
      ShellRoute(
        builder: (BuildContext context, GoRouterState state, Widget child) {
          return MainShell(location: state.matchedLocation, child: child);
        },
        routes: <RouteBase>[
          GoRoute(
            path: '/',
            builder: (BuildContext context, GoRouterState state) =>
                const HomePage(),
          ),
          GoRoute(
            path: '/transactions',
            builder: (BuildContext context, GoRouterState state) =>
                const TransactionsPage(),
          ),
          GoRoute(
            path: '/profile',
            builder: (BuildContext context, GoRouterState state) =>
                const ProfilePage(),
          ),
        ],
      ),
      GoRoute(
        path: '/deposit',
        builder: (BuildContext context, GoRouterState state) =>
            const DepositPage(),
      ),
      GoRoute(
        path: '/withdraw',
        builder: (BuildContext context, GoRouterState state) =>
            const WithdrawPage(),
      ),
      GoRoute(
        path: '/transfer',
        builder: (BuildContext context, GoRouterState state) =>
            const TransferPage(),
      ),
      GoRoute(
        path: '/notices',
        builder: (BuildContext context, GoRouterState state) =>
            const NoticesPage(),
      ),
    ],
  );
});
