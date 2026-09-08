import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';

class AgentService {
  final Dio _dio;

  AgentService(this._dio);

  /// 流式聊天，返回文本片段流
  Stream<String> chat(String query) async* {
    final response = await _dio.post<ResponseBody>(
      '/agent/chat',
      data: {'query': query},
      options: Options(
        responseType: ResponseType.stream,
        headers: {'Accept': 'text/event-stream'},
      ),
    );

    await for (final text in utf8.decoder.bind(response.data!.stream)) {
      yield text;
    }
  }
}
