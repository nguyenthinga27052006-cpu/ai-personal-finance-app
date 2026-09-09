import 'package:flutter/material.dart';

import 'auth/api_client.dart';
import 'auth/auth_app.dart';

void main() {
  runApp(const PersonalFinanceApp());
}

class PersonalFinanceApp extends StatelessWidget {
  const PersonalFinanceApp({super.key, this.api});

  final ApiClient? api;

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Personal Finance',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
          useMaterial3: true,
        ),
        home: AuthApp(
          api: api ??
              ApiClient(
                baseUrl: const String.fromEnvironment(
                  'API_BASE_URL',
                  defaultValue: 'http://localhost:8000',
                ),
              ),
        ),
      );
}
