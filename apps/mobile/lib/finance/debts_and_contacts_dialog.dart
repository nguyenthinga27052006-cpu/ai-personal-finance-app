import 'package:flutter/material.dart';

import 'components.dart';
import 'finance_view_model.dart';
import 'models.dart';

class DebtsAndContactsDialog extends StatefulWidget {
  const DebtsAndContactsDialog({
    super.key,
    required this.model,
    this.initialTab = 0,
  });

  final FinanceViewModel model;
  final int initialTab;

  static Future<void> show(
    BuildContext context, {
    required FinanceViewModel model,
    int initialTab = 0,
  }) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => DebtsAndContactsDialog(
        model: model,
        initialTab: initialTab,
      ),
    );
  }

  @override
  State<DebtsAndContactsDialog> createState() => _DebtsAndContactsDialogState();
}

class _DebtsAndContactsDialogState extends State<DebtsAndContactsDialog>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: 2,
      vsync: this,
      initialIndex: widget.initialTab,
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.model,
      builder: (context, _) {
        return SizedBox(
          height: MediaQuery.of(context).size.height * 0.88,
          child: Column(
            children: [
              const SizedBox(height: 12),
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade400,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 8),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Sổ Nợ & Danh Bạ Hỗ Trợ',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ],
                ),
              ),
              TabBar(
                controller: _tabController,
                tabs: const [
                  Tab(icon: Icon(Icons.handshake_outlined), text: 'Sổ Nợ / Cho Vay'),
                  Tab(icon: Icon(Icons.contacts_outlined), text: 'Danh Bạ Hỗ Trợ'),
                ],
              ),
              Expanded(
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _DebtsTab(model: widget.model),
                    _ContactsTab(model: widget.model),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _DebtsTab extends StatelessWidget {
  const _DebtsTab({required this.model});

  final FinanceViewModel model;

  @override
  Widget build(BuildContext context) {
    final borrowDebts = model.debts.where((d) => d.type == 'BORROW').toList();
    final lendDebts = model.debts.where((d) => d.type == 'LEND').toList();

    final totalBorrow = borrowDebts
        .where((d) => d.status == 'ACTIVE')
        .fold<int>(0, (sum, d) => sum + d.remainingAmount);
    final totalLend = lendDebts
        .where((d) => d.status == 'ACTIVE')
        .fold<int>(0, (sum, d) => sum + d.remainingAmount);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: Card(
                color: Colors.orange.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Tôi nợ (Cần trả)',
                        style: TextStyle(fontSize: 12, color: Colors.orange, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      MoneyText(
                        totalBorrow,
                        currency: 'VND',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.deepOrange),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Card(
                color: Colors.green.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Người nợ tôi (Cần thu)',
                        style: TextStyle(fontSize: 12, color: Colors.green, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      MoneyText(
                        totalLend,
                        currency: 'VND',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.green),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ElevatedButton.icon(
          onPressed: () => _showAddDebtDialog(context, model),
          icon: const Icon(Icons.add),
          label: const Text('Thêm Khoản Vay / Cho Vay Mới'),
          style: ElevatedButton.styleFrom(
            backgroundColor: Theme.of(context).colorScheme.primary,
            foregroundColor: Theme.of(context).colorScheme.onPrimary,
          ),
        ),
        const SizedBox(height: 16),
        if (model.debts.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 32),
            child: EmptyState(label: 'Chưa có khoản vay hoặc cho vay nào.'),
          )
        else
          ...model.debts.map((debt) => _DebtItemCard(debt: debt, model: model)),
      ],
    );
  }

  void _showAddDebtDialog(BuildContext context, FinanceViewModel model) {
    showDialog<void>(
      context: context,
      builder: (dialogCtx) => _AddDebtDialog(model: model),
    );
  }
}

class _DebtItemCard extends StatelessWidget {
  const _DebtItemCard({required this.debt, required this.model});

  final DebtModel debt;
  final FinanceViewModel model;

  @override
  Widget build(BuildContext context) {
    final isBorrow = debt.type == 'BORROW';
    final isPaid = debt.status == 'PAID';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(
                      isBorrow ? Icons.arrow_downward : Icons.arrow_upward,
                      color: isBorrow ? Colors.orange : Colors.green,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      isBorrow ? 'Tôi nợ' : 'Cho vay',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: isBorrow ? Colors.orange.shade800 : Colors.green.shade800,
                      ),
                    ),
                    Text(' • ${debt.counterpartyName}', style: const TextStyle(fontWeight: FontWeight.bold)),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: isPaid ? Colors.green.shade100 : Colors.blue.shade100,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    isPaid ? 'ĐÃ TRẢ HẾT' : 'ĐANG NỢ',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: isPaid ? Colors.green.shade900 : Colors.blue.shade900,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Còn lại', style: TextStyle(fontSize: 12, color: Colors.grey)),
                    MoneyText(
                      debt.remainingAmount,
                      currency: debt.currency,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: isPaid ? Colors.grey : (isBorrow ? Colors.deepOrange : Colors.green),
                      ),
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    const Text('Tổng gốc', style: TextStyle(fontSize: 12, color: Colors.grey)),
                    MoneyText(
                      debt.totalAmount,
                      currency: debt.currency,
                      style: const TextStyle(fontSize: 14, color: Colors.black87),
                    ),
                  ],
                ),
              ],
            ),
            if (debt.dueDate != null) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.event, size: 14, color: Colors.grey),
                  const SizedBox(width: 4),
                  Text('Hẹn trả: ${debt.dueDate}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                ],
              ),
            ],
            if (debt.notes != null && debt.notes!.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                debt.notes!,
                style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: Colors.black54),
              ),
            ],
            if (!isPaid) ...[
              const Divider(height: 20),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  onPressed: () => _showPaymentDialog(context, model, debt),
                  icon: const Icon(Icons.payment, size: 18),
                  label: Text(isBorrow ? 'Trả Bớt / Tất Toán' : 'Ghi Nhận Thu Nợ'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showPaymentDialog(BuildContext context, FinanceViewModel model, DebtModel debt) {
    showDialog<void>(
      context: context,
      builder: (dialogCtx) => _AddPaymentDialog(model: model, debt: debt),
    );
  }
}

class _ContactsTab extends StatelessWidget {
  const _ContactsTab({required this.model});

  final FinanceViewModel model;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        ElevatedButton.icon(
          onPressed: () => _showAddContactDialog(context, model),
          icon: const Icon(Icons.person_add),
          label: const Text('Thêm Người Thân Hỗ Trợ'),
          style: ElevatedButton.styleFrom(
            backgroundColor: Theme.of(context).colorScheme.primary,
            foregroundColor: Theme.of(context).colorScheme.onPrimary,
          ),
        ),
        const SizedBox(height: 16),
        if (model.financialContacts.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 32),
            child: EmptyState(
              label: 'Chưa có người thân nào trong danh bạ hỗ trợ.\nHãy lưu danh bạ bố mẹ, bạn bè để kích hoạt trợ lý tài chính khi khẩn cấp!',
            ),
          )
        else
          ...model.financialContacts.map(
            (c) => Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                  child: Text(
                    c.name.isNotEmpty ? c.name[0].toUpperCase() : '?',
                    style: TextStyle(color: Theme.of(context).colorScheme.onPrimaryContainer),
                  ),
                ),
                title: Row(
                  children: [
                    Text(c.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                    if (c.relationshipType != null) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          c.relationshipType!,
                          style: TextStyle(fontSize: 11, color: Colors.blue.shade900),
                        ),
                      ),
                    ],
                  ],
                ),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (c.phone != null && c.phone!.isNotEmpty) Text('SĐT: ${c.phone}'),
                    if (c.notes != null && c.notes!.isNotEmpty)
                      Text(c.notes!, style: const TextStyle(fontStyle: FontStyle.italic)),
                  ],
                ),
                trailing: c.isSupportContact
                    ? const Tooltip(
                        message: 'Có thể hỗ trợ tài chính',
                        child: Icon(Icons.verified, color: Colors.green, size: 20),
                      )
                    : null,
              ),
            ),
          ),
      ],
    );
  }

  void _showAddContactDialog(BuildContext context, FinanceViewModel model) {
    showDialog<void>(
      context: context,
      builder: (dialogCtx) => _AddContactDialog(model: model),
    );
  }
}

