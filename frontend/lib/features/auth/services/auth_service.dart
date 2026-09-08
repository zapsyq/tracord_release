import '../../../core/network/api_client.dart';
import '../models/user.dart';

class AuthService {
  final ApiClient _client;

  AuthService(this._client);

  Future<void> sendVerifyCode(String email) async {
    await _client.dio.post('/user/verify-code', data: {
      'email': email,
    });
  }

  Future<({User user, String accessToken, String refreshToken})> register({
    required String email,
    required String username,
    required String password,
    required String confirmPassword,
    required String code,
  }) async {
    final response = await _client.dio.post('/user/register', data: {
      'email': email,
      'username': username,
      'password': password,
      'confirm_password': confirmPassword,
      'code': code,
    });
    return _parseAuthResponse(response.data);
  }

  Future<({User user, String accessToken, String refreshToken})> login({
    required String email,
    required String password,
  }) async {
    final response = await _client.dio.post('/user/login', data: {
      'email': email,
      'password': password,
    });
    return _parseAuthResponse(response.data);
  }

  ({User user, String accessToken, String refreshToken}) _parseAuthResponse(
      Map<String, dynamic> data) {
    return (
      user: User.fromJson(data['user'] as Map<String, dynamic>),
      accessToken: data['access_token'] as String,
      refreshToken: data['refresh_token'] as String,
    );
  }

}
