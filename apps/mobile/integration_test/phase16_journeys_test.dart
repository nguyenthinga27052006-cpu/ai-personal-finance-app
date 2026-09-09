import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:integration_test/integration_test.dart';

import 'package:ai_personal_finance/auth/api_client.dart';
import 'package:ai_personal_finance/auth/secure_token_storage.dart';
import 'package:ai_personal_finance/main.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Phase 16 Journey B: budget expense alert', (tester) async {
    final fixture = await _createFixture();
    final budget = await _post(fixture, '/api/v1/budgets', {
      'name': 'Phase 16 Budget',
      'start_date': '2026-09-01',
      'end_date': '2026-09-30',
      'total_limit': 10000,
      'currency': 'VND',
    });

    await _pumpAuthenticatedApp(tester, fixture.api);
    await _waitForText(tester, 'Home');
    await tester.tap(find.text('Accounts').last);
    await _waitForText(tester, 'Accounts');
    await tester.tap(find.byTooltip('Create account'));
    await tester.pumpAndSettle();
    await _enter(tester, 'Name', 'Phase 16 Budget account');
    await _enter(tester, 'Opening balance', '100000');
    await tester.tap(find.text('Create'));
    print(
      'PHASE16_JOURNEY_B_TEXTS ${find.byType(Text).evaluate().map((element) => (element.widget as Text).data).whereType<String>().toList()}',
    );
    await _waitForText(tester, 'Phase 16 Budget account');
    await tester.tap(find.text('Transactions').last);
    await _waitForText(tester, 'Transactions');
    expect(find.widgetWithText(AppBar, 'Transactions'), findsOneWidget);
    expect(find.byType(FloatingActionButton), findsOneWidget);
    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();
    await _waitForText(tester, 'Add transaction');
    await _enter(tester, 'Amount', '9000');
    await _enter(tester, 'Note', 'Phase 16 budget expense');
    await tester.tap(find.text('Save'));
    await _waitForText(tester, 'Phase 16 budget expense');

    final workerToken = const String.fromEnvironment(
      'NOTIFICATION_WORKER_TOKEN',
    );
    expect(
      workerToken,
      isNotEmpty,
      reason: 'Pass the local worker token to evaluate alerts.',
    );
    final evaluation = await http.post(
      Uri.parse('${fixture.baseUrl}/api/v1/internal/notifications/evaluate'),
      headers: {'X-Worker-Token': workerToken},
    );
    print('B01 EVALUATION status=${evaluation.statusCode} body=${evaluation.body}');
    expect(evaluation.statusCode, 200);
    expect(int.parse(evaluation.body), greaterThan(0));

    final notifications = await fixture.api.notifications();
    print(
      'B02 API notifications count=${notifications.length} '
      'types=${notifications.map((item) => item.type).toList()}',
    );
    expect(notifications, isNotEmpty);
    expect(
      notifications.any((item) => item.type == 'BUDGET_THRESHOLD'),
      isTrue,
    );
    expect(notifications.every((item) => item.id.isNotEmpty), isTrue);
    expect(budget['id'], isNotEmpty);

    await _pumpAuthenticatedApp(tester, fixture.api);
    await _waitForText(tester, 'Home');
    await tester.tap(find.text('Notifications').last);
    await _waitForText(tester, 'Notifications');
    print(
      'B03 UI notification titles=${find.byType(Text).evaluate().map((element) => (element.widget as Text).data).whereType<String>().toList()}',
    );
    expect(find.text(notifications.first.title), findsWidgets);
  });

  testWidgets('Phase 16 Journey C: goal contribution progress', (tester) async {
    final fixture = await _createFixture();
    final goal = await _post(fixture, '/api/v1/goals', {
      'name': 'Phase 16 Goal',
      'target_amount': 10000,
      'currency': 'VND',
      'target_date': '2026-12-31',
    });
    await _post(fixture, '/api/v1/goals/${goal['id']}/contributions', {
      'amount': 4000,
    });

    final goals = await fixture.api.goals();
    final loadedGoal = goals.singleWhere((item) => item.id == goal['id']);
    expect(loadedGoal.current, 4000);
    expect(loadedGoal.remaining, 6000);
    expect(loadedGoal.progress, 0.4);

    await _pumpAuthenticatedApp(tester, fixture.api);
    await _waitForText(tester, 'Home');
    await tester.tap(find.text('Goals').last);
    await _waitForText(tester, 'Goals');
    expect(find.text('Phase 16 Goal'), findsOneWidget);
    expect(find.text('Remaining: 6000 VND'), findsOneWidget);
    expect(find.text('40%'), findsOneWidget);
  });

  testWidgets('Phase 16 Journey D: AI query tool answer', (tester) async {
    _markD('D01 APP START');
    final fixture = await _createFixture();
    final account = await fixture.api.createAccount({
      'name': 'Phase 16 AI account',
      'type': 'BANK',
      'currency': 'VND',
      'opening_balance': 100000,
    });
    await fixture.api.createTransaction(
      {
        'type': 'EXPENSE',
        'account_id': account.id,
        'amount': 5000,
        'currency': 'VND',
        'transaction_date': '2026-09-03T12:00:00+00:00',
      },
      idempotencyKey: 'phase16-ai-expense',
    );
    final rawResponse = await _post(fixture, '/api/v1/ai/query', {
      'question': 'How much did I spend this month?',
      'currency': 'VND',
    });
    _markD('D02 API RESPONSE RECEIVED status=${rawResponse['status']}');
    expect(rawResponse['intent'], 'monthly_expense');
    expect(rawResponse['tool'], 'get_monthly_expense');
    expect(rawResponse['source'], 'analytics.service');
    expect((rawResponse['answer'] as String).isNotEmpty, isTrue);

    final unsupported = await _post(fixture, '/api/v1/ai/query', {
      'question': 'Recommend a stock to buy',
      'currency': 'VND',
    });
    expect(unsupported['status'], 'UNSUPPORTED_REQUEST');
    expect(unsupported['tool'], isNull);

    await _pumpAuthenticatedApp(tester, fixture.api);
    await _waitForText(tester, 'Home');
    _markD('D03 AUTH COMPLETE');
    await tester.tap(find.byType(NavigationDestination).at(8));
    _markD(
      'D04 AI TAP COMPLETE appBar=${find.widgetWithText(AppBar, 'AI Assistant').evaluate().length} '
      'home=${find.text('Home').evaluate().length} ai=${find.text('AI').evaluate().length}',
    );
    await _waitForText(tester, 'Ask your finances');
    _markD('D04 AI SCREEN OPEN');
    final question = find.widgetWithText(TextField, 'Ask a financial question');
    await tester.tap(question);
    await tester.enterText(question, 'How much did I spend this month?');
    await tester.tap(find.byTooltip('Ask'));
    _markD('D05 REQUEST SUBMITTED');
    _markD('D06 SUCCESS EXPECTATION START expected=${rawResponse['status']}');
    await _waitForText(tester, rawResponse['status'] as String);
    _markD('D07 SUCCESS VISIBLE');
    expect(find.text(rawResponse['answer'] as String), findsOneWidget);
    expect(find.text('Source: analytics.service'), findsOneWidget);
  });
}

