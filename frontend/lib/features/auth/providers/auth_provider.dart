import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../services/auth_service.dart';
import '../../../core/storage/token_storage.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService authService;
  final TokenStorage tokenStorage;

  User? currentUser;
  bool isLoading = false;
  bool isSendingCode = false;
  String? errorMessage;
  bool isLoggedIn = false;
  int cooldownSeconds = 0;
  Timer? _cooldownTimer;

  AuthProvider({
    required this.authService,
    required this.tokenStorage,
  });

  Future<void> tryAutoLogin() async {
    final token = await tokenStorage.getAccessToken();
    if (token != null) {
      isLoggedIn = true;
      notifyListeners();
    }
  }

  /// 发送验证码，无论成败均启动冷却
  /// 429（频繁操作）: 静默冷却，不弹提示
  /// 断网: "当前无网络连接" + 冷却
  /// 超时/其他: "发送失败" + 冷却
  Future<void> sendVerifyCode(String email) async {
    isSendingCode = true;
    errorMessage = null;
    notifyListeners();
    try {
      await authService.sendVerifyCode(email);
      _startCooldown(60);
    } on DioException catch (e) {
      final code = e.response?.statusCode;
      if (code == 429) {
        final retryAfter = e.response?.headers.value('retry-after');
        _startCooldown(int.tryParse(retryAfter ?? '') ?? 60);
        // 429 不设 errorMessage，静默冷却
      } else {
        _startCooldown(60);
        errorMessage = _parseError(e);
      }
    } on Exception catch (e) {
      _startCooldown(60);
      errorMessage = _parseError(e);
    }
    isSendingCode = false;
    notifyListeners();
  }

  void _startCooldown(int seconds) {
    _cooldownTimer?.cancel();
    cooldownSeconds = seconds;
    _cooldownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (cooldownSeconds <= 1) {
        timer.cancel();
        cooldownSeconds = 0;
      } else {
        cooldownSeconds--;
      }
      notifyListeners();
    });
  }

  /// 注册新用户 — 后端返回 Token，直接自动登录
  Future<bool> register({
    required String email,
    required String username,
    required String password,
    required String confirmPassword,
    required String code,
  }) async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();
    try {
      final result = await authService.register(
        email: email,
        username: username,
        password: password,
        confirmPassword: confirmPassword,
        code: code,
      );
      await tokenStorage.saveTokens(
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
      );
      currentUser = result.user;
      isLoggedIn = true;
      isLoading = false;
      notifyListeners();
      return true;
    } on Exception catch (e) {
      errorMessage = _parseError(e);
      isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// 邮箱 + 密码登录
  Future<bool> login({
    required String email,
    required String password,
  }) async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();
    try {
      final result = await authService.login(
        email: email,
        password: password,
      );
      await tokenStorage.saveTokens(
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
      );
      currentUser = result.user;
      isLoggedIn = true;
      isLoading = false;
      notifyListeners();
      return true;
    } on Exception catch (e) {
      errorMessage = _parseError(e);
      isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _cooldownTimer?.cancel();
    await tokenStorage.clearTokens();
    currentUser = null;
    isLoggedIn = false;
    cooldownSeconds = 0;
    errorMessage = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _cooldownTimer?.cancel();
    super.dispose();
  }

  /// 将网络异常转为用户可读的中文提示
  String _parseError(Exception e) {
    if (e is DioException) {
      // 有响应体 = 服务端返回了错误（422/401/500 等）
      if (e.response != null) {
        final code = e.response!.statusCode;
        final detail = _extractDetail(e.response!.data);
        switch (code) {
          case 401:
            return '邮箱或密码错误';
          case 422:
            return detail ?? '请检查输入信息是否正确';
          default:
            return detail ?? '服务器异常 (${code ?? '未知'})';
        }
      }
      // 无响应体 = 网络层面的错误
      switch (e.type) {
        case DioExceptionType.connectionError:
          return '当前无网络连接，请检查网络设置';
        case DioExceptionType.connectionTimeout:
        case DioExceptionType.receiveTimeout:
          return '请求超时，请稍后重试';
        default:
          return '发送失败，请稍后重试';
      }
    }
    return '发送失败，请稍后重试';
  }

  /// 从 FastAPI HTTPException 或 ValidationError 中提取 detail
  String? _extractDetail(dynamic data) {
    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is String) return detail;
      if (detail is List && detail.isNotEmpty) {
        final first = detail[0];
        if (first is Map<String, dynamic>) return first['msg'] as String?;
      }
    }
    return null;
  }
}
