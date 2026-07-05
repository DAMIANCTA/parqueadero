import 'package:flutter/material.dart';

import 'parking_app_state.dart';

class ParkingAppScope extends InheritedNotifier<ParkingAppState> {
  const ParkingAppScope({
    super.key,
    required ParkingAppState notifier,
    required super.child,
  }) : super(notifier: notifier);

  static ParkingAppState of(BuildContext context) {
    final scope = context.dependOnInheritedWidgetOfExactType<ParkingAppScope>();
    assert(scope != null, 'ParkingAppScope not found in context');
    return scope!.notifier!;
  }
}