void _markD(String marker) => print(marker);

class _MemoryTokenStorage implements TokenStorage {
  String? accessToken;
  String? refreshToken;

  @override
  Future<(String?, String?)> read() async => (accessToken, refreshToken);

  @override
  Future<void> write({
    required String accessToken,
    required String refreshToken,
  }) async {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
  }

  @override
  Future<void> clear() async {
    accessToken = null;
    refreshToken = null;
  }
}

class _Fixture {
  _Fixture(this.baseUrl, this.storage, this.api);

  final String baseUrl;
  final _MemoryTokenStorage storage;
  final ApiClient api;
}

Future<_Fixture> _createFixture() async {
  final baseUrl = const String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
  final storage = _MemoryTokenStorage();
  final api = ApiClient(baseUrl: baseUrl, storage: storage);
  final email = 'phase16-${DateTime.now().microsecondsSinceEpoch}@example.com';
  await api.register(email, 'correct horse battery staple', 'Phase 16 E2E');
  return _Fixture(baseUrl, storage, api);
}

Future<Map<String, dynamic>> _post(
  _Fixture fixture,
  String path,
  Map<String, dynamic> body,
) async {
  final (accessToken, _) = await fixture.storage.read();
  final response = await http.post(
    Uri.parse('${fixture.baseUrl}$path'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $accessToken',
    },
    body: jsonEncode(body),
  );
  expect(
    response.statusCode,
    inInclusiveRange(200, 299),
    reason: response.body,
  );
  return jsonDecode(response.body) as Map<String, dynamic>;
}

Future<void> _pumpAuthenticatedApp(WidgetTester tester, ApiClient api) async {
  await tester.pumpWidget(PersonalFinanceApp(api: api));
  await tester.pumpAndSettle(const Duration(milliseconds: 250));
  await tester.pump(const Duration(seconds: 2));
}

Future<void> _enter(WidgetTester tester, String label, String value) async {
  final field = find.widgetWithText(TextField, label);
  await tester.tap(field);
  await tester.enterText(field, value);
}

Future<void> _waitForText(WidgetTester tester, String text) async {
  for (var attempt = 0; attempt < 40; attempt++) {
    await tester.pump(const Duration(milliseconds: 250));
    if (find.text(text).evaluate().isNotEmpty) return;
  }
  if (text == 'SUCCESS') {
    _markD(
      'D08 timeout states success=${find.text('SUCCESS').evaluate().isNotEmpty} '
      'error=${find.text('Provider or network error').evaluate().isNotEmpty} '
      'ready=${find.text('Ready').evaluate().isNotEmpty} '
      'loading=${find.byType(CircularProgressIndicator).evaluate().isNotEmpty}',
    );
  }
  expect(find.text(text), findsWidgets, reason: 'Expected E2E state: $text');
}
