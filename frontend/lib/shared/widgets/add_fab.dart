import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

/// 右下角悬浮添加按钮（黑底白 + 号）
class AddFab extends StatelessWidget {
  final VoidCallback onTap;
  const AddFab({super.key, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 56,
        height: 56,
        decoration: BoxDecoration(
          color: AppColors.black,
          border: Border.all(color: AppColors.black, width: 2),
          borderRadius: BorderRadius.circular(16),
          boxShadow: const [
            BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12),
          ],
        ),
        child: const Icon(Icons.add, color: AppColors.white, size: 28),
      ),
    );
  }
}
