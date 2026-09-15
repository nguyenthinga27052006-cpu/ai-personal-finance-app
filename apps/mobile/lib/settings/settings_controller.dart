import 'package:flutter/material.dart';

enum AppLanguage { vi, en }

enum AppCurrency { vnd, usd }

class SettingsController extends ChangeNotifier {
  SettingsController({
    AppLanguage language = AppLanguage.vi,
    ThemeMode themeMode = ThemeMode.light,
    AppCurrency currency = AppCurrency.vnd,
  })  : _language = language,
        _themeMode = themeMode,
        _currency = currency;

  AppLanguage _language;
  ThemeMode _themeMode;
  AppCurrency _currency;

  AppLanguage get language => _language;
  ThemeMode get themeMode => _themeMode;
  AppCurrency get currency => _currency;

  bool get isDarkMode => _themeMode == ThemeMode.dark;

  void setLanguage(AppLanguage language) {
    if (_language == language) return;
    _language = language;
    notifyListeners();
  }

  void setThemeMode(ThemeMode themeMode) {
    if (_themeMode == themeMode) return;
    _themeMode = themeMode;
    notifyListeners();
  }

  void toggleTheme() {
    _themeMode = isDarkMode ? ThemeMode.light : ThemeMode.dark;
    notifyListeners();
  }

  void setCurrency(AppCurrency currency) {
    if (_currency == currency) return;
    _currency = currency;
    notifyListeners();
  }

  String formatAmount(num amountInVnd) {
    if (_currency == AppCurrency.usd) {
      final inUsd = amountInVnd / 25000.0;
      return '\$${_group(inUsd.toInt())}';
    }
    return '${_group(amountInVnd.toInt())} VND';
  }

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

  String tr(String key) {
    return _dictionary[_language]?[key] ?? _dictionary[AppLanguage.vi]?[key] ?? key;
  }

  String trText(String text) {
    if (text.isEmpty) return text;
    if (_language == AppLanguage.en) return text;

    if (_systemTranslations.containsKey(text)) {
      return _systemTranslations[text]!;
    }

    var result = text;
    _systemTranslations.forEach((key, val) {
      if (result.contains(key)) {
        result = result.replaceAll(key, val);
      }
    });

    result = result.replaceAll(
      RegExp(r'accounts for ([\d\.]+%?) of effective spending in this period\.?'),
      r'chiếm \1 tổng chi tiêu thực tế trong kỳ này.',
    );
    result = result.replaceAll(
      RegExp(r'has reached (\d+%?) of its limit\.?'),
      r'đã đạt \1 hạn mức.',
    );
    result = result.replaceAll(
      RegExp(r'ESTIMATE: review budget headroom; source utilization=([\d\.]+)'),
      r'DỰ BÁO: Xem xét hạn mức ngân sách còn lại; mức sử dụng = \1',
    );
    result = result.replaceAll(
      RegExp(r'Based on summary\.budget_utilization:?'),
      r'Dựa trên mức sử dụng ngân sách:',
    );

    return result;
  }

  static const Map<String, String> _systemTranslations = {
    'ADJUST_BUDGET': 'Điều chỉnh ngân sách',
    'CUT_UNNECESSARY': 'Cắt giảm chi tiêu không thiết yếu',
    'EMERGENCY_FUND': 'Quỹ khẩn cấp',
    'Budget risk:': 'Rủi ro ngân sách:',
    'Budget alert:': 'Cảnh báo ngân sách:',
    'Spending increased': 'Chi tiêu gia tăng',
    'Spending reduced': 'Chi tiêu giảm',
    'Unusual spending detected': 'Phát hiện chi tiêu bất thường',
    'Uncategorized dominates spending': 'Chi tiêu chưa phân loại chiếm ưu thế',
    'Healthy saving behavior': 'Hành vi tiết kiệm tích cực',
    'Saving rate improved': 'Tỷ lệ tiết kiệm cải thiện',
    'Saving rate declined': 'Tỷ lệ tiết kiệm sụt giảm',
    'Effective spending has reached the warning threshold for this budget.':
        'Chi tiêu thực tế đã đạt ngưỡng cảnh báo cho ngân sách này.',
    'Effective spending is up versus the previous equivalent period.':
        'Chi tiêu thực tế tăng so với kỳ tương đương trước đó.',
    'Current effective expense is at least 150% of the three preceding equivalent periods.':
        'Chi tiêu thực tế hiện tại cao hơn ít nhất 150% so với 3 kỳ tương đương trước đó.',
    'Income exceeded effective spending by a healthy margin in this period.':
        'Thu nhập vượt chi tiêu thực tế một khoản đáng kể trong kỳ này.',
    'Your saving rate changed materially versus the previous equivalent period.':
        'Tỷ lệ tiết kiệm của bạn thay đổi đáng kể so với kỳ tương đương trước đó.',
    'Review this budget against effective spending and adjust it deliberately if needed.':
        'Xem xét lại ngân sách này so với chi tiêu thực tế và điều chỉnh hợp lý nếu cần.',
  };

