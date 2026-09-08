import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/utils/city.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/add_fab.dart';
import '../../map/models/city_data.dart';
import '../../map/services/city_service.dart';
import '../../planning/pages/city_picker_page.dart';
import '../../trips/models/trip.dart';
import '../../trips/pages/trip_home_page.dart';
import '../../trips/services/bill_service.dart';
import '../../trips/services/note_service.dart';
import '../../trips/services/trip_service.dart';

/// 记录页：底部导航第二个 tab，按「手账卡片」列出所有旅行记录。
/// 数据来源：旅行列表 + 城市名映射(geojson) + 账单汇总花费 + 笔记摘录。
class RecordsPage extends StatefulWidget {
  final Dio? authDio;
  final int refreshVersion;
  const RecordsPage({super.key, this.authDio, this.refreshVersion = 0});

  @override
  State<RecordsPage> createState() => _RecordsPageState();
}

class _RecordsPageState extends State<RecordsPage> {
  List<Trip>? _trips;
  final Map<String, String> _cityNameByAdcode = {};
  final Map<int, double> _spendByTrip = {};
  final Map<int, String> _noteByTrip = {};
  int _sort = 0; // 0 按时间 1 按消费

  TripService? _tripService;
  BillService? _billService;
  NoteService? _noteService;
  CityService? _cityService;

  @override
  void initState() {
    super.initState();
    final dio = widget.authDio;
    if (dio != null) {
      _tripService = TripService(dio);
      _billService = BillService(dio);
      _noteService = NoteService(dio);
      _cityService = CityService(dio);
    }
    _load();
  }

  @override
  void didUpdateWidget(covariant RecordsPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    // 切到记录 tab 时 HomePage 会递增版本号，这里重新拉数据
    if (widget.refreshVersion != oldWidget.refreshVersion) {
      _load();
    }
  }

  Future<void> _load() async {
    try {
      // 并行加载：城市名映射 + 旅行列表
      final citiesFuture = CityLoader.load('assets/中国_市.geojson');
      final tripsFuture = _tripService?.getTrips() ?? Future.value(<Trip>[]);
      final cities = await citiesFuture;
      final trips = await tripsFuture;

      final nameMap = <String, String>{};
      for (final c in cities) {
        nameMap[toAdcode(c.code)] = stripCitySuffix(c.name);
      }

      // 并行拉每个旅行的花费汇总 + 笔记摘录
      final spendMap = <int, double>{};
      final noteMap = <int, String>{};
      if (_billService != null && _noteService != null) {
        await Future.wait(trips.map((t) async {
          try {
            final bills = await _billService!.getBillsForTrip(t.id);
            spendMap[t.id] = bills.fold(0.0, (s, b) => s + b.amountValue);
          } catch (_) {
            spendMap[t.id] = 0;
          }
          try {
            noteMap[t.id] = await _noteService!.getNote(t.id);
          } catch (_) {}
        }));
      }

      if (!mounted) return;
      setState(() {
        _cityNameByAdcode
          ..clear()
          ..addAll(nameMap);
        _spendByTrip
          ..clear()
          ..addAll(spendMap);
        _noteByTrip
          ..clear()
          ..addAll(noteMap);
        _trips = trips;
      });
    } catch (_) {
      if (mounted) setState(() => _trips = []);
    }
  }

  List<Trip> get _sorted {
    final list = [..._trips!];
    if (_sort == 1) {
      // 按消费：消费多的在前
      list.sort((a, b) =>
          (_spendByTrip[b.id] ?? 0).compareTo(_spendByTrip[a.id] ?? 0));
    } else {
      // 按时间：最新的在前
      list.sort((a, b) => b.createTime.compareTo(a.createTime));
    }
    return list;
  }

  String _cityName(Trip t) => _cityNameByAdcode[t.adcode] ?? t.adcode;

  Future<void> _onAdd() async {
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => CityPickerPage(onPick: (adcode, name) async {
        try {
          // 没点亮就点亮（自动建一条旅行），点亮过就再添加一条旅行
          final lit = await _cityService!.getLitList();
          if (lit.contains(adcode)) {
            await _tripService!.addTrip(adcode);
          } else {
            await _cityService!.lightUp(adcode);
          }
          // 找到该城市最新的旅行，进入详情页
          final trips = await _tripService!.getTrips();
          final cityTrips = trips.where((t) => t.adcode == adcode).toList()
            ..sort((a, b) => b.createTime.compareTo(a.createTime));
          if (cityTrips.isEmpty) return '添加失败';
          final latest = cityTrips.first;
          if (!mounted) return null;
          await Navigator.of(context).push(MaterialPageRoute(
            builder: (_) => TripHomePage(
              tripId: latest.id,
              cityName: name,
              tripLabel: '旅行 #${latest.id}',
              authDio: widget.authDio!,
            ),
          ));
          return null;
        } on DioException catch (e) {
          return _parseApiError(e);
        } catch (_) {
          return '添加失败';
        }
      }),
    ));
    if (mounted) _load();
  }

  String _parseApiError(DioException e) {
    if (e.response?.data is Map) {
      final detail = (e.response!.data as Map)['detail'];
      if (detail is String) return detail;
    }
    return '添加失败';
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: true,
      bottom: false,
      child: Stack(
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _SortChips(sort: _sort, onSelect: (i) => setState(() => _sort = i)),
              Expanded(child: _buildBody()),
            ],
          ),
          Positioned(
            bottom: 20,
            right: 20,
            child: AddFab(onTap: _onAdd),
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    final trips = _trips;
    if (trips == null) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.black),
      );
    }
    if (trips.isEmpty) return const _EmptyState();

    final list = _sorted;
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(20, 4, 20, 28),
      itemCount: list.length,
      itemBuilder: (_, i) {
        final t = list[i];
        return _RecordCard(
          cityName: _cityName(t),
          tripLabel: '旅行 #${t.id}',
          spend: _spendByTrip[t.id] ?? 0,
          note: _noteByTrip[t.id] ?? '',
          onTap: () async {
            await Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => TripHomePage(
                tripId: t.id,
                cityName: _cityName(t),
                tripLabel: '旅行 #${t.id}',
                authDio: widget.authDio!,
              ),
            ));
            _load();
          },
        );
      },
    );
  }
}

