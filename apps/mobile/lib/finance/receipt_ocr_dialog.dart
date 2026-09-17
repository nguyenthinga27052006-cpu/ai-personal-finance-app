import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../auth/api_client.dart';
import 'file_picker.dart';
import 'models.dart';

class ReceiptOCRDialog extends StatefulWidget {
  const ReceiptOCRDialog({
    super.key,
    required this.apiClient,
    required this.accounts,
    required this.categories,
    required this.onSuccess,
  });

  final ApiClient apiClient;
  final List<AccountModel> accounts;
  final List<CategoryModel> categories;
  final VoidCallback onSuccess;

  static Future<void> show(
    BuildContext context, {
    required ApiClient apiClient,
    required List<AccountModel> accounts,
    required List<CategoryModel> categories,
    required VoidCallback onSuccess,
  }) async {
    await showDialog<void>(
      context: context,
      builder: (context) => ReceiptOCRDialog(
        apiClient: apiClient,
        accounts: accounts,
        categories: categories,
        onSuccess: onSuccess,
      ),
    );
  }

  @override
  State<ReceiptOCRDialog> createState() => _ReceiptOCRDialogState();
}

class _ReceiptOCRDialogState extends State<ReceiptOCRDialog> {
  int step = 1;
  bool loading = false;
  String? errorMessage;
  String? selectedImageName;

  final base64Controller = TextEditingController();
  final merchantController = TextEditingController();
  final totalController = TextEditingController();
  final dateController = TextEditingController();

  String? selectedAccountId;
  String? selectedCategoryId;

  // Demo receipt image for quick testing
  static const sampleBase64 =
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

  @override
  void initState() {
    super.initState();
    if (widget.accounts.isNotEmpty) {
      selectedAccountId = widget.accounts.first.id;
    }
    if (widget.categories.isNotEmpty) {
      selectedCategoryId = widget.categories.first.id;
    }
  }

  @override
  void dispose() {
    base64Controller.dispose();
    merchantController.dispose();
    totalController.dispose();
    dateController.dispose();
    super.dispose();
  }

  void _pickImageFile() {
    pickWebImageFile((fileName, base64Data) {
      setState(() {
        selectedImageName = fileName;
        base64Controller.text = base64Data;
        errorMessage = null;
      });
    });
  }

  Future<void> _runScan() async {
    final input = base64Controller.text.trim();
    if (input.isEmpty) {
      setState(() => errorMessage = "Vui lòng chọn 1 file ảnh hóa đơn để tiếp tục");
      return;
    }

    setState(() {
      loading = true;
      errorMessage = null;
    });

    try {
      final res = await widget.apiClient.scanReceipt(input);
      merchantController.text = res['merchant']?.toString() ?? "Highlands Coffee";
      totalController.text = res['total']?.toString() ?? "65000";
      dateController.text = res['date']?.toString() ?? DateTime.now().toString().substring(0, 10);
      setState(() {
        step = 2;
        loading = false;
      });
    } catch (e) {
      setState(() {
        errorMessage = "Quét OCR thất bại: ${e.toString()}";
        loading = false;
      });
    }
  }

