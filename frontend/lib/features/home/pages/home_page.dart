import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../map/pages/map_page.dart';
import '../../records/pages/records_page.dart';
import '../../planning/pages/planning_page.dart';
import '../../profile/pages/profile_page.dart';

class HomePage extends StatefulWidget {
  final Dio authDio;
  const HomePage({super.key, required this.authDio});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _currentIndex = 0;
  // 每次切到对应 tab 时递增，触发该页面重新拉数据
  int _mapVersion = 0;
  int _recordsVersion = 0;
  int _planningVersion = 0;

  List<Widget> get _pages => [
        MapPage(authDio: widget.authDio, refreshVersion: _mapVersion),
        RecordsPage(authDio: widget.authDio, refreshVersion: _recordsVersion),
        PlanningPage(authDio: widget.authDio, refreshVersion: _planningVersion),
        const ProfilePage(),
      ];

  void _onTabTap(int i) {
    setState(() {
      if (i == 0) _mapVersion++;
      if (i == 1) _recordsVersion++;
      if (i == 2) _planningVersion++;
      _currentIndex = i;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        top: false,
        child: Column(
          children: [
            Expanded(child: IndexedStack(index: _currentIndex, children: _pages)),
            _BottomNav(
              currentIndex: _currentIndex,
              onTap: _onTabTap,
            ),
          ],
        ),
      ),
    );
  }
}

/// 底部导航栏
class _BottomNav extends StatelessWidget {
  final int currentIndex;
  final void Function(int) onTap;
  const _BottomNav({required this.currentIndex, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 4),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.black, width: 1)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _NavItem(icon: Icons.map_outlined, label: '地图', isActive: currentIndex == 0, onTap: () => onTap(0)),
          _NavItem(icon: Icons.edit_note_outlined, label: '记录', isActive: currentIndex == 1, onTap: () => onTap(1)),
          _NavItem(icon: Icons.calendar_month_outlined, label: '规划', isActive: currentIndex == 2, onTap: () => onTap(2)),
          _NavItem(icon: Icons.person_outline, label: '我的', isActive: currentIndex == 3, onTap: () => onTap(3)),
        ],
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isActive;
  final VoidCallback onTap;
  const _NavItem({required this.icon, required this.label, required this.isActive, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        decoration: isActive
            ? BoxDecoration(
                color: const Color(0x0D000000),
                borderRadius: BorderRadius.circular(20),
              )
            : null,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 22, color: isActive ? AppColors.black : AppColors.greyMedium),
            const SizedBox(height: 2),
            Text(label, style: TextStyle(fontSize: 10, fontWeight: isActive ? FontWeight.w600 : FontWeight.w400, color: isActive ? AppColors.black : AppColors.greyMedium)),
          ],
        ),
      ),
    );
  }
}