/// 顶部筛选 chips：按时间 / 按消费
class _SortChips extends StatelessWidget {
  final int sort;
  final ValueChanged<int> onSelect;
  const _SortChips({required this.sort, required this.onSelect});

  static const _labels = ['按时间', '按消费'];

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.fromLTRB(20, 14, 20, 16),
      child: Row(
        children: [
          for (int i = 0; i < _labels.length; i++) ...[
            _Chip(
              label: _labels[i],
              active: sort == i,
              onTap: () => onSelect(i),
            ),
            if (i != _labels.length - 1) const SizedBox(width: 12),
          ],
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final bool active;
  final VoidCallback onTap;
  const _Chip({required this.label, required this.active, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
        decoration: BoxDecoration(
          color: active ? AppColors.black : AppColors.surface,
          border: Border.all(color: AppColors.black, width: 2),
          borderRadius: BorderRadius.circular(999),
          boxShadow: const [
            BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12),
          ],
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
            color: active ? AppColors.white : AppColors.black,
          ),
        ),
      ),
    );
  }
}

/// 单张旅行记录卡片（手账风格）
class _RecordCard extends StatelessWidget {
  final String cityName;
  final String tripLabel;
  final double spend;
  final String note;
  final VoidCallback onTap;
  const _RecordCard({
    required this.cityName,
    required this.tripLabel,
    required this.spend,
    required this.note,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 20),
        child: Stack(
          children: [
            Container(
              decoration: _cardDecoration(AppColors.surface),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _Header(cityName: cityName, tripLabel: tripLabel, spend: spend),
                  const SizedBox(height: 12),
                  const _DashedDivider(),
                  const SizedBox(height: 12),
                  const _AlbumPlaceholder(),
                  if (note.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    _NoteBlock(note: note),
                  ],
                ],
              ),
            ),
            // 右上角图钉装饰（半透明、轻微旋转）
            Positioned(
              top: 6,
              right: 10,
              child: Transform.rotate(
                angle: 0.2,
                child: const Opacity(
                  opacity: 0.22,
                  child: Icon(Icons.push_pin, size: 30, color: AppColors.black),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  final String cityName;
  final String tripLabel;
  final double spend;
  const _Header({
    required this.cityName,
    required this.tripLabel,
    required this.spend,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                cityName,
                style: const TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: AppColors.black,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                tripLabel,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppColors.greyText,
                ),
              ),
            ],
          ),
        ),
        _SpendBadge(spend: spend),
      ],
    );
  }
}

class _SpendBadge extends StatelessWidget {
  final double spend;
  const _SpendBadge({required this.spend});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surfaceVariant,
        border: Border.all(color: AppColors.black, width: 2),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.payments, size: 14, color: AppColors.black),
          const SizedBox(width: 4),
          Text(
            formatMoney(spend),
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppColors.black,
            ),
          ),
        ],
      ),
    );
  }
}

class _AlbumPlaceholder extends StatelessWidget {
  const _AlbumPlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.surfaceVariant,
        border: Border.all(color: AppColors.black, width: 2),
        borderRadius: BorderRadius.circular(6),
      ),
      child: const Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.photo_outlined, size: 16, color: AppColors.greyText),
          SizedBox(width: 6),
          Text(
            '相册即将上线',
            style: TextStyle(fontSize: 12, color: AppColors.greyText),
          ),
        ],
      ),
    );
  }
}

class _NoteBlock extends StatelessWidget {
  final String note;
  const _NoteBlock({required this.note});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLow,
        border: Border.all(color: AppColors.black, width: 2),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.edit, size: 16, color: AppColors.black),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              note,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 14, color: AppColors.black),
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.edit_note_outlined, size: 64, color: AppColors.greyMedium),
          SizedBox(height: 12),
          Text('还没有记录', style: TextStyle(fontSize: 16, color: AppColors.greyText)),
          SizedBox(height: 4),
          Text(
            '在地图上长按点亮城市，开始记录旅行',
            style: TextStyle(fontSize: 14, color: AppColors.greyMedium),
          ),
        ],
      ),
    );
  }
}

/// 不规则圆角 + 3px 黑边 + 硬偏移阴影（新粗野主义卡片）
BoxDecoration _cardDecoration(Color bg) => BoxDecoration(
      color: bg,
      border: Border.all(color: AppColors.black, width: 2),
      borderRadius: BorderRadius.circular(12),
      boxShadow: const [
        BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12),
      ],
    );

class _DashedDivider extends StatelessWidget {
  const _DashedDivider();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 2,
      width: double.infinity,
      child: CustomPaint(painter: _DashedPainter()),
    );
  }
}

class _DashedPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppColors.black
      ..strokeWidth = 2;
    const dash = 8.0;
    const gap = 6.0;
    var x = 0.0;
    while (x < size.width) {
      canvas.drawLine(
        Offset(x, 0),
        Offset((x + dash).clamp(0, size.width), 0),
        paint,
      );
      x += dash + gap;
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
