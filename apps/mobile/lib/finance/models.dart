class AccountModel {
  const AccountModel({
    required this.id,
    required this.name,
    required this.type,
    required this.currency,
    required this.openingBalance,
    required this.currentBalance,
    required this.status,
    required this.isArchived,
    this.creditLimit,
  });

  final String id;
  final String name;
  final String type;
  final String currency;
  final int openingBalance;
  final int currentBalance;
  final String status;
  final bool isArchived;
  final int? creditLimit;

  factory AccountModel.fromJson(Map<String, dynamic> json) {
    return AccountModel(
      id: json['id'] as String,
      name: json['name'] as String,
      type: json['type'] as String,
      currency: json['currency'] as String,
      openingBalance: json['opening_balance'] as int,
      currentBalance: json['current_balance'] as int,
      status: json['status'] as String,
      isArchived: json['is_archived'] as bool,
      creditLimit: json['credit_limit'] as int?,
    );
  }
}

class CategoryModel {
  const CategoryModel({
    required this.id,
    required this.name,
    required this.type,
    required this.isSystem,
  });

  final String id;
  final String name;
  final String type;
  final bool isSystem;

  factory CategoryModel.fromJson(Map<String, dynamic> json) {
    return CategoryModel(
      id: json['id'] as String,
      name: json['name'] as String,
      type: json['type'] as String,
      isSystem: json['is_system'] as bool,
    );
  }
}

class TransactionModel {
  const TransactionModel({
    required this.id,
    required this.type,
    required this.accountId,
    required this.amount,
    required this.currency,
    required this.transactionDate,
    this.description,
  });

  final String id;
  final String type;
  final String accountId;
  final int amount;
  final String currency;
  final DateTime transactionDate;
  final String? description;

  factory TransactionModel.fromJson(Map<String, dynamic> json) {
    return TransactionModel(
      id: json['id'] as String,
      type: json['type'] as String,
      accountId: json['account_id'] as String,
      amount: json['amount'] as int,
      currency: json['currency'] as String,
      transactionDate: DateTime.parse(json['transaction_date'] as String),
      description: json['description'] as String?,
    );
  }
}

class BudgetModel {
  const BudgetModel({
    required this.id,
    required this.name,
    required this.limit,
    required this.spent,
    required this.remaining,
    required this.utilization,
    required this.risk,
    required this.projectedSpending,
    required this.currency,
  });

  final String id;
  final String name;
  final int limit;
  final int spent;
  final int remaining;
  final double utilization;
  final String risk;
  final int projectedSpending;
  final String currency;

  factory BudgetModel.fromJson(Map<String, dynamic> json) {
    final calculation = json['calculation'] as Map<String, dynamic>;
    return BudgetModel(
      id: json['id'] as String,
      name: json['name'] as String,
      limit: json['total_limit'] as int,
      spent: calculation['spent'] as int,
      remaining: calculation['remaining'] as int,
      utilization: _asDouble(calculation['utilization']),
      risk: calculation['risk'] as String,
      projectedSpending: calculation['projected_spending'] as int,
      currency: json['currency'] as String,
    );
  }
}

class GoalModel {
  const GoalModel({
    required this.id,
    required this.name,
    required this.target,
    required this.current,
    required this.remaining,
    required this.progress,
    required this.requiredMonthly,
    required this.forecast,
    required this.currency,
    this.targetDate,
  });

  final String id;
  final String name;
  final int target;
  final int current;
  final int remaining;
  final double progress;
  final int requiredMonthly;
  final String forecast;
  final String currency;
  final String? targetDate;

  factory GoalModel.fromJson(Map<String, dynamic> json) {
    final calculation = json['calculation'] as Map<String, dynamic>;
    return GoalModel(
      id: json['id'] as String,
      name: json['name'] as String,
      target: json['target_amount'] as int,
      current: calculation['current'] as int,
      remaining: calculation['remaining'] as int,
      progress: _asDouble(calculation['progress']),
      requiredMonthly: calculation['required_monthly_saving'] as int,
      forecast: calculation['forecast'] as String,
      currency: json['currency'] as String,
      targetDate: json['target_date'] as String?,
    );
  }
}

double _asDouble(Object? value) =>
    value is num ? value.toDouble() : double.parse(value as String);

class InsightModel {
  const InsightModel({
    required this.id,
    required this.type,
    required this.title,
    required this.description,
    required this.severity,
    required this.confidence,
    required this.periodStart,
    required this.periodEnd,
    required this.source,
    required this.sourceMetric,
    required this.expiresAt,
  });

  final String id;
  final String type;
  final String title;
  final String description;
  final String severity;
  final double confidence;
  final DateTime periodStart;
  final DateTime periodEnd;
  final String source;
  final String sourceMetric;
  final DateTime expiresAt;

  factory InsightModel.fromJson(Map<String, dynamic> json) {
    return InsightModel(
      id: json['id'] as String,
      type: json['type'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      severity: json['severity'] as String,
      confidence: _asDouble(json['confidence']),
      periodStart: DateTime.parse(json['period_start'] as String),
      periodEnd: DateTime.parse(json['period_end'] as String),
      source: json['source'] as String,
      sourceMetric: json['source_metric'] as String,
      expiresAt: DateTime.parse(json['expires_at'] as String),
    );
  }
}

class NotificationModel {
  const NotificationModel({
    required this.id,
    required this.type,
    required this.title,
    required this.description,
    required this.severity,
    required this.priority,
    required this.readAt,
    required this.createdAt,
  });

  final String id;
  final String type;
  final String title;
  final String description;
  final String severity;
  final int priority;
  final DateTime? readAt;
  final DateTime createdAt;

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['id'] as String,
      type: json['type'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      severity: json['severity'] as String,
      priority: json['priority'] as int,
      readAt: json['read_at'] == null
          ? null
          : DateTime.parse(json['read_at'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class RecommendationModel {
  const RecommendationModel({
    required this.id,
    required this.type,
    required this.reason,
    required this.suggestedAction,
    required this.expectedImpact,
    required this.priority,
    required this.status,
  });

  final String id;
  final String type;
  final String reason;
  final String suggestedAction;
  final String expectedImpact;
  final int priority;
  final String status;

  factory RecommendationModel.fromJson(Map<String, dynamic> json) {
    return RecommendationModel(
      id: json['id'] as String,
      type: json['type'] as String,
      reason: json['reason'] as String,
      suggestedAction: json['suggested_action'] as String,
      expectedImpact: json['expected_impact'] as String,
      priority: json['priority'] as int,
      status: json['status'] as String,
    );
  }
}

class DashboardModel {
  const DashboardModel({
    required this.totalBalance,
    required this.income,
    required this.expense,
    required this.saving,
    required this.savingRate,
    required this.periodStart,
    required this.periodEnd,
  });

  final int totalBalance;
  final int income;
  final int expense;
  final int saving;
  final double savingRate;
  final DateTime periodStart;
  final DateTime periodEnd;

  factory DashboardModel.fromJson(Map<String, dynamic> json) {
    final summary = json['summary'] as Map<String, dynamic>;
    final period = json['period'] as Map<String, dynamic>;
    return DashboardModel(
      totalBalance: summary['total_balance'] as int,
      income: summary['income'] as int,
      expense: summary['expense'] as int,
      saving: summary['saving'] as int,
      savingRate: _asDouble(summary['saving_rate']),
      periodStart: DateTime.parse(period['start'] as String),
      periodEnd: DateTime.parse(period['end'] as String),
    );
  }
}
