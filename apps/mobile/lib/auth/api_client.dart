import 'dart:convert';

import 'package:http/http.dart' as http;

import 'auth_models.dart';
import 'secure_token_storage.dart';

abstract interface class AuthGateway {
  Future<AuthResult> login(String email, String password);

  Future<AuthResult> register(String email, String password, String? displayName);

  Future<AuthResult> refresh();

  Future<AuthUser> me();

  Future<void> logout();
}

class ApiClient implements AuthGateway {
  ApiClient({
    required this.baseUrl,
    http.Client? client,
    SecureTokenStorage? storage,
  })  : _client = client ?? http.Client(),
        _storage = storage ?? SecureTokenStorage();

  final String baseUrl;
  final http.Client _client;
  final SecureTokenStorage _storage;
  Future<AuthResult>? _refreshInFlight;

  @override
  Future<AuthResult> login(String email, String password) async {
    return _authRequest('/api/v1/auth/login', email, password);
  }

  @override
  Future<AuthResult> register(String email, String password, String? displayName) async {
    return _authRequest('/api/v1/auth/register', email, password, displayName: displayName);
  }

  Future<AuthResult> _authRequest(
    String path,
    String email,
    String password, {
    String? displayName,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        if (displayName != null && displayName.isNotEmpty) 'display_name': displayName,
      }),
    );
    return _parseAuth(response);
  }

  @override
  Future<AuthResult> refresh() async {
    final existingRefresh = _refreshInFlight;
    if (existingRefresh != null) {
      return existingRefresh;
    }
    final refreshFuture = _refreshTokens();
    _refreshInFlight = refreshFuture;
    try {
      return await refreshFuture;
    } finally {
      if (identical(_refreshInFlight, refreshFuture)) {
        _refreshInFlight = null;
      }
    }
  }

  Future<AuthResult> _refreshTokens() async {
    final (_, refreshToken) = await _storage.read();
    if (refreshToken == null) {
      throw const AuthException('No refresh session');
    }
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/refresh'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh_token': refreshToken}),
    );
    return _parseAuth(response);
  }

  @override
  Future<AuthUser> me() async {
    final response = await request('GET', '/api/v1/me');
    return AuthUser.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  @override
  Future<void> logout() async {
    try {
      await request('POST', '/api/v1/auth/logout', retryOnUnauthorized: false);
    } finally {
      await _storage.clear();
    }
  }

  Future<http.Response> request(
    String method,
    String path, {
    bool retryOnUnauthorized = true,
    Map<String, dynamic>? body,
  }) async {
    final response = await _send(method, path, body: body);
    if (response.statusCode != 401 || !retryOnUnauthorized || path.contains('/auth/refresh')) {
      return response;
    }
    try {
      final refreshed = await refresh();
      await _storage.write(
        accessToken: refreshed.tokens.accessToken,
        refreshToken: refreshed.tokens.refreshToken,
      );
    } catch (_) {
      await _storage.clear();
      rethrow;
    }
    return _send(method, path, body: body);
  }

  Future<http.Response> _send(String method, String path, {Map<String, dynamic>? body}) async {
    final (accessToken, _) = await _storage.read();
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (accessToken != null) {
      headers['Authorization'] = 'Bearer $accessToken';
    }
    final uri = Uri.parse('$baseUrl$path');
    final encodedBody = body == null ? null : jsonEncode(body);
    return switch (method) {
      'POST' => _client.post(uri, headers: headers, body: encodedBody),
      'GET' => _client.get(uri, headers: headers),
      _ => throw ArgumentError('Unsupported HTTP method'),
    };
  }

  Future<AuthResult> _parseAuth(http.Response response) async {
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = json['detail'];
      throw AuthException(detail is Map ? detail['message'] as String? ?? 'Authentication failed' : 'Authentication failed');
    }
    final result = AuthResult.fromJson(json);
    return _storeAndReturn(result);
  }

  Future<AuthResult> _storeAndReturn(AuthResult result) async {
    await _storage.write(
      accessToken: result.tokens.accessToken,
      refreshToken: result.tokens.refreshToken,
    );
    return result;
  }
}

class AuthException implements Exception {
  const AuthException(this.message);

  final String message;

  @override
  String toString() => message;
}
