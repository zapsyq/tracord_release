import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

/// 横线稿纸文本框，给笔记和计划共用
class LinedPad extends StatelessWidget {
  final TextEditingController ctrl;
  final TextStyle style;
  final EdgeInsetsGeometry padding;
  final double baseOffset;
  final double lineH;
  const LinedPad({super.key, required this.ctrl, required this.style, required this.padding, required this.baseOffset, required this.lineH});

  @override
  Widget build(BuildContext context) {
    return Theme(
      data: Theme.of(context).copyWith(inputDecorationTheme: const InputDecorationTheme(filled: true, fillColor: Colors.transparent, border: InputBorder.none, enabledBorder: InputBorder.none, focusedBorder: InputBorder.none)),
      child: CustomPaint(
        painter: _LinesPainter(baseOffset: baseOffset, lineH: lineH, padding: padding),
        child: TextField(
          controller: ctrl, maxLines: null, expands: true, textAlignVertical: TextAlignVertical.top, style: style,
          cursorHeight: style.fontSize, cursorColor: AppColors.black,
          decoration: InputDecoration(hintText: '', contentPadding: padding),
        ),
      ),
    );
  }
}

class _LinesPainter extends CustomPainter {
  final double baseOffset, lineH;
  final EdgeInsetsGeometry padding;
  _LinesPainter({required this.baseOffset, required this.lineH, required this.padding});

  @override
  void paint(Canvas canvas, Size size) {
    final p = padding.resolve(TextDirection.ltr);
    final paint = Paint()..color = const Color(0xFFE0E0E0)..strokeWidth = 1;
    var y = p.top + baseOffset;
    while (y < size.height) {
      canvas.drawLine(Offset(16, y), Offset(size.width - 16, y), paint);
      y += lineH;
    }
  }

  @override
  bool shouldRepaint(covariant _LinesPainter old) => old.baseOffset != baseOffset || old.lineH != lineH;
}
