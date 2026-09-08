import 'package:dio/dio.dart';
import '../storage/token_storage.dart';
import 'api_config.dart';

/// Dio 封装：自动附加 Bearer Token + 401 时用 refresh_token 无感刷新
class ApiClient {
  late final Dio dio;
  final TokenStorage tokenStorage;
  void Function()? onAuthExpired;

  ApiClient({
    required this.tokenStorage,
    this.onAuthExpired,
  }) {
    dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ));
    dio.interceptors.add(_authInterceptor());
  }

  InterceptorsWrapper _authInterceptor() {
    return InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await tokenStorage.getAccessToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        // 非 401 错误直接透传
        if (error.response?.statusCode != 401) {
          handler.next(error);
          return;
        }
        final refreshToken = await tokenStorage.getRefreshToken();
        if (refreshToken == null) {
          onAuthExpired?.call();
          handler.next(error);
          return;
        }
        // 用独立 Dio 实例刷新 Token，避免死循环
        try {
          final response = await Dio(BaseOptions(
            baseUrl: ApiConfig.baseUrl,
            connectTimeout: const Duration(seconds: 10),
          )).post('/user/refresh-token', data: {
            'refresh_token': refreshToken,
          });
          final newAccessToken = response.data['access_token'] as String;
          await tokenStorage.saveTokens(
            accessToken: newAccessToken,
            refreshToken: refreshToken,
          );
          // 用新 Token 重试原请求
          error.requestOptions.headers['Authorization'] =
              'Bearer $newAccessToken';
          final retryResponse = await dio.fetch(error.requestOptions);
          handler.resolve(retryResponse);
        } catch (_) {
          await tokenStorage.clearTokens();
          onAuthExpired?.call();
          handler.next(error);
        }
      },
    );
  }
}
