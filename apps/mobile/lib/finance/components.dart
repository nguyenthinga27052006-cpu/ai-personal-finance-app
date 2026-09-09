import 'package:flutter/material.dart';

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
  Widget build(BuildContext context) => Text(
        '${_group(amount)} $currency',
        style: style,
        semanticsLabel: '${_group(amount)} $currency',
      );

  String _group(int value) {
    final sign = value < 0 ? '-' : '';
    final digits = value.abs().toString();
    final buffer = StringBuffer(sign);
    for (var index = 0; index < digits.length; index++) {
      if (index > 0 && (digits.length - index) % 3 == 0) buffer.write(',');
      buffer.write(digits[index]);
    }
    return buffer.toString();
  }
}

class BalanceCard extends StatelessWidget {
  const BalanceCard({super.key, required this.account});

  final AccountModel account;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: const Icon(Icons.account_balance_wallet),
          title: Text(account.name),
          subtitle: Text(account.type),
          trailing: MoneyText(account.currentBalance, currency: account.currency),
        ),
      );
}

class TransactionTile extends StatelessWidget {
  const TransactionTile({super.key, required this.transaction, required this.onTap});

  final TransactionModel transaction;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ListTile(
        onTap: onTap,
        leading: Icon(transaction.type == 'INCOME' ? Icons.arrow_downward : Icons.arrow_upward),
        title: Text(transaction.description?.isNotEmpty == true ? transaction.description! : transaction.type),
        subtitle: Text(_date(context, transaction.transactionDate)),
        trailing: MoneyText(transaction.amount, currency: transaction.currency),
      );

  String _date(BuildContext context, DateTime value) =>
      MaterialLocalizations.of(context).formatMediumDate(value.toLocal());
}

class BudgetProgress extends StatelessWidget {
  const BudgetProgress({super.key, required this.budget});

  final BudgetModel budget;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(budget.name, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            LinearProgressIndicator(value: budget.utilization.clamp(0, 1)),
            const SizedBox(height: 8),
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              MoneyText(budget.spent, currency: budget.currency),
              Text('${(budget.utilization * 100).toStringAsFixed(0)}% · ${budget.risk}'),
            ]),
            Text('Remaining: ${budget.remaining} ${budget.currency}'),
          ]),
        ),
      );
}
