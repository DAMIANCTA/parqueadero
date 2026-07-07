import 'package:flutter_test/flutter_test.dart';

import 'package:smart_parking_university_mobile/app.dart';

void main() {
  testWidgets('loads login screen', (WidgetTester tester) async {
    await tester.pumpWidget(const SmartParkingApp());

    expect(find.text('Smart Parking University'), findsOneWidget);
    expect(find.text('Entrar'), findsOneWidget);
  });
}
