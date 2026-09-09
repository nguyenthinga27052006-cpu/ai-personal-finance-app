import 'package:ai_personal_finance/ai/ai_screen.dart';
import 'package:ai_personal_finance/ai/models.dart';
import 'package:ai_personal_finance/auth/api_client.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeAIGateway implements AIGateway {
  @override
  Future<AIQueryResult> query(String question) async => const AIQueryResult(
    status: 'SUCCESS',
    answer: 'This month you spent 5000 VND.',
    source: 'analytics.service',
  );
}

void main() {
  testWidgets('AI success response reaches the success result card', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(home: Scaffold(body: AIScreen(gateway: _FakeAIGateway()))),
    );

    final question = find.widgetWithText(TextField, 'Ask a financial question');
    await tester.enterText(question, 'How much did I spend this month?');
    await tester.tap(find.byTooltip('Ask'));
    await tester.pumpAndSettle();

    expect(find.text('SUCCESS'), findsOneWidget);
    expect(find.text('This month you spent 5000 VND.'), findsOneWidget);
    expect(find.text('Source: analytics.service'), findsOneWidget);
  });
}