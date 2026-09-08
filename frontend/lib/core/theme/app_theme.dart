import 'package:flutter/material.dart';

class AppColors {
  static const black = Color(0xFF000000);
  static const white = Color(0xFFFFFFFF);
  static const greyLight = Color(0xFFF5F5F5);
  static const greyMedium = Color(0xFF999999);
  static const greyText = Color(0xFF666666);
  static const surface = Color(0xFFFBF9F9);
  static const surfaceVariant = Color(0xFFE3E2E2);
  static const surfaceContainerLow = Color(0xFFF5F3F3);
}

/// 新粗野主义（Neo-Brutalism）主题
/// 特征：黑白 + 粗边框 + 偏移阴影
class AppTheme {
  static ThemeData get light => ThemeData(
        useMaterial3: false,
        scaffoldBackgroundColor: AppColors.white,
        colorScheme: const ColorScheme.light(
          primary: AppColors.black,
          surface: AppColors.white,
        ),
        textTheme: const TextTheme(
          headlineLarge: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.w700,
            color: AppColors.black,
            letterSpacing: 1,
          ),
          titleMedium: TextStyle(
            fontSize: 14,
            color: AppColors.greyText,
            fontWeight: FontWeight.w400,
          ),
          labelMedium: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: AppColors.black,
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: AppColors.greyLight,
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.greyMedium, width: 1),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.greyMedium, width: 1),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.black, width: 1),
          ),
          hintStyle: const TextStyle(color: Color(0xFF888888), fontSize: 14),
        ),
      );
}
