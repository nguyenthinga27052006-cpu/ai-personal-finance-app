import 'package:flutter/material.dart';

import '../auth/api_client.dart';
import '../ai/ai_screen.dart';
import 'components.dart';
import 'finance_repository.dart';
import 'finance_view_model.dart';
import 'models.dart';

class FinanceHome extends StatefulWidget {
  const FinanceHome({
    super.key,
    required this.gateway,
    this.aiGateway,
    required this.email,
    required this.onLogout,
  });

  final FinanceGateway gateway;
  final AIGateway? aiGateway;
  final String email;
  final Future<void> Function() onLogout;

  @override
  State<FinanceHome> createState() => _FinanceHomeState();
}

class _FinanceHomeState extends State<FinanceHome> {
  late final FinanceViewModel viewModel;
  int tab = 0;

  @override
  void initState() {
    super.initState();
    viewModel = FinanceViewModel(FinanceRepository(widget.gateway))..loadCore();
  }

  @override
  void dispose() {
    viewModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: viewModel,
    builder: (context, _) => Scaffold(
      appBar: AppBar(
        title: Text(
          [
            'Home',
            'Accounts',
            'Transactions',
            'Budget',
            'Goals',
            'Insights',
            'Notifications',
            'Recommendations',
            'AI Assistant',
          ][tab],
        ),
        actions: [
          if (tab == 1)
            IconButton(
              onPressed: () => _createAccount(context),
              icon: const Icon(Icons.add_card),
              tooltip: 'Create account',
            ),
          IconButton(
            onPressed: widget.onLogout,
            icon: const Icon(Icons.logout),
            tooltip: 'Log out',
          ),
        ],
      ),
      body: viewModel.loading && viewModel.accounts.isEmpty
          ? const Loading()
          : viewModel.error != null && viewModel.accounts.isEmpty
          ? ErrorState(message: viewModel.error!, onRetry: viewModel.loadCore)
          : IndexedStack(
              index: tab,
              children: [
                _HomeView(model: viewModel),
                _AccountsView(model: viewModel, onEdit: _editAccount),
                _TransactionsView(model: viewModel),
                _BudgetView(model: viewModel),
                _GoalsView(model: viewModel),
                _InsightsView(model: viewModel),
                _NotificationsView(model: viewModel),
                _RecommendationsView(model: viewModel),
                if (widget.aiGateway case final aiGateway?)
                  AIScreen(gateway: aiGateway)
                else
                  const Center(child: Text('AI Assistant is unavailable')),
              ],
            ),
      floatingActionButton: tab == 2
          ? FloatingActionButton(
              onPressed: () => _addTransaction(context),
              tooltip: 'Add transaction',
              child: const Icon(Icons.add),
            )
          : null,
      bottomNavigationBar: NavigationBar(
        selectedIndex: tab,
        onDestinationSelected: (value) {
          setState(() => tab = value);
          if (value == 6) {
            viewModel.loadCore();
          }
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.account_balance_wallet_outlined),
            selectedIcon: Icon(Icons.account_balance_wallet),
            label: 'Accounts',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long),
            label: 'Transactions',
          ),
          NavigationDestination(
            icon: Icon(Icons.pie_chart_outline),
            selectedIcon: Icon(Icons.pie_chart),
            label: 'Budget',
          ),
          NavigationDestination(
            icon: Icon(Icons.flag_outlined),
            selectedIcon: Icon(Icons.flag),
            label: 'Goals',
          ),
          NavigationDestination(
            icon: Icon(Icons.insights_outlined),
            selectedIcon: Icon(Icons.insights),
            label: 'Insights',
          ),
          NavigationDestination(
            icon: Icon(Icons.notifications_outlined),
            selectedIcon: Icon(Icons.notifications),
            label: 'Notifications',
          ),
          NavigationDestination(
            icon: Icon(Icons.lightbulb_outline),
            selectedIcon: Icon(Icons.lightbulb),
            label: 'Recommendations',
          ),
          NavigationDestination(
            icon: Icon(Icons.auto_awesome_outlined),
            selectedIcon: Icon(Icons.auto_awesome),
            label: 'AI',
          ),
        ],
      ),
    ),
  );

  Future<void> _addTransaction(BuildContext context) async {
    if (viewModel.accounts.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Create an account first')));
      return;
    }
    final values = await showDialog<TransactionInput>(
      context: context,
      builder: (context) => TransactionDialog(accounts: viewModel.accounts),
    );
    if (values == null) return;
    final error = await viewModel.addTransaction(
      type: values.type,
      account: values.account,
      amount: values.amount,
      description: values.description,
    );
    if (error != null && context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error)));
    } else if (context.mounted) {
      setState(() => tab = 2);
    }
  }

  Future<void> _createAccount(BuildContext context) async {
    final values = await showDialog<AccountInput>(
      context: context,
      builder: (context) => const AccountDialog(),
    );
    if (values == null) return;
    final error = await viewModel.createAccount(
      name: values.name,
      type: values.type,
      openingBalance: values.openingBalance,
    );
    if (error != null && context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error)));
    }
  }

  Future<void> _editAccount(AccountModel account) async {
    final values = await showDialog<AccountInput>(
      context: context,
      builder: (context) => AccountDialog(account: account),
    );
    if (values == null) return;
    final error = values.archive
        ? await viewModel.archiveAccount(account.id)
        : await viewModel.updateAccount(account.id, values.name, values.type);
    if (error != null && mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error)));
    }
  }
}

