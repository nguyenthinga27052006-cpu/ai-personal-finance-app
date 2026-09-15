import 'package:flutter/material.dart';

import '../settings/settings_controller.dart';
import 'models.dart';

class Loading extends StatelessWidget {
  const Loading({super.key});

  @override
  Widget build(BuildContext context) => const Center(child: CircularProgressIndicator());
}

class ErrorState extends StatelessWidget {
  const ErrorState({super.key, required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.cloud_off, size: 40),
          const SizedBox(height: 8),
          Text(message, textAlign: TextAlign.center),
          if (onRetry != null) TextButton(onPressed: onRetry, child: const Text('Retry')),
        ]),
      );
}

class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.label});

  final String label;

  @override
  Widget build(BuildContext context) => Center(child: Text(label));
}

class MoneyText extends StatelessWidget {
  const MoneyText(this.amount, {super.key, required this.currency, this.style});

  final int amount;
  final String currency;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    final formatted = settings.formatAmount(amount);
    return Text(
      formatted,
      style: style,
      semanticsLabel: formatted,
    );
  }
}

class BalanceCard extends StatelessWidget {
  const BalanceCard({
    super.key,
    required this.account,
    this.onTap,
    this.onEdit,
    this.onArchive,
  });

  final AccountModel account;
  final VoidCallback? onTap;
  final VoidCallback? onEdit;
  final VoidCallback? onArchive;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          onTap: onTap ?? onEdit,
          leading: const Icon(Icons.account_balance_wallet, color: Colors.teal),
          title: Text(account.name, style: const TextStyle(fontWeight: FontWeight.bold)),
          subtitle: Text(account.type),
          trailing: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              MoneyText(account.currentBalance, currency: account.currency),
              if (onEdit != null || onArchive != null)
                PopupMenuButton<String>(
                  icon: const Icon(Icons.more_vert, size: 20),
                  onSelected: (value) {
                    if (value == 'edit') onEdit?.call();
                    if (value == 'archive') onArchive?.call();
                  },
                  itemBuilder: (context) => [
                    if (onEdit != null)
                      const PopupMenuItem(
                        value: 'edit',
                        child: Row(
                          children: [
                            Icon(Icons.edit, size: 18),
                            SizedBox(width: 8),
                            Text('Sửa tài khoản'),
                          ],
                        ),
                      ),
                    if (onArchive != null)
                      const PopupMenuItem(
                        value: 'archive',
                        child: Row(
                          children: [
                            Icon(Icons.archive_outlined, color: Colors.orange, size: 18),
                            SizedBox(width: 8),
                            Text('Lưu trữ', style: TextStyle(color: Colors.orange)),
                          ],
                        ),
                      ),
                  ],
                ),
            ],
          ),
        ),
      );
}

class TransactionTile extends StatelessWidget {
  const TransactionTile({
    super.key,
    required this.transaction,
    required this.onTap,
    this.onEdit,
    this.onDelete,
  });

  final TransactionModel transaction;
  final VoidCallback onTap;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) => ListTile(
        onTap: onTap,
        leading: Icon(
          transaction.type == 'INCOME' ? Icons.arrow_downward : Icons.arrow_upward,
          color: transaction.type == 'INCOME' ? Colors.green : Colors.red,
        ),
        title: Text(transaction.description?.isNotEmpty == true ? transaction.description! : transaction.type),
        subtitle: Text(_date(context, transaction.transactionDate)),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            MoneyText(transaction.amount, currency: transaction.currency),
            if (onEdit != null || onDelete != null)
              PopupMenuButton<String>(
                icon: const Icon(Icons.more_vert, size: 20),
                onSelected: (value) {
                  if (value == 'edit') onEdit?.call();
                  if (value == 'delete') onDelete?.call();
                },
                itemBuilder: (context) => [
                  if (onEdit != null)
                    const PopupMenuItem(
                      value: 'edit',
                      child: Row(
                        children: [
                          Icon(Icons.edit, size: 18),
                          SizedBox(width: 8),
                          Text('Sửa giao dịch'),
                        ],
                      ),
                    ),
                  if (onDelete != null)
                    const PopupMenuItem(
                      value: 'delete',
                      child: Row(
                        children: [
                          Icon(Icons.delete, color: Colors.red, size: 18),
                          SizedBox(width: 8),
                          Text('Xóa giao dịch', style: TextStyle(color: Colors.red)),
                        ],
                      ),
                    ),
                ],
              ),
          ],
        ),
      );

  String _date(BuildContext context, DateTime value) =>
      MaterialLocalizations.of(context).formatMediumDate(value.toLocal());
}

class BudgetProgress extends StatelessWidget {
  const BudgetProgress({
    super.key,
    required this.budget,
    this.onEdit,
    this.onDelete,
  });

  final BudgetModel budget;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  budget.name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ),
              if (onEdit != null || onDelete != null)
                PopupMenuButton<String>(
                  icon: const Icon(Icons.more_vert, size: 20),
                  onSelected: (value) {
                    if (value == 'edit') onEdit?.call();
                    if (value == 'delete') onDelete?.call();
                  },
                  itemBuilder: (context) => [
                    if (onEdit != null)
                      const PopupMenuItem(
                        value: 'edit',
                        child: Row(
                          children: [
                            Icon(Icons.edit, size: 18),
                            SizedBox(width: 8),
                            Text('Sửa hạn mức'),
                          ],
                        ),
                      ),
                    if (onDelete != null)
                      const PopupMenuItem(
                        value: 'delete',
                        child: Row(
                          children: [
                            Icon(Icons.delete, color: Colors.red, size: 18),
                            SizedBox(width: 8),
                            Text('Xóa ngân sách', style: TextStyle(color: Colors.red)),
                          ],
                        ),
                      ),
                  ],
                ),
            ],
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(value: budget.utilization.clamp(0, 1)),
          const SizedBox(height: 8),
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            MoneyText(budget.spent, currency: budget.currency),
            Text('${(budget.utilization * 100).toStringAsFixed(0)}% · ${budget.risk}'),
          ]),
          Text('Còn lại: ${settings.formatAmount(budget.remaining)}'),
        ]),
      ),
    );
  }
}
