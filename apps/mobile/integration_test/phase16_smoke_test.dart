import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:integration_test/integration_test.dart';

import 'package:ai_personal_finance/auth/api_client.dart';
import 'package:ai_personal_finance/auth/secure_token_storage.dart';
import 'package:ai_personal_finance/main.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Phase 16 Android smoke: first frame renders', (tester) async {
    await tester.pumpWidget(const PersonalFinanceApp());
    await tester.pump(const Duration(seconds: 2));
    expect(find.text('Create an account'), findsOneWidget);
  });

  testWidgets('Phase 16 Android smoke: API health is reachable', (
    tester,
  ) async {
    await tester.pumpWidget(const MaterialApp(home: SizedBox.shrink()));
    final baseUrl = const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://10.0.2.2:8000',
    );
    final response = await http
        .get(Uri.parse('$baseUrl/health'))
        .timeout(const Duration(seconds: 10));
    expect(response.statusCode, 200, reason: response.body);
    expect(response.body, contains('ok'));
  });

  testWidgets('Phase 16 Android smoke: register and current user', (
    tester,
  ) async {
    await tester.pumpWidget(const MaterialApp(home: SizedBox.shrink()));
    final baseUrl = const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://10.0.2.2:8000',
    );
    final api = ApiClient(baseUrl: baseUrl, storage: _MemoryTokenStorage());
    final email =
        'phase16-smoke-${DateTime.now().microsecondsSinceEpoch}@example.com';
    final result = await api.register(
      email,
      'correct horse battery staple',
      'Phase 16 smoke',
    );
    final user = await api.me();
    expect(user.id, result.user.id);
    expect(user.email, email);
  });
}

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