class _HomeView extends StatelessWidget {
  const _HomeView({required this.model});
  final FinanceViewModel model;

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: model.loadCore,
    child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Welcome back', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 8),
        if (model.dashboard case final dashboard?) ...[
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.account_balance_wallet),
                  title: const Text('Total balance'),
                  trailing: MoneyText(dashboard.totalBalance, currency: 'VND'),
                ),
                ListTile(
                  title: const Text('Income'),
                  trailing: MoneyText(dashboard.income, currency: 'VND'),
                ),
                ListTile(
                  title: const Text('Expense'),
                  trailing: MoneyText(dashboard.expense, currency: 'VND'),
                ),
                ListTile(
                  title: const Text('Saving'),
                  trailing: MoneyText(dashboard.saving, currency: 'VND'),
                ),
              ],
            ),
          ),
        ] else
          const SizedBox(
            height: 160,
            child: EmptyState(label: 'No dashboard data yet'),
          ),
        const SizedBox(height: 16),
        Text('Accounts', style: Theme.of(context).textTheme.titleLarge),
        ...model.accounts.map((account) => BalanceCard(account: account)),
        const SizedBox(height: 16),
        Text(
          'Recent transactions',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        if (model.transactions.isEmpty)
          const SizedBox(
            height: 80,
            child: EmptyState(label: 'No transactions yet'),
          ),
        ...model.transactions
            .take(5)
            .map(
              (item) => TransactionTile(
                transaction: item,
                onTap: () => _showDetail(context, item),
              ),
            ),
      ],
    ),
  );
}

class _AccountsView extends StatelessWidget {
  const _AccountsView({required this.model, required this.onEdit});
  final FinanceViewModel model;
  final ValueChanged<AccountModel> onEdit;
  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: model.loadCore,
    child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (model.accounts.isEmpty)
          const SizedBox(
            height: 200,
            child: EmptyState(label: 'No accounts yet'),
          ),
        ...model.accounts.map(
          (account) => GestureDetector(
            onTap: () => onEdit(account),
            child: BalanceCard(account: account),
          ),
        ),
      ],
    ),
  );
}

class _TransactionsView extends StatelessWidget {
  const _TransactionsView({required this.model});
  final FinanceViewModel model;
  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: model.loadCore,
    child: ListView(
      children: [
        if (model.transactions.isEmpty)
          const SizedBox(
            height: 200,
            child: EmptyState(label: 'No transactions yet'),
          ),
        ...model.transactions.map(
          (item) => TransactionTile(
            transaction: item,
            onTap: () => _showDetail(context, item),
          ),
        ),
      ],
    ),
  );
}

class _BudgetView extends StatelessWidget {
  const _BudgetView({required this.model});
  final FinanceViewModel model;
  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: model.loadCore,
    child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (model.budgets.isEmpty)
          const SizedBox(
            height: 200,
            child: EmptyState(label: 'No budgets yet'),
          ),
        ...model.budgets.map((budget) => BudgetProgress(budget: budget)),
      ],
    ),
  );
}

class _GoalsView extends StatelessWidget {
  const _GoalsView({required this.model});
  final FinanceViewModel model;
  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: model.loadCore,
    child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (model.goals.isEmpty)
          const SizedBox(height: 200, child: EmptyState(label: 'No goals yet')),
        ...model.goals.map(
          (goal) => Card(
            child: ListTile(
              title: Text(goal.name),
              subtitle: Text('Remaining: ${goal.remaining} ${goal.currency}'),
              trailing: Text('${(goal.progress * 100).toStringAsFixed(0)}%'),
            ),
          ),
        ),
      ],
    ),
  );
}

