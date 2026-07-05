import 'package:flutter/foundation.dart';

import '../models/app_models.dart';

class ParkingAppState extends ChangeNotifier {
  OperatorSession? _session;
  AccessPointSelection? _selection;
  final List<HistoryItem> _history = [];

  OperatorSession? get session => _session;
  AccessPointSelection? get selection => _selection;
  List<HistoryItem> get history => List.unmodifiable(_history.reversed);

  bool get isLoggedIn => _session != null;

  void login({required String username, required String displayName}) {
    _session = OperatorSession(
      username: username,
      displayName: displayName,
      loggedAt: DateTime.now(),
    );
    notifyListeners();
  }

  void logout() {
    _session = null;
    _selection = null;
    _history.clear();
    notifyListeners();
  }

  void setSelection(AccessPointSelection selection) {
    _selection = selection;
    notifyListeners();
  }

  void addHistory(HistoryItem item) {
    _history.add(item);
    notifyListeners();
  }
}
