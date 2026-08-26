import 'package:flutter/material.dart';

import 'api_client.dart';
import 'auth_controller.dart';

class AuthApp extends StatefulWidget {
  const AuthApp({super.key, required this.api});

  final ApiClient api;

  @override
  State<AuthApp> createState() => _AuthAppState();
}

class _AuthAppState extends State<AuthApp> {
  late final AuthController controller;

  @override
  void initState() {
    super.initState();
    controller = AuthController(widget.api)..restore();
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
        return switch (controller.status) {
          AuthStatus.unknown || AuthStatus.refreshing when controller.user == null => const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            ),
          AuthStatus.authenticated => _ProtectedHome(controller: controller),
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
    final success = registerMode
        ? await widget.controller.register(email.text, password.text, displayName.text)
        : await widget.controller.login(email.text, password.text);
    if (!success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(widget.controller.errorMessage ?? 'Authentication failed')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final loading = widget.controller.status == AuthStatus.refreshing;
    return Scaffold(
      appBar: AppBar(title: Text(registerMode ? 'Create account' : 'Sign in')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (registerMode)
                  TextField(controller: displayName, decoration: const InputDecoration(labelText: 'Name')),
                TextField(
                  controller: email,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(labelText: 'Email'),
                ),
                TextField(
                  controller: password,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'Password'),
                ),
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: loading ? null : submit,
                  child: Text(registerMode ? 'Register' : 'Login'),
                ),
                TextButton(
                  onPressed: loading ? null : () => setState(() => registerMode = !registerMode),
                  child: Text(registerMode ? 'Already have an account?' : 'Create an account'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ProtectedHome extends StatelessWidget {
  const _ProtectedHome({required this.controller});

  final AuthController controller;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Personal Finance'),
        actions: [
          IconButton(
            tooltip: 'Log out',
            onPressed: controller.logout,
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Center(child: Text('Signed in as ${controller.user?.email ?? ''}')),
    );
  }
}
