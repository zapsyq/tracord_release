import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

/// 地图长按弹出菜单
/// 未点亮: 点亮 / 规划
/// 已点亮: 取消点亮 / 记录 / 规划
class CityPopup extends StatelessWidget {
  final bool isLit;
  final VoidCallback? onLightUp;
  final VoidCallback? onUnLight;
  final VoidCallback? onPlan;
  final VoidCallback? onRecord;
  final VoidCallback onClose;

  const CityPopup({
    super.key,
    required this.isLit,
    this.onLightUp,
    this.onUnLight,
    this.onPlan,
    this.onRecord,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    final options = isLit ? [
      _PopupOption(icon: Icons.light_mode_outlined, label: '取消点亮', onTap: onUnLight ?? onClose),
      Container(width: 1, height: 26, color: AppColors.greyMedium),
      _PopupOption(icon: Icons.edit_outlined, label: '规划', onTap: onPlan ?? onClose),
      Container(width: 1, height: 26, color: AppColors.greyMedium),
      _PopupOption(icon: Icons.edit_note_outlined, label: '记录', onTap: onRecord ?? onClose),
    ] : [
      _PopupOption(icon: Icons.light_mode_outlined, label: '点亮', onTap: onLightUp ?? onClose),
      Container(width: 1, height: 26, color: AppColors.greyMedium),
      _PopupOption(icon: Icons.edit_outlined, label: '规划', onTap: onPlan ?? onClose),
    ];

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
          decoration: BoxDecoration(
            color: AppColors.white,
            border: Border.all(color: AppColors.black, width: 1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: options),
        ),
        SizedBox(width: 24, height: 12, child: CustomPaint(painter: _TrianglePainter())),
      ],
    );
  }
}

class _PopupOption extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _PopupOption({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.all(6),
        child: SizedBox(
          width: 44,
          child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: AppColors.black),
            const SizedBox(height: 2),
            Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppColors.black)),
          ],
        ),
        ),
      ),
    );
  }
}

class _TrianglePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()..moveTo(0, 0)..lineTo(size.width, 0)..lineTo(size.width / 2, size.height)..close();
    // 白色填充
    canvas.drawPath(path, Paint()..color = AppColors.white..style = PaintingStyle.fill);
    // 黑色描边（除顶部外）
    canvas.drawLine(const Offset(0, 0), Offset(size.width / 2, size.height), Paint()..color = AppColors.black..style = PaintingStyle.stroke..strokeWidth = 1);
    canvas.drawLine(Offset(size.width / 2, size.height), Offset(size.width, 0), Paint()..color = AppColors.black..style = PaintingStyle.stroke..strokeWidth = 1);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
