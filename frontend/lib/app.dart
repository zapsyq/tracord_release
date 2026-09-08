import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'core/network/api_client.dart';
import 'core/storage/token_storage.dart';
import 'features/auth/providers/auth_provider.dart';
import 'features/auth/services/auth_service.dart';
import 'features/auth/pages/login_page.dart';
import 'features/home/pages/home_page.dart';

class App extends StatelessWidget {
  final TokenStorage tokenStorage;
  final ApiClient apiClient;

  const App({
    super.key,
    required this.tokenStorage,
    required this.apiClient,
  });

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) {
        final auth = AuthProvider(authService: AuthService(apiClient), tokenStorage: tokenStorage);
        apiClient.onAuthExpired = () => auth.logout();
        auth.tryAutoLogin();
        return auth;
      },
      child: MaterialApp(
        title: '迹录 · Tracord',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        // 根据登录状态切换首页：已登录→主页，未登录→登录页
        home: Consumer<AuthProvider>(
          builder: (context, auth, _) {
            if (auth.isLoggedIn) return HomePage(authDio: apiClient.dio);
            return const LoginPage();
          },
        ),
      ),
    );
  }
}
