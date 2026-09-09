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

  testWidgets('Phase 16 State Trace: createAccount → loadCore → UI', (tester) async {
    // STEP 1: Create account via API
    print('\n=== STEP 1: Create account via API ===');
    final fixture = await _createFixture();
    final accountResponse = await _post(fixture, '/api/v1/accounts', {
      'name': 'StateTrace Account',
      'type': 'BANK',
      'balance': '50000',
      'currency': 'VND',
    });
    final accountId = accountResponse['id'] as String;
    final accountName = accountResponse['name'] as String;
    print('✓ Account created via API:');
    print('  - ID: $accountId');
    print('  - Name: $accountName');

    // STEP 2: Verify account exists on backend
    print('\n=== STEP 2: Verify account on backend ===');
    final listResponse = await http.get(
      Uri.parse('${fixture.baseUrl}/api/v1/accounts'),
      headers: {
        'Authorization': 'Bearer ${(await fixture.storage.read()).$1}',
      },
    );
    expect(listResponse.statusCode, 200);
    final listData = jsonDecode(listResponse.body) as dynamic;
    final accounts = (listData is List) ? listData : (listData is Map ? (listData['items'] ?? []) as List : []);
    print('✓ Backend GET /accounts returned ${accounts.length} account(s):');
    for (final acc in accounts) {
      print('  - ${acc['name']} (ID: ${acc['id']})');
    }
    expect(
      accounts.any((a) => a['id'] == accountId),
      isTrue,
      reason: 'Created account not in backend response',
    );

    // STEP 3: Pump app (triggers loadCore)
    print('\n=== STEP 3: Pump app (triggers loadCore) ===');
    await tester.pumpWidget(PersonalFinanceApp(api: fixture.api));
    await tester.pumpAndSettle(const Duration(milliseconds: 250));
    print('✓ App pumped, calling pumpAndSettle...');

    // STEP 4: Wait for home, log all Text widgets
    print('\n=== STEP 4: After loadCore, inspect UI state ===');
    await tester.pump(const Duration(seconds: 2));
    final allText = find.byType(Text).evaluate()
        .map((e) => ((e.widget as Text).data ?? '').trim())
        .where((t) => t.isNotEmpty)
        .toList();
    print('✓ All Text widgets on screen (${allText.length} total):');
    for (final t in allText.take(30)) {
      print('  - "$t"');
    }
    if (allText.length > 30) {
      print('  ... and ${allText.length - 30} more');
    }

    // Check for error state
    print('\n=== STEP 5: Check ViewModel state ===');
    if (allText.contains('Retry') || allText.any((t) => t.contains('error'))) {
      print('⚠️  ERROR STATE DETECTED in UI');
      print('  Text widgets containing "error" or "Retry":');
      for (final t in allText.where((t) => t.toLowerCase().contains('error') || t.contains('Retry'))) {
        print('    - "$t"');
      }
    } else if (allText.contains('Home')) {
      print('✓ App loaded (found "Home" widget)');
    } else {
      print('⚠️  UNKNOWN STATE - "Home" not found');
    }

    // STEP 6: Navigate to Accounts and log state
    print('\n=== STEP 6: Navigate to Accounts tab ===');
    if (find.text('Accounts').evaluate().isNotEmpty) {
      await tester.tap(find.text('Accounts').last);
      await tester.pumpAndSettle(const Duration(milliseconds: 250));
      print('✓ Tapped Accounts tab');

      // Log all Text widgets after navigation
      final accountsPageText = find.byType(Text).evaluate()
          .map((e) => ((e.widget as Text).data ?? '').trim())
          .where((t) => t.isNotEmpty)
          .toList();
      print('✓ Text widgets on Accounts page (${accountsPageText.length} total):');
      for (final t in accountsPageText.take(20)) {
        print('  - "$t"');
      }
      if (accountsPageText.length > 20) {
        print('  ... and ${accountsPageText.length - 20} more');
      }

      // STEP 7: Check if created account is visible
      print('\n=== STEP 7: Check for created account in UI ===');
      if (accountsPageText.contains(accountName)) {
        print('✓ FOUND account in UI: "$accountName"');
      } else {
        print('✗ MISSING account in UI: "$accountName"');
        print('  Expected to find: "$accountName"');
        print('  Account text widgets on page:');
        for (final t in accountsPageText) {
          if (!['Accounts', 'Create account', 'Type', 'Balance', 'Actions'].contains(t)) {
            print('    - "$t"');
          }
        }
      }
    } else {
      print('⚠️  CANNOT TAP ACCOUNTS - "Accounts" tab not found');
    }

    print('\n=== STATE TRACE COMPLETE ===\n');
  });
}

class _MemoryTokenStorage extends SecureTokenStorage {
  String? accessToken;
  String? refreshToken;

  @override
  Future<(String?, String?)> read() async => (accessToken, refreshToken);

  @override
  Future<void> write({required String accessToken, required String refreshToken}) async {
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
  final email = 'statetrace-${DateTime.now().microsecondsSinceEpoch}@example.com';
  await api.register(email, 'correct horse battery staple', 'State Trace');
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
    reason: 'API Error: ${response.statusCode} ${response.body}',
  );
  return jsonDecode(response.body) as Map<String, dynamic>;
}