class _InsightsView extends StatelessWidget {
  const _InsightsView({required this.model});

  final FinanceViewModel model;

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: model.loadCore,
    child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (model.insights.isEmpty)
          const SizedBox(
            height: 200,
            child: EmptyState(label: 'No insights available'),
          ),
        ...model.insights.map(
          (insight) => Card(
            child: ListTile(
              leading: Icon(
                _severityIcon(insight.severity),
                color: _severityColor(insight.severity),
              ),
              title: Text(insight.title),
              subtitle: Text(
                '${insight.description}\n${insight.periodStart.toLocal().toString().substring(0, 10)} - '
                '${insight.periodEnd.toLocal().toString().substring(0, 10)}\nSource: ${insight.sourceMetric}',
              ),
              isThreeLine: true,
            ),
          ),
        ),
      ],
    ),
  );
}

class _NotificationsView extends StatelessWidget {
  const _NotificationsView({required this.model});

  final FinanceViewModel model;

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: model.loadCore,
    child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (model.notifications.isEmpty)
          const SizedBox(
            height: 200,
            child: EmptyState(label: 'No notifications yet'),
          ),
        ...model.notifications.map(
          (notification) => Card(
            child: ListTile(
              leading: Icon(
                notification.readAt == null
                    ? _severityIcon(notification.severity)
                    : Icons.check_circle_outline,
                color: notification.readAt == null
                    ? _severityColor(notification.severity)
                    : Colors.grey,
              ),
              title: Text(notification.title),
              subtitle: Text(notification.description),
              onTap: notification.readAt == null
                  ? () async {
                      final error = await model.markNotificationRead(notification.id);
                      if (error != null && context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(error)),
                        );
                      }
                    }
                  : null,
            ),
          ),
        ),
      ],
    ),
  );
}

class _RecommendationsView extends StatelessWidget {
  const _RecommendationsView({required this.model});

  final FinanceViewModel model;

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: model.loadCore,
    child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (model.recommendations.isEmpty)
          const SizedBox(
            height: 200,
            child: EmptyState(label: 'No recommendations yet'),
          ),
        ...model.recommendations.map(
          (recommendation) => Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    recommendation.type,
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                  const SizedBox(height: 8),
                  Text(recommendation.reason),
                  const SizedBox(height: 8),
                  Text(recommendation.suggestedAction),
                  const SizedBox(height: 8),
                  Text(recommendation.expectedImpact),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    children: [
                      FilledButton.tonal(
                        onPressed: () => model.updateRecommendation(
                          recommendation.id,
                          model.repository.acceptRecommendation,
                        ),
                        child: const Text('Accept'),
                      ),
                      OutlinedButton(
                        onPressed: () => model.updateRecommendation(
                          recommendation.id,
                          model.repository.dismissRecommendation,
                        ),
                        child: const Text('Dismiss'),
                      ),
                      TextButton(
                        onPressed: () => model.updateRecommendation(
                          recommendation.id,
                          (id) => model.repository.giveRecommendationFeedback(
                            id,
                            'HELPFUL',
                          ),
                        ),
                        child: const Text('Helpful'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    ),
  );
}

IconData _severityIcon(String severity) => switch (severity) {
  'HIGH' => Icons.warning,
  'MEDIUM' => Icons.priority_high,
  'LOW' => Icons.info_outline,
  _ => Icons.check_circle_outline,
};

Color _severityColor(String severity) => switch (severity) {
  'HIGH' => Colors.red,
  'MEDIUM' => Colors.orange,
  'LOW' => Colors.blue,
  _ => Colors.green,
};

void _showDetail(BuildContext context, TransactionModel transaction) {
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (_) => TransactionDetailScreen(transaction: transaction),
    ),
  );
}

class TransactionDetailScreen extends StatelessWidget {
  const TransactionDetailScreen({super.key, required this.transaction});
  final TransactionModel transaction;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Transaction detail')),
    body: ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          transaction.type,
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        MoneyText(
          transaction.amount,
          currency: transaction.currency,
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 16),
        Text(
          transaction.description?.isNotEmpty == true
              ? transaction.description!
              : 'No note',
        ),
        Text(transaction.transactionDate.toLocal().toString()),
        Text('Account: ${transaction.accountId}'),
      ],
    ),
  );
}

class AccountInput {
  const AccountInput({
    required this.name,
    required this.type,
    required this.openingBalance,
    this.archive = false,
  });