class _AddDebtDialog extends StatefulWidget {
  const _AddDebtDialog({required this.model});

  final FinanceViewModel model;

  @override
  State<_AddDebtDialog> createState() => _AddDebtDialogState();
}

class _AddDebtDialogState extends State<_AddDebtDialog> {
  final _formKey = GlobalKey<FormState>();
  String _type = 'BORROW';
  final _nameController = TextEditingController();
  final _amountController = TextEditingController();
  final _notesController = TextEditingController();
  DateTime? _dueDate;
  bool _submitting = false;

  @override
  void dispose() {
    _nameController.dispose();
    _amountController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Thêm Khoản Vay / Cho Vay'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'BORROW', label: Text('Tôi Vay')),
                  ButtonSegment(value: 'LEND', label: Text('Tôi Cho Vay')),
                ],
                selected: {_type},
                onSelectionChanged: (set) => setState(() => _type = set.first),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _nameController,
                decoration: InputDecoration(
                  labelText: _type == 'BORROW' ? 'Vay của ai (Người / Đơn vị)' : 'Cho ai vay',
                  border: const OutlineInputBorder(),
                ),
                validator: (val) => (val == null || val.trim().isEmpty) ? 'Vui lòng nhập tên' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _amountController,
                decoration: const InputDecoration(
                  labelText: 'Số tiền (VND)',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                validator: (val) {
                  if (val == null || val.isEmpty) return 'Vui lòng nhập số tiền';
                  final n = int.tryParse(val.replaceAll(RegExp(r'[,.]'), ''));
                  if (n == null || n <= 0) return 'Số tiền không hợp lệ';
                  return null;
                },
              ),
              const SizedBox(height: 12),
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(
                  _dueDate == null
                      ? 'Chọn ngày hẹn trả (Tùy chọn)'
                      : 'Hạn trả: ${_dueDate!.toIso8601String().substring(0, 10)}',
                ),
                trailing: const Icon(Icons.calendar_today),
                onTap: () async {
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: DateTime.now().add(const Duration(days: 7)),
                    firstDate: DateTime.now().subtract(const Duration(days: 365)),
                    lastDate: DateTime.now().add(const Duration(days: 3650)),
                  );
                  if (picked != null) setState(() => _dueDate = picked);
                },
              ),
              TextFormField(
                controller: _notesController,
                decoration: const InputDecoration(
                  labelText: 'Ghi chú thêm',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Hủy')),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting ? const CircularProgressIndicator() : const Text('Lưu'),
        ),
      ],
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);
    final amount = int.parse(_amountController.text.replaceAll(RegExp(r'[,.]'), ''));
    final err = await widget.model.createDebt(
      type: _type,
      counterpartyName: _nameController.text.trim(),
      totalAmount: amount,
      dueDate: _dueDate?.toIso8601String().substring(0, 10),
      notes: _notesController.text.trim(),
    );
    if (mounted) {
      setState(() => _submitting = false);
      if (err == null) {
        Navigator.of(context).pop();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(err)));
      }
    }
  }
}

