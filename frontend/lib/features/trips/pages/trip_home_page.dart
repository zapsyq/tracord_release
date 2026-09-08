import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import 'trip_detail_page.dart';
import 'note_page.dart';

class TripHomePage extends StatelessWidget {
  final int tripId;
  final String cityName;
  final String tripLabel;
  final Dio authDio;

  const TripHomePage({
    super.key,
    required this.tripId,
    required this.cityName,
    required this.tripLabel,
    required this.authDio,
  });

  String get _tripName => '$cityName $tripLabel';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _Header(tripName: _tripName),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: GridView.count(
                  crossAxisCount: 2,
                  mainAxisSpacing: 16,
                  crossAxisSpacing: 16,
                  childAspectRatio: 1,
                  children: [
                    _EntryCard(
                      icon: Icons.receipt_long_outlined,
                      label: '消费',
                      onTap: () => Navigator.of(context).push(MaterialPageRoute(
                        builder: (_) => TripDetailPage(
                          tripId: tripId,
                          tripName: _tripName,
                          authDio: authDio,
                        ),
                      )),
                    ),
                    _EntryCard(
                      icon: Icons.photo,
                      label: '相册',
                      onTap: () => _showComingSoon(context),
                    ),
                    _EntryCard(
                      icon: Icons.edit,
                      label: '笔记',
                      onTap: () => Navigator.of(context).push(MaterialPageRoute(
                        builder: (_) => NotePage(
                          tripId: tripId,
                          tripName: _tripName,
                          authDio: authDio,
                        ),
                      )),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showComingSoon(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('即将上线'), backgroundColor: Colors.black, behavior: SnackBarBehavior.floating),
    );
  }
}

class _Header extends StatelessWidget {
  final String tripName;
  const _Header({required this.tripName});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.black, width: 2)),
      ),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.of(context).pop(),
            child: const Icon(Icons.arrow_back, color: AppColors.black),
          ),
          const SizedBox(width: 16),
          Text(tripName,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.black)),
        ],
      ),
    );
  }
}

class _EntryCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _EntryCard({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.white,
          border: Border.all(color: AppColors.black, width: 2),
          borderRadius: BorderRadius.circular(16),
          boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12)],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 36, color: AppColors.black),
            const SizedBox(height: 8),
            Text(label,
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.black)),
          ],
        ),
      ),
    );
  }
}
