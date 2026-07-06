import 'package:flutter/material.dart';

import 'screens/demo_iot_screen.dart';
import 'screens/entry_mode_screen.dart';
import 'screens/exit_mode_screen.dart';
import 'screens/history_screen.dart';
import 'screens/login_screen.dart';
import 'screens/mode_hub_screen.dart';
import 'screens/result_screen.dart';
import 'screens/setup_screen.dart';
import 'state/parking_app_scope.dart';
import 'state/parking_app_state.dart';

class SmartParkingApp extends StatefulWidget {
  const SmartParkingApp({super.key});

  @override
  State<SmartParkingApp> createState() => _SmartParkingAppState();
}

class _SmartParkingAppState extends State<SmartParkingApp> {
  final ParkingAppState _appState = ParkingAppState();

  @override
  Widget build(BuildContext context) {
    return ParkingAppScope(
      notifier: _appState,
      child: MaterialApp(
        title: 'Smart Parking University',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0F766E)),
          useMaterial3: true,
        ),
        initialRoute: LoginScreen.routeName,
        routes: {
          LoginScreen.routeName: (_) => const LoginScreen(),
          SetupScreen.routeName: (_) => const SetupScreen(),
          ModeHubScreen.routeName: (_) => const ModeHubScreen(),
          DemoIotScreen.routeName: (_) => const DemoIotScreen(),
          EntryModeScreen.routeName: (_) => const EntryModeScreen(),
          ExitModeScreen.routeName: (_) => const ExitModeScreen(),
          HistoryScreen.routeName: (_) => const HistoryScreen(),
          ResultScreen.routeName: (_) => const ResultScreen(),
        },
      ),
    );
  }
}
