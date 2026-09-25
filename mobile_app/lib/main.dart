import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'core/constants/app_constants.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/presentation/bloc/auth_bloc.dart';
import 'features/dashboard/presentation/bloc/dashboard_bloc.dart';
import 'features/payments/presentation/bloc/payments_bloc.dart';
import 'features/upload_evidence/presentation/bloc/upload_bloc.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialisation du formatage de dates en français
  await initializeDateFormatting('fr_FR', null);

  // Initialisation du stockage local Hive pour l'offline-first
  await Hive.initFlutter();
  await Hive.openBox(AppConstants.kpiBoxName);
  await Hive.openBox(AppConstants.paymentsBoxName);

  runApp(const MoneXaApp());
}

class MoneXaApp extends StatelessWidget {
  const MoneXaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<AuthBloc>(
          create: (context) => AuthBloc()..add(CheckAuthStatusEvent()),
        ),
        BlocProvider<DashboardBloc>(
          create: (context) => DashboardBloc(),
        ),
        BlocProvider<UploadBloc>(
          create: (context) => UploadBloc(),
        ),
        BlocProvider<PaymentsBloc>(
          create: (context) => PaymentsBloc(),
        ),
      ],
      child: MaterialApp.router(
        title: 'MoneXa — CFO Virtuel PME',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        routerConfig: appRouter,
      ),
    );
  }
}
