import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../auth/providers/auth_provider.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 头像占位
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: AppColors.black,
                borderRadius: BorderRadius.circular(36),
                boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 16)],
              ),
              child: const Icon(Icons.person, size: 36, color: AppColors.white),
            ),
            const SizedBox(height: 16),
            // 用户名
            Text(
              auth.currentUser?.username ?? '用户',
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.black),
            ),
            const SizedBox(height: 4),
            // 邮箱
            Text(
              auth.currentUser?.email ?? '',
              style: const TextStyle(fontSize: 14, color: AppColors.greyText),
            ),
            const SizedBox(height: 40),
            // 退出登录按钮
            GestureDetector(
              onTap: () => _confirmLogout(context),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  color: AppColors.white,
                  border: Border.all(color: AppColors.black, width: 2),
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 16)],
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.logout, size: 20, color: AppColors.black),
                    SizedBox(width: 8),
                    Text('退出登录',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.black)),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmLogout(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: AppColors.black, width: 2),
        ),
        title: const Text('确认退出', style: TextStyle(fontWeight: FontWeight.w700)),
        content: const Text('退出后需要重新登录，确定继续吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('取消', style: TextStyle(color: AppColors.greyText)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('退出', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirmed == true && context.mounted) {
      context.read<AuthProvider>().logout();
    }
  }
}
