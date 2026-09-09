import 'package:ai_personal_finance/auth/api_client.dart';
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
  Future<List<BudgetModel>> budgets() async => const [];
  @override
  Future<List<GoalModel>> goals() async => const [];
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
    await tester.pumpAndSettle();

    await tester.tap(find.text('Accounts').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Create account'));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextField, 'Name'), 'First');
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Create account'));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextField, 'Name'), 'Created');
    await tester.enterText(
      find.widgetWithText(TextField, 'Opening balance'),
      '1000',
    );
    await tester.tap(find.text('Create'));
    await tester.pumpAndSettle();
    expect(find.text('Created'), findsOneWidget);

    await tester.tap(find.text('Created'));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextField, 'Name'), 'Edited');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(find.text('Edited'), findsOneWidget);

    await tester.tap(find.text('Edited'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Archive'));
    await tester.pumpAndSettle();
    expect(find.text('No accounts yet'), findsOneWidget);
  });
}
