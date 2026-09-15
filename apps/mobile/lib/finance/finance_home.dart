import 'package:flutter/material.dart';

import '../auth/api_client.dart';
import '../admin/admin_dashboard.dart';
import '../ai/ai_screen.dart';
import '../settings/settings_controller.dart';
import '../settings/settings_dialog.dart';
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
    this.userRole = 'USER',
    required this.onLogout,
  });

  final FinanceGateway gateway;
  final AIGateway? aiGateway;
  final String email;
  final String userRole;
  final Future<void> Function() onLogout;

  @override
  State<FinanceHome> createState() => _FinanceHomeState();
}

class _FinanceHomeState extends State<FinanceHome> {
  late final FinanceViewModel viewModel;
  late int tab;

  @override
  void initState() {
    super.initState();
    final isAdmin = widget.userRole.toUpperCase() == 'ADMIN' ||
        widget.email == 'admin@finance.app';
    tab = isAdmin ? 9 : 0;
    viewModel = FinanceViewModel(FinanceRepository(widget.gateway))..loadCore();
  }

  @override
  void dispose() {
    viewModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width >= 800;
    final settings = InheritedSettings.of(context);
    final isAdmin = widget.userRole.toUpperCase() == 'ADMIN' ||
        widget.email == 'admin@finance.app';

    if (isAdmin) {
      final adminTitles = [
        '📊 Báo Cáo Tổng Quan & Biểu Đồ Hệ Thống',
        '👥 Quản Lý Người Dùng & Phân Quyền Hệ Thống',
        '🤖 Cấu Hình AI Models & Quản Lý Rate Limits',
        '💬 Hỏi Đáp Trợ Lý AI System',
      ];

      final adminViews = [
        if (widget.gateway is ApiClient)
          AdminDashboardScreen(api: widget.gateway as ApiClient, initialTabIndex: 0, showHeader: false)
        else
          const Center(child: Text('Admin Portal is unavailable')),
        if (widget.gateway is ApiClient)
          AdminDashboardScreen(api: widget.gateway as ApiClient, initialTabIndex: 1, showHeader: false)
        else
          const Center(child: Text('Admin Portal is unavailable')),
        if (widget.gateway is ApiClient)
          AdminDashboardScreen(api: widget.gateway as ApiClient, initialTabIndex: 2, showHeader: false)
        else
          const Center(child: Text('Admin Portal is unavailable')),
        if (widget.aiGateway case final aiGateway?)
          AIScreen(gateway: aiGateway)
        else
          const Center(child: Text('AI Assistant is unavailable')),
      ];

      final activeAdminTab = tab.clamp(0, adminViews.length - 1);

      final adminRail = NavigationRail(
        selectedIndex: activeAdminTab,
        onDestinationSelected: _selectTab,
        labelType: NavigationRailLabelType.selected,
        leading: const Padding(
          padding: EdgeInsets.symmetric(vertical: 8.0),
          child: CircleAvatar(
            backgroundColor: Colors.amber,
            child: Icon(Icons.admin_panel_settings, color: Colors.white),
          ),
        ),
        destinations: const [
          NavigationRailDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard, color: Colors.amber),
            label: Text('Tổng quan'),
          ),
          NavigationRailDestination(
            icon: Icon(Icons.people_outline),
            selectedIcon: Icon(Icons.people, color: Colors.amber),
            label: Text('Người dùng'),
          ),
          NavigationRailDestination(
            icon: Icon(Icons.psychology_outlined),
            selectedIcon: Icon(Icons.psychology, color: Colors.amber),
            label: Text('AI & Quotas'),
          ),
          NavigationRailDestination(
            icon: Icon(Icons.smart_toy_outlined),
            selectedIcon: Icon(Icons.smart_toy, color: Colors.teal),
            label: Text('Trợ lý AI'),
          ),
        ],
      );

      return Scaffold(
        appBar: AppBar(
          title: Text(adminTitles[activeAdminTab]),
          actions: [
            IconButton(
              icon: const Icon(Icons.settings),
              tooltip: settings.tr('settings_title'),
              onPressed: () {
                SettingsDialog.show(
                  context,
                  controller: settings,
                  api: widget.gateway is AuthGateway ? widget.gateway as AuthGateway : null,
                  onLogout: () async {
                    await widget.onLogout();
                  },
                );
              },
            ),
            IconButton(
              onPressed: widget.onLogout,
              icon: const Icon(Icons.logout),
              tooltip: settings.tr('logout'),
            ),
          ],
        ),
        body: isDesktop
            ? Row(
                children: [
                  adminRail,
                  const VerticalDivider(thickness: 1, width: 1),
                  Expanded(
                    child: IndexedStack(
                      index: activeAdminTab,
                      children: adminViews,
                    ),
                  ),
                ],
              )
            : IndexedStack(
                index: activeAdminTab,
                children: adminViews,
              ),
        bottomNavigationBar: isDesktop
            ? null
            : NavigationBar(
                selectedIndex: activeAdminTab,
                onDestinationSelected: _selectTab,
                destinations: const [
                  NavigationDestination(
                    icon: Icon(Icons.dashboard_outlined),
                    selectedIcon: Icon(Icons.dashboard, color: Colors.amber),
                    label: 'Tổng quan',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.people_outline),
                    selectedIcon: Icon(Icons.people, color: Colors.amber),
                    label: 'Người dùng',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.psychology_outlined),
                    selectedIcon: Icon(Icons.psychology, color: Colors.amber),
                    label: 'AI & Rate',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.smart_toy_outlined),
                    selectedIcon: Icon(Icons.smart_toy, color: Colors.teal),
                    label: 'Trợ lý AI',
                  ),
                ],
              ),
      );
    }

    return AnimatedBuilder(
      animation: viewModel,
      builder: (context, _) {
        final mainContent = viewModel.loading && viewModel.accounts.isEmpty
            ? const Loading()
            : viewModel.error != null && viewModel.accounts.isEmpty
            ? ErrorState(message: viewModel.error!, onRetry: viewModel.loadCore)
            : IndexedStack(
                index: tab,
                children: [
                  _HomeView(key: ValueKey('home-${viewModel.accounts.map((a) => "${a.id}:${a.name}").join(",")}'), model: viewModel),
                  _AccountsView(key: ValueKey('accs-${viewModel.accounts.map((a) => "${a.id}:${a.name}").join(",")}'), model: viewModel, onEdit: _editAccount),
                  _TransactionsView(
                    model: viewModel,
                    onEdit: (item) => _editTransaction(context, item),
                    onDelete: (item) => _confirmDeleteTransaction(context, item),
                  ),
                  _BudgetView(
                    model: viewModel,
                    onEdit: (budget) => _editBudget(context, budget),
                    onDelete: (budget) => _confirmDeleteBudget(context, budget),
                  ),
                  _GoalsView(
                    model: viewModel,
                    onEditGoal: (goal) => _editGoal(context, goal),
                    onAddContribution: (goal) => _addGoalContribution(context, goal),
                    onDeleteGoal: (goal) => _confirmDeleteGoal(context, goal),
                  ),
                  _InsightsView(model: viewModel),
                  _NotificationsView(model: viewModel),
                  _RecommendationsView(model: viewModel),
                  if (widget.aiGateway case final aiGateway?)
                    AIScreen(gateway: aiGateway)
                  else
                    const Center(child: Text('AI Assistant is unavailable')),
                ],
              );

        return Scaffold(
          appBar: AppBar(
            title: Text(
              [
                settings.tr('nav_home'),
                settings.tr('nav_accounts'),
                settings.tr('nav_transactions'),
                settings.tr('nav_budgets'),
                settings.tr('nav_goals'),
                settings.tr('nav_analytics'),
                settings.tr('nav_notifications'),
                settings.tr('nav_recommendations'),
                settings.tr('nav_ai_assistant'),
              ][tab.clamp(0, 8)],
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.settings),
                tooltip: settings.tr('settings_title'),
                onPressed: () {
                  SettingsDialog.show(
                    context,
                    controller: settings,
                    api: widget.gateway is AuthGateway ? widget.gateway as AuthGateway : null,
                    onLogout: () async {
                      await widget.onLogout();
                    },
                  );
                },
              ),
              IconButton(
                onPressed: widget.onLogout,
                icon: const Icon(Icons.logout),
                tooltip: settings.tr('logout'),
              ),
            ],
          ),
        body: isDesktop
            ? Row(
                children: [
                  NavigationRail(
                    selectedIndex: tab.clamp(0, 8),
                    onDestinationSelected: _selectTab,
                    labelType: NavigationRailLabelType.selected,
                    leading: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8.0),
                      child: CircleAvatar(
                        backgroundColor: Colors.teal.shade100,
                        child: const Icon(Icons.account_balance, color: Colors.teal),
                      ),
                    ),
                    destinations: [
                      NavigationRailDestination(
                        icon: const Icon(Icons.home_outlined),
                        selectedIcon: const Icon(Icons.home),
                        label: Text(settings.tr('nav_home')),
                      ),
                      NavigationRailDestination(
                        icon: const Icon(Icons.account_balance_wallet_outlined),
                        selectedIcon: const Icon(Icons.account_balance_wallet),
                        label: Text(settings.tr('nav_accounts')),
                      ),
                      NavigationRailDestination(
                        icon: const Icon(Icons.receipt_long_outlined),
                        selectedIcon: const Icon(Icons.receipt_long),
                        label: Text(settings.tr('nav_transactions')),
                      ),
                      NavigationRailDestination(
                        icon: const Icon(Icons.pie_chart_outline),
                        selectedIcon: const Icon(Icons.pie_chart),
                        label: Text(settings.tr('nav_budgets')),
                      ),
                      NavigationRailDestination(
                        icon: const Icon(Icons.flag_outlined),
                        selectedIcon: const Icon(Icons.flag),
                        label: Text(settings.tr('nav_goals')),
                      ),
                      NavigationRailDestination(
                        icon: const Icon(Icons.insights_outlined),
                        selectedIcon: const Icon(Icons.insights),
                        label: Text(settings.tr('nav_analytics')),
                      ),
                      NavigationRailDestination(
                        icon: const Icon(Icons.notifications_outlined),
                        selectedIcon: const Icon(Icons.notifications),
                        label: Text(settings.tr('nav_notifications')),
                      ),
                      NavigationRailDestination(
                        icon: const Icon(Icons.psychology_outlined),
                        selectedIcon: const Icon(Icons.psychology),
                        label: Text(settings.tr('nav_recommendations')),
                      ),
                      NavigationRailDestination(
                        icon: const Icon(Icons.smart_toy_outlined),
                        selectedIcon: const Icon(Icons.smart_toy),
                        label: Text(settings.tr('nav_ai_assistant')),
                      ),
                    ],
                  ),
                  const VerticalDivider(thickness: 1, width: 1),
                  Expanded(child: mainContent),
                ],
              )
            : mainContent,
        floatingActionButton: switch (tab) {
          1 => FloatingActionButton(
              onPressed: () => _createAccount(context),
              tooltip: settings.tr('add_account'),
              child: const Icon(Icons.add),
            ),
          2 => FloatingActionButton(
              onPressed: () => _addTransaction(context),
              tooltip: settings.tr('add_transaction'),
              child: const Icon(Icons.add),
            ),
          3 => FloatingActionButton(
              onPressed: () => _addBudget(context),
              tooltip: settings.tr('add_budget'),
              child: const Icon(Icons.add),
            ),
          4 => FloatingActionButton(
              onPressed: () => _createGoal(context),
              tooltip: settings.tr('add_goal'),
              child: const Icon(Icons.add),
            ),
          _ => null,
        },
        bottomNavigationBar: isDesktop
            ? null
            : NavigationBar(
                selectedIndex: tab < 4 ? tab : 4,
                onDestinationSelected: (value) {
                  if (value == 4) {
                    _showMoreNavigation(context);
                    return;
                  }
                  _selectTab(value);
                },
                destinations: [
                  NavigationDestination(
                    icon: const Icon(Icons.home_outlined),
                    selectedIcon: const Icon(Icons.home),
                    label: settings.tr('nav_home'),
                  ),
                  NavigationDestination(
                    icon: const Icon(Icons.account_balance_wallet_outlined),
                    selectedIcon: const Icon(Icons.account_balance_wallet),
                    label: settings.tr('nav_accounts'),
                  ),
                  NavigationDestination(
                    icon: const Icon(Icons.receipt_long_outlined),
                    selectedIcon: const Icon(Icons.receipt_long),
                    label: settings.tr('nav_transactions'),
                  ),
                  NavigationDestination(
                    icon: const Icon(Icons.pie_chart_outline),
                    selectedIcon: const Icon(Icons.pie_chart),
                    label: settings.tr('nav_budgets'),
                  ),
                  NavigationDestination(
                    icon: const Icon(Icons.more_horiz),
                    selectedIcon: const Icon(Icons.more_horiz),
                    label: settings.tr('nav_more'),
                  ),
                ],
              ),
        );
      },
    );
  }

  void _selectTab(int value) {
    setState(() => tab = value);
    if (value == 6) {
      viewModel.loadCore();
    }
  }

  Future<void> _showMoreNavigation(BuildContext context) async {
    final settings = InheritedSettings.of(context);
    final selectedTab = await showModalBottomSheet<int>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            _MoreNavigationTile(
              icon: Icons.flag_outlined,
              label: settings.tr('nav_goals'),
              onTap: () => Navigator.pop(context, 4),
            ),
            _MoreNavigationTile(
              icon: Icons.insights_outlined,
              label: settings.tr('nav_analytics'),
              onTap: () => Navigator.pop(context, 5),
            ),
            _MoreNavigationTile(
              icon: Icons.notifications_outlined,
              label: settings.tr('nav_notifications'),
              onTap: () => Navigator.pop(context, 6),
            ),
            _MoreNavigationTile(
              icon: Icons.lightbulb_outline,
              label: settings.tr('nav_recommendations'),
              onTap: () => Navigator.pop(context, 7),
            ),
            _MoreNavigationTile(
              icon: Icons.auto_awesome_outlined,
              label: settings.tr('nav_ai_assistant'),
              onTap: () => Navigator.pop(context, 8),
            ),
            if (widget.userRole.toUpperCase() == 'ADMIN' ||
                widget.email == 'admin@finance.app')
              _MoreNavigationTile(
                icon: Icons.admin_panel_settings_outlined,
                label: settings.tr('nav_admin_portal'),
                onTap: () => Navigator.pop(context, 9),
              ),
          ],
        ),
      ),
    );
    if (selectedTab != null && mounted) {
      _selectTab(selectedTab);
    }
  }

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

  Future<void> _editTransaction(BuildContext context, TransactionModel item) async {
    final amountController = TextEditingController(text: item.amount.toString());
    final descriptionController = TextEditingController(text: item.description ?? '');

    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Chỉnh sửa giao dịch'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: amountController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Số tiền (VND)'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: descriptionController,
              decoration: const InputDecoration(labelText: 'Mô tả / Ghi chú'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Hủy'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Cập nhật'),
          ),
        ],
      ),
    );

    if (result == true) {
      final amount = int.tryParse(amountController.text.trim()) ?? item.amount;
      final error = await viewModel.editTransaction(
        id: item.id,
        amount: amount,
        description: descriptionController.text.trim(),
      );
      if (error != null && mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(SnackBar(content: Text(error)));
      } else if (mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(
          const SnackBar(content: Text('Đã cập nhật giao dịch thành công!')),
        );
      }
    }
  }

  Future<void> _confirmDeleteTransaction(BuildContext context, TransactionModel item) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Xác nhận xóa giao dịch'),
        content: Text(
          'Bạn có chắc chắn muốn xóa giao dịch "${item.description?.isNotEmpty == true ? item.description : item.type}" '
          'với số tiền ${item.amount} ${item.currency} không?\nSố dư tài khoản sẽ được hoàn lại tương ứng.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Hủy'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Xóa'),
          ),
        ],
      ),
    );

    if (result == true) {
      final error = await viewModel.deleteTransaction(item.id);
      if (error != null && mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(SnackBar(content: Text(error)));
      } else if (mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(
          const SnackBar(content: Text('Đã xóa giao dịch thành công!')),
        );
      }
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

  Future<void> _createGoal(BuildContext context) async {
    final values = await showDialog<GoalInput>(
      context: context,
      builder: (context) => const GoalDialog(),
    );
    if (values == null) return;
    final error = await viewModel.createGoal(
      name: values.name,
      targetAmount: values.targetAmount,
      currency: values.currency,
      targetDate: values.targetDate,
      priority: values.priority,
      description: values.description,
    );
    if (error != null && mounted) {
      ScaffoldMessenger.of(this.context).showSnackBar(SnackBar(content: Text(error)));
    }
  }

  Future<void> _addGoalContribution(BuildContext context, GoalModel goal) async {
    final values = await showDialog<GoalContributionInput>(
      context: context,
      builder: (context) => GoalContributionDialog(
        goal: goal,
        accounts: viewModel.accounts,
      ),
    );
    if (values == null) return;
    final error = await viewModel.addGoalContribution(
      goalId: goal.id,
      amount: values.amount,
      accountId: values.accountId,
      note: values.note,
    );
    if (error != null && mounted) {
      ScaffoldMessenger.of(this.context).showSnackBar(SnackBar(content: Text(error)));
    }
  }

  Future<void> _confirmDeleteGoal(BuildContext context, GoalModel goal) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Goal'),
        content: Text('Are you sure you want to delete goal "${goal.name}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      final error = await viewModel.deleteGoal(goal.id);
      if (error != null && mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(SnackBar(content: Text(error)));
      }
    }
  }

  Future<void> _addBudget(BuildContext context) async {
    if (viewModel.categories.isEmpty) {
      await viewModel.loadCore();
    }
    final categoryController = TextEditingController();
    final nameController = TextEditingController();
    final limitController = TextEditingController();

    String selectedCategoryId = viewModel.categories.isNotEmpty ? viewModel.categories.first.id : '';

    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Thêm ngân sách mới'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameController,
                  decoration: const InputDecoration(labelText: 'Tên ngân sách (VD: Ngân sách Tháng 9)'),
                ),
                const SizedBox(height: 8),
                if (viewModel.categories.isNotEmpty)
                  DropdownButtonFormField<String>(
                    value: selectedCategoryId,
                    decoration: const InputDecoration(labelText: 'Danh mục'),
                    items: viewModel.categories
                        .map((c) => DropdownMenuItem(value: c.id, child: Text(c.name)))
                        .toList(),
                    onChanged: (val) {
                      if (val != null) setDialogState(() => selectedCategoryId = val);
                    },
                  )
                else
                  TextField(
                    controller: categoryController,
                    decoration: const InputDecoration(labelText: 'Mã danh mục'),
                  ),
                const SizedBox(height: 8),
                TextField(
                  controller: limitController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Hạn mức (VND)'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Hủy'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text('Tạo'),
            ),
          ],
        ),
      ),
    );

    if (result == true) {
      final name = nameController.text.trim();
      final limit = int.tryParse(limitController.text.trim()) ?? 0;
      final catId = selectedCategoryId.isNotEmpty ? selectedCategoryId : categoryController.text.trim();
      if (name.isNotEmpty && limit > 0 && catId.isNotEmpty) {
        final error = await viewModel.createBudget(
          name: name,
          categoryId: catId,
          limitAmount: limit,
        );
        if (error != null && mounted) {
          ScaffoldMessenger.of(this.context).showSnackBar(SnackBar(content: Text(error)));
        } else if (mounted) {
          ScaffoldMessenger.of(this.context).showSnackBar(
            const SnackBar(content: Text('Đã tạo ngân sách thành công!')),
          );
        }
      }
    }
  }

  Future<void> _editBudget(BuildContext context, BudgetModel budget) async {
    final nameController = TextEditingController(text: budget.name);
    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Sửa thông tin ngân sách'),
        content: TextField(
          controller: nameController,
          decoration: const InputDecoration(labelText: 'Tên ngân sách'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Cập nhật'),
          ),
        ],
      ),
    );

    if (result == true) {
      final error = await viewModel.editBudget(id: budget.id, name: nameController.text.trim());
      if (error != null && mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(SnackBar(content: Text(error)));
      } else if (mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(
          const SnackBar(content: Text('Đã cập nhật ngân sách!')),
        );
      }
    }
  }

  Future<void> _confirmDeleteBudget(BuildContext context, BudgetModel budget) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Xác nhận xóa ngân sách'),
        content: Text('Bạn có chắc chắn muốn xóa ngân sách "${budget.name}" không?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Xóa'),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      final error = await viewModel.deleteBudget(budget.id);
      if (error != null && mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(SnackBar(content: Text(error)));
      } else if (mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(
          const SnackBar(content: Text('Đã xóa ngân sách!')),
        );
      }
    }
  }

  Future<void> _editGoal(BuildContext context, GoalModel goal) async {
    final nameController = TextEditingController(text: goal.name);
    final targetController = TextEditingController(text: goal.target.toString());

    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Chỉnh sửa mục tiêu'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: const InputDecoration(labelText: 'Tên mục tiêu'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: targetController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Mục tiêu số tiền (VND)'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Cập nhật'),
          ),
        ],
      ),
    );

    if (result == true) {
      final target = int.tryParse(targetController.text.trim());
      final error = await viewModel.editGoal(
        id: goal.id,
        name: nameController.text.trim(),
        targetAmount: target,
      );
      if (error != null && mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(SnackBar(content: Text(error)));
      } else if (mounted) {
        ScaffoldMessenger.of(this.context).showSnackBar(
          const SnackBar(content: Text('Đã cập nhật mục tiêu!')),
        );
      }
    }
  }
}

class _HomeView extends StatelessWidget {
  const _HomeView({super.key, required this.model});
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
        ...model.accounts.map((account) => BalanceCard(key: ValueKey('home-${account.id}-${account.name}'), account: account)),
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
  const _AccountsView({super.key, required this.model, required this.onEdit});
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
            child: EmptyState(label: 'Chưa có tài khoản nào. Bấm nút + để tạo!'),
          ),
        ...model.accounts.map(
          (account) => BalanceCard(
            key: ValueKey('card-${account.id}-${account.name}'),
            account: account,
            onEdit: () => onEdit(account),
          ),
        ),
      ],
    ),
  );
}

class _TransactionsView extends StatelessWidget {
  const _TransactionsView({
    required this.model,
    required this.onEdit,
    required this.onDelete,
  });

  final FinanceViewModel model;
  final ValueChanged<TransactionModel> onEdit;
  final ValueChanged<TransactionModel> onDelete;

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: model.loadCore,
    child: ListView(
      children: [
        if (model.transactions.isEmpty)
          const SizedBox(
            height: 200,
            child: EmptyState(label: 'Chưa có giao dịch nào. Bấm nút + để thêm mới!'),
          ),
        ...model.transactions.map(
          (item) => TransactionTile(
            transaction: item,
            onTap: () => _showDetail(context, item),
            onEdit: () => onEdit(item),
            onDelete: () => onDelete(item),
          ),
        ),
      ],
    ),
  );
}

class _BudgetView extends StatelessWidget {
  const _BudgetView({
    required this.model,
    required this.onEdit,
    required this.onDelete,
  });

  final FinanceViewModel model;
  final ValueChanged<BudgetModel> onEdit;
  final ValueChanged<BudgetModel> onDelete;

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: model.loadCore,
    child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (model.budgets.isEmpty)
          const SizedBox(
            height: 200,
            child: EmptyState(label: 'Chưa có ngân sách nào. Bấm nút + để thêm mới!'),
          ),
        ...model.budgets.map(
          (budget) => BudgetProgress(
            budget: budget,
            onEdit: () => onEdit(budget),
            onDelete: () => onDelete(budget),
          ),
        ),
      ],
    ),
  );
}

class _GoalsView extends StatelessWidget {
  const _GoalsView({
    required this.model,
    required this.onEditGoal,
    required this.onAddContribution,
    required this.onDeleteGoal,
  });

  final FinanceViewModel model;
  final ValueChanged<GoalModel> onEditGoal;
  final ValueChanged<GoalModel> onAddContribution;
  final ValueChanged<GoalModel> onDeleteGoal;

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    return RefreshIndicator(
      onRefresh: model.loadCore,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (model.goals.isEmpty)
            const SizedBox(height: 200, child: EmptyState(label: 'Chưa có mục tiêu tiết kiệm nào. Bấm + để tạo!')),
          ...model.goals.map(
            (goal) => Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            goal.name,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        _ForecastBadge(forecast: goal.forecast),
                        IconButton(
                          icon: const Icon(Icons.edit_outlined, size: 20),
                          tooltip: settings.tr('edit_goal'),
                          onPressed: () => onEditGoal(goal),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete_outline, size: 20, color: Colors.red),
                          tooltip: settings.tr('delete_goal'),
                          onPressed: () => onDeleteGoal(goal),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(children: [Text('${settings.tr('nav_goals')}: '), MoneyText(goal.target, currency: goal.currency)]),
                        Row(children: [Text('${settings.tr('add_contribution')}: '), MoneyText(goal.current, currency: goal.currency)]),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: goal.progress.clamp(0.0, 1.0),
                        minHeight: 8,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          '${(goal.progress * 100).toStringAsFixed(1)}% ${settings.tr('goal_completed')}',
                          style: Theme.of(context).textTheme.labelMedium,
                        ),
                        Text(
                          '${settings.tr('goal_remaining')} ${settings.formatAmount(goal.remaining)}',
                          style: Theme.of(context).textTheme.labelMedium,
                        ),
                      ],
                    ),
                    if (goal.requiredMonthly > 0) ...[
                      const SizedBox(height: 6),
                      Text(
                        '${settings.tr('goal_required_saving')} ${settings.formatAmount(goal.requiredMonthly)}/${settings.tr('per_month')}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.blueGrey,
                        ),
                      ),
                    ],
                    if (goal.targetDate != null && goal.targetDate!.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        '${settings.tr('goal_target_date')} ${goal.targetDate}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey,
                        ),
                      ),
                    ],
                    const SizedBox(height: 12),
                    Align(
                      alignment: Alignment.centerRight,
                      child: FilledButton.icon(
                        onPressed: () => onAddContribution(goal),
                        icon: const Icon(Icons.savings, size: 18),
                        label: Text(settings.tr('add_contribution')),
                      ),
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
}

