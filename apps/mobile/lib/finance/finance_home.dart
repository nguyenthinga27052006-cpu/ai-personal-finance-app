import 'package:flutter/material.dart';
import 'dart:math' as math;

import '../auth/api_client.dart';
import '../admin/admin_dashboard.dart';
import '../ai/ai_screen.dart';
import '../settings/settings_controller.dart';
import '../settings/settings_dialog.dart';
import 'components.dart';
import 'finance_repository.dart';
import 'finance_view_model.dart';
import 'models.dart';
import 'receipt_ocr_dialog.dart';

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
                  _CategorySpendingReportView(model: viewModel),
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
                '📊 Biểu Đồ Chi Tiêu & Gợi Ý AI',
                settings.tr('nav_analytics'),
                settings.tr('nav_notifications'),
                settings.tr('nav_recommendations'),
                settings.tr('nav_ai_assistant'),
              ][tab.clamp(0, 9)],
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
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
                    selectedIndex: tab.clamp(0, 9),
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
                      const NavigationRailDestination(
                        icon: Icon(Icons.pie_chart_outline, color: Colors.teal),
                        selectedIcon: Icon(Icons.pie_chart, color: Colors.teal),
                        label: Text('Biểu đồ chi tiêu'),
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
    if (value == 7) {
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
              icon: Icons.pie_chart_outline,
              label: '📊 Biểu Đồ Chi Tiêu & Gợi Ý AI',
              onTap: () => Navigator.pop(context, 5),
            ),
            _MoreNavigationTile(
              icon: Icons.insights_outlined,
              label: settings.tr('nav_analytics'),
              onTap: () => Navigator.pop(context, 6),
            ),
            _MoreNavigationTile(
              icon: Icons.notifications_outlined,
              label: settings.tr('nav_notifications'),
              onTap: () => Navigator.pop(context, 7),
            ),
            _MoreNavigationTile(
              icon: Icons.lightbulb_outline,
              label: settings.tr('nav_recommendations'),
              onTap: () => Navigator.pop(context, 8),
            ),
            _MoreNavigationTile(
              icon: Icons.auto_awesome_outlined,
              label: settings.tr('nav_ai_assistant'),
              onTap: () => Navigator.pop(context, 9),
            ),
            if (widget.userRole.toUpperCase() == 'ADMIN' ||
                widget.email == 'admin@finance.app')
              _MoreNavigationTile(
                icon: Icons.admin_panel_settings_outlined,
                label: settings.tr('nav_admin_portal'),
                onTap: () => Navigator.pop(context, 10),
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
      builder: (context) => TransactionDialog(
        accounts: viewModel.accounts,
        categories: viewModel.categories,
      ),
    );
    if (values == null) return;
    final error = await viewModel.addTransaction(
      type: values.type,
      account: values.account,
      amount: values.amount,
      category: values.category,
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
    CategoryModel? selectedCategory = viewModel.categories.firstWhere(
      (cat) => cat.id == item.categoryId || cat.name == item.categoryName,
      orElse: () => viewModel.categories.isNotEmpty ? viewModel.categories.first : CategoryModel(id: '', name: '', type: 'BOTH', isSystem: true),
    );
    if (selectedCategory.id.isEmpty) selectedCategory = null;

    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text('Chỉnh sửa giao dịch'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: amountController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Số tiền (VND)'),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<CategoryModel?>(
                  initialValue: selectedCategory,
                  items: [
                    const DropdownMenuItem<CategoryModel?>(
                      value: null,
                      child: Text('Chưa chọn danh mục'),
                    ),
                    ...viewModel.categories.map(
                      (cat) => DropdownMenuItem<CategoryModel?>(
                        value: cat,
                        child: Text(cat.name),
                      ),
                    ),
                  ],
                  onChanged: (val) => setDialogState(() => selectedCategory = val),
                  decoration: const InputDecoration(
                    labelText: 'Danh mục',
                    prefixIcon: Icon(Icons.category),
                  ),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: descriptionController,
                  decoration: const InputDecoration(labelText: 'Mô tả / Ghi chú'),
                ),
              ],
            ),
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
      ),
    );

    if (result == true) {
      final amount = int.tryParse(amountController.text.trim()) ?? item.amount;
      final error = await viewModel.editTransaction(
        id: item.id,
        amount: amount,
        categoryId: selectedCategory?.id,
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
        AnimatedTapScale(
          onTap: () {
            final state = context.findAncestorStateOfType<_FinanceHomeState>();
            if (state != null && state.widget.gateway is ApiClient) {
              ReceiptOCRDialog.show(
                context,
                apiClient: state.widget.gateway as ApiClient,
                accounts: model.accounts,
                categories: model.categories,
                onSuccess: model.loadCore,
              );
            }
          },
          child: Card(
            color: Colors.teal.shade700,
            elevation: 4,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: const BoxDecoration(
                      color: Colors.white24,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.document_scanner, size: 28, color: Colors.white),
                  ),
                  const SizedBox(width: 14),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '📷 Quét Hóa Đơn OCR (AI)',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Bấm vào đây để chọn file ảnh hóa đơn & trích xuất tự động!',
                          style: TextStyle(fontSize: 12, color: Colors.white70),
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.arrow_forward_ios, color: Colors.white, size: 16),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
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
        _QuickFeatureShortcuts(onSelectTab: (index) {
          final state = context.findAncestorStateOfType<_FinanceHomeState>();
          if (state != null) {
            state._selectTab(index);
          }
        }),
        const SizedBox(height: 16),
        _CategoryAnalyticsCard(model: model),
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

class _QuickFeatureShortcuts extends StatelessWidget {
  const _QuickFeatureShortcuts({required this.onSelectTab});
  final ValueChanged<int> onSelectTab;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 4, bottom: 8),
          child: Text(
            '🚀 Tính Năng Nổi Bật',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
        ),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              _FeatureShortcutChip(
                icon: Icons.pie_chart,
                color: Colors.teal,
                label: 'Biểu đồ & Gợi ý AI',
                onTap: () => onSelectTab(5),
              ),
              const SizedBox(width: 8),
              _FeatureShortcutChip(
                icon: Icons.flag,
                color: Colors.orange,
                label: 'Mục tiêu tiết kiệm',
                onTap: () => onSelectTab(4),
              ),
              const SizedBox(width: 8),
              _FeatureShortcutChip(
                icon: Icons.insights,
                color: Colors.purple,
                label: 'Phân tích AI',
                onTap: () => onSelectTab(6),
              ),
              const SizedBox(width: 8),
              _FeatureShortcutChip(
                icon: Icons.smart_toy,
                color: Colors.blue,
                label: 'Trợ lý AI Chat',
                onTap: () => onSelectTab(9),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _FeatureShortcutChip extends StatelessWidget {
  const _FeatureShortcutChip({
    required this.icon,
    required this.color,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final Color color;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return AnimatedTapScale(
      onTap: onTap,
      child: Material(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: color.withOpacity(0.3)),
            ),
            child: Row(
              children: [
                Icon(icon, color: color, size: 18),
                const SizedBox(width: 8),
                Text(
                  label,
                  style: TextStyle(
                    color: Colors.teal.shade900,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

Color _getCategoryColor(String name, int index) {
  final lower = name.toLowerCase();
  if (lower.contains('ăn') || lower.contains('cafe') || lower.contains('cơm') || lower.contains('nhà hàng') || lower.contains('bánh')) {
    return const Color(0xFFE55737); // Orange Red
  }
  if (lower.contains('hóa đơn') || lower.contains('tiện ích') || lower.contains('điện') || lower.contains('nước') || lower.contains('mạng')) {
    return const Color(0xFF2E7D32); // Emerald Green
  }
  if (lower.contains('siêu thị') || lower.contains('bách hóa') || lower.contains('winmart') || lower.contains('chợ')) {
    return const Color(0xFF009688); // Teal Green
  }
  if (lower.contains('mua sắm') || lower.contains('đồ dùng') || lower.contains('shopee') || lower.contains('quần áo') || lower.contains('lazada') || lower.contains('tiki')) {
    return const Color(0xFF0288D1); // Ocean Blue
  }
  if (lower.contains('đi lại') || lower.contains('xăng') || lower.contains('grab') || lower.contains('be') || lower.contains('xe') || lower.contains('taxi')) {
    return const Color(0xFFF57C00); // Amber Gold
  }
  if (lower.contains('giải trí') || lower.contains('phim') || lower.contains('game') || lower.contains('du lịch')) {
    return const Color(0xFF8E24AA); // Purple
  }
  if (lower.contains('sức khỏe') || lower.contains('thuốc') || lower.contains('khám') || lower.contains('bệnh viện')) {
    return const Color(0xFFD81B60); // Rose Pink
  }

  final palette = [
    const Color(0xFFE55737),
    const Color(0xFF2E7D32),
    const Color(0xFF0288D1),
    const Color(0xFFF57C00),
    const Color(0xFF009688),
    const Color(0xFF8E24AA),
    const Color(0xFFD81B60),
    const Color(0xFF3F51B5),
  ];
  return palette[index % palette.length];
}

class _CategoryAnalyticsCard extends StatelessWidget {
  const _CategoryAnalyticsCard({required this.model});
  final FinanceViewModel model;

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    final map = <String, _CategoryAccumulator>{};
    int totalExpense = 0;

    for (final tx in model.transactions) {
      if (tx.type.toUpperCase() == 'EXPENSE') {
        final catInfo = _resolveCategoryInfo(tx, model.categories);
        final acc = map.putIfAbsent(
          catInfo.name,
          () => _CategoryAccumulator(catInfo.name, catInfo.color, catInfo.icon),
        );
        acc.amount += tx.amount;
        acc.count += 1;
        totalExpense += tx.amount;
      }
    }

    final categoryItems = map.values.map((acc) {
      final pct = totalExpense > 0 ? (acc.amount / totalExpense) * 100 : 0.0;
      return CategorySpendingItem(
        name: acc.name,
        amount: acc.amount,
        percentage: pct,
        color: acc.color,
        icon: acc.icon,
        count: acc.count,
      );
    }).toList()..sort((a, b) => b.amount.compareTo(a.amount));

    final topCategory = categoryItems.isNotEmpty ? categoryItems.first.name : '';
    final topAmount = categoryItems.isNotEmpty ? categoryItems.first.amount : 0;
    final targetSaving = (topAmount * 0.25).round();

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.pie_chart, color: Colors.teal, size: 20),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    '📊 Biểu Đồ Chi Tiêu & Gợi Ý AI',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                  ),
                ),
                const SizedBox(width: 4),
                InkWell(
                  borderRadius: BorderRadius.circular(8),
                  onTap: () {
                    final state = context.findAncestorStateOfType<_FinanceHomeState>();
                    state?._selectTab(5);
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: const [
                        Text(
                          'Chi tiết',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.teal,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(width: 2),
                        Icon(Icons.arrow_forward_ios, size: 10, color: Colors.teal),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (categoryItems.isNotEmpty) ...[
              // Pie chart visual
              Center(
                child: SizedBox(
                  width: 180,
                  height: 180,
                  child: CustomPaint(
                    painter: _SolidPiePainter(
                      items: categoryItems,
                      backgroundColor: Colors.grey.shade200,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Chi Tiêu Theo Danh Mục:',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.grey.shade800),
              ),
              const SizedBox(height: 10),
              ...categoryItems.map((item) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 12,
                                height: 12,
                                decoration: BoxDecoration(color: item.color, shape: BoxShape.circle),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                item.name,
                                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                              ),
                            ],
                          ),
                          MoneyText(
                            item.amount,
                            currency: 'VND',
                            style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.red.shade700),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: (item.percentage / 100).clamp(0.0, 1.0),
                          minHeight: 8,
                          backgroundColor: item.color.withOpacity(0.15),
                          valueColor: AlwaysStoppedAnimation<Color>(item.color),
                        ),
                      ),
                    ],
                  ),
                );
              }),
              const Divider(height: 24),
              // AI Recommendation Box matching Web
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50.withOpacity(0.8),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.amber.shade300, width: 1.2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(
                            color: Colors.amber.shade700,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.lightbulb, color: Colors.white, size: 16),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            '💡 Gợi Ý AI Cho Ngày Mai & Kế Hoạch Chi Tiêu',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: Colors.amber.shade900,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.amber.shade200),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.trending_down, color: Colors.red, size: 16),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  'Mục chi tiêu nhiều nhất: $topCategory',
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Hôm nay / kỳ này bạn đã tiêu ${settings.trText(settings.formatAmount(topAmount))} vào [$topCategory].',
                            style: const TextStyle(fontSize: 12),
                          ),
                          const Divider(height: 12),
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('👉 ', style: TextStyle(fontSize: 13)),
                              Expanded(
                                child: Text(
                                  'Gợi ý ngày mai: Đặt mục tiêu cắt giảm 20 - 30% chi tiêu cho [$topCategory] (tiết kiệm khoảng ${settings.trText(settings.formatAmount(targetSaving))}) bằng cách ưu tiên nhu cầu thiết yếu hơn.',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.teal.shade900,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.check_circle_outline, color: Colors.green, size: 16),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            'Dành ${settings.trText(settings.formatAmount(targetSaving))} tiết kiệm được bổ sung ngay vào Quỹ Tiết Kiệm.',
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ] else ...[
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
                child: Column(
                  children: [
                    Icon(Icons.pie_chart_outline, size: 48, color: Colors.teal.shade200),
                    const SizedBox(height: 12),
                    Text(
                      'Chưa có dữ liệu chi tiêu',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.grey.shade800),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Hãy tạo giao dịch chi tiêu đầu tiên để xem biểu đồ phân tích và gợi ý AI!',
                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

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

class _TransactionsView extends StatefulWidget {
  const _TransactionsView({
    required this.model,
    required this.onEdit,
    required this.onDelete,
  });

  final FinanceViewModel model;
  final ValueChanged<TransactionModel> onEdit;
  final ValueChanged<TransactionModel> onDelete;

  @override
  State<_TransactionsView> createState() => _TransactionsViewState();
}

class _TransactionsViewState extends State<_TransactionsView> {
  String searchQuery = '';

  @override
  Widget build(BuildContext context) {
    final query = searchQuery.trim().toLowerCase();
    final filtered = widget.model.transactions.where((item) {
      if (query.isEmpty) return true;
      final desc = (item.description ?? '').toLowerCase();
      final amountStr = item.amount.toString();
      final typeStr = item.type.toLowerCase();
      return desc.contains(query) || amountStr.contains(query) || typeStr.contains(query);
    }).toList();

    return RefreshIndicator(
      onRefresh: widget.model.loadCore,
      child: ListView(
        padding: const EdgeInsets.symmetric(vertical: 8),
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              decoration: InputDecoration(
                hintText: '🔍 Tìm kiếm giao dịch (mô tả, số tiền)...',
                prefixIcon: const Icon(Icons.search, color: Colors.teal),
                suffixIcon: searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, size: 18),
                        onPressed: () => setState(() => searchQuery = ''),
                      )
                    : null,
                filled: true,
                fillColor: Colors.teal.shade50.withValues(alpha: 0.3),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
              onChanged: (val) => setState(() => searchQuery = val),
            ),
          ),
          const SizedBox(height: 4),
          if (filtered.isEmpty)
            SizedBox(
              height: 200,
              child: EmptyState(
                label: searchQuery.isNotEmpty
                    ? 'Không tìm thấy giao dịch nào với từ khóa "$searchQuery"'
                    : 'Chưa có giao dịch nào. Bấm nút + bên dưới để thêm mới!',
              ),
            ),
          ...filtered.map(
            (item) => TransactionTile(
              transaction: item,
              onTap: () => _showDetail(context, item),
              onEdit: () => widget.onEdit(item),
              onDelete: () => widget.onDelete(item),
            ),
          ),
        ],
      ),
    );
  }
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
            (goal) => AnimatedTapScale(
              onTap: () => onAddContribution(goal),
              child: Card(
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
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('${settings.tr('nav_goals')}: ', style: TextStyle(color: Colors.grey.shade700, fontSize: 13)),
                            MoneyText(goal.target, currency: goal.currency, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('${settings.tr('add_contribution')}: ', style: TextStyle(color: Colors.grey.shade700, fontSize: 13)),
                            MoneyText(goal.current, currency: goal.currency, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.teal.shade700)),
                          ],
                        ),
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

class _CategoryInfo {
  const _CategoryInfo({
    required this.name,
    required this.color,
    required this.icon,
  });

  final String name;
  final Color color;
  final IconData icon;
}

_CategoryInfo _resolveCategoryInfo(TransactionModel tx, List<CategoryModel> categories) {
  String? rawName = tx.categoryName;
  if ((rawName == null || rawName.trim().isEmpty) && tx.categoryId != null && tx.categoryId!.isNotEmpty) {
    for (final cat in categories) {
      if (cat.id == tx.categoryId) {
        rawName = cat.name;
        break;
      }
    }
  }

  // 1. If an explicit Category was assigned, ALWAYS use its exact name without alias mutation
  if (rawName != null && rawName.trim().isNotEmpty && rawName.trim() != 'Chưa chọn danh mục') {
    final cleanName = rawName.trim();
    final lowerName = cleanName.toLowerCase();

    IconData icon = Icons.category_outlined;
    Color color = _getCategoryColor(cleanName, cleanName.hashCode);

    if (lowerName == 'shopping' || lowerName == 'mua sắm & thiết bị' || lowerName == 'mua sắm đồ dùng' || lowerName == 'mua sắm') {
      icon = Icons.shopping_bag_outlined;
      color = const Color(0xFF29B6F6);
    } else if (lowerName == 'food' || lowerName == 'ăn uống & siêu thị' || lowerName == 'ăn uống & cafe' || lowerName == 'ăn uống' || lowerName == 'siêu thị & bách hóa') {
      icon = Icons.restaurant;
      color = const Color(0xFFE55737);
    } else if (lowerName == 'housing' || lowerName == 'tiền nhà & hóa đơn' || lowerName == 'tiền nhà') {
      icon = Icons.home_outlined;
      color = Colors.indigo.shade600;
    } else if (lowerName == 'utilities' || lowerName == 'điện nước & internet' || lowerName == 'hóa đơn & tiện ích' || lowerName == 'điện nước') {
      icon = Icons.receipt_long_outlined;
      color = const Color(0xFF2E7D32);
    } else if (lowerName == 'transportation' || lowerName == 'di chuyển & xăng xe' || lowerName == 'di chuyển' || lowerName == 'đi lại') {
      icon = Icons.directions_car_outlined;
      color = const Color(0xFFFBC02D);
    } else if (lowerName == 'health' || lowerName == 'sức khỏe') {
      icon = Icons.medical_services_outlined;
      color = Colors.teal.shade600;
    } else if (lowerName == 'education' || lowerName == 'giáo dục') {
      icon = Icons.school_outlined;
      color = Colors.deepOrange.shade600;
    } else if (lowerName == 'entertainment' || lowerName == 'giải trí' || lowerName == 'giải trí & tiếp khách') {
      icon = Icons.sports_esports_outlined;
      color = Colors.purple.shade600;
    } else if (lowerName == 'subscription' || lowerName == 'đăng ký dịch vụ') {
      icon = Icons.subscriptions_outlined;
      color = Colors.pink.shade600;
    } else if (lowerName == 'other' || lowerName == 'chi tiêu khác') {
      icon = Icons.category_outlined;
      color = Colors.blueGrey.shade600;
    }

    return _CategoryInfo(
      name: cleanName,
      color: color,
      icon: icon,
    );
  }

  // 2. Fallback ONLY when NO category is assigned: infer from description keywords
  final desc = (tx.description ?? '').toLowerCase();
  if (desc.contains('điện') || desc.contains('nước') || desc.contains('mạng') ||
      desc.contains('internet') || desc.contains('wifi') || desc.contains('electric') ||
      desc.contains('power') || desc.contains('utility') || desc.contains('utilities') ||
      desc.contains('bill')) {
    return const _CategoryInfo(
      name: 'Điện nước & Internet',
      color: Color(0xFF2E7D32),
      icon: Icons.receipt_long_outlined,
    );
  } else if (desc.contains('cơm') || desc.contains('phở') || desc.contains('bún') ||
             desc.contains('ăn') || desc.contains('lẩu') || desc.contains('cafe') ||
             desc.contains('trà') || desc.contains('coffee') || desc.contains('nhà hàng') ||
             desc.contains('bánh') || desc.contains('food') || desc.contains('restaurant')) {
    return const _CategoryInfo(
      name: 'Ăn uống & Siêu thị',
      color: Color(0xFFE55737),
      icon: Icons.restaurant,
    );
  } else if (desc.contains('chợ') || desc.contains('siêu thị') || desc.contains('shopee') ||
             desc.contains('tiki') || desc.contains('lazada') || desc.contains('quần áo') ||
             desc.contains('mua sắm') || desc.contains('đồ') || desc.contains('shopping') ||
             desc.contains('store')) {
    return const _CategoryInfo(
      name: 'Mua sắm & Thiết bị',
      color: Color(0xFF29B6F6),
      icon: Icons.shopping_bag_outlined,
    );
  } else if (desc.contains('xăng') || desc.contains('grab') || desc.contains('be') ||
             desc.contains('taxi') || desc.contains('gửi xe') || desc.contains('vé') ||
             desc.contains('xe') || desc.contains('transport') || desc.contains('gas')) {
    return const _CategoryInfo(
      name: 'Di chuyển & Xăng xe',
      color: Color(0xFFFBC02D),
      icon: Icons.directions_car_outlined,
    );
  } else if (desc.contains('phim') || desc.contains('game') || desc.contains('du lịch') ||
             desc.contains('chơi') || desc.contains('entertainment') || desc.contains('movie')) {
    return _CategoryInfo(
      name: 'Giải trí',
      color: Colors.purple.shade600,
      icon: Icons.sports_esports_outlined,
    );
  } else if (desc.contains('thuốc') || desc.contains('khám') || desc.contains('bệnh viện') ||
             desc.contains('sức khỏe') || desc.contains('health') || desc.contains('doctor')) {
    return _CategoryInfo(
      name: 'Sức khỏe',
      color: Colors.teal.shade600,
      icon: Icons.medical_services_outlined,
    );
  }

  return _CategoryInfo(
    name: 'Chi tiêu khác',
    color: Colors.blueGrey.shade600,
    icon: Icons.category_outlined,
  );
}

class _CategoryAccumulator {
  _CategoryAccumulator(this.name, this.color, this.icon);
  final String name;
  final Color color;
  final IconData icon;
  int amount = 0;
  int count = 0;
}

class CategorySpendingItem {
  CategorySpendingItem({
    required this.name,
    required this.amount,
    required this.percentage,
    required this.color,
    required this.icon,
    required this.count,
  });

  final String name;
  final int amount;
  final double percentage;
  final Color color;
  final IconData icon;
  final int count;
}

class _SolidPiePainter extends CustomPainter {
  _SolidPiePainter({required this.items, required this.backgroundColor});

  final List<CategorySpendingItem> items;
  final Color backgroundColor;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    final rect = Rect.fromCircle(center: center, radius: radius);

    if (items.isEmpty) {
      final bgPaint = Paint()
        ..color = backgroundColor
        ..style = PaintingStyle.fill;
      canvas.drawCircle(center, radius, bgPaint);
      return;
    }

    double startAngle = -3.141592653589793 / 2;
    for (final item in items) {
      final sweepAngle = (item.percentage / 100) * 2 * 3.141592653589793;
      final slicePaint = Paint()
        ..color = item.color
        ..style = PaintingStyle.fill;

      canvas.drawArc(rect, startAngle, sweepAngle, true, slicePaint);

      final borderPaint = Paint()
        ..color = Colors.white
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.0;
      canvas.drawArc(rect, startAngle, sweepAngle, true, borderPaint);

      if (sweepAngle >= 0.15) {
        final midAngle = startAngle + sweepAngle / 2;
        final textRadius = radius * 0.62;
        
        // Calculate exact (x, y) along midAngle ray
        final textXCalc = center.dx + textRadius * _cos(midAngle);
        final textYCalc = center.dy + textRadius * _sin(midAngle);

        final pctText = '${item.percentage.toStringAsFixed(0)}%';
        final textSpan = TextSpan(
          text: pctText,
          style: const TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        );

        final textPainter = TextPainter(
          text: textSpan,
          textDirection: TextDirection.ltr,
        );
        textPainter.layout();

        final textOffset = Offset(
          textXCalc - textPainter.width / 2,
          textYCalc - textPainter.height / 2,
        );
        textPainter.paint(canvas, textOffset);
      }

      startAngle += sweepAngle;
    }
  }

  double _cos(double radians) {
    return math.cos(radians);
  }

  double _sin(double radians) {
    return math.sin(radians);
  }

  @override
  bool shouldRepaint(covariant _SolidPiePainter oldDelegate) => true;
}

class _CategorySpendingReportView extends StatefulWidget {
  const _CategorySpendingReportView({required this.model});
  final FinanceViewModel model;

  @override
  State<_CategorySpendingReportView> createState() => _CategorySpendingReportViewState();
}

class _CategorySpendingReportViewState extends State<_CategorySpendingReportView> {
  String timeFrame = 'TODAY'; // 'TODAY', 'MONTH', 'ALL'

  List<CategorySpendingItem> _getCategoryItems() {
    final now = DateTime.now();
    final expenseTx = widget.model.transactions.where((t) {
      if (t.type != 'EXPENSE') return false;
      if (timeFrame == 'TODAY') {
        return t.transactionDate.year == now.year &&
            t.transactionDate.month == now.month &&
            t.transactionDate.day == now.day;
      } else if (timeFrame == 'MONTH') {
        return t.transactionDate.year == now.year &&
            t.transactionDate.month == now.month;
      }
      return true;
    }).toList();

    if (expenseTx.isEmpty) return [];

    final map = <String, _CategoryAccumulator>{};
    for (final t in expenseTx) {
      final catInfo = _resolveCategoryInfo(t, widget.model.categories);
      final acc = map.putIfAbsent(
        catInfo.name,
        () => _CategoryAccumulator(catInfo.name, catInfo.color, catInfo.icon),
      );
      acc.amount += t.amount;
      acc.count += 1;
    }

    final totalSpend = map.values.fold<int>(0, (sum, acc) => sum + acc.amount);
    if (totalSpend <= 0) return [];

    final list = map.values.map((acc) {
      return CategorySpendingItem(
        name: acc.name,
        amount: acc.amount,
        percentage: (acc.amount / totalSpend) * 100,
        color: acc.color,
        icon: acc.icon,
        count: acc.count,
      );
    }).toList();

    list.sort((a, b) => b.amount.compareTo(a.amount));
    return list;
  }

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    final categoryItems = _getCategoryItems();
    final totalSpend = categoryItems.fold<int>(0, (sum, item) => sum + item.amount);

    return RefreshIndicator(
      onRefresh: widget.model.loadCore,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Time range filter bar
          Card(
            margin: const EdgeInsets.only(bottom: 16),
            elevation: 1.5,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.pie_chart, color: Colors.teal),
                      const SizedBox(width: 8),
                      Text(
                        'Phân Tích Chi Tiêu Theo Danh Mục',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        FilterChip(
                          avatar: const Icon(Icons.today, size: 16),
                          label: const Text('Hôm nay'),
                          selected: timeFrame == 'TODAY',
                          onSelected: (_) => setState(() => timeFrame = 'TODAY'),
                        ),
                        const SizedBox(width: 8),
                        FilterChip(
                          avatar: const Icon(Icons.calendar_month, size: 16),
                          label: const Text('Tháng này'),
                          selected: timeFrame == 'MONTH',
                          onSelected: (_) => setState(() => timeFrame = 'MONTH'),
                        ),
                        const SizedBox(width: 8),
                        FilterChip(
                          avatar: const Icon(Icons.all_inclusive, size: 16),
                          label: const Text('Tất cả'),
                          selected: timeFrame == 'ALL',
                          onSelected: (_) => setState(() => timeFrame = 'ALL'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Solid Pie Chart Card (Matching User Reference Image)
          Card(
            margin: const EdgeInsets.only(bottom: 16),
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        timeFrame == 'TODAY'
                            ? 'Biểu Đồ Chi Tiêu Hôm Nay'
                            : timeFrame == 'MONTH'
                                ? 'Biểu Đồ Chi Tiêu Tháng Này'
                                : 'Biểu Đồ Chi Tiêu Tổng Thể',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: Colors.grey.shade800,
                            ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.red.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.red.shade200),
                        ),
                        child: MoneyText(
                          totalSpend,
                          currency: 'VND',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: Colors.red.shade700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  
                  // Top Legend (Colored Square Blocks + Category Names)
                  if (categoryItems.isNotEmpty) ...[
                    Wrap(
                      alignment: WrapAlignment.center,
                      spacing: 16,
                      runSpacing: 10,
                      children: categoryItems.map((item) {
                        return Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 16,
                              height: 16,
                              decoration: BoxDecoration(
                                color: item.color,
                                borderRadius: BorderRadius.circular(3),
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              item.name,
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 24),
                    // Solid Pie Chart with Percentage drawn inside slices
                    Center(
                      child: SizedBox(
                        width: 220,
                        height: 220,
                        child: CustomPaint(
                          painter: _SolidPiePainter(
                            items: categoryItems,
                            backgroundColor: Colors.grey.shade200,
                          ),
                        ),
                      ),
                    ),
                  ] else ...[
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 24),
                      child: Text(
                        'Chưa có giao dịch chi tiêu nào trong khoảng thời gian này.',
                        style: TextStyle(color: Colors.grey.shade600, fontStyle: FontStyle.italic),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),

          // Category Spending Breakdown List
          if (categoryItems.isNotEmpty) ...[
            Padding(
              padding: const EdgeInsets.only(left: 4, bottom: 8),
              child: Text(
                '📊 Chi Tiêu Theo Danh Mục',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ),
            ...categoryItems.map((item) {
              return Card(
                margin: const EdgeInsets.only(bottom: 10),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 18,
                            backgroundColor: item.color.withValues(alpha: 0.15),
                            child: Icon(item.icon, color: item.color, size: 20),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  item.name,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                ),
                                Text(
                                  '${item.count} giao dịch (${item.percentage.toStringAsFixed(1)}% tổng chi)',
                                  style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                                ),
                              ],
                            ),
                          ),
                          MoneyText(
                            item.amount,
                            currency: 'VND',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 15,
                              color: Colors.red.shade700,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(6),
                        child: LinearProgressIndicator(
                          value: (item.percentage / 100).clamp(0.0, 1.0),
                          minHeight: 6,
                          color: item.color,
                          backgroundColor: item.color.withValues(alpha: 0.15),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }),
            const SizedBox(height: 12),
          ],

          // AI Smart Advice Card for Tomorrow
          Card(
            margin: const EdgeInsets.only(bottom: 20),
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: Colors.amber.shade400, width: 1.5),
            ),
            color: Colors.amber.shade50.withValues(alpha: 0.5),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade700,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.lightbulb, color: Colors.white, size: 20),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          '💡 Gợi Ý AI Cho Ngày Mai & Kế Hoạch Chi Tiêu',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: Colors.amber.shade900,
                              ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (categoryItems.isNotEmpty) ...[
                    Builder(
                      builder: (context) {
                        final topCategory = categoryItems.first;
                        final targetSaving = (topCategory.amount * 0.25).round();
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(10),
                                border: Border.all(color: Colors.amber.shade200),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      const Icon(Icons.trending_down, color: Colors.red, size: 18),
                                      const SizedBox(width: 6),
                                      Expanded(
                                        child: Text(
                                          'Mục chi tiêu nhiều nhất: ${topCategory.name}',
                                          style: const TextStyle(fontWeight: FontWeight.bold),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    'Hôm nay / kỳ này bạn đã tiêu ${settings.trText(settings.formatAmount(topCategory.amount))} vào [${topCategory.name}], chiếm ${topCategory.percentage.toStringAsFixed(1)}% tổng chi tiêu.',
                                    style: const TextStyle(fontSize: 13),
                                  ),
                                  const Divider(height: 16),
                                  Row(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text('👉 ', style: TextStyle(fontSize: 14)),
                                      Expanded(
                                        child: Text(
                                          'Gợi ý ngày mai: Đặt mục tiêu cắt giảm 20 - 30% chi tiêu cho [${topCategory.name}] (tiết kiệm khoảng ${settings.trText(settings.formatAmount(targetSaving))}) bằng cách ưu tiên các nhu cầu thiết yếu hơn.',
                                          style: TextStyle(
                                            fontSize: 13,
                                            fontWeight: FontWeight.w600,
                                            color: Colors.teal.shade900,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 10),
                            Row(
                              children: [
                                const Icon(Icons.check_circle_outline, color: Colors.green, size: 18),
                                const SizedBox(width: 6),
                                Expanded(
                                  child: Text(
                                    'Dành ${settings.trText(settings.formatAmount(targetSaving))} tiết kiệm được bổ sung ngay vào Quỹ Tiết Kiệm hoặc Dự Phòng Khẩn Cấp.',
                                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        );
                      },
                    ),
                  ] else ...[
                    const Text(
                      'Tài chính ngày hôm nay của bạn rất tuyệt vời! Chưa có khoản chi tiêu lớn nào được ghi nhận. Hãy tiếp tục duy trì thói quen tiết kiệm cho ngày mai nhé!',
                      style: TextStyle(fontSize: 13),
                    ),
                  ],
                ],
              ),
            ),
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
                            '${(insight.confidence * 100).toStringAsFixed(0)}% tin cậy',
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
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
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
                if (unreadCount > 0) ...[
                  const SizedBox(width: 12),
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
              ],
            ),
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
    this.category,
    required this.description,
  });

  final String type;
  final AccountModel account;
  final int amount;
  final CategoryModel? category;
  final String description;
}

class TransactionDialog extends StatefulWidget {
  const TransactionDialog({
    super.key,
    required this.accounts,
    this.categories = const [],
  });

  final List<AccountModel> accounts;
  final List<CategoryModel> categories;

  @override
  State<TransactionDialog> createState() => _TransactionDialogState();
}

class _TransactionDialogState extends State<TransactionDialog> {
  late final TextEditingController amountController;
  late final TextEditingController noteController;
  var type = 'EXPENSE';
  late AccountModel account;
  CategoryModel? category;

  @override
  void initState() {
    super.initState();
    amountController = TextEditingController();
    noteController = TextEditingController();
    account = widget.accounts.first;
    if (widget.categories.isNotEmpty) {
      final filtered = widget.categories
          .where((cat) => cat.type == type || cat.type == 'BOTH')
          .toList();
      category = filtered.isNotEmpty ? filtered.first : widget.categories.first;
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
    title: const Text('Tạo giao dịch mới'),
    content: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          DropdownButtonFormField<String>(
            initialValue: type,
            items: const [
              DropdownMenuItem(value: 'EXPENSE', child: Text('Chi tiêu (Expense)')),
              DropdownMenuItem(value: 'INCOME', child: Text('Thu nhập (Income)')),
            ],
            onChanged: (value) {
              if (value == null) return;
              setState(() {
                type = value;
                if (widget.categories.isNotEmpty) {
                  final filtered = widget.categories
                      .where((cat) => cat.type == type || cat.type == 'BOTH')
                      .toList();
                  category = filtered.isNotEmpty ? filtered.first : widget.categories.first;
                }
              });
            },
            decoration: const InputDecoration(labelText: 'Loại giao dịch'),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: amountController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Số tiền (VND)'),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<AccountModel>(
            initialValue: account,
            items: widget.accounts
                .map(
                  (item) =>
                      DropdownMenuItem(value: item, child: Text(item.name)),
                )
                .toList(),
            onChanged: (value) => setState(() => account = value!),
            decoration: const InputDecoration(labelText: 'Tài khoản thanh toán'),
          ),
          const SizedBox(height: 8),
          if (widget.categories.isNotEmpty)
            DropdownButtonFormField<CategoryModel?>(
              initialValue: category,
              items: [
                const DropdownMenuItem<CategoryModel?>(
                  value: null,
                  child: Text('Chưa chọn danh mục'),
                ),
                ...widget.categories
                    .where((cat) => cat.type == type || cat.type == 'BOTH')
                    .map(
                      (cat) => DropdownMenuItem<CategoryModel?>(
                        value: cat,
                        child: Text(cat.name),
                      ),
                    ),
              ],
              onChanged: (value) => setState(() => category = value),
              decoration: const InputDecoration(
                labelText: 'Danh mục (Category)',
                prefixIcon: Icon(Icons.category),
              ),
            ),
          const SizedBox(height: 8),
          TextField(
            controller: noteController,
            decoration: const InputDecoration(labelText: 'Ghi chú / Mô tả'),
          ),
        ],
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Hủy'),
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
              category: category,
              description: noteController.text,
            ),
          );
        },
        child: const Text('Lưu giao dịch'),
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
