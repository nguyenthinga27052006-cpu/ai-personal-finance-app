import 'package:flutter/material.dart';

import '../admin/admin_dashboard.dart';
import '../auth/api_client.dart';
import '../components/sliding_tab_navigation.dart';
import 'settings_controller.dart';

class SettingsDialog extends StatefulWidget {
  const SettingsDialog({
    super.key,
    required this.controller,
    this.api,
    required this.onLogout,
  });

  final SettingsController controller;
  final AuthGateway? api;
  final VoidCallback onLogout;

  static void show(
    BuildContext context, {
    required SettingsController controller,
    AuthGateway? api,
    required VoidCallback onLogout,
  }) {
    showDialog(
      context: context,
      builder: (context) => SettingsDialog(
        controller: controller,
        api: api,
        onLogout: onLogout,
      ),
    );
  }

  @override
  State<SettingsDialog> createState() => _SettingsDialogState();
}

class _SettingsDialogState extends State<SettingsDialog>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String? _userEmail;
  String? _displayName;
  String? _userRole;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadUser();
  }

  Future<void> _loadUser() async {
    final api = widget.api;
    if (api == null) return;
    try {
      final user = await api.me();
      if (mounted) {
        setState(() {
          _userEmail = user.email;
          _displayName = user.displayName;
          _userRole = user.role;
        });
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        width: 500,
        constraints: const BoxConstraints(maxHeight: 520),
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.settings, size: 24, color: Colors.teal),
                const SizedBox(width: 10),
                Text(
                  controller.tr('settings_title'),
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SlidingIndicatorTabBar(
              controller: _tabController,
              isScrollable: true,
              activeColor: Colors.teal,
              indicatorColor: Colors.teal,
              tabs: [
                Tab(
                  icon: const Icon(Icons.person_outline, size: 18),
                  text: controller.tr('account_tab'),
                ),
                Tab(
                  icon: const Icon(Icons.translate, size: 18),
                  text: controller.tr('language_tab'),
                ),
                Tab(
                  icon: const Icon(Icons.palette_outlined, size: 18),
                  text: controller.tr('appearance_tab'),
                ),
                Tab(
                  icon: const Icon(Icons.attach_money, size: 18),
                  text: controller.tr('currency_tab'),
                ),
              ],
            ),
            const Divider(height: 1),
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  // Tab 1: Account
                  _buildAccountTab(context, controller),
                  // Tab 2: Language
                  _buildLanguageTab(context, controller),
                  // Tab 3: Appearance
                  _buildAppearanceTab(context, controller),
                  // Tab 4: Currency
                  _buildCurrencyTab(context, controller),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAccountTab(BuildContext context, SettingsController controller) {
    final isAdmin = _userRole?.toUpperCase() == 'ADMIN' || _userEmail == 'admin@finance.app';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            controller.tr('user_profile'),
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          const SizedBox(height: 12),
          ListTile(
            leading: const CircleAvatar(
              backgroundColor: Colors.teal,
              child: Icon(Icons.person, color: Colors.white),
            ),
            title: Text(_displayName ?? _userEmail ?? 'User'),
            subtitle: Text(_userEmail ?? ''),
          ),
          const Spacer(),
          if (isAdmin) ...[
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                style: FilledButton.styleFrom(
                  backgroundColor: Colors.amber.shade800,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                icon: const Icon(Icons.admin_panel_settings),
                label: Text(
                  controller.tr('admin_portal_btn'),
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                onPressed: () {
                  Navigator.of(context).pop();
                  if (widget.api is ApiClient) {
                    AdminDashboardScreen.open(context, widget.api as ApiClient);
                  }
                },
              ),
            ),
            const SizedBox(height: 12),
          ],
          OutlinedButton.icon(
            icon: const Icon(Icons.lock_reset),
            label: Text(controller.tr('change_password')),
            onPressed: () {
              _showChangePasswordDialog(context, controller);
            },
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            icon: const Icon(Icons.pin),
            label: const Text('Đổi / Tạo mã PIN 6 số'),
            onPressed: () {
              _showUpdatePinDialog(context);
            },
          ),
          if (!isAdmin) ...[
            const SizedBox(height: 12),
            OutlinedButton.icon(
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.red,
                side: const BorderSide(color: Colors.red),
              ),
              icon: const Icon(Icons.delete_forever),
              label: Text(controller.tr('delete_account')),
              onPressed: () {
                _confirmDeleteAccount(context, controller);
              },
            ),
          ],
          const SizedBox(height: 12),
          FilledButton.icon(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.redAccent,
              foregroundColor: Colors.white,
            ),
            icon: const Icon(Icons.logout),
            label: Text(controller.tr('logout')),
            onPressed: () {
              Navigator.of(context).pop();
              widget.onLogout();
            },
          ),
        ],
      ),
    );
  }

  Future<void> _confirmDeleteAccount(
      BuildContext context, SettingsController controller) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(controller.tr('delete_account')),
        content: Text(controller.tr('delete_account_confirm')),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(controller.tr('cancel')),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(controller.tr('delete')),
          ),
        ],
      ),
    );

    if (result == true && widget.api != null) {
      try {
        await widget.api!.deleteAccount();
        if (context.mounted) {
          Navigator.of(context).pop();
          widget.onLogout();
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Tài khoản đã được xóa thành công!'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Xóa tài khoản thất bại: $e'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

  Widget _buildLanguageTab(
      BuildContext context, SettingsController controller) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Text(
          controller.tr('select_language'),
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        const SizedBox(height: 12),
        RadioListTile<AppLanguage>(
          title: Text(controller.tr('lang_vi')),
          value: AppLanguage.vi,
          groupValue: controller.language,
          activeColor: Colors.teal,
          onChanged: (val) {
            if (val != null) controller.setLanguage(val);
          },
        ),
        RadioListTile<AppLanguage>(
          title: Text(controller.tr('lang_en')),
          value: AppLanguage.en,
          groupValue: controller.language,
          activeColor: Colors.teal,
          onChanged: (val) {
            if (val != null) controller.setLanguage(val);
          },
        ),
      ],
    );
  }

  Widget _buildAppearanceTab(
      BuildContext context, SettingsController controller) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        SwitchListTile(
          title: Text(controller.tr('theme_dark')),
          secondary: Icon(
            controller.isDarkMode ? Icons.dark_mode : Icons.light_mode,
            color: Colors.teal,
          ),
          value: controller.isDarkMode,
          activeColor: Colors.teal,
          onChanged: (isDark) {
            controller.setThemeMode(isDark ? ThemeMode.dark : ThemeMode.light);
          },
        ),
      ],
    );
  }

  Widget _buildCurrencyTab(
      BuildContext context, SettingsController controller) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Text(
          controller.tr('select_currency'),
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        const SizedBox(height: 12),
        RadioListTile<AppCurrency>(
          title: Text(controller.tr('curr_vnd')),
          value: AppCurrency.vnd,
          groupValue: controller.currency,
          activeColor: Colors.teal,
          onChanged: (val) {
            if (val != null) controller.setCurrency(val);
          },
        ),
        RadioListTile<AppCurrency>(
          title: Text(controller.tr('curr_usd')),
          value: AppCurrency.usd,
          groupValue: controller.currency,
          activeColor: Colors.teal,
          onChanged: (val) {
            if (val != null) controller.setCurrency(val);
          },
        ),
      ],
    );
  }

  void _showChangePasswordDialog(
      BuildContext context, SettingsController controller) {
    final currentPassController = TextEditingController();
    final newPassController = TextEditingController();
    final confirmPassController = TextEditingController();
    bool loading = false;
    String? errorMsg;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            title: Text(controller.tr('change_password')),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (errorMsg != null)
                    Container(
                      padding: const EdgeInsets.all(8),
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(
                        color: Colors.red.shade100,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        errorMsg!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    ),
                  TextField(
                    controller: currentPassController,
                    obscureText: true,
                    decoration: InputDecoration(
                      labelText: controller.tr('current_password'),
                      border: const OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: newPassController,
                    obscureText: true,
                    decoration: InputDecoration(
                      labelText: controller.tr('new_password'),
                      border: const OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: confirmPassController,
                    obscureText: true,
                    decoration: InputDecoration(
                      labelText: controller.tr('confirm_new_password'),
                      border: const OutlineInputBorder(),
                    ),
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: loading ? null : () => Navigator.of(ctx).pop(),
                child: Text(controller.tr('cancel')),
              ),
              FilledButton(
                onPressed: loading
                    ? null
                    : () async {
                        final currentPass = currentPassController.text.trim();
                        final newPass = newPassController.text.trim();
                        final confirmPass = confirmPassController.text.trim();

                        if (currentPass.isEmpty || newPass.isEmpty) {
                          setDialogState(() {
                            errorMsg = 'Vui lòng điền đầy đủ các trường';
                          });
                          return;
                        }
                        if (newPass != confirmPass) {
                          setDialogState(() {
                            errorMsg = controller.tr('passwords_do_not_match');
                          });
                          return;
                        }

                        setDialogState(() {
                          loading = true;
                          errorMsg = null;
                        });

                        try {
                          if (widget.api != null) {
                            await widget.api!.changePassword(currentPass, newPass);
                          }
                          if (ctx.mounted) {
                            Navigator.of(ctx).pop();
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text(controller.tr('password_changed_success')),
                                backgroundColor: Colors.green,
                              ),
                            );
                          }
                        } catch (e) {
                          setDialogState(() {
                            loading = false;
                            errorMsg = e.toString();
                          });
                        }
                      },
                child: loading
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : Text(controller.tr('save')),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showUpdatePinDialog(BuildContext context) {
    final currentPassController = TextEditingController();
    final newPinController = TextEditingController();
    String? errorMsg;
    bool loading = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            title: const Text('Đổi / Tạo mã PIN 6 số'),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (errorMsg != null)
                    Container(
                      padding: const EdgeInsets.all(8),
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(
                        color: Colors.red.shade100,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        errorMsg!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    ),
                  TextField(
                    controller: currentPassController,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: 'Mật khẩu hiện tại',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: newPinController,
                    keyboardType: TextInputType.number,
                    maxLength: 6,
                    decoration: const InputDecoration(
                      labelText: 'Mã PIN 6 số mới',
                      counterText: '',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.pin),
                    ),
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: loading ? null : () => Navigator.of(ctx).pop(),
                child: const Text('Hủy'),
              ),
              FilledButton(
                onPressed: loading
                    ? null
                    : () async {
                        final currentPass = currentPassController.text.trim();
                        final newPin = newPinController.text.trim();

                        if (currentPass.isEmpty || newPin.length != 6) {
                          setDialogState(() {
                            errorMsg = 'Vui lòng nhập mật khẩu và đủ 6 chữ số cho Mã PIN';
                          });
                          return;
                        }

                        setDialogState(() {
                          loading = true;
                          errorMsg = null;
                        });

                        try {
                          if (widget.api is ApiClient) {
                            await (widget.api as ApiClient).updateSecurityPin(currentPass, newPin);
                          }
                          if (ctx.mounted) {
                            Navigator.of(ctx).pop();
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                backgroundColor: Colors.green,
                                content: Text('Đổi mã PIN 6 số thành công!'),
                              ),
                            );
                          }
                        } catch (e) {
                          setDialogState(() {
                            loading = false;
                            errorMsg = e.toString().replaceFirst('Exception: ', '');
                          });
                        }
                      },
                child: loading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Cập nhật'),
              ),
            ],
          );
        },
      ),
    );
  }
}
