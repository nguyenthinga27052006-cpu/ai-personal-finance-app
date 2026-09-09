import 'package:ai_personal_finance/auth/api_client.dart';
import 'package:ai_personal_finance/finance/finance_repository.dart';
import 'package:ai_personal_finance/finance/finance_view_model.dart';
import 'package:ai_personal_finance/finance/models.dart';
import 'package:flutter_test/flutter_test.dart';

class _AccountGateway implements FinanceGateway {
  final List<AccountModel> _accounts = [];

  @override
  Future<List<AccountModel>> accounts() async => List.of(_accounts);

  @override
  Future<AccountModel> createAccount(Map<String, dynamic> values) async {
    final account = AccountModel(
      id: 'created-account',
      name: values['name'] as String,
      type: values['type'] as String,
      currency: values['currency'] as String,
      openingBalance: values['opening_balance'] as int,
      currentBalance: values['opening_balance'] as int,
      status: 'ACTIVE',
      isArchived: false,
    );
    _accounts.add(account);
    return account;
  }

  @override
  Future<AccountModel> updateAccount(String id, Map<String, dynamic> values) =>
      throw UnimplementedError();

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
  Future<List<RecommendationModel>> recommendations({
    DateTime? start,
    DateTime? end,
  }) async => const [];

  @override
  Future<RecommendationModel> acceptRecommendation(String id) =>
      throw UnimplementedError();

  @override
  Future<RecommendationModel> dismissRecommendation(String id) =>
      throw UnimplementedError();

  @override
  Future<RecommendationModel> giveRecommendationFeedback(
    String id,
    String feedback,
  ) => throw UnimplementedError();

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
  test('createAccount stores the created account in application state', () async {
    final viewModel = FinanceViewModel(FinanceRepository(_AccountGateway()));

    final error = await viewModel.createAccount(
      name: 'E2E Checking',
      type: 'CASH',
      openingBalance: 100000,
    );

    expect(error, isNull);
    expect(viewModel.accounts, hasLength(1));
    expect(viewModel.accounts.single.name, 'E2E Checking');
  });
}