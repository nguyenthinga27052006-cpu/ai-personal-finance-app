import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_personal_finance/auth/api_client.dart';
import 'package:ai_personal_finance/auth/auth_app.dart';
import 'package:ai_personal_finance/auth/auth_models.dart';

class MockAuthGateway implements AuthGateway {
  MockAuthGateway({this.shouldFail = false, this.errorToThrow});

  bool shouldFail;
  Object? errorToThrow;
  String? lastLoginEmail;
  String? lastLoginPassword;
  String? lastRegisterEmail;
  String? lastRegisterPassword;
  String? lastRegisterName;

  static const sampleUser = AuthUser(id: 'user-123', email: 'test@example.com');
  static const sampleResult = AuthResult(
    tokens: AuthTokens(accessToken: 'at', refreshToken: 'rt', expiresIn: 900),
    user: sampleUser,
  );

  @override
  Future<AuthResult> login(String email, String password) async {
    lastLoginEmail = email;
    lastLoginPassword = password;
    if (shouldFail) {
      throw errorToThrow ??
          const ApiException(
            statusCode: 401,
            code: 'invalid_credentials',
            message: 'Invalid credentials',
          );
    }
    return sampleResult;
  }

  @override
  Future<AuthResult> register(
    String email,
    String password,
    String? displayName,
  ) async {
    lastRegisterEmail = email;
    lastRegisterPassword = password;
    lastRegisterName = displayName;
    if (shouldFail) {
      throw errorToThrow ??
          const ApiException(
            statusCode: 409,
            code: 'email_already_registered',
            message: 'Email is already registered',
          );
    }
    return sampleResult;
  }

  @override
  Future<AuthResult> refresh() async {
    throw const AuthException('no refresh token');
  }

  @override
  Future<AuthUser> me() async {
    throw const AuthException('unauthenticated');
  }

  @override
  Future<void> logout() async {}

  @override
  Future<void> changePassword(String currentPassword, String newPassword) async {}

  @override
  Future<void> deleteAccount() async {}
}

void main() {
  testWidgets('validates empty inputs on submit', (tester) async {
    final gateway = MockAuthGateway();

    await tester.pumpWidget(MaterialApp(home: AuthApp(api: gateway)));
    await tester.pump();

    final loginButton = find.widgetWithText(FilledButton, 'Login');
    expect(loginButton, findsOneWidget);
    await tester.tap(loginButton);
    await tester.pump();

    expect(
      find.text('Vui lòng nhập đầy đủ Email và Mật khẩu!'),
      findsOneWidget,
    );
  });

  testWidgets('shows error SnackBar when login fails', (tester) async {
    final gateway = MockAuthGateway(shouldFail: true);

    await tester.pumpWidget(MaterialApp(home: AuthApp(api: gateway)));
    await tester.pump();

    final textFields = find.byType(TextField);
    await tester.enterText(textFields.at(0), 'test@example.com');
    await tester.enterText(textFields.at(1), 'wrongpassword');

    final loginButton = find.widgetWithText(FilledButton, 'Login');
    await tester.tap(loginButton);
    await tester.pump();

    expect(find.text('Invalid credentials'), findsAtLeast(1));
  });

  testWidgets('switches to register mode and displays Name field', (
    tester,
  ) async {
    final gateway = MockAuthGateway();

    await tester.pumpWidget(MaterialApp(home: AuthApp(api: gateway)));
    await tester.pump();

    final createAccountButton = find.widgetWithText(
      TextButton,
      'Create an account',
    );
    expect(createAccountButton, findsOneWidget);
    await tester.tap(createAccountButton);
    await tester.pump();

    expect(find.text('Create account'), findsOneWidget);
    expect(find.byType(TextField), findsNWidgets(3));
  });
}
