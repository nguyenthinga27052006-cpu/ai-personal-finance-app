import 'dart:convert';

import 'package:ai_personal_finance/auth/api_client.dart';
import 'package:ai_personal_finance/auth/secure_token_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:flutter_test/flutter_test.dart';

class MemoryTokenStorage implements TokenStorage {
  MemoryTokenStorage({this.access = 'expired-access', this.refresh = 'refresh-token'});

  String? access;
  String? refresh;
  int clearCount = 0;

  @override
  Future<(String?, String?)> read() async => (access, refresh);

  @override
  Future<void> write({required String accessToken, required String refreshToken}) async {
    access = accessToken;
    refresh = refreshToken;
  }

  @override
  Future<void> clear() async {
    access = null;
    refresh = null;
    clearCount++;
  }
}

Map<String, dynamic> authResponse() => {
      'access_token': 'fresh-access',
      'refresh_token': 'fresh-refresh',
      'expires_in': 900,
      'user': {'id': 'user', 'email': 'person@example.com', 'display_name': null},
    };

void main() {
  test('401 refreshes exactly once and retries the original request', () async {
    final storage = MemoryTokenStorage();
    var protectedCalls = 0;
    var refreshCalls = 0;
    final client = MockClient((request) async {
      if (request.url.path.endsWith('/auth/refresh')) {
        refreshCalls++;
        return http.Response(jsonEncode(authResponse()), 200);
      }
      protectedCalls++;
      if (protectedCalls == 1) return http.Response('{}', 401);
      return http.Response(jsonEncode({'items': [], 'total': 0}), 200);
    });
    final api = ApiClient(baseUrl: 'https://finance.test', client: client, storage: storage);

    final response = await api.request('GET', '/api/v1/accounts');

    expect(response.statusCode, 200);
    expect(protectedCalls, 2);
    expect(refreshCalls, 1);
    expect(storage.access, 'fresh-access');
    expect(storage.refresh, 'fresh-refresh');
  });

  test('refresh failure clears the auth session and remains unavailable', () async {
    final storage = MemoryTokenStorage();
    var protectedCalls = 0;
    var refreshCalls = 0;
    final client = MockClient((request) async {
      if (request.url.path.endsWith('/auth/refresh')) {
        refreshCalls++;
        return http.Response(
          jsonEncode({'detail': {'code': 'invalid_refresh_session', 'message': 'Invalid refresh session'}}),
          401,
        );
      }
      protectedCalls++;
      return http.Response('{}', 401);
    });
    final api = ApiClient(baseUrl: 'https://finance.test', client: client, storage: storage);

    await expectLater(
      api.request('GET', '/api/v1/accounts'),
      throwsA(isA<ApiException>()),
    );

    expect(protectedCalls, 1);
    expect(refreshCalls, 1);
    expect(storage.clearCount, 1);
    expect(storage.access, isNull);
    expect(storage.refresh, isNull);
  });
}