class _ForecastBadge extends StatelessWidget {
  const _ForecastBadge({required this.forecast});
  final String forecast;

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    final (color, label, icon) = switch (forecast) {
      'AHEAD' => (Colors.green, settings.tr('forecast_ahead'), Icons.trending_up),
      'BEHIND' => (Colors.orange, settings.tr('forecast_behind'), Icons.trending_down),
      _ => (Colors.blue, settings.tr('forecast_on_track'), Icons.trending_flat),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}

class _InsightsView extends StatefulWidget {
  const _InsightsView({required this.model});
  final FinanceViewModel model;

  @override
  State<_InsightsView> createState() => _InsightsViewState();
}

class _InsightsViewState extends State<_InsightsView> {
  String selectedFilter = 'ALL';

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    final filtered = widget.model.insights.where((insight) {
      if (selectedFilter == 'HIGH') return insight.severity == 'HIGH';
      if (selectedFilter == 'MEDIUM') return insight.severity == 'MEDIUM';
      if (selectedFilter == 'LOW') return insight.severity == 'LOW';
      return true;
    }).toList();

    return RefreshIndicator(
      onRefresh: widget.model.loadCore,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                FilterChip(
                  label: Text(settings.tr('filter_all')),
                  selected: selectedFilter == 'ALL',
                  onSelected: (_) => setState(() => selectedFilter = 'ALL'),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: Text(settings.tr('filter_high')),
                  selected: selectedFilter == 'HIGH',
                  onSelected: (_) => setState(() => selectedFilter = 'HIGH'),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: Text(settings.tr('filter_medium')),
                  selected: selectedFilter == 'MEDIUM',
                  onSelected: (_) => setState(() => selectedFilter = 'MEDIUM'),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: Text(settings.tr('filter_low')),
                  selected: selectedFilter == 'LOW',
                  onSelected: (_) => setState(() => selectedFilter = 'LOW'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          if (filtered.isEmpty)
            SizedBox(
              height: 200,
              child: EmptyState(label: settings.tr('no_insights')),
            ),
          ...filtered.map(
            (insight) => Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          _severityIcon(insight.severity),
                          color: _severityColor(insight.severity),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            settings.trText(insight.title),
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        Chip(
                          visualDensity: VisualDensity.compact,
                          label: Text(
                            settings.language == AppLanguage.vi
                                ? '${settings.tr('confidence')} ${(insight.confidence * 100).toStringAsFixed(0)}%'
                                : '${(insight.confidence * 100).toStringAsFixed(0)}% ${settings.tr('confidence')}',
                            style: const TextStyle(fontSize: 11),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(settings.trText(insight.description)),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: [
                        Chip(
                          avatar: const Icon(Icons.analytics, size: 14),
                          label: Text(insight.sourceMetric, style: const TextStyle(fontSize: 11)),
                          visualDensity: VisualDensity.compact,
                        ),
                        Chip(
                          avatar: const Icon(Icons.date_range, size: 14),
                          label: Text(
                            '${insight.periodStart.toLocal().toString().substring(0, 10)} ${settings.tr('date_to')} ${insight.periodEnd.toLocal().toString().substring(0, 10)}',
                            style: const TextStyle(fontSize: 11),
                          ),
                          visualDensity: VisualDensity.compact,
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
}

class _NotificationsView extends StatefulWidget {
  const _NotificationsView({required this.model});
  final FinanceViewModel model;

  @override
  State<_NotificationsView> createState() => _NotificationsViewState();
}

class _NotificationsViewState extends State<_NotificationsView> {
  bool unreadOnly = false;

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    final filtered = widget.model.notifications.where((n) {
      if (unreadOnly) return n.readAt == null;
      return true;
    }).toList();

    final unreadCount = widget.model.notifications.where((n) => n.readAt == null).length;

    return RefreshIndicator(
      onRefresh: widget.model.loadCore,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  FilterChip(
                    label: Text(settings.tr('filter_all')),
                    selected: !unreadOnly,
                    onSelected: (_) => setState(() => unreadOnly = false),
                  ),
                  const SizedBox(width: 8),
                  FilterChip(
                    label: Text('${settings.tr('filter_unread')} ($unreadCount)'),
                    selected: unreadOnly,
                    onSelected: (_) => setState(() => unreadOnly = true),
                  ),
                ],
              ),
              if (unreadCount > 0)
                TextButton.icon(
                  onPressed: () async {
                    final error = await widget.model.markAllNotificationsRead();
                    if (error != null && context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text(error)),
                      );
                    }
                  },
                  icon: const Icon(Icons.done_all, size: 18),
                  label: Text(settings.tr('mark_all_read')),
                ),
            ],
          ),
          const SizedBox(height: 12),
          if (filtered.isEmpty)
            SizedBox(
              height: 200,
              child: EmptyState(label: settings.tr('no_notifications')),
            ),
          ...filtered.map(
            (notification) => Card(
              margin: const EdgeInsets.only(bottom: 8),
              color: notification.readAt == null
                  ? Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.15)
                  : null,
              child: ListTile(
                leading: Icon(
                  notification.readAt == null
                      ? _severityIcon(notification.severity)
                      : Icons.mark_email_read_outlined,
                  color: _severityColor(notification.severity),
                ),
                title: Text(
                  settings.trText(notification.title),
                  style: TextStyle(
                    fontWeight: notification.readAt == null ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
                subtitle: Text(
                  '${settings.trText(notification.description)}\n${notification.createdAt.toLocal().toString().substring(0, 16)}',
                ),
                isThreeLine: true,
                onTap: notification.readAt == null
                    ? () async {
                        final error = await widget.model.markNotificationRead(notification.id);
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
}

class _MoreNavigationTile extends StatelessWidget {
  const _MoreNavigationTile({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ListTile(
    leading: Icon(icon),
    title: Text(label),
    trailing: const Icon(Icons.chevron_right),
    onTap: onTap,
  );
}

class _RecommendationsView extends StatelessWidget {
  const _RecommendationsView({required this.model});

  final FinanceViewModel model;

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    return RefreshIndicator(
      onRefresh: model.loadCore,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (model.recommendations.isEmpty)
            SizedBox(
              height: 200,
              child: EmptyState(label: settings.tr('no_recommendations')),
            ),
          ...model.recommendations.map(
            (recommendation) => Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Chip(
                          label: Text(settings.trText(recommendation.type)),
                          visualDensity: VisualDensity.compact,
                        ),
                        Chip(
                          avatar: const Icon(Icons.star, size: 14),
                          label: Text('${settings.tr('priority')} ${recommendation.priority}'),
                          visualDensity: VisualDensity.compact,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      settings.trText(recommendation.reason),
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            settings.tr('suggested_action'),
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(settings.trText(recommendation.suggestedAction)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.trending_up, size: 16, color: Colors.green),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            '${settings.tr('expected_impact')} ${settings.trText(recommendation.expectedImpact)}',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.green.shade800,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      children: [
                        FilledButton.tonal(
                          onPressed: () => model.updateRecommendation(
                            recommendation.id,
                            model.repository.acceptRecommendation,
                          ),
                          child: Text(settings.tr('btn_accept')),
                        ),
                        OutlinedButton(
                          onPressed: () => model.updateRecommendation(
                            recommendation.id,
                            model.repository.dismissRecommendation,
                          ),
                          child: Text(settings.tr('btn_dismiss')),
                        ),
                        TextButton.icon(
                          onPressed: () => model.updateRecommendation(
                            recommendation.id,
                            (id) => model.repository.giveRecommendationFeedback(
                              id,
                              'HELPFUL',
                            ),
                          ),
                          icon: const Icon(Icons.thumb_up_outlined, size: 16),
                          label: Text(settings.tr('btn_helpful')),
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

class GoalInput {
  const GoalInput({
    required this.name,
    required this.targetAmount,
    required this.currency,
    this.targetDate,
    this.priority = 1,
    this.description,
  });

  final String name;
  final int targetAmount;
  final String currency;
  final String? targetDate;
  final int priority;
  final String? description;
}

class GoalDialog extends StatefulWidget {
  const GoalDialog({super.key});

  @override
  State<GoalDialog> createState() => _GoalDialogState();
}

class _GoalDialogState extends State<GoalDialog> {
  final nameController = TextEditingController();
  final targetController = TextEditingController();
  final dateController = TextEditingController();
  final descController = TextEditingController();
  int priority = 1;

  @override
  void dispose() {
    nameController.dispose();
    targetController.dispose();
    dateController.dispose();
    descController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Create financial goal'),
    content: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: nameController,
            decoration: const InputDecoration(labelText: 'Goal Name (e.g. Emergency Fund)'),
          ),
          TextField(
            controller: targetController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Target Amount (VND)'),
          ),
          TextField(
            controller: dateController,
            decoration: const InputDecoration(
              labelText: 'Target Date (YYYY-MM-DD)',
              hintText: '2026-12-31',
            ),
          ),
          DropdownButtonFormField<int>(
            initialValue: priority,
            decoration: const InputDecoration(labelText: 'Priority'),
            items: const [1, 2, 3, 4, 5]
                .map((p) => DropdownMenuItem(value: p, child: Text('Priority $p')))
                .toList(),
            onChanged: (val) => setState(() => priority = val ?? 1),
          ),
          TextField(
            controller: descController,
            decoration: const InputDecoration(labelText: 'Description (optional)'),
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
          final target = int.tryParse(targetController.text);
          if (nameController.text.trim().isEmpty || target == null || target <= 0) {
            return;
          }
          Navigator.pop(
            context,
            GoalInput(
              name: nameController.text.trim(),
              targetAmount: target,
              currency: 'VND',
              targetDate: dateController.text.trim().isNotEmpty
                  ? dateController.text.trim()
                  : null,
              priority: priority,
              description: descController.text.trim().isNotEmpty
                  ? descController.text.trim()
                  : null,
            ),
          );
        },
        child: const Text('Create'),
      ),
    ],
  );
}

class GoalContributionInput {
  const GoalContributionInput({
    required this.amount,
    this.accountId,
    this.note,
  });

  final int amount;
  final String? accountId;
  final String? note;
}

class GoalContributionDialog extends StatefulWidget {
  const GoalContributionDialog({
    super.key,
    required this.goal,
    required this.accounts,
  });

  final GoalModel goal;
  final List<AccountModel> accounts;

  @override
  State<GoalContributionDialog> createState() => _GoalContributionDialogState();
}

class _GoalContributionDialogState extends State<GoalContributionDialog> {
  final amountController = TextEditingController();
  final noteController = TextEditingController();
  AccountModel? selectedAccount;

  @override
  void initState() {
    super.initState();
    if (widget.accounts.isNotEmpty) {
      selectedAccount = widget.accounts.first;
    }
  }

  @override
  void dispose() {
    amountController.dispose();
    noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text('Contribute to ${widget.goal.name}'),
    content: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        TextField(
          controller: amountController,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Contribution Amount (VND)'),
        ),
        if (widget.accounts.isNotEmpty)
          DropdownButtonFormField<AccountModel>(
            initialValue: selectedAccount,
            items: widget.accounts
                .map((a) => DropdownMenuItem(value: a, child: Text(a.name)))
                .toList(),
            onChanged: (val) => setState(() => selectedAccount = val),
            decoration: const InputDecoration(labelText: 'Source Account (optional)'),
          ),
        TextField(
          controller: noteController,
          decoration: const InputDecoration(labelText: 'Note (optional)'),
        ),
      ],
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
            GoalContributionInput(
              amount: amount,
              accountId: selectedAccount?.id,
              note: noteController.text.trim().isNotEmpty
                  ? noteController.text.trim()
                  : null,
            ),
          );
        },
        child: const Text('Contribute'),
      ),
    ],
  );
}
