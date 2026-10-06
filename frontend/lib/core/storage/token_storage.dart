import 'package:shared_preferences/shared_preferences.dart';

class TokenStorage {
  static const _kAccess = 'access_token';
  static const _kRefresh = 'refresh_token';
  static const _kUserId = 'user_id';

  Future<void> saveTokens({required String accessToken, required String refreshToken}) async {
    final p = await SharedPreferences.getInstance();
    await p.setString(_kAccess, accessToken);
    await p.setString(_kRefresh, refreshToken);
  }

  //保存当前登录用户ID(本地缓存按账号隔离时用)
  Future<void> saveUserId(int userId) async {
    final p = await SharedPreferences.getInstance();
    await p.setInt(_kUserId, userId);
  }

  //读取当前登录用户ID
  Future<int?> getUserId() async {
    return (await SharedPreferences.getInstance()).getInt(_kUserId);
  }

  Future<String?> getAccessToken() async {
    return (await SharedPreferences.getInstance()).getString(_kAccess);
  }

  Future<String?> getRefreshToken() async {
    return (await SharedPreferences.getInstance()).getString(_kRefresh);
  }

  Future<void> clearTokens() async {
    final p = await SharedPreferences.getInstance();
    await p.remove(_kAccess);
    await p.remove(_kRefresh);
    await p.remove(_kUserId);   // 退出登录时一并清除账号标识
  }
}
