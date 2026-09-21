import 'package:flutter/foundation.dart';

import 'finance_repository.dart';
import 'models.dart';

class FinanceViewModel extends ChangeNotifier {
  FinanceViewModel(this.repository);

  final FinanceRepository repository;
  bool loading = false;
  String? error;
  List<AccountModel> accounts = const [];
  List<TransactionModel> transactions = const [];
  List<CategoryModel> categories = const [];
  List<BudgetModel> budgets = const [];
  List<GoalModel> goals = const [];
  List<InsightModel> insights = const [];
  List<NotificationModel> notifications = const [];
  List<RecommendationModel> recommendations = const [];
  DashboardModel? dashboard;
  var _disposed = false;

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }

  Future<void> loadCore() async {
    if (_disposed) return;
    loading = true;
    error = null;
    notifyListeners();
    try {
      final results = await Future.wait([
        repository.accounts(),
        repository.transactions(),
        repository.categories(),
        repository.budgets(),
        repository.goals(),
        repository.insights(),
        repository.notifications(),
        repository.recommendations(),
        repository.dashboard(),
      ]);
      if (_disposed) return;
      accounts = results[0] as List<AccountModel>;
      transactions = results[1] as List<TransactionModel>;
      categories = results[2] as List<CategoryModel>;
      budgets = results[3] as List<BudgetModel>;
      goals = results[4] as List<GoalModel>;
      insights = results[5] as List<InsightModel>;
      notifications = results[6] as List<NotificationModel>;
      recommendations = results[7] as List<RecommendationModel>;
      dashboard = results[8] as DashboardModel;
    } catch (exception) {
      if (_disposed) return;
      error = exception.toString();
    } finally {
      loading = false;
      if (!_disposed) notifyListeners();
    }
  }

  Future<String?> markNotificationRead(String id) async {
    try {
      final updated = await repository.markNotificationRead(id);
      notifications = notifications
          .map((item) => item.id == id ? updated : item)
          .toList();
      notifyListeners();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> updateRecommendation(
    String id,
    Future<RecommendationModel> Function(String id) action,
  ) async {
    try {
      final updated = await action(id);
      recommendations = recommendations
          .map((item) => item.id == id ? updated : item)
          .where((item) => item.status == 'ACTIVE')
          .toList();
      notifyListeners();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> addTransaction({
    required String type,
    required AccountModel account,
    required int amount,
    CategoryModel? category,
    String? categoryId,
    String? description,
  }) async {
    try {
      final targetCategoryId = category?.id ?? categoryId;
      final values = {
        'type': type,
        'account_id': account.id,
        'amount': amount,
        'currency': account.currency,
        if (targetCategoryId != null && targetCategoryId.isNotEmpty)
          'category_id': targetCategoryId,
        if (description != null && description.trim().isNotEmpty)
          'description': description.trim(),
      };
      final key = 'mobile-${DateTime.now().microsecondsSinceEpoch}';
      await repository.createTransaction(values, idempotencyKey: key);
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> editTransaction({
    required String id,
    int? amount,
    String? categoryId,
    String? description,
  }) async {
    try {
      final values = <String, dynamic>{
        if (amount != null && amount > 0) 'amount': amount,
        if (categoryId != null && categoryId.isNotEmpty) 'category_id': categoryId,
        if (description != null) 'description': description.trim(),
      };
      await repository.updateTransaction(id, values);
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> deleteTransaction(String id) async {
    try {
      await repository.deleteTransaction(id);
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> createAccount({
    required String name,
    required String type,
    required int openingBalance,
  }) async {
    try {
      await repository.createAccount({
        'name': name.trim(),
        'type': type,
        'currency': 'VND',
        'opening_balance': openingBalance,
      });
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> updateAccount(String id, String name, String type) async {
    try {
      await repository.gateway.updateAccount(id, {
        'name': name.trim(),
        'type': type,
      });
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> archiveAccount(String id) async {
    try {
      await repository.gateway.updateAccount(id, {'is_archived': true});
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> createBudget({
    required String name,
    required String categoryId,
    required int limitAmount,
    String currency = 'VND',
    String? startDate,
    String? endDate,
  }) async {
    try {
      final today = DateTime.now();
      final defaultStart = '${today.year}-${today.month.toString().padLeft(2, '0')}-01';
      final defaultEnd = '${today.year}-${today.month.toString().padLeft(2, '0')}-28';
      final values = {
        'name': name.trim(),
        'period_type': 'MONTHLY',
        'start_date': startDate ?? defaultStart,
        'end_date': endDate ?? defaultEnd,
        'total_limit': limitAmount,
        'currency': currency,
        'categories': [
          {
            'category_id': categoryId,
            'limit_amount': limitAmount,
          }
        ],
      };
      await repository.createBudget(values);
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> editBudget({
    required String id,
    required String name,
  }) async {
    try {
      await repository.updateBudget(id, {'name': name.trim()});
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> deleteBudget(String id) async {
    try {
      await repository.deleteBudget(id);
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> editGoal({
    required String id,
    String? name,
    int? targetAmount,
    String? targetDate,
    String? description,
  }) async {
    try {
      final values = <String, dynamic>{
        if (name != null && name.trim().isNotEmpty) 'name': name.trim(),
        if (targetAmount != null && targetAmount > 0) 'target_amount': targetAmount,
        if (targetDate != null && targetDate.isNotEmpty) 'target_date': targetDate,
        if (description != null) 'description': description.trim(),
      };
      await repository.updateGoal(id, values);
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> createGoal({
    required String name,
    required int targetAmount,
    required String currency,
    String? targetDate,
    int priority = 1,
    String? description,
  }) async {
    try {
      final values = <String, dynamic>{
        'name': name.trim(),
        'target_amount': targetAmount,
        'currency': currency,
        'priority': priority,
        if (targetDate != null && targetDate.isNotEmpty)
          'target_date': targetDate,
        if (description != null && description.trim().isNotEmpty)
          'description': description.trim(),
      };
      await repository.createGoal(values);
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> deleteGoal(String id) async {
    try {
      await repository.deleteGoal(id);
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> addGoalContribution({
    required String goalId,
    required int amount,
    String? accountId,
    String? note,
  }) async {
    try {
      final values = <String, dynamic>{
        'amount': amount,
        if (accountId != null && accountId.isNotEmpty) 'account_id': accountId,
        if (note != null && note.trim().isNotEmpty) 'note': note.trim(),
      };
      await repository.createGoalContribution(goalId, values);
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }

  Future<String?> markAllNotificationsRead() async {
    try {
      final unread = notifications.where((item) => item.readAt == null).toList();
      for (final notification in unread) {
        await repository.markNotificationRead(notification.id);
      }
      await loadCore();
      return null;
    } catch (exception) {
      return exception.toString();
    }
  }
}
