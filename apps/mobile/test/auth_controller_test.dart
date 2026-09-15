import 'package:flutter_test/flutter_test.dart';

import 'package:ai_personal_finance/auth/api_client.dart';
import 'package:ai_personal_finance/auth/auth_controller.dart';
import 'package:ai_personal_finance/auth/auth_models.dart';

class FakeAuthGateway implements AuthGateway {
  FakeAuthGateway(this.result);

  final AuthResult result;
  bool logoutCalled = false;
  bool refreshFails = false;

  @override
  Future<AuthResult> login(String email, String password) async => result;

  @override
  Future<AuthResult> register(String email, String password, String? displayName) async => result;

  @override
  Future<AuthResult> refresh() async {
    if (refreshFails) throw const AuthException('refresh failed');
    return result;
  }

  @override
  Future<AuthUser> me() async => result.user;

  @override
  Future<void> logout() async => logoutCalled = true;

  @override
  Future<void> changePassword(String currentPassword, String newPassword) async {}

  @override
  Future<void> deleteAccount() async {}
}

AuthResult result() {
  return const AuthResult(
    tokens: AuthTokens(accessToken: 'access', refreshToken: 'refresh', expiresIn: 900),
    user: AuthUser(id: 'user-id', email: 'person@example.com'),
  );
}

void main() {
  test('login transitions to authenticated and logout clears state', () async {
    final gateway = FakeAuthGateway(result());
    final controller = AuthController(gateway);

    expect(controller.status, AuthStatus.unknown);
    expect(await controller.login('person@example.com', 'password'), isTrue);
    expect(controller.status, AuthStatus.authenticated);
    expect(controller.user?.email, 'person@example.com');

    await controller.logout();
    expect(controller.status, AuthStatus.unauthenticated);
    expect(controller.user, isNull);
    expect(gateway.logoutCalled, isTrue);
  });

  test('refresh failure returns to unauthenticated state', () async {
    final gateway = FakeAuthGateway(result())..refreshFails = true;
    final controller = AuthController(gateway);

    await controller.refresh();

    expect(controller.status, AuthStatus.unauthenticated);
    expect(controller.user, isNull);
  });
}
