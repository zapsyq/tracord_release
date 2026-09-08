import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_map_cancellable_tile_provider/flutter_map_cancellable_tile_provider.dart';
import 'package:latlong2/latlong.dart';
import '../../../core/network/api_config.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/utils/city.dart';
import '../models/city_data.dart';
import '../../agent/pages/agent_chat_page.dart';
import '../../agent/services/agent_service.dart';
import '../../trips/pages/trip_list_page.dart';
import '../../plans/pages/plan_page.dart';
import '../services/city_service.dart';
import '../widgets/city_popup.dart';

class MapPage extends StatefulWidget {
  final Dio? authDio;
  final int refreshVersion;
  const MapPage({super.key, this.authDio, this.refreshVersion = 0});

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  List<CityData>? _cities;
  CityService? _cityService;
  String? _tileKey;
  final Set<String> _litCodes = {};
  bool _loadFailed = false;
  double _zoom = 5;
  CityData? _selectedCity;
  LatLng? _popupLatLng;

  String get _baseUrl =>
      'https://t{s}.tianditu.gov.cn/DataServer?T=vec_w&x={x}&y={y}&l={z}&tk=${_tileKey ?? ""}';
  String get _labelUrl =>
      'https://t{s}.tianditu.gov.cn/DataServer?T=cva_w&x={x}&y={y}&l={z}&tk=${_tileKey ?? ""}';

  @override
  void initState() {
    super.initState();
    if (widget.authDio != null) _cityService = CityService(widget.authDio!);
    _load();
  }

  @override
  void didUpdateWidget(covariant MapPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    // 切到地图 tab 时刷新点亮列表（记录/规划页可能点了新城市）
    if (widget.refreshVersion != oldWidget.refreshVersion) {
      _refreshLitList();
    }
  }

  Future<void> _load() async {
    try {
      final results = await Future.wait([
        _fetchKey(),
        CityLoader.load('assets/中国_市.geojson'),
        _cityService?.getLitList() ?? Future.value(<String>[]),
      ]);
      if (mounted) {
        setState(() {
          _tileKey = results[0] as String;
          _cities = results[1] as List<CityData>;
          _litCodes.addAll(results[2] as List<String>);
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadFailed = true);
    }
  }

  Future<String> _fetchKey() async {
    final res = await Dio(BaseOptions(baseUrl: ApiConfig.baseUrl)).get('/user/map/key');
    return res.data['key'] as String;
  }

  Future<void> _refreshLitList() async {
    if (_cityService == null) return;
    try {
      final list = await _cityService!.getLitList();
      if (mounted) setState(() => _litCodes..clear()..addAll(list));
    } catch (_) {}
  }

  void _onLongPress(TapPosition tapPos, LatLng latlng) {
    final city = _cities != null ? _findCity(_cities!, latlng) : null;
    setState(() {
      _selectedCity = city;
      _popupLatLng = latlng;
    });
  }

  CityData? _findCity(List<CityData> cities, LatLng tap) {
    for (final city in cities) {
      for (final ring in city.rings) {
        if (_pointInRing(tap, ring)) return city;
      }
    }
    return null;
  }

  bool _pointInRing(LatLng point, List<LatLng> ring) {
    bool inside = false;
    for (int i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      final pi = ring[i], pj = ring[j];
      if ((pi.longitude > point.longitude) != (pj.longitude > point.longitude) &&
          point.latitude < (pj.latitude - pi.latitude) * (point.longitude - pi.longitude) / (pj.longitude - pi.longitude) + pi.latitude) {
        inside = !inside;
      }
    }
    return inside;
  }

  void _dismissPopup() => setState(() { _selectedCity = null; _popupLatLng = null; });

  void _onRecord() {
    final city = _selectedCity;
    if (city == null || widget.authDio == null) return;
    final adcode = toAdcode(city.code);
    _dismissPopup();
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => TripListPage(adcode: adcode, cityName: city.name.replaceAll('市', ''), authDio: widget.authDio!),
    ));
  }

