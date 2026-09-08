import 'package:dio/dio.dart';

/// 笔记 API
class NoteService {
  final Dio _dio;

  NoteService(this._dio);

  /// 获取某次旅行的笔记（没有则返回空字符串）
  Future<String> getNote(int tripId) async {
    final res = await _dio.get('/notes/trip/$tripId');
    final notes = res.data['notes'] as List?;
    if (notes != null && notes.isNotEmpty) {
      return notes[0]['content'] as String? ?? '';
    }
    return '';
  }

  /// 添加笔记
  Future<void> addNote(int tripId, String content) async {
    await _dio.post('/notes/add', data: {
      'trip_id': tripId,
      'content': content,
    });
  }
}