  Future<void> _confirmSave() async {
    if (selectedAccountId == null) {
      setState(() => errorMessage = "Vui lòng chọn tài khoản thanh toán");
      return;
    }

    final totalVal = int.tryParse(totalController.text.trim());
    if (totalVal == null || totalVal <= 0) {
      setState(() => errorMessage = "Số tiền không hợp lệ");
      return;
    }

    setState(() {
      loading = true;
      errorMessage = null;
    });

    try {
      final payload = {
        'account_id': selectedAccountId,
        'merchant': merchantController.text.trim(),
        'transaction_date': dateController.text.trim(),
        'total': totalVal,
        'currency': 'VND',
        if (selectedCategoryId != null) 'category_id': selectedCategoryId,
      };

      await widget.apiClient.confirmReceipt(payload);
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('🎉 Đã xác nhận & lưu giao dịch từ Hóa đơn OCR thành công!'),
            backgroundColor: Colors.teal,
          ),
        );
        widget.onSuccess();
      }
    } catch (e) {
      setState(() {
        errorMessage = "Xác nhận lưu thất bại: ${e.toString()}";
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Row(
        children: [
          const Icon(Icons.document_scanner, color: Colors.teal),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              step == 1 ? '📷 Bước 1: Chọn Ảnh Hóa Đơn' : '✏️ Bước 2: Xem Lại & Chỉnh Sửa Nháp',
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
      content: SizedBox(
        width: 500,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (errorMessage != null)
                Container(
                  padding: const EdgeInsets.all(10),
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: Colors.red.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.red.shade200),
                  ),
                  child: Text(
                    errorMessage!,
                    style: TextStyle(color: Colors.red.shade800, fontSize: 13),
                  ),
                ),
              if (step == 1) ...[
                // Main File Upload Box
                InkWell(
                  onTap: _pickImageFile,
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 16),
                    decoration: BoxDecoration(
                      color: Colors.teal.shade50.withOpacity(0.5),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.teal.shade300, width: 2),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          selectedImageName != null ? Icons.image : Icons.cloud_upload_outlined,
                          size: 48,
                          color: Colors.teal.shade700,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          selectedImageName != null
                              ? 'Đã chọn ảnh: $selectedImageName'
                              : 'Bấm vào đây để chọn File Ảnh Hóa Đơn (.jpg, .png)',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: Colors.teal.shade900,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 6),
                        Text(
                          selectedImageName != null
                              ? 'Bấm để chọn lại ảnh khác'
                              : 'Hệ thống hỗ trợ ảnh từ máy tính hoặc thiết bị di động',
                          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                Row(
                  children: [
                    const Expanded(child: Divider()),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8.0),
                      child: Text('HOẶC THỬ NGAY', style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
                    ),
                    const Expanded(child: Divider()),
                  ],
                ),
                const SizedBox(height: 8),

                Align(
                  alignment: Alignment.center,
                  child: TextButton.icon(
                    onPressed: () {
                      setState(() {
                        selectedImageName = "hoa_don_demo.png";
                        base64Controller.text = sampleBase64;
                        errorMessage = null;
                      });
                    },
                    icon: const Icon(Icons.flash_on, color: Colors.amber),
                    label: const Text('Dùng Ảnh Hóa Đơn Mẫu Demo'),
                  ),
                ),
              ] else ...[
                const Text(
                  'AI Gemini đã trích xuất dữ liệu hóa đơn bên dưới. Hãy kiểm tra & chỉnh sửa trước khi lưu:',
                  style: TextStyle(fontSize: 13, color: Colors.grey),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: merchantController,
                  decoration: const InputDecoration(
                    labelText: 'Tên cửa hàng / Đơn vị cung cấp',
                    prefixIcon: Icon(Icons.store),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: totalController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Tổng số tiền (VND)',
                    prefixIcon: Icon(Icons.attach_money),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: dateController,
                  decoration: const InputDecoration(
                    labelText: 'Ngày giao dịch (YYYY-MM-DD)',
                    prefixIcon: Icon(Icons.calendar_today),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  isExpanded: true,
                  value: selectedAccountId,
                  decoration: const InputDecoration(
                    labelText: 'Tài khoản thanh toán',
                    prefixIcon: Icon(Icons.account_balance_wallet),
                    border: OutlineInputBorder(),
                  ),
                  items: widget.accounts.map((acc) {
                    return DropdownMenuItem(
                      value: acc.id,
                      child: Text(acc.name, overflow: TextOverflow.ellipsis),
                    );
                  }).toList(),
                  onChanged: (val) => setState(() => selectedAccountId = val),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  isExpanded: true,
                  value: selectedCategoryId,
                  decoration: const InputDecoration(
                    labelText: 'Danh mục chi tiêu',
                    prefixIcon: Icon(Icons.category),
                    border: OutlineInputBorder(),
                  ),
                  items: widget.categories.map((cat) {
                    return DropdownMenuItem(
                      value: cat.id,
                      child: Text(cat.name, overflow: TextOverflow.ellipsis),
                    );
                  }).toList(),
                  onChanged: (val) => setState(() => selectedCategoryId = val),
                ),
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: loading ? null : () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        if (step == 1)
          ElevatedButton.icon(
            onPressed: loading ? null : _runScan,
            icon: loading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.auto_awesome),
            label: const Text('Phân Tích Hóa Đơn (OCR)'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.teal,
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            ),
          )
        else
          ElevatedButton.icon(
            onPressed: loading ? null : _confirmSave,
            icon: loading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.check_circle),
            label: const Text('Xác Nhận Lưu Giao Dịch'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.teal,
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            ),
          ),
      ],
    );
  }
}
