import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/assistant/presentation/screens/assistant_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/dashboard/presentation/screens/dashboard_screen.dart';
import '../../features/payments/presentation/screens/payments_screen.dart';
import '../../features/profile/presentation/screens/profile_screen.dart';
import '../../features/shell/presentation/screens/main_shell_screen.dart';
import '../../features/upload_evidence/presentation/screens/upload_screen.dart';
import '../../features/intelligence/presentation/screens/anomalies_screen.dart';
import '../../features/intelligence/presentation/screens/audit_screen.dart';
import '../../features/intelligence/presentation/screens/explain_screen.dart';
import '../../features/intelligence/presentation/screens/forecast_screen.dart';
import '../../features/intelligence/presentation/screens/sources_screen.dart';
import '../../features/invoices/presentation/screens/invoice_create_screen.dart';
import '../../features/invoices/presentation/screens/invoices_screen.dart';

final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>();

final GoRouter appRouter = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      name: 'login',
      builder: (context, state) => const LoginScreen(),
    ),
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) {
        return MainShellScreen(navigationShell: navigationShell);
      },
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/dashboard',
              name: 'dashboard',
              builder: (context, state) => const DashboardScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/upload',
              name: 'upload',
              builder: (context, state) => const UploadScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/payments',
              name: 'payments',
              builder: (context, state) => const PaymentsScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/assistant',
              name: 'assistant',
              builder: (context, state) => const AssistantScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/profile',
              name: 'profile',
              builder: (context, state) => const ProfileScreen(),
            ),
          ],
        ),
      ],
    ),
    GoRoute(
      parentNavigatorKey: _rootNavigatorKey,
      path: '/invoices',
      name: 'invoices',
      builder: (context, state) => const InvoicesScreen(),
    ),
    GoRoute(
      parentNavigatorKey: _rootNavigatorKey,
      path: '/invoices/new',
      name: 'invoice-create',
      builder: (context, state) => const InvoiceCreateScreen(),
    ),
    GoRoute(
      parentNavigatorKey: _rootNavigatorKey,
      path: '/sources',
      name: 'sources',
      builder: (context, state) => const SourcesScreen(),
    ),
    GoRoute(
      parentNavigatorKey: _rootNavigatorKey,
      path: '/anomalies',
      name: 'anomalies',
      builder: (context, state) => const AnomaliesScreen(),
    ),
    GoRoute(
      parentNavigatorKey: _rootNavigatorKey,
      path: '/forecast',
      name: 'forecast',
      builder: (context, state) => const ForecastScreen(),
    ),
    GoRoute(
      parentNavigatorKey: _rootNavigatorKey,
      path: '/audit',
      name: 'audit',
      builder: (context, state) => const AuditScreen(),
    ),
    GoRoute(
      parentNavigatorKey: _rootNavigatorKey,
      path: '/payments/:id/explain',
      name: 'explain',
      builder: (context, state) {
        final id = int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
        return ExplainScreen(paymentId: id);
      },
    ),
  ],
);
