import 'package:flutter/foundation.dart';

import 'api_client.dart';
import 'auth_models.dart';

enum AuthStatus { unknown, authenticated, unauthenticated, refreshing, error }

class AuthController extends ChangeNotifier {
  AuthController(this._api);

  final AuthGateway _api;
  AuthStatus status = AuthStatus.unknown;
  AuthUser? user;
  String? errorMessage;

  Future<void> restore() async {
    try {
      final restoredUser = await _api.me();
      user = restoredUser;
      status = AuthStatus.authenticated;
    } catch (_) {
      try {
        final result = await _api.refresh();
        user = result.user;
        status = AuthStatus.authenticated;
      } catch (_) {
        status = AuthStatus.unauthenticated;
      }
    }
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    return _authenticate(() => _api.login(email, password));
  }

  Future<bool> register(String email, String password, String? displayName) async {
    return _authenticate(() => _api.register(email, password, displayName));
  }

  Future<void> refresh() async {
    status = AuthStatus.refreshing;
    notifyListeners();
    try {
      final result = await _api.refresh();
      user = result.user;
      status = AuthStatus.authenticated;
      errorMessage = null;
    } catch (error) {
      await logout();
      errorMessage = error.toString();
    }
    notifyListeners();
  }

  Future<void> logout() async {
    await _api.logout();
    user = null;
    status = AuthStatus.unauthenticated;
    errorMessage = null;
    notifyListeners();
  }

  Future<bool> _authenticate(Future<AuthResult> Function() operation) async {
    status = AuthStatus.refreshing;
    errorMessage = null;
    notifyListeners();
    try {
      final result = await operation();
      user = result.user;
      status = AuthStatus.authenticated;
      return true;
    } catch (error) {
      status = AuthStatus.error;
      errorMessage = error.toString();
      return false;
    } finally {
      notifyListeners();
    }
  }
}
