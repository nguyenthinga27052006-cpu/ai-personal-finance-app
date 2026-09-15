import 'package:ai_personal_finance/finance/components.dart';
import 'package:ai_personal_finance/finance/models.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const account = AccountModel(
  id: 'account',
  name: 'Checking',
  type: 'BANK',
  currency: 'VND',
  openingBalance: 1000000,
  currentBalance: 1250000,
  status: 'ACTIVE',
  isArchived: false,
);

const budget = BudgetModel(
  id: 'budget',
  name: 'Monthly',
  limit: 5000000,
  spent: 1750000,
  remaining: 3250000,
  utilization: 0.35,
  risk: 'SAFE',
  projectedSpending: 4000000,
  currency: 'VND',
);

const goal = GoalModel(
  id: 'goal',
  name: 'Emergency fund',
  target: 10000000,
  current: 2500000,
  remaining: 7500000,
  progress: 0.25,
  requiredMonthly: 1000000,
  forecast: 'ON_TRACK',
  currency: 'VND',
);

void main() {
  test('decodes API numeric strings for budget and goal calculations', () {
    final decodedBudget = BudgetModel.fromJson({
      'id': 'budget-string',
      'name': 'Monthly',
      'total_limit': 10000,
      'currency': 'VND',
      'calculation': {
        'spent': 9000,
        'remaining': 1000,
        'utilization': '0.9',
        'risk': 'DANGER',
        'projected_spending': 12000,
      },
    });
    final decodedGoal = GoalModel.fromJson({
      'id': 'goal-string',
      'name': 'Goal',
      'target_amount': 10000,
      'currency': 'VND',
      'calculation': {
        'current': 4000,
        'remaining': 6000,
        'progress': '0.4',
        'required_monthly_saving': 1000,
        'forecast': 'ON_TRACK',
      },
    });

    expect(decodedBudget.utilization, 0.9);
    expect(decodedGoal.progress, 0.4);

    // Also test InsightModel with both num and string confidence
    final insightWithNum = InsightModel.fromJson({
      'id': 'insight-num',
      'type': 'SPENDING',
      'title': 'Test',
      'description': 'Test insight',
      'severity': 'HIGH',
      'confidence': 0.85,
      'period_start': '2024-01-01T00:00:00',
      'period_end': '2024-01-31T23:59:59',
      'source': 'ML',
      'source_metric': 'spending_pattern',
      'expires_at': '2024-02-01T00:00:00',
    });
    final insightWithString = InsightModel.fromJson({
      'id': 'insight-string',
      'type': 'SPENDING',
      'title': 'Test',
      'description': 'Test insight',
      'severity': 'HIGH',
      'confidence': '0.85',
      'period_start': '2024-01-01T00:00:00',
      'period_end': '2024-01-31T23:59:59',
      'source': 'ML',
      'source_metric': 'spending_pattern',
      'expires_at': '2024-02-01T00:00:00',
    });
    expect(insightWithNum.confidence, 0.85);
    expect(insightWithString.confidence, 0.85);
  });

  testWidgets('renders the backend account balance', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: BalanceCard(account: account)),
      ),
    );
    expect(find.text('1,250,000 VND'), findsOneWidget);
  });

  testWidgets('renders backend budget values and risk', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: BudgetProgress(budget: budget)),
      ),
    );
    expect(find.text('1,750,000 VND'), findsOneWidget);
    expect(find.text('35% · SAFE'), findsOneWidget);
    expect(find.text('Còn lại: 3,250,000 VND'), findsOneWidget);
  });

  testWidgets('renders backend goal progress and remaining amount', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ListTile(
            title: Text(goal.name),
            subtitle: Text('Remaining: ${goal.remaining} ${goal.currency}'),
            trailing: Text('${(goal.progress * 100).toStringAsFixed(0)}%'),
          ),
        ),
      ),
    );
    expect(find.text('Remaining: 7500000 VND'), findsOneWidget);
    expect(find.text('25%'), findsOneWidget);
  });

  testWidgets('renders backend error state without changing financial values', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: ErrorState(message: 'transaction_validation_error'),
        ),
      ),
    );
    expect(find.text('transaction_validation_error'), findsOneWidget);
    expect(find.text('1,250,000 VND'), findsNothing);
  });
}
