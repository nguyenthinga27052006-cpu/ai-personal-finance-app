import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ai_personal_finance/auth/api_client.dart';
import 'package:ai_personal_finance/auth/secure_token_storage.dart';
import 'package:ai_personal_finance/main.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('critical Phase 08 user journey', (tester) async {
    final email = 'e2e-${DateTime.now().microsecondsSinceEpoch}@example.com';
    const password = 'correct horse battery staple';
    const accountName = 'E2E Checking';
    const incomeNote = 'E2E income';
    const expenseNote = 'E2E expense';

    final baseUrl = const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://10.0.2.2:8000',
    );
    await SecureTokenStorage().clear();
    await tester.pumpWidget(
      PersonalFinanceApp(api: ApiClient(baseUrl: baseUrl)),
    );
    await _settle(tester, 'Create an account');

    await tester.tap(find.text('Create an account'));
    await tester.pumpAndSettle();
    await _enter(tester, 'Name', 'E2E User');
    await _enter(tester, 'Email', email);
    await _enter(tester, 'Password', password);
    await tester.tap(find.text('Register'));
    await _settle(tester, 'Home');

    await tester.tap(find.byTooltip('Log out'));
    await _settle(tester, 'Sign in');
    await _enter(tester, 'Email', email);
    await _enter(tester, 'Password', password);
    await tester.tap(find.text('Login'));
    await _settle(tester, 'Home');

    await tester.tap(find.text('Accounts').last);
    await _settle(tester, 'Accounts');
    await tester.tap(find.byTooltip('Create account'));
    await tester.pumpAndSettle();
    await _enter(tester, 'Name', accountName);
    await _enter(tester, 'Opening balance', '100000');
    await tester.tap(find.text('Create'));
    // Explicitly wait for the dialog close animation and state update to complete
    await tester.pumpAndSettle(const Duration(milliseconds: 250));
    await tester.pump(const Duration(seconds: 2));
    await _waitForText(tester, accountName);
    expect(find.text('100,000 VND'), findsOneWidget);

    await _waitForText(tester, 'Transactions');
    await tester.tap(find.byType(NavigationDestination).at(2));
    await _settle(tester, 'Transactions');
    await tester.tap(find.byTooltip('Add transaction'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('EXPENSE').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('INCOME').last);
    await _enter(tester, 'Amount', '50000');
    await _enter(tester, 'Note', incomeNote);
    await tester.tap(find.text('Save'));
    // Explicitly wait for the dialog close animation and state update to complete
    await tester.pumpAndSettle(const Duration(milliseconds: 250));
    await tester.pump(const Duration(seconds: 1));
    await _settle(tester, incomeNote);

    await tester.tap(find.byTooltip('Add transaction'));
    await tester.pumpAndSettle();
    await _enter(tester, 'Amount', '25000');
    await _enter(tester, 'Note', expenseNote);
    await tester.tap(find.text('Save'));
    // Explicitly wait for the dialog close animation and state update to complete
    await tester.pumpAndSettle(const Duration(milliseconds: 250));
    await tester.pump(const Duration(seconds: 1));
    await _settle(tester, expenseNote);
    expect(find.text('25,000 VND'), findsOneWidget);

    await tester.tap(find.text(expenseNote));
    await _settle(tester, 'Transaction detail');
    expect(find.text('25,000 VND'), findsOneWidget);
    await tester.pageBack();
    await _settle(tester, 'Transactions');

    await tester.tap(find.text('Home'));
    await _settle(tester, 'Home');
    expect(find.text('125,000 VND'), findsWidgets);
    expect(find.text('50,000 VND'), findsWidgets);
    expect(find.text('25,000 VND'), findsWidgets);

    await tester.tap(find.text('Budget'));
    await _settle(tester, 'Budget');
    expect(find.text('No budgets yet'), findsOneWidget);

    await tester.tap(find.text('Goals'));
    await _settle(tester, 'Goals');
    expect(find.text('No goals yet'), findsOneWidget);

    await tester.tap(find.byTooltip('Log out'));
    await _settle(tester, 'Sign in');
    expect(find.text('Home'), findsNothing);
  });
}

Future<void> _enter(WidgetTester tester, String label, String value) async {
  final field = find.widgetWithText(TextField, label);
  await tester.tap(field);
  await tester.enterText(field, value);
}

Future<void> _settle(WidgetTester tester, String text) async {
  await tester.pumpAndSettle(const Duration(milliseconds: 250));
  await tester.pump(const Duration(seconds: 1));
  expect(find.text(text), findsWidgets, reason: 'Expected screen state: $text');
}

Future<void> _waitForText(WidgetTester tester, String text) async {
  for (var attempt = 0; attempt < 40; attempt++) {
    await tester.pump(const Duration(milliseconds: 250));
    if (find.text(text).evaluate().isNotEmpty) return;
  }
  expect(
    find.text(text),
    findsWidgets,
    reason: 'Expected authoritative state: $text',
  );
}
