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
    String? description,
  }) async {
    try {
      final values = {
        'type': type,
        'account_id': account.id,
        'amount': amount,
        'currency': account.currency,
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
}