  final String name;
  final String type;
  final int openingBalance;
  final bool archive;
}

class AccountDialog extends StatefulWidget {
  const AccountDialog({super.key, this.account});

  final AccountModel? account;

  @override
  State<AccountDialog> createState() => _AccountDialogState();
}

class _AccountDialogState extends State<AccountDialog> {
  late final TextEditingController nameController;
  late final TextEditingController openingController;
  var type = 'CASH';

  @override
  void initState() {
    super.initState();
    nameController = TextEditingController(text: widget.account?.name ?? '');
    openingController = TextEditingController(
      text: widget.account?.openingBalance.toString() ?? '0',
    );
    type = widget.account?.type ?? 'CASH';
  }

  @override
  void dispose() {
    nameController.dispose();
    openingController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text(widget.account == null ? 'Create account' : 'Edit account'),
    content: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        TextField(
          controller: nameController,
          decoration: const InputDecoration(labelText: 'Name'),
        ),
        if (widget.account == null)
          TextField(
            controller: openingController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Opening balance'),
          ),
        DropdownButtonFormField<String>(
          initialValue: type,
          items:
              const [
                    'CASH',
                    'BANK',
                    'E_WALLET',
                    'CREDIT_CARD',
                    'SAVINGS',
                    'OTHER',
                  ]
                  .map(
                    (value) =>
                        DropdownMenuItem(value: value, child: Text(value)),
                  )
                  .toList(),
          onChanged: (value) => setState(() => type = value!),
          decoration: const InputDecoration(labelText: 'Type'),
        ),
      ],
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancel'),
      ),
      if (widget.account != null)
        TextButton(
          onPressed: () => Navigator.pop(
            context,
            AccountInput(
              name: nameController.text,
              type: type,
              openingBalance: 0,
              archive: true,
            ),
          ),
          child: const Text('Archive'),
        ),
      FilledButton(
        onPressed: () {
          final opening = int.tryParse(openingController.text);
          if (nameController.text.trim().isEmpty ||
              opening == null ||
              opening < 0) {
            return;
          }
          Navigator.pop(
            context,
            AccountInput(
              name: nameController.text,
              type: type,
              openingBalance: opening,
            ),
          );
        },
        child: Text(widget.account == null ? 'Create' : 'Save'),
      ),
    ],
  );
}

class TransactionInput {
  const TransactionInput({
    required this.type,
    required this.account,
    required this.amount,
    required this.description,
  });

  final String type;
  final AccountModel account;
  final int amount;
  final String description;
}

class TransactionDialog extends StatefulWidget {
  const TransactionDialog({super.key, required this.accounts});

  final List<AccountModel> accounts;

  @override
  State<TransactionDialog> createState() => _TransactionDialogState();
}

class _TransactionDialogState extends State<TransactionDialog> {
  late final TextEditingController amountController;
  late final TextEditingController noteController;
  var type = 'EXPENSE';
  late AccountModel account;

  @override
  void initState() {
    super.initState();
    amountController = TextEditingController();
    noteController = TextEditingController();
    account = widget.accounts.first;
  }

  @override
  void dispose() {
    amountController.dispose();
    noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Add transaction'),
    content: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          DropdownButtonFormField<String>(
            initialValue: type,
            items: const ['EXPENSE', 'INCOME']
                .map(
                  (value) => DropdownMenuItem(value: value, child: Text(value)),
                )
                .toList(),
            onChanged: (value) => setState(() => type = value!),
            decoration: const InputDecoration(labelText: 'Type'),
          ),
          TextField(
            controller: amountController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Amount'),
          ),
          DropdownButtonFormField<AccountModel>(
            initialValue: account,
            items: widget.accounts
                .map(
                  (item) =>
                      DropdownMenuItem(value: item, child: Text(item.name)),
                )
                .toList(),
            onChanged: (value) => setState(() => account = value!),
            decoration: const InputDecoration(labelText: 'Account'),
          ),
          TextField(
            controller: noteController,
            decoration: const InputDecoration(labelText: 'Note'),
          ),
        ],
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancel'),
      ),
      FilledButton(
        onPressed: () {
          final amount = int.tryParse(amountController.text);
          if (amount == null || amount <= 0) return;
          Navigator.pop(
            context,
            TransactionInput(
              type: type,
              account: account,
              amount: amount,
              description: noteController.text,
            ),
          );
        },
        child: const Text('Save'),
      ),
    ],
  );
}
