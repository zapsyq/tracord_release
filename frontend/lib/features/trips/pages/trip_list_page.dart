import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../services/trip_service.dart';
import '../models/trip.dart';
import 'trip_home_page.dart';

class TripListPage extends StatefulWidget {
  final String adcode;
  final String cityName;
  final Dio authDio;

  const TripListPage({
    super.key,
    required this.adcode,
    required this.cityName,
    required this.authDio,
  });

  @override
  State<TripListPage> createState() => _TripListPageState();
}

class _TripListPageState extends State<TripListPage> {
  late final TripService _tripService;
  List<Trip>? _trips;

  List<Trip> get _filtered =>
      _trips?.where((t) => t.adcode == widget.adcode).toList() ?? [];

  @override
  void initState() {
    super.initState();
    _tripService = TripService(widget.authDio);
    _load();
  }

  Future<void> _load() async {
    try {
      final trips = await _tripService.getTrips();
      if (mounted) setState(() => _trips = trips);
    } catch (_) {
      if (mounted) setState(() => _trips = []);
    }
  }

  Future<void> _addTrip() async {
    try {
      await _tripService.addTrip(widget.adcode);
      await _load();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('添加失败'), backgroundColor: Colors.black, behavior: SnackBarBehavior.floating),
        );
      }
    }
  }

  Future<void> _deleteTrip(int tripId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: AppColors.black, width: 2),
        ),
        title: const Text('确认删除', style: TextStyle(fontWeight: FontWeight.w700)),
        content: const Text('删除前请确保该旅行下无账单记录，否则无法删除。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('取消', style: TextStyle(color: AppColors.greyText)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('删除', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await _tripService.deleteTrip(tripId);
      await _load();
    } on DioException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(_parseApiError(e)), backgroundColor: Colors.black, behavior: SnackBarBehavior.floating),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('删除失败'), backgroundColor: Colors.black, behavior: SnackBarBehavior.floating),
        );
      }
    }
  }

  String _parseApiError(DioException e) {
    if (e.response?.data is Map) {
      final detail = (e.response!.data as Map)['detail'];
      if (detail is String) return detail;
    }
    return '删除失败';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _Header(cityName: widget.cityName),
            Expanded(child: _buildBody()),
            _BottomButton(onTap: _addTrip),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_trips == null) {
      return const Center(child: CircularProgressIndicator(color: Colors.black));
    }
    if (_filtered.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.edit_note_outlined, size: 64, color: AppColors.greyMedium),
            const SizedBox(height: 12),
            const Text('还没有旅行记录', style: TextStyle(fontSize: 16, color: AppColors.greyText)),
            const SizedBox(height: 4),
            Text('点击下方按钮添加', style: TextStyle(fontSize: 14, color: AppColors.greyMedium)),
          ],
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: _filtered.length,
      itemBuilder: (_, i) {
        final trip = _filtered[i];
        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          decoration: BoxDecoration(
            color: AppColors.white,
            border: Border.all(color: AppColors.black, width: 2),
            borderRadius: BorderRadius.circular(12),
            boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12)],
          ),
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: () async {
              await Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => TripHomePage(
                  tripId: trip.id,
                  cityName: widget.cityName,
                  tripLabel: '旅行 #${i + 1}',
                  authDio: widget.authDio,
                ),
              ));
              _load();
            },
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 30),
              child: Row(
                children: [
                  Text('旅行 #${i + 1}',
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 18, color: AppColors.black)),
                  const Spacer(),
                  GestureDetector(
                    onTap: () => _deleteTrip(trip.id),
                    child: const Icon(Icons.close, size: 20, color: AppColors.greyText),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _Header extends StatelessWidget {
  final String cityName;
  const _Header({required this.cityName});

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
          Text(cityName,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.black)),
        ],
      ),
    );
  }
}

class _BottomButton extends StatelessWidget {
  final VoidCallback onTap;
  const _BottomButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.black, width: 2)),
      ),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: AppColors.black,
            border: Border.all(color: AppColors.black, width: 2),
            borderRadius: BorderRadius.circular(12),
            boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12)],
          ),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.add, color: AppColors.white, size: 20),
              SizedBox(width: 8),
              Text('添加旅行',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.white)),
            ],
          ),
        ),
      ),
    );
  }
}
