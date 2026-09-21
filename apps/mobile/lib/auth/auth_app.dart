import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'api_client.dart';
import 'auth_controller.dart';
import '../finance/finance_home.dart';

class AuthApp extends StatefulWidget {
  const AuthApp({super.key, required this.api});

  final AuthGateway api;

  @override
  State<AuthApp> createState() => _AuthAppState();
}

class _AuthAppState extends State<AuthApp> {
  late final AuthController controller;

  @override
  void initState() {
    super.initState();
    controller = AuthController(widget.api)..restore();
    debugPrint('STARTUP_05_AUTH_RESTORE_START');
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        debugPrint('STARTUP_07_FIRST_ROUTE status=${controller.status}');
        return switch (controller.status) {
          AuthStatus.unknown => const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          ),
          AuthStatus.authenticated => _ProtectedHome(
            controller: controller,
            api: widget.api,
          ),
          _ => _AuthPage(controller: controller),
        };
      },
    );
  }
}

class _AuthPage extends StatefulWidget {
  const _AuthPage({required this.controller});

  final AuthController controller;

  @override
  State<_AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends State<_AuthPage> {
  final email = TextEditingController();
  final password = TextEditingController();
  final displayName = TextEditingController();
  final securityPin = TextEditingController();
  bool registerMode = false;

  @override
  void dispose() {
    email.dispose();
    password.dispose();
    displayName.dispose();
    securityPin.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    final emailText = email.text.trim();
    final passwordText = password.text.trim();
    debugPrint(
      'SUBMIT_CLICKED registerMode=$registerMode email=$emailText passwordLen=${passwordText.length}',
    );
    if (emailText.isEmpty || passwordText.isEmpty) {
      debugPrint('SUBMIT_VALIDATION_FAILED email or password empty');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Vui lòng nhập đầy đủ Email và Mật khẩu!'),
        ),
      );
      return;
    }
    final success = registerMode
        ? await widget.controller.register(
            emailText,
            passwordText,
            displayName.text.trim(),
            securityPin: securityPin.text.trim().isNotEmpty
                ? securityPin.text.trim()
                : null,
          )
        : await widget.controller.login(emailText, passwordText);
    debugPrint(
      'SUBMIT_RESULT success=$success errorMessage=${widget.controller.errorMessage}',
    );
    if (!success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: Colors.red.shade700,
          content: Text(
            widget.controller.errorMessage ?? 'Đăng nhập / Đăng ký thất bại',
          ),
        ),
      );
    }
  }

  void _showForgotPasswordDialog() {
    showDialog(
      context: context,
      builder: (context) => _ForgotPasswordDialog(
        initialEmail: email.text.trim(),
        controller: widget.controller,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final loading = widget.controller.status == AuthStatus.refreshing;
    final errorMessage = widget.controller.errorMessage;
    return Scaffold(
      appBar: AppBar(title: Text(registerMode ? 'Create account' : 'Sign in')),
      body: Center(
        child: SingleChildScrollView(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (errorMessage != null && errorMessage.isNotEmpty) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.red.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.red.shade200),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.error_outline, color: Colors.red.shade700),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              errorMessage,
                              style: TextStyle(
                                color: Colors.red.shade900,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                  if (registerMode) ...[
                    TextField(
                      controller: displayName,
                      decoration: const InputDecoration(labelText: 'Name'),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: securityPin,
                      keyboardType: TextInputType.number,
                      maxLength: 6,
                      decoration: const InputDecoration(
                        labelText: 'Security PIN (6 chữ số - Dùng để khôi phục)',
                        counterText: '',
                        prefixIcon: Icon(Icons.pin),
                      ),
                    ),
                    const SizedBox(height: 8),
                  ],
                  TextField(
                    controller: email,
                    keyboardType: TextInputType.emailAddress,
                    textInputAction: TextInputAction.next,
                    decoration: const InputDecoration(labelText: 'Email'),
                  ),
                  TextField(
                    controller: password,
                    obscureText: true,
                    textInputAction: TextInputAction.done,
                    onSubmitted: (_) => loading ? null : submit(),
                    decoration: const InputDecoration(labelText: 'Password'),
                  ),
                  if (!registerMode) ...[
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: _showForgotPasswordDialog,
                        child: const Text('Quên mật khẩu?'),
                      ),
                    ),
                  ],
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: FilledButton(
                      onPressed: loading ? null : submit,
                      child: loading
                          ? const SizedBox(
                              width: 24,
                              height: 24,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : Text(registerMode ? 'Register' : 'Login'),
                    ),
                  ),
                  if (!kIsWeb)
                    TextButton(
                      onPressed: loading
                          ? null
                          : () => setState(() {
                                registerMode = !registerMode;
                                widget.controller.errorMessage = null;
                              }),
                      child: Text(
                        registerMode
                            ? 'Already have an account?'
                            : 'Create an account',
                      ),
                    )
                  else
                    const Padding(
                      padding: EdgeInsets.only(top: 16),
                      child: Text(
                        'Vui lòng đăng ký tài khoản trên ứng dụng di động (App Mobile). Trang Web chỉ dành cho đăng nhập.',
                        style: TextStyle(fontSize: 12, color: Colors.grey),
                        textAlign: TextAlign.center,
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ForgotPasswordDialog extends StatefulWidget {
  const _ForgotPasswordDialog({
    required this.initialEmail,
    required this.controller,
  });

  final String initialEmail;
  final AuthController controller;

  @override
  State<_ForgotPasswordDialog> createState() => _ForgotPasswordDialogState();
}

class _ForgotPasswordDialogState extends State<_ForgotPasswordDialog> {
  late final TextEditingController emailController;
  final pinController = TextEditingController();
  final newPasswordController = TextEditingController();
  final confirmPasswordController = TextEditingController();
  bool submitting = false;
  String? error;

  @override
  void initState() {
    super.initState();
    emailController = TextEditingController(text: widget.initialEmail);
  }

  @override
  void dispose() {
    emailController.dispose();
    pinController.dispose();
    newPasswordController.dispose();
    confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _submitReset() async {
    final email = emailController.text.trim();
    final pin = pinController.text.trim();
    final newPass = newPasswordController.text;
    final confirmPass = confirmPasswordController.text;

    if (email.isEmpty || pin.length != 6 || newPass.isEmpty) {
      setState(() {
        error = 'Vui lòng nhập đầy đủ Email, Mã PIN (6 số) và Mật khẩu mới!';
      });
      return;
    }

    if (newPass != confirmPass) {
      setState(() {
        error = 'Mật khẩu xác nhận không khớp!';
      });
      return;
    }

    setState(() {
      submitting = true;
      error = null;
    });

    final success = await widget.controller.resetPasswordWithPin(
      email,
      pin,
      newPass,
    );

    if (mounted) {
      if (success) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            backgroundColor: Colors.green,
            content: Text('Đổi mật khẩu thành công và đã tự động đăng nhập!'),
          ),
        );
      } else {
        setState(() {
          submitting = false;
          error = widget.controller.errorMessage ?? 'Khôi phục mật khẩu thất bại';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Khôi phục mật khẩu bằng PIN'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (error != null) ...[
              Text(
                error!,
                style: const TextStyle(color: Colors.red, fontSize: 13),
              ),
              const SizedBox(height: 12),
            ],
            TextField(
              controller: emailController,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(
                labelText: 'Email đã đăng ký',
                prefixIcon: Icon(Icons.email),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: pinController,
              keyboardType: TextInputType.number,
              maxLength: 6,
              decoration: const InputDecoration(
                labelText: 'Mã PIN 6 số bảo mật',
                counterText: '',
                prefixIcon: Icon(Icons.pin),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: newPasswordController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Mật khẩu mới (tối thiểu 8 ký tự)',
                prefixIcon: Icon(Icons.lock),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: confirmPasswordController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Xác nhận mật khẩu mới',
                prefixIcon: Icon(Icons.lock_outline),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: submitting ? null : () => Navigator.pop(context),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: submitting ? null : _submitReset,
          child: submitting
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Text('Đổi mật khẩu & Đăng nhập'),
        ),
      ],
    );
  }
}

class _ProtectedHome extends StatelessWidget {
  const _ProtectedHome({required this.controller, required this.api});

  final AuthController controller;
  final dynamic api;

  @override
  Widget build(BuildContext context) {
    return FinanceHome(
      gateway: api,
      aiGateway: api,
      email: controller.user?.email ?? '',
      userRole: controller.user?.role ?? 'USER',
      onLogout: controller.logout,
    );
  }
}
