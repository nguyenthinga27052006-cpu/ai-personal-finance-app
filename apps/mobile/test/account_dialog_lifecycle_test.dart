import 'package:ai_personal_finance/auth/api_client.dart';
import 'package:ai_personal_finance/finance/components.dart';
import 'package:ai_personal_finance/finance/finance_home.dart';
import 'package:ai_personal_finance/finance/models.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeFinanceGateway implements FinanceGateway {
  var account = const AccountModel(
    id: 'a1',
    name: 'Checking',
    type: 'CASH',
    currency: 'VND',
    openingBalance: 0,
    currentBalance: 0,
    status: 'ACTIVE',
    isArchived: false,
  );
  @override
  Future<List<AccountModel>> accounts() async =>
      account.isArchived ? const [] : [account];
  @override
  Future<AccountModel> createAccount(Map<String, dynamic> values) async =>
      account = AccountModel(
        id: 'a1',
        name: values['name'] as String,
        type: values['type'] as String,
        currency: 'VND',
        openingBalance: values['opening_balance'] as int,
        currentBalance: values['opening_balance'] as int,
        status: 'ACTIVE',
        isArchived: false,
      );
  @override
  Future<AccountModel> updateAccount(
    String id,
    Map<String, dynamic> values,
  ) async => account = AccountModel(
    id: id,
    name: values['name'] as String? ?? account.name,
    type: values['type'] as String? ?? account.type,
    currency: account.currency,
    openingBalance: account.openingBalance,
    currentBalance: account.currentBalance,
    status: 'ACTIVE',
    isArchived: values['is_archived'] as bool? ?? account.isArchived,
  );
  @override
  Future<List<CategoryModel>> categories() async => const [];
  @override
  Future<List<TransactionModel>> transactions() async => const [];
  @override
  Future<TransactionModel> transaction(String id) => throw UnimplementedError();
  @override
  Future<TransactionModel> createTransaction(
    Map<String, dynamic> values, {
    String? idempotencyKey,
  }) => throw UnimplementedError();
  @override
  Future<TransactionModel> createTransfer(
    Map<String, dynamic> values, {
    String? idempotencyKey,
  }) => throw UnimplementedError();
  @override
  Future<TransactionModel> updateTransaction(String id, Map<String, dynamic> values) => throw UnimplementedError();
  @override
  Future<void> deleteTransaction(String id) async {}
  @override
  Future<List<BudgetModel>> budgets() async => const [];
  @override
  Future<BudgetModel> createBudget(Map<String, dynamic> values) => throw UnimplementedError();
  @override
  Future<BudgetModel> updateBudget(String id, Map<String, dynamic> values) => throw UnimplementedError();
  @override
  Future<void> deleteBudget(String id) async {}
  @override
  Future<List<GoalModel>> goals() async => const [];
  @override
  Future<GoalModel> createGoal(Map<String, dynamic> values) => throw UnimplementedError();
  @override
  Future<GoalModel> updateGoal(String id, Map<String, dynamic> values) => throw UnimplementedError();
  @override
  Future<void> deleteGoal(String id) => throw UnimplementedError();
  @override
  Future<void> createGoalContribution(String goalId, Map<String, dynamic> values) => throw UnimplementedError();
  @override
  Future<List<InsightModel>> insights({DateTime? start, DateTime? end}) async =>
      const [];
    @override
    Future<List<NotificationModel>> notifications({bool unreadOnly = false}) async =>
      const [];
    @override
    Future<NotificationModel> markNotificationRead(String id) =>
      throw UnimplementedError();
      @override
      Future<List<RecommendationModel>> recommendations({DateTime? start, DateTime? end}) async =>
        const [];
      @override
      Future<RecommendationModel> acceptRecommendation(String id) =>
        throw UnimplementedError();
      @override
      Future<RecommendationModel> dismissRecommendation(String id) =>
        throw UnimplementedError();
      @override
      Future<RecommendationModel> giveRecommendationFeedback(String id, String feedback) =>
        throw UnimplementedError();
  @override
  Future<Map<String, dynamic>> scanReceipt(String base64Image) => throw UnimplementedError();
  @override
  Future<Map<String, dynamic>> confirmReceipt(Map<String, dynamic> data) => throw UnimplementedError();
  @override
  Future<DashboardModel> dashboard() async => DashboardModel(
    totalBalance: 0,
    income: 0,
    expense: 0,
    saving: 0,
    savingRate: 0,
    periodStart: DateTime(2026, 9, 1),
    periodEnd: DateTime(2026, 9, 30),
  );
}

void main() {
  testWidgets('account dialog can reopen, create, edit and archive safely', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    final gateway = FakeFinanceGateway();
    await tester.pumpWidget(
      MaterialApp(
        home: FinanceHome(
          gateway: gateway,
          email: 'test@example.com',
          onLogout: () async {},
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 300));

    (tester.widget(find.byType(NavigationRail)) as NavigationRail).onDestinationSelected!(1);
    await tester.pumpAndSettle();
    await tester.tap(find.byType(FloatingActionButton), warnIfMissed: false);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(find.byType(AccountDialog), findsOneWidget);

    await tester.enterText(
      find.descendant(
        of: find.byType(AccountDialog),
        matching: find.byType(TextField),
      ).first,
      'First',
    );
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(find.byType(AccountDialog), findsNothing);

    await tester.tap(find.byType(FloatingActionButton), warnIfMissed: false);
    await tester.pumpAndSettle();
    expect(find.byType(AccountDialog), findsOneWidget);

    await tester.enterText(
      find.descendant(
        of: find.byType(AccountDialog),
        matching: find.byType(TextField),
      ).first,
      'Created',
    );
    await tester.enterText(
      find.descendant(
        of: find.byType(AccountDialog),
        matching: find.byType(TextField),
      ).at(1),
      '1000',
    );
    await tester.tap(find.text('Create'));
    for (var i = 0; i < 10; i++) {
      await tester.pump();
    }
    await tester.pumpAndSettle();
    expect(find.byType(AccountDialog), findsNothing);

    final dynamic state = tester.state(find.byType(FinanceHome));
    expect(find.text('Created'), findsOneWidget);

    await tester.tap(find.text('Created'));
    for (var i = 0; i < 10; i++) {
      await tester.pump();
    }
    await tester.pumpAndSettle();
    await tester.enterText(
      find.descendant(
        of: find.byType(AccountDialog),
        matching: find.byType(TextField),
      ).first,
      'Edited',
    );
    await tester.tap(find.text('Save'));
    for (var i = 0; i < 10; i++) {
      await tester.pump();
    }
    await tester.pumpAndSettle();
    expect(find.text('Edited'), findsOneWidget);

    await tester.tap(find.text('Edited'));
    for (var i = 0; i < 10; i++) {
      await tester.pump();
    }
    await tester.pumpAndSettle();
    await tester.tap(find.text('Archive'));
    for (var i = 0; i < 10; i++) {
      await tester.pump();
    }
    await tester.pumpAndSettle();
    expect(find.byType(EmptyState), findsOneWidget);
  });
}
