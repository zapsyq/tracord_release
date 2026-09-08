import 'package:dio/dio.dart';
import '../models/trip.dart';

class TripService {
  final Dio _dio;
  TripService(this._dio);

  /// 获取所有旅行记录
  Future<List<Trip>> getTrips() async {
    final res = await _dio.get('/trips');
    return (res.data['trips'] as List)
        .map((j) => Trip.fromJson(j as Map<String, dynamic>))
        .toList();
  }

  /// 为指定城市创建旅行记录
  Future<void> addTrip(String adcode) async {
    await _dio.post('/trips/add', data: {'adcode': adcode});
  }

  /// 删除旅行记录（后端级联删除该旅行下全部账单）
  Future<void> deleteTrip(int tripId) async {
    await _dio.delete('/trips/$tripId');
  }
}
