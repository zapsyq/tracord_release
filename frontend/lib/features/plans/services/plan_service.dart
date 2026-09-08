import 'package:dio/dio.dart';

/// 计划 + 预算 API
class PlanService {
  final Dio _dio;

  PlanService(this._dio);

  /// 获取某城市计划（没有则返回空字符串）
  Future<String> getPlan(String adcode) async {
    final res = await _dio.get('/plans/$adcode');
    return res.data['content'] as String? ?? '';
  }

  /// 获取所有计划
  Future<List<Map<String, dynamic>>> getPlans() async {
    final res = await _dio.get('/plans');
    return List<Map<String, dynamic>>.from(res.data ?? []);
  }

  /// 保存计划
  Future<void> setPlan(String adcode, String content) async {
    await _dio.post('/plans/set', data: {'adcode': adcode, 'content': content});
  }

  /// 获取某城市预算列表
  Future<List<Map<String, dynamic>>> getBudgets(String adcode) async {
    final res = await _dio.get('/budget', queryParameters: {'adcode': adcode});
    return List<Map<String, dynamic>>.from(res.data['budgets'] ?? []);
  }

  /// 获取所有预算（不按城市过滤）
  Future<List<Map<String, dynamic>>> getAllBudgets() async {
    final res = await _dio.get('/budget');
    return List<Map<String, dynamic>>.from(res.data['budgets'] ?? []);
  }

  /// 设置预算
  Future<void> setBudget({
    required String adcode,
    required int category,
    required double amount,
    String? customCategory,
  }) async {
    final data = <String, dynamic>{
      'adcode': adcode,
      'category': category,
      'amount': amount,
    };
    if (customCategory != null) data['custom_category'] = customCategory;
    await _dio.post('/budget/set', data: data);
  }

  /// 删除预算
  Future<void> deleteBudget(int budgetId) async {
    await _dio.delete('/budget/$budgetId');
  }
}