  static const Map<AppLanguage, Map<String, String>> _dictionary = {
    AppLanguage.vi: {
      'app_title': 'Trợ lý Tài chính Cá nhân AI',
      'nav_home': 'Trang chủ',
      'nav_accounts': 'Tài khoản',
      'nav_transactions': 'Giao dịch',
      'nav_budgets': 'Ngân sách',
      'nav_goals': 'Mục tiêu',
      'nav_analytics': 'Phân tích',
      'nav_notifications': 'Thông báo',
      'nav_recommendations': 'Gợi ý',
      'nav_ai_assistant': 'Trợ lý AI',
      'nav_admin_portal': 'Quản lý Admin',
      'nav_more': 'Thêm',
      'settings_title': 'Cài đặt hệ thống',
      'account_tab': 'Tài khoản',
      'appearance_tab': 'Giao diện',
      'language_tab': 'Ngôn ngữ',
      'currency_tab': 'Tiền tệ',
      'user_profile': 'Hồ sơ người dùng',
      'change_password': 'Đổi mật khẩu',
      'logout': 'Đăng xuất',
      'theme_dark': 'Chế độ tối (Dark Mode)',
      'theme_light': 'Chế độ sáng (Light Mode)',
      'select_language': 'Chọn ngôn ngữ hệ thống',
      'lang_vi': 'Tiếng Việt 🇻🇳',
      'lang_en': 'English 🇬🇧',
      'select_currency': 'Đơn vị tiền tệ hiển thị',
      'curr_vnd': 'Việt Nam Đồng (VND - ₫)',
      'curr_usd': 'Đô la Mỹ (USD - \$)',
      'add_transaction': 'Thêm giao dịch',
      'edit_transaction': 'Sửa giao dịch',
      'delete_transaction': 'Xóa giao dịch',
      'confirm_delete': 'Bạn có chắc chắn muốn xóa không?',
      'cancel': 'Hủy',
      'save': 'Lưu',
      'delete': 'Xóa',
      'add_account': 'Thêm tài khoản',
      'edit_account': 'Sửa tài khoản',
      'archive_account': 'Lưu trữ tài khoản',
      'add_budget': 'Thêm ngân sách',
      'edit_budget': 'Sửa hạn mức ngân sách',
      'delete_budget': 'Xóa ngân sách',
      'add_goal': 'Thêm mục tiêu tiết kiệm',
      'edit_goal': 'Sửa mục tiêu',
      'delete_goal': 'Xóa mục tiêu',
      'add_contribution': 'Nạp tiền vào mục tiêu',
      'goal_completed': 'Đã hoàn thành',
      'goal_remaining': 'Còn lại:',
      'goal_required_saving': 'Cần tiết kiệm:',
      'per_month': 'tháng',
      'goal_target_date': 'Hạn chót:',
      'forecast_ahead': 'Vượt tiến độ',
      'forecast_behind': 'Chậm tiến độ',
      'forecast_on_track': 'Đúng tiến độ',
      'date_to': 'đến',
      'confidence': 'Độ tin cậy',
      'filter_all': 'Tất cả',
      'filter_high': 'Mức độ cao',
      'filter_medium': 'Trung bình',
      'filter_low': 'Thấp',
      'filter_unread': 'Chưa đọc',
      'no_insights': 'Không có phân tích nào phù hợp',
      'no_recommendations': 'Chưa có gợi ý nào',
      'no_notifications': 'Không có thông báo nào',
      'mark_all_read': 'Đánh dấu tất cả đã đọc',
      'suggested_action': 'Hành động gợi ý:',
      'expected_impact': 'Tác động dự kiến:',
      'priority': 'Độ ưu tiên',
      'btn_accept': 'Chấp nhận',
      'btn_dismiss': 'Bỏ qua',
      'btn_helpful': 'Hữu ích',
      'ai_header_title': 'Hỏi đáp Tài chính AI',
      'ai_header_subtitle': 'Câu trả lời dựa trên dữ liệu tài chính của bạn.',
      'ai_clear': 'Xóa trò chuyện',
      'ai_empty_hint': 'Chọn một câu hỏi gợi ý ở trên hoặc nhập câu hỏi của bạn bên dưới.',
      'ai_user_label': 'Bạn',
      'ai_assistant_label': 'Trợ lý AI',
      'ai_source_label': 'Nguồn:',
      'ai_input_hint': 'Hỏi trợ lý tài chính AI...',
      'ai_send': 'Gửi',
      'current_password': 'Mật khẩu hiện tại',
      'new_password': 'Mật khẩu mới',
      'confirm_new_password': 'Xác nhận mật khẩu mới',
      'password_changed_success': 'Đổi mật khẩu thành công!',
      'passwords_do_not_match': 'Mật khẩu xác nhận không khớp',
      'admin_portal_btn': '🛡️ Trình Quản Lý Admin (Admin Portal)',
      'delete_account': 'Xóa tài khoản',
      'delete_account_confirm': 'Bạn có chắc chắn muốn XÓA TÀI KHOẢN vĩnh viễn không? Tất cả dữ liệu tài chính của bạn sẽ bị xóa hoàn toàn khỏi hệ thống.',
    },
    AppLanguage.en: {
      'app_title': 'AI Personal Finance Assistant',
      'nav_home': 'Home',
      'nav_accounts': 'Accounts',
      'nav_transactions': 'Transactions',
      'nav_budgets': 'Budgets',
      'nav_goals': 'Goals',
      'nav_analytics': 'Analytics',
      'nav_notifications': 'Notifications',
      'nav_recommendations': 'Recommendations',
      'nav_ai_assistant': 'AI Assistant',
      'nav_admin_portal': 'Admin Portal',
      'nav_more': 'More',
      'settings_title': 'System Settings',
      'account_tab': 'Account',
      'appearance_tab': 'Appearance',
      'language_tab': 'Language',
      'currency_tab': 'Currency',
      'user_profile': 'User Profile',
      'change_password': 'Change Password',
      'logout': 'Log Out',
      'theme_dark': 'Dark Mode',
      'theme_light': 'Light Mode',
      'select_language': 'System Language Selection',
      'lang_vi': 'Tiếng Việt 🇻🇳',
      'lang_en': 'English 🇬🇧',
      'select_currency': 'Display Currency Unit',
      'curr_vnd': 'Vietnamese Dong (VND - ₫)',
      'curr_usd': 'US Dollar (USD - \$)',
      'add_transaction': 'Add Transaction',
      'edit_transaction': 'Edit Transaction',
      'delete_transaction': 'Delete Transaction',
      'confirm_delete': 'Are you sure you want to delete this item?',
      'cancel': 'Cancel',
      'save': 'Save',
      'delete': 'Delete',
      'add_account': 'Add Account',
      'edit_account': 'Edit Account',
      'archive_account': 'Archive Account',
      'add_budget': 'Add Budget',
      'edit_budget': 'Edit Budget Limit',
      'delete_budget': 'Delete Budget',
      'add_goal': 'Add Savings Goal',
      'edit_goal': 'Edit Goal',
      'delete_goal': 'Delete Goal',
      'add_contribution': 'Add Contribution',
      'goal_completed': 'completed',
      'goal_remaining': 'Remaining:',
      'goal_required_saving': 'Required saving:',
      'per_month': 'month',
      'goal_target_date': 'Target date:',
      'forecast_ahead': 'Ahead',
      'forecast_behind': 'Behind',
      'forecast_on_track': 'On Track',
      'date_to': 'to',
      'confidence': 'confidence',
      'filter_all': 'All',
      'filter_high': 'High Severity',
      'filter_medium': 'Medium',
      'filter_low': 'Low',
      'filter_unread': 'Unread',
      'no_insights': 'No insights matching filter',
      'no_recommendations': 'No recommendations available',
      'no_notifications': 'No notifications',
      'mark_all_read': 'Mark all read',
      'suggested_action': 'Suggested Action:',
      'expected_impact': 'Expected Impact:',
      'priority': 'Priority',
      'btn_accept': 'Accept',
      'btn_dismiss': 'Dismiss',
      'btn_helpful': 'Helpful',
      'ai_header_title': 'Ask your finances',
      'ai_header_subtitle': 'Answers are grounded in your financial records.',
      'ai_clear': 'Clear chat',
      'ai_empty_hint': 'Choose a suggested question above or type your own question below.',
      'ai_user_label': 'You',
      'ai_assistant_label': 'AI Assistant',
      'ai_source_label': 'Source:',
      'ai_input_hint': 'Ask financial AI assistant...',
      'ai_send': 'Send',
      'current_password': 'Current Password',
      'new_password': 'New Password',
      'confirm_new_password': 'Confirm New Password',
      'password_changed_success': 'Password changed successfully!',
      'passwords_do_not_match': 'Passwords do not match',
      'admin_portal_btn': '🛡️ Admin Management Portal',
      'delete_account': 'Delete Account',
      'delete_account_confirm': 'Are you sure you want to PERMANENTLY DELETE your account? All your financial data will be completely erased.',
    },
  };
}

class InheritedSettings extends InheritedWidget {
  const InheritedSettings({
    super.key,
    required this.controller,
    required super.child,
  });

  final SettingsController controller;

  static SettingsController of(BuildContext context) {
    final widget =
        context.dependOnInheritedWidgetOfExactType<InheritedSettings>();
    return widget?.controller ?? SettingsController();
  }

  @override
  bool updateShouldNotify(InheritedSettings oldWidget) {
    return controller != oldWidget.controller;
  }
}
