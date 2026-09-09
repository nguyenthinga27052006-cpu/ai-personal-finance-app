import 'dart:convert';

import 'package:http/http.dart' as http;

import 'auth_models.dart';
import 'secure_token_storage.dart';
import '../ai/models.dart';
import '../finance/models.dart';

abstract interface class AuthGateway {
  Future<AuthResult> login(String email, String password);

  Future<AuthResult> register(
    String email,
    String password,
    String? displayName,
  );

  Future<AuthResult> refresh();

  Future<AuthUser> me();

  Future<void> logout();
}

abstract interface class FinanceGateway {
  Future<List<AccountModel>> accounts();

  Future<AccountModel> createAccount(Map<String, dynamic> values);

  Future<AccountModel> updateAccount(String id, Map<String, dynamic> values);

  Future<List<CategoryModel>> categories();

  Future<List<TransactionModel>> transactions();

  Future<TransactionModel> transaction(String id);

  Future<TransactionModel> createTransaction(
    Map<String, dynamic> values, {
    String? idempotencyKey,
  });

  Future<TransactionModel> createTransfer(
    Map<String, dynamic> values, {
    String? idempotencyKey,
  });

  Future<List<BudgetModel>> budgets();

  Future<List<GoalModel>> goals();

  Future<List<InsightModel>> insights({DateTime? start, DateTime? end});

  Future<List<NotificationModel>> notifications({bool unreadOnly = false});

  Future<NotificationModel> markNotificationRead(String id);

  Future<List<RecommendationModel>> recommendations({DateTime? start, DateTime? end});

  Future<RecommendationModel> acceptRecommendation(String id);

  Future<RecommendationModel> dismissRecommendation(String id);

  Future<RecommendationModel> giveRecommendationFeedback(String id, String feedback);

  Future<DashboardModel> dashboard();
}

abstract interface class AIGateway {
  Future<AIQueryResult> query(String question);
}

class ApiClient implements AuthGateway, FinanceGateway, AIGateway {
  ApiClient({required this.baseUrl, http.Client? client, TokenStorage? storage})
    : _client = client ?? http.Client(),
      _storage = storage ?? SecureTokenStorage();

  final String baseUrl;
  final http.Client _client;
  final TokenStorage _storage;
  Future<AuthResult>? _refreshInFlight;

  @override
  Future<AuthResult> login(String email, String password) async {
    return _authRequest('/api/v1/auth/login', email, password);
  }

