// ignore_for_file: avoid_print

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ai_personal_finance/auth/api_client.dart';
import 'package:ai_personal_finance/auth/secure_token_storage.dart';
import 'package:ai_personal_finance/finance/finance_home.dart';
import 'package:ai_personal_finance/main.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('critical Phase 08 user journey', (tester) async {
    _mark('A01 APP START');
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
    _mark('A02 SIGN UP SCREEN');

    await tester.tap(find.text('Create an account'));
    await tester.pumpAndSettle();
    await _enter(tester, 'Name', 'E2E User');
    await _enter(tester, 'Email', email);
    await _enter(tester, 'Password', password);
    await tester.tap(find.text('Register'));
    _mark('A03 REGISTER SUBMITTED');
    await _settle(tester, 'Home');
    _mark('A04 HOME AFTER REGISTER');

    await tester.tap(find.byTooltip('Log out'));
    await _settle(tester, 'Sign in');
    _mark('A05 LOGOUT COMPLETE');
    await _enter(tester, 'Email', email);
    await _enter(tester, 'Password', password);
    await tester.tap(find.text('Login'));
    _mark('A06 LOGIN SUBMITTED');
    await _settle(tester, 'Home');
    _mark('A07 HOME AFTER LOGIN');

    await tester.tap(find.text('Accounts').last);
    await _settle(tester, 'Accounts');
    _mark('A08 ACCOUNTS SCREEN');
    await tester.tap(find.byTooltip('Create account'));
    await tester.pumpAndSettle();
    _mark('A09 CREATE ACCOUNT DIALOG OPEN');
    await _enter(tester, 'Name', accountName);
    await _enter(tester, 'Opening balance', '100000');
    await tester.tap(find.text('Create'));
    await tester.pumpAndSettle();
    _mark('A10 ACCOUNT CREATE SUBMITTED');
    await _waitForText(tester, accountName);
    _mark('A11 ACCOUNT CREATE RESPONSE');
    _mark('A12 ACCOUNT STATE UPDATED');
    expect(find.text('100,000 VND'), findsOneWidget);
    _mark('A13 ACCOUNT LIST VISIBLE');

    await _waitForText(tester, 'Transactions');
    await tester.tap(find.byType(NavigationDestination).at(2));
    await _settle(tester, 'Transactions');
    _mark('A14 TRANSACTIONS SCREEN');
    final addTransaction = find.byTooltip('Add transaction');
    final addTransactionRect = tester.getRect(addTransaction);
    _mark(
      'A14 FAB count=${addTransaction.evaluate().length} '
      'rect=$addTransactionRect '
      'view=${tester.binding.platformDispatcher.views.first.physicalSize}',
    );
    await tester.ensureVisible(addTransaction);
    await tester.tap(addTransaction);
    await tester.pumpAndSettle();
    await tester.tap(find.text('EXPENSE').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('INCOME').last);
    await _enter(tester, 'Amount', '50000');
    await _enter(tester, 'Note', incomeNote);
    await tester.tap(find.text('Save'));
    await _settle(tester, incomeNote);
    _mark('A15 INCOME CREATED');

    await tester.tap(find.byTooltip('Add transaction'));
    await tester.pumpAndSettle();
    await _enter(tester, 'Amount', '25000');
    await _enter(tester, 'Note', expenseNote);
    await tester.tap(find.text('Save'));
    await _settle(tester, expenseNote);
    final expenseTile = find.ancestor(
      of: find.text(expenseNote),
      matching: find.byType(ListTile),
    );
    expect(expenseTile, findsOneWidget);
    expect(
      find.descendant(of: expenseTile, matching: find.text('25,000 VND')),
      findsOneWidget,
    );
    _mark('A16 EXPENSE CREATED');

    await tester.tap(find.text(expenseNote));
    await _settle(tester, 'Transaction detail');
    _mark('A17 TRANSACTION DETAIL');
    expect(
      find.descendant(
        of: find.byType(TransactionDetailScreen),
        matching: find.text('25,000 VND'),
      ),
      findsOneWidget,
    );
    await tester.pageBack();
    await _settle(tester, 'Transactions');

    await tester.tap(find.text('Home'));
    await _settle(tester, 'Home');
    expect(find.text('125,000 VND'), findsWidgets);
    expect(find.text('50,000 VND'), findsWidgets);
    expect(find.text('25,000 VND'), findsWidgets);
    _mark('A18 HOME VERIFIED');

    await tester.tap(find.text('Budget'));
    await _settle(tester, 'Budget');
    expect(find.text('No budgets yet'), findsOneWidget);
    _mark('A19 BUDGET VERIFIED');

    await tester.tap(find.text('Goals'));
    await _settle(tester, 'Goals');
    expect(find.text('No goals yet'), findsOneWidget);
    _mark('A20 GOALS VERIFIED');

    await tester.tap(find.byTooltip('Log out'));
    await _settle(tester, 'Sign in');
    expect(find.text('Home'), findsNothing);
    _mark('A21 FINAL LOGOUT');
  });
}

void _mark(String marker) => print(marker);

Future<void> _enter(WidgetTester tester, String label, String value) async {
  final field = find.widgetWithText(TextField, label);
  await tester.ensureVisible(field);
  await tester.tap(field);
  await tester.enterText(field, value);
}

Future<void> _settle(WidgetTester tester, String text) async {
  await _waitForText(tester, text);
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
