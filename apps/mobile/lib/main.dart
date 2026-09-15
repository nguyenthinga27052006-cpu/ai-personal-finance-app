import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'auth/api_client.dart';
import 'auth/auth_app.dart';
import 'settings/settings_controller.dart';

String defaultApiBaseUrl() {
  const configuredBaseUrl = String.fromEnvironment('API_BASE_URL');
  if (configuredBaseUrl.isNotEmpty) {
    return configuredBaseUrl;
  }
  return switch (defaultTargetPlatform) {
    TargetPlatform.android => 'http://10.0.2.2:8000',
    _ => 'http://localhost:8000',
  };
}

void main() {
  debugPrint('STARTUP_01_MAIN_ENTER');
  FlutterError.onError = (details) {
    debugPrint('STARTUP_ERROR_FLUTTER ${details.exceptionAsString()}');
    FlutterError.presentError(details);
  };
  WidgetsFlutterBinding.ensureInitialized();
  debugPrint('STARTUP_02_BINDING_READY');
  WidgetsBinding.instance.addPostFrameCallback((_) {
    debugPrint('STARTUP_08_FIRST_FRAME');
  });
  runApp(const PersonalFinanceApp());
  debugPrint('STARTUP_03_APP_CREATED');
}

class PersonalFinanceApp extends StatefulWidget {
  const PersonalFinanceApp({super.key, this.api});

  final ApiClient? api;

  @override
  State<PersonalFinanceApp> createState() => _PersonalFinanceAppState();
}

class _PersonalFinanceAppState extends State<PersonalFinanceApp> {
  final _settingsController = SettingsController();

  @override
  Widget build(BuildContext context) {
    debugPrint('STARTUP_04_ROOT_BUILD');
    return ListenableBuilder(
      listenable: _settingsController,
      builder: (context, _) {
        return InheritedSettings(
          controller: _settingsController,
          child: MaterialApp(
            title: 'Personal Finance',
            themeMode: _settingsController.themeMode,
            theme: ThemeData(
              colorScheme: ColorScheme.fromSeed(
                seedColor: Colors.teal,
                brightness: Brightness.light,
              ),
              useMaterial3: true,
            ),
            darkTheme: ThemeData(
              colorScheme: ColorScheme.fromSeed(
                seedColor: Colors.teal,
                brightness: Brightness.dark,
              ),
              useMaterial3: true,
            ),
            home: AuthApp(
              api: widget.api ??
                  ApiClient(
                    baseUrl: const String.fromEnvironment(
                      'API_BASE_URL',
                      defaultValue: '',
                    ).isNotEmpty
                        ? const String.fromEnvironment('API_BASE_URL')
                        : defaultApiBaseUrl(),
                  ),
            ),
          ),
        );
      },
    );
  }
}