  @override
  Future<AuthResult> register(
    String email,
    String password,
    String? displayName,
  ) async {
    return _authRequest(
      '/api/v1/auth/register',
      email,
      password,
      displayName: displayName,
    );
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
        if (displayName != null && displayName.isNotEmpty)
          'display_name': displayName,
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

  @override
  Future<List<AccountModel>> accounts() async {
    final response = await request('GET', '/api/v1/accounts');
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    _throwForError(response, json);
    return (json['items'] as List<dynamic>)
        .map((item) => AccountModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<AccountModel> createAccount(Map<String, dynamic> values) async {
    final response = await request('POST', '/api/v1/accounts', body: values);
    return AccountModel.fromJson(_decodeSuccess(response));
  }

  @override
  Future<AccountModel> updateAccount(
    String id,
    Map<String, dynamic> values,
  ) async {
    final response = await request(
      'PATCH',
      '/api/v1/accounts/$id',
      body: values,
    );
    return AccountModel.fromJson(_decodeSuccess(response));
  }

  @override
  Future<List<CategoryModel>> categories() async {
    final response = await request('GET', '/api/v1/categories');
    final json = _decodeSuccess(response);
    return (json['items'] as List<dynamic>)
        .map((item) => CategoryModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<List<TransactionModel>> transactions() async {
    final response = await request('GET', '/api/v1/transactions');
    final json = _decodeSuccess(response);
    return (json['items'] as List<dynamic>)
        .map((item) => TransactionModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<TransactionModel> transaction(String id) async {
    return TransactionModel.fromJson(
      _decodeSuccess(await request('GET', '/api/v1/transactions/$id')),
    );
  }

  @override
  Future<TransactionModel> createTransaction(
    Map<String, dynamic> values, {
    String? idempotencyKey,
  }) async {
    final response = await request(
      'POST',
      '/api/v1/transactions',
      body: values,
      idempotencyKey: idempotencyKey,
    );
    return TransactionModel.fromJson(_decodeSuccess(response));
  }

  @override
  Future<TransactionModel> createTransfer(
    Map<String, dynamic> values, {
    String? idempotencyKey,
  }) async {
    final response = await request(
      'POST',
      '/api/v1/transactions/transfer',
      body: values,
      idempotencyKey: idempotencyKey,
    );
    return TransactionModel.fromJson(_decodeSuccess(response));
  }

  @override
  Future<List<BudgetModel>> budgets() async {
    final json = _decodeListSuccess(await request('GET', '/api/v1/budgets'));
    return json
        .map((item) => BudgetModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<List<GoalModel>> goals() async {
    final json = _decodeListSuccess(await request('GET', '/api/v1/goals'));
    return json
        .map((item) => GoalModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<List<InsightModel>> insights({DateTime? start, DateTime? end}) async {
    final today = DateTime.now();
    final resolvedStart = start ?? DateTime(today.year, today.month);
    final resolvedEnd = end ?? today;
    final path =
        '/api/v1/insights?start=${resolvedStart.toIso8601String().substring(0, 10)}&end=${resolvedEnd.toIso8601String().substring(0, 10)}';
    final json = _decodeSuccess(await request('GET', path));
    return (json['items'] as List<dynamic>)
        .map((item) => InsightModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<List<NotificationModel>> notifications({bool unreadOnly = false}) async {
    final suffix = unreadOnly ? '?unread_only=true' : '';
    final json = _decodeSuccess(
      await request('GET', '/api/v1/notifications$suffix'),
    );
    return (json['items'] as List<dynamic>)
        .map((item) => NotificationModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<NotificationModel> markNotificationRead(String id) async {
    return NotificationModel.fromJson(
      _decodeSuccess(await request('POST', '/api/v1/notifications/$id/read')),
    );
  }

  @override
  Future<List<RecommendationModel>> recommendations({DateTime? start, DateTime? end}) async {
    final today = DateTime.now();
    final resolvedStart = start ?? DateTime(today.year, today.month);
    final resolvedEnd = end ?? today;
    final path =
        '/api/v1/recommendations?start=${resolvedStart.toIso8601String().substring(0, 10)}&end=${resolvedEnd.toIso8601String().substring(0, 10)}';
    final json = _decodeSuccess(await request('GET', path));
    return (json['items'] as List<dynamic>)
        .map((item) => RecommendationModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<RecommendationModel> acceptRecommendation(String id) async {
    return RecommendationModel.fromJson(
      _decodeSuccess(await request('POST', '/api/v1/recommendations/$id/accept')),
    );
  }

  @override
  Future<RecommendationModel> dismissRecommendation(String id) async {
    return RecommendationModel.fromJson(
      _decodeSuccess(await request('POST', '/api/v1/recommendations/$id/dismiss')),
    );
  }

  @override
  Future<RecommendationModel> giveRecommendationFeedback(String id, String feedback) async {
    return RecommendationModel.fromJson(
      _decodeSuccess(
        await request(
          'POST',
          '/api/v1/recommendations/$id/feedback',
          body: {'feedback': feedback},
        ),
      ),
    );
  }

  @override
  Future<DashboardModel> dashboard() async {
    return DashboardModel.fromJson(
      _decodeSuccess(await request('GET', '/api/v1/dashboard')),
    );
  }

  @override
  Future<AIQueryResult> query(String question) async {
    final json = _decodeSuccess(
      await request(
        'POST',
        '/api/v1/ai/query',
        body: {'question': question, 'currency': 'VND'},
      ),
    );
    return AIQueryResult.fromJson(json);
  }

  Future<http.Response> request(
    String method,
    String path, {
    bool retryOnUnauthorized = true,
    Map<String, dynamic>? body,
    String? idempotencyKey,
  }) async {
    final response = await _send(
      method,
      path,
      body: body,
      idempotencyKey: idempotencyKey,
    );
    if (response.statusCode != 401 ||
        !retryOnUnauthorized ||
        path.contains('/auth/refresh')) {
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
    final retried = await _send(
      method,
      path,
      body: body,
      idempotencyKey: idempotencyKey,
    );
    return retried;
  }

  Future<http.Response> _send(
    String method,
    String path, {
    Map<String, dynamic>? body,
    String? idempotencyKey,
  }) async {
    final (accessToken, _) = await _storage.read();
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (accessToken != null) {
      headers['Authorization'] = 'Bearer $accessToken';
    }
    if (idempotencyKey != null) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    final uri = Uri.parse('$baseUrl$path');
    final encodedBody = body == null ? null : jsonEncode(body);
    final responseFuture = switch (method) {
      'POST' => _client.post(uri, headers: headers, body: encodedBody),
      'GET' => _client.get(uri, headers: headers),
      'PATCH' => _client.patch(uri, headers: headers, body: encodedBody),
      _ => throw ArgumentError('Unsupported HTTP method'),
    };
    final response = await responseFuture;
    return response;
  }

  Map<String, dynamic> _decodeSuccess(http.Response response) {
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    _throwForError(response, json);
    return json;
  }

  List<dynamic> _decodeListSuccess(http.Response response) {
    final json = jsonDecode(response.body);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      _throwForError(response, json is Map<String, dynamic> ? json : {});
    }
    return json as List<dynamic>;
  }

  void _throwForError(http.Response response, Map<String, dynamic> json) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = json['detail'];
      throw ApiException.fromResponse(response, detail);
    }
  }

  Future<AuthResult> _parseAuth(http.Response response) async {
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = json['detail'];
      throw ApiException.fromResponse(response, detail);
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

class ApiException implements Exception {
  const ApiException({
    required this.statusCode,
    required this.code,
    required this.message,
  });

  final int statusCode;
  final String code;
  final String message;

  factory ApiException.fromResponse(http.Response response, Object? detail) {
    final map = detail is Map ? detail : const <String, dynamic>{};
    return ApiException(
      statusCode: response.statusCode,
      code: map['code'] as String? ?? 'request_failed',
      message: map['message'] as String? ?? 'Request failed',
    );
  }

  @override
  String toString() => message;
}
