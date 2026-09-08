import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../services/bill_service.dart';
import '../models/bill.dart';
import '../models/category.dart';
import 'add_bill_page.dart';

class TripDetailPage extends StatefulWidget {
  final int tripId;
  final String tripName;
  final Dio authDio;

  const TripDetailPage({
    super.key,
    required this.tripId,
    required this.tripName,
    required this.authDio,
  });

  @override
  State<TripDetailPage> createState() => _TripDetailPageState();
}

class _TripDetailPageState extends State<TripDetailPage> {
  late final BillService _billService;
  List<Bill>? _bills;
  Map<int, String>? _categories;

  double get _totalSpent {
    if (_bills == null) return 0;
    return _bills!.fold(0.0, (sum, b) => sum + b.amountValue);
  }

  @override
  void initState() {
    super.initState();
    _billService = BillService(widget.authDio);
    _load();
  }

  Future<void> _load() async {
    try {
      final results = await Future.wait([
        _billService.getCategories(),
        _billService.getBillsForTrip(widget.tripId),
      ]);
      if (mounted) {
        setState(() {
          _categories = results[0] as Map<int, String>;
          _bills = results[1] as List<Bill>;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _categories = {};
          _bills = [];
        });
      }
    }
  }

  Future<void> _deleteBill(int billId) async {
    try {
      await _billService.deleteBill(billId);
      await _load();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('删除失败'), backgroundColor: Colors.black, behavior: SnackBarBehavior.floating),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _Header(title: widget.tripName),
            if (_bills != null) _TotalSpent(amount: _totalSpent),
            Expanded(child: _buildBody()),
            _BottomButton(onTap: () async {
              await Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => AddBillPage(tripId: widget.tripId, tripName: widget.tripName, authDio: widget.authDio),
              ));
              _load();
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_bills == null) {
      return const Center(child: CircularProgressIndicator(color: Colors.black));
    }
    if (_bills!.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.receipt_long_outlined, size: 64, color: AppColors.greyMedium),
            const SizedBox(height: 12),
            const Text('还没有支出记录', style: TextStyle(fontSize: 16, color: AppColors.greyText)),
          ],
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: _bills!.length,
      itemBuilder: (_, i) {
        final bill = _bills![i];
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: AppColors.white,
            border: Border.all(color: AppColors.black, width: 2),
            borderRadius: BorderRadius.circular(8),
            boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12)],
          ),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AppColors.black,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(BillCategory.icon(bill.category), color: AppColors.white, size: 20),
              ),
              const SizedBox(width: 12),
              Text(
                  bill.customCategory?.isNotEmpty == true
                      ? bill.customCategory!
                      : BillCategory.name(bill.category, serverCategories: _categories),
                  style: const TextStyle(fontSize: 14, color: AppColors.black)),
              const Spacer(),
              Text('¥ ${bill.amount}',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.black)),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: () => _deleteBill(bill.id),
                child: const Icon(Icons.close, size: 18, color: AppColors.greyMedium),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _Header extends StatelessWidget {
  final String title;
  const _Header({required this.title});

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
          Expanded(
            child: Text(title,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.black),
                overflow: TextOverflow.ellipsis),
          ),
        ],
      ),
    );
  }
}

class _TotalSpent extends StatelessWidget {
  final double amount;
  const _TotalSpent({required this.amount});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Column(
        children: [
          const Text('总花费', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.greyText, letterSpacing: 1)),
          const SizedBox(height: 4),
          Text('¥ ${amount.toStringAsFixed(2)}',
              style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: AppColors.black)),
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
              Icon(Icons.add_circle_outline, color: AppColors.white, size: 20),
              SizedBox(width: 8),
              Text('添加支出',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.white)),
            ],
          ),
        ),
      ),
    );
  }
}
