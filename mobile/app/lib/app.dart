import 'package:flutter/material.dart';

import 'screens/demo_iot_screen.dart';
import 'screens/entry_mode_screen.dart';
import 'screens/exit_mode_screen.dart';
import 'screens/garita_face_capture_screen.dart';
import 'screens/history_screen.dart';
import 'screens/login_screen.dart';
import 'screens/mode_hub_screen.dart';
import 'screens/result_screen.dart';
import 'screens/setup_screen.dart';
import 'state/parking_app_scope.dart';
import 'state/parking_app_state.dart';
import 'theme/ucepark_theme.dart';

class SmartParkingApp extends StatelessWidget {
  const SmartParkingApp({super.key, required this.appState});

  final ParkingAppState appState;

  String get _initialRoute {
    if (!appState.isLoggedIn) return LoginScreen.routeName;
    if (appState.selection == null) return SetupScreen.routeName;
    return ModeHubScreen.routeName;
  }

  @override
  Widget build(BuildContext context) {
    return ParkingAppScope(
      notifier: appState,
      child: MaterialApp(
        title: 'UCEPark',
        debugShowCheckedModeBanner: false,
        theme: UceParkTheme.build(),
        initialRoute: _initialRoute,
        routes: {
          LoginScreen.routeName: (_) => const LoginScreen(),
          SetupScreen.routeName: (_) => const SetupScreen(),
          ModeHubScreen.routeName: (_) => const ModeHubScreen(),
          DemoIotScreen.routeName: (_) => const DemoIotScreen(),
          EntryModeScreen.routeName: (_) => const EntryModeScreen(),
          ExitModeScreen.routeName: (_) => const ExitModeScreen(),
          HistoryScreen.routeName: (_) => const HistoryScreen(),
          GaritaFisicaScreen.routeName: (_) => const GaritaFisicaScreen(),
          ResultScreen.routeName: (_) => const ResultScreen(),
        },
      ),
    );
  }
}
