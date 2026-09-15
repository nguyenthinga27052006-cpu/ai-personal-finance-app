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
  bool registerMode = false;

  @override
  void dispose() {
    email.dispose();
    password.dispose();
    displayName.dispose();
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
                  if (registerMode)
                    TextField(
                      controller: displayName,
                      decoration: const InputDecoration(labelText: 'Name'),
                    ),
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
                  const SizedBox(height: 20),
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
