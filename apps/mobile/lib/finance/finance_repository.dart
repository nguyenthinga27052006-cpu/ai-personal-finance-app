import '../auth/api_client.dart';
import 'models.dart';

class FinanceRepository {
  const FinanceRepository(this.gateway);

  final FinanceGateway gateway;

  Future<List<AccountModel>> accounts() => gateway.accounts();
  Future<AccountModel> createAccount(Map<String, dynamic> values) =>
      gateway.createAccount(values);
  Future<List<TransactionModel>> transactions() => gateway.transactions();
  Future<TransactionModel> transaction(String id) => gateway.transaction(id);
  Future<List<CategoryModel>> categories() => gateway.categories();
  Future<List<BudgetModel>> budgets() => gateway.budgets();
  Future<BudgetModel> createBudget(Map<String, dynamic> values) =>
      gateway.createBudget(values);
  Future<BudgetModel> updateBudget(String id, Map<String, dynamic> values) =>
      gateway.updateBudget(id, values);
  Future<void> deleteBudget(String id) => gateway.deleteBudget(id);
  Future<List<GoalModel>> goals() => gateway.goals();
  Future<GoalModel> createGoal(Map<String, dynamic> values) =>
      gateway.createGoal(values);
  Future<GoalModel> updateGoal(String id, Map<String, dynamic> values) =>
      gateway.updateGoal(id, values);
  Future<void> deleteGoal(String id) => gateway.deleteGoal(id);
  Future<void> createGoalContribution(
          String goalId, Map<String, dynamic> values) =>
      gateway.createGoalContribution(goalId, values);
  Future<List<InsightModel>> insights() => gateway.insights();
  Future<List<NotificationModel>> notifications() => gateway.notifications();
  Future<NotificationModel> markNotificationRead(String id) =>
      gateway.markNotificationRead(id);
    Future<List<RecommendationModel>> recommendations() => gateway.recommendations();
    Future<RecommendationModel> acceptRecommendation(String id) =>
      gateway.acceptRecommendation(id);
    Future<RecommendationModel> dismissRecommendation(String id) =>
      gateway.dismissRecommendation(id);
    Future<RecommendationModel> giveRecommendationFeedback(String id, String feedback) =>
      gateway.giveRecommendationFeedback(id, feedback);
  Future<DashboardModel> dashboard() => gateway.dashboard();

  Future<void> createTransaction(
    Map<String, dynamic> values, {
    required String idempotencyKey,
  }) async {
    await gateway.createTransaction(values, idempotencyKey: idempotencyKey);
  }

  Future<void> createTransfer(
    Map<String, dynamic> values, {
    required String idempotencyKey,
  }) async {
    await gateway.createTransfer(values, idempotencyKey: idempotencyKey);
  }

  Future<TransactionModel> updateTransaction(String id, Map<String, dynamic> values) =>
      gateway.updateTransaction(id, values);

  Future<void> deleteTransaction(String id) => gateway.deleteTransaction(id);
}