  void _onPlan() {
    final city = _selectedCity;
    if (city == null || widget.authDio == null) return;
    final adcode = toAdcode(city.code);
    _dismissPopup();
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => PlanPage(adcode: adcode, cityName: city.name.replaceAll('市', ''), authDio: widget.authDio!),
    ));
  }

  Future<void> _lightUp() async {
    final city = _selectedCity;
    if (city == null || _cityService == null || widget.authDio == null) return;
    try {
      final adcode = toAdcode(city.code);
      await _cityService!.lightUp(adcode);
      if (mounted) setState(() => _litCodes.add(adcode));
    } catch (_) {
      if (mounted) _showError('点亮失败');
    }
    if (mounted) _dismissPopup();
  }

  Future<void> _unLight() async {
    final city = _selectedCity;
    if (city == null || _cityService == null || widget.authDio == null) return;
    final adcode = toAdcode(city.code);
    try {
      await _cityService!.unLight(adcode);
      if (mounted) setState(() => _litCodes.remove(adcode));
    } on DioException catch (e) {
      if (mounted) _showError(_parseApiError(e));
    } catch (_) {
      if (mounted) _showError('取消失败');
    }
    if (mounted) _dismissPopup();
  }

  /// 从 FastAPI HTTPException 中提取 detail 错误信息
  String _parseApiError(DioException e) {
    if (e.response?.data is Map) {
      final detail = (e.response!.data as Map)['detail'];
      if (detail is String) return detail;
    }
    return '取消失败';
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.black, behavior: SnackBarBehavior.floating),
    );
  }

  List<Polygon> _buildPolygons() {
    if (_cities == null || _zoom > 8) return [];
    return _cities!
        .where((c) => _litCodes.contains(toAdcode(c.code)))
        .expand((c) => c.rings.map((ring) => Polygon(
              points: ring,
              color: const Color(0x44000000),
              borderStrokeWidth: 0.5,
              borderColor: const Color(0x88000000),
            )))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    // 加载失败(服务器不在线/未联网): 友好提示 + 重试, 不糊原始报错
    if (_loadFailed) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.wifi_off_outlined, size: 48, color: AppColors.greyMedium),
            const SizedBox(height: 12),
            const Text('网络连接不上',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.black)),
            const SizedBox(height: 4),
            const Text('请检查网络后再试',
                style: TextStyle(fontSize: 13, color: AppColors.greyText)),
            const SizedBox(height: 16),
            GestureDetector(
              onTap: () {
                setState(() => _loadFailed = false);
                _load();
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.black,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text('重新加载',
                    style: TextStyle(color: AppColors.white, fontSize: 14, fontWeight: FontWeight.w600)),
              ),
            ),
          ],
        ),
      );
    }
    if (_tileKey == null) return const Center(child: CircularProgressIndicator(color: Colors.black));

    final hasPopup = _popupLatLng != null && _selectedCity != null;
    final isLit = _selectedCity != null && _litCodes.contains(toAdcode(_selectedCity!.code));

    return Stack(
      children: [
        FlutterMap(
          options: MapOptions(
            initialCenter: const LatLng(35.86, 104.19),
            initialZoom: 5,
            onPositionChanged: (p, _) {
              final crossed = (_zoom <= 8 && p.zoom > 8) || (_zoom > 8 && p.zoom <= 8);
              _zoom = p.zoom;
              if (crossed) setState(() {});
            },
            onLongPress: _onLongPress,
            onTap: (_, _) { if (_popupLatLng != null) _dismissPopup(); },
          ),
          children: [
            TileLayer(
              urlTemplate: _baseUrl,
              subdomains: const ['0', '1', '2', '3', '4', '5', '6', '7'],
              tileProvider: CancellableNetworkTileProvider(),
            ),
            TileLayer(
              urlTemplate: _labelUrl,
              subdomains: const ['0', '1', '2', '3', '4', '5', '6', '7'],
              tileProvider: CancellableNetworkTileProvider(),
            ),
            PolygonLayer(polygons: _buildPolygons()),
            MarkerLayer(
              markers: hasPopup
                  ? [
                      Marker(
                        point: _popupLatLng!,
                        width: 190,
                        height: 68,
                        alignment: Alignment.topCenter,
                        child: CityPopup(
                          isLit: isLit,
                          onLightUp: isLit ? null : _lightUp,
                          onUnLight: isLit ? _unLight : null,
                          onRecord: isLit ? _onRecord : null,
                          onPlan: _onPlan,
                          onClose: _dismissPopup,
                        ),
                      ),
                    ]
                  : [],
            ),
          ],
        ),
        Positioned(
          bottom: 20,
          right: 20,
          child: GestureDetector(
            onTap: () async {
              if (widget.authDio != null) {
                await Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) => AgentChatPage(service: AgentService(widget.authDio!)),
                ));
                _refreshLitList();
              }
            },
            child: Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: AppColors.white,
                border: Border.all(color: AppColors.black, width: 2),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(Icons.smart_toy_outlined, size: 28, color: AppColors.black),
            ),
          ),
        ),
      ],
    );
  }
}
