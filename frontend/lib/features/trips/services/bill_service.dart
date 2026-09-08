import 'package:dio/dio.dart';
import '../models/bill.dart';

class BillService {
  final Dio _dio;
  BillService(this._dio);

  /// 获取消费分类 {1: "交通", 2: "餐饮", ...}
  Future<Map<int, String>> getCategories() async {
    final res = await _dio.get('/bills/categories');
    final raw = res.data as Map<String, dynamic>;
    return raw.map((k, v) => MapEntry(int.parse(k), v as String));
  }

  /// 获取某次旅行的所有账单
  Future<List<Bill>> getBillsForTrip(int tripId) async {
    final res = await _dio.get('/bills/trip/$tripId');
    return (res.data['bills'] as List)
        .map((j) => Bill.fromJson(j as Map<String, dynamic>))
        .toList();
  }

  /// 添加账单
  Future<void> addBill({
    required int tripId,
    required double amount,
    required int category,
    String? customCategory,
  }) async {
    await _dio.post('/bills/add', data: {
      'trip_id': tripId,
      'amount': amount,
      'category': category,
      'custom_category': customCategory,
    });
  }

  /// 删除单个账单
  Future<void> deleteBill(int billId) async {
    await _dio.delete('/bills/$billId');
  }
}