class _AddPaymentDialog extends StatefulWidget {
  const _AddPaymentDialog({required this.model, required this.debt});

  final FinanceViewModel model;
  final DebtModel debt;

  @override
  State<_AddPaymentDialog> createState() => _AddPaymentDialogState();
}

class _AddPaymentDialogState extends State<_AddPaymentDialog> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _notesController = TextEditingController();
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _amountController.text = widget.debt.remainingAmount.toString();
  }

  @override
  void dispose() {
    _amountController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Thanh Toán Nợ: ${widget.debt.counterpartyName}'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextFormField(
              controller: _amountController,
              decoration: const InputDecoration(
                labelText: 'Số tiền thanh toán (VND)',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
              validator: (val) {
                if (val == null || val.isEmpty) return 'Vui lòng nhập số tiền';
                final n = int.tryParse(val.replaceAll(RegExp(r'[,.]'), ''));
                if (n == null || n <= 0) return 'Số tiền không hợp lệ';
                return null;
              },
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _notesController,
              decoration: const InputDecoration(
                labelText: 'Ghi chú thanh toán',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Hủy')),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting ? const CircularProgressIndicator() : const Text('Xác nhận'),
        ),
      ],
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);
    final amount = int.parse(_amountController.text.replaceAll(RegExp(r'[,.]'), ''));
    final err = await widget.model.addDebtPayment(
      debtId: widget.debt.id,
      amount: amount,
      notes: _notesController.text.trim(),
    );
    if (mounted) {
      setState(() => _submitting = false);
      if (err == null) {
        Navigator.of(context).pop();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(err)));
      }
    }
  }
}

class _AddContactDialog extends StatefulWidget {
  const _AddContactDialog({required this.model});

  final FinanceViewModel model;

  @override
  State<_AddContactDialog> createState() => _AddContactDialogState();
}

class _AddContactDialogState extends State<_AddContactDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _relationController = TextEditingController();
  final _phoneController = TextEditingController();
  final _notesController = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    _nameController.dispose();
    _relationController.dispose();
    _phoneController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Thêm Người Thân Hỗ Trợ'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Họ tên / Tên gọi',
                  border: OutlineInputBorder(),
                ),
                validator: (val) => (val == null || val.trim().isEmpty) ? 'Vui lòng nhập tên' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _relationController,
                decoration: const InputDecoration(
                  labelText: 'Mối quan hệ (Bố mẹ, anh chị, bạn thân...)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _phoneController,
                decoration: const InputDecoration(
                  labelText: 'Số điện thoại',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.phone,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _notesController,
                decoration: const InputDecoration(
                  labelText: 'Ghi chú (Khả năng hỗ trợ, liên hệ)',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Hủy')),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting ? const CircularProgressIndicator() : const Text('Lưu'),
        ),
      ],
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);
    final err = await widget.model.createFinancialContact(
      name: _nameController.text.trim(),
      relationshipType: _relationController.text.trim(),
      phone: _phoneController.text.trim(),
      notes: _notesController.text.trim(),
    );
    if (mounted) {
      setState(() => _submitting = false);
      if (err == null) {
        Navigator.of(context).pop();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(err)));
      }
    }
  }
}
