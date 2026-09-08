import 'package:dio/dio.dart';

/// 城市点亮/取消/查询 API
/// adcode 为 gb 编码的后 6 位
class CityService {
  final Dio _dio;

  CityService(this._dio);

  /// 点亮城市
  Future<void> lightUp(String adcode) async {
    await _dio.post('/cities/light', data: {'adcode': adcode});
  }

  /// 取消点亮
  Future<void> unLight(String adcode) async {
    await _dio.delete('/cities/$adcode');
  }

  /// 查询已点亮城市 adcode 列表
  Future<List<String>> getLitList() async {
    final res = await _dio.get('/cities/lighted');
    return List<String>.from(res.data['adcode'] ?? []);
  }
}
