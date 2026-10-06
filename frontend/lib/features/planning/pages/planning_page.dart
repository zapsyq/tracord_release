import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/utils/city.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/add_fab.dart';
import '../../map/models/city_data.dart';
import '../../plans/pages/plan_page.dart';
import '../../plans/services/plan_service.dart';
import 'city_picker_page.dart';

/// 规划页：底部导航第三个 tab，列出所有「未来计划」。
/// 一个计划 = 一个已设过计划或预算的城市。
class PlanningPage extends StatefulWidget {
  final Dio? authDio;
  final int refreshVersion;
  const PlanningPage({super.key, this.authDio, this.refreshVersion = 0});

  @override
  State<PlanningPage> createState() => _PlanningPageState();
}

class _PlanCard {
  final String adcode;
  final String cityName;
  final double budget;
  final String note;
  final int? planId;          // 该城市计划文本的记录ID(没有计划则为null)
  final List<int> budgetIds;  // 该城市全部预算的记录ID
  const _PlanCard({
    required this.adcode,
    required this.cityName,
    required this.budget,
    required this.note,
    this.planId,
    this.budgetIds = const [],
  });
}

class _PlanningPageState extends State<PlanningPage> {
  List<_PlanCard>? _cards;
  PlanService? _service;

  @override
  void initState() {
    super.initState();
    final dio = widget.authDio;
    if (dio != null) _service = PlanService(dio);
    _load();
  }

  @override
  void didUpdateWidget(covariant PlanningPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    // 切到规划 tab 时 HomePage 会递增版本号，这里重新拉数据
    if (widget.refreshVersion != oldWidget.refreshVersion) {
      _load();
    }
  }

  Future<void> _load() async {
    try {
      // 并行加载：城市名映射 + 全部计划 + 全部预算
      final citiesFuture = CityLoader.load('assets/中国_市.geojson');
      final plansFuture = _service?.getPlans() ?? Future.value(<Map<String, dynamic>>[]);
      final budgetsFuture = _service?.getAllBudgets() ?? Future.value(<Map<String, dynamic>>[]);
      final cities = await citiesFuture;
      final plans = await plansFuture;
      final budgets = await budgetsFuture;

      final nameMap = <String, String>{};
      for (final c in cities) {
        nameMap[toAdcode(c.code)] = stripCitySuffix(c.name);
      }

      // 计划文本（adcode -> content）与记录ID，并记录最新更新时间用于排序
      final notes = <String, String>{};
      final planIds = <String, int>{};
      final latestTime = <String, String>{};
      for (final p in plans) {
        final adcode = p['adcode'] as String? ?? '';
        if (adcode.isEmpty) continue;
        notes[adcode] = p['content'] as String? ?? '';
        final id = _parseId(p['id']);
        if (id != null) planIds[adcode] = id;
        final t = p['update_time'] as String? ?? '';
        if (t.compareTo(latestTime[adcode] ?? '') > 0) latestTime[adcode] = t;
      }

      // 预算汇总（adcode -> 总额）与记录ID，并记录最新更新时间
      final budgetByAdcode = <String, double>{};
      final budgetIdsByAdcode = <String, List<int>>{};
      for (final b in budgets) {
        final adcode = b['adcode'] as String? ?? '';
        if (adcode.isEmpty) continue;
        final amt = b['amount'];
        double v = 0;
        if (amt is num) {
          v = amt.toDouble();
        } else if (amt is String) {
          v = double.tryParse(amt) ?? 0;
        }
        budgetByAdcode[adcode] = (budgetByAdcode[adcode] ?? 0) + v;
        final id = _parseId(b['id']);
        if (id != null) (budgetIdsByAdcode[adcode] ??= []).add(id);
        final t = b['update_time'] as String? ?? '';
        if (t.compareTo(latestTime[adcode] ?? '') > 0) latestTime[adcode] = t;
      }

      // 合并两个数据源的城市，各成一张卡片，按最新更新时间降序（最近添加的在前）
      final adcodes = <String>{...notes.keys, ...budgetByAdcode.keys};
      final cards = adcodes.map((adcode) => _PlanCard(
            adcode: adcode,
            cityName: nameMap[adcode] ?? adcode,
            budget: budgetByAdcode[adcode] ?? 0,
            note: notes[adcode] ?? '',
            planId: planIds[adcode],
            budgetIds: budgetIdsByAdcode[adcode] ?? const [],
          )).toList()
        ..sort((a, b) => (latestTime[b.adcode] ?? '')
            .compareTo(latestTime[a.adcode] ?? ''));

      if (mounted) setState(() => _cards = cards);
    } catch (_) {
      if (mounted) setState(() => _cards = []);
    }
  }

  Future<void> _onAdd() async {
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => CityPickerPage(onPick: (adcode, name) async {
        await Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => PlanPage(
            adcode: adcode,
            cityName: name,
            authDio: widget.authDio!,
          ),
        ));
        return null;
      }),
    ));
    if (mounted) _load();
  }

  //把接口返回的ID宽松地转成int, 转不了返回null
  int? _parseId(dynamic v) {
    if (v is int) return v;
    if (v is String) return int.tryParse(v);
    return null;
  }

  //删除一张计划卡片: 计划文本 + 该城市全部预算, 删前先确认
  Future<void> _confirmDelete(_PlanCard card) async {
    final parts = <String>[];
    if (card.planId != null) parts.add('计划');
    if (card.budgetIds.isNotEmpty) parts.add('${card.budgetIds.length} 条预算');
    if (parts.isEmpty) return;

    final sure = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: AppColors.black, width: 2),
        ),
        title: const Text('删除计划',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.black)),
        content: Text('将删除${card.cityName}的${parts.join('与')}，删除后无法恢复。',
            style: const TextStyle(fontSize: 14, color: AppColors.greyText)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('取消', style: TextStyle(color: AppColors.greyText)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('删除',
                style: TextStyle(color: AppColors.black, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
    if (sure != true) return;

    try {
      if (card.planId != null) {
        await _service!.deletePlan(card.planId!);
      }
      for (final id in card.budgetIds) {
        await _service!.deleteBudget(id);
      }
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
    return SafeArea(
      top: true,
      bottom: false,
      child: Stack(
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _Header(count: _cards?.length ?? 0),
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
    final cards = _cards;
    if (cards == null) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.black),
      );
    }
    if (cards.isEmpty) return const _EmptyState();

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(20, 4, 20, 28),
      itemCount: cards.length,
      itemBuilder: (_, i) {
        final c = cards[i];
        return _PlanCardView(
          card: c,
          onTap: () async {
            await Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => PlanPage(
                adcode: c.adcode,
                cityName: c.cityName,
                authDio: widget.authDio!,
              ),
            ));
            _load();
          },
          onDelete: () => _confirmDelete(c),
        );
      },
    );
  }
}

/// 顶部标题栏：未来计划 + 数量
class _Header extends StatelessWidget {
  final int count;
  const _Header({required this.count});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 14, 20, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '未来计划',
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: AppColors.black),
          ),
          const SizedBox(height: 4),
          Text(
            '$count个即将开启的旅程',
            style: const TextStyle(fontSize: 16, color: AppColors.greyText),
          ),
        ],
      ),
    );
  }
}

/// 单张未来计划卡片
class _PlanCardView extends StatelessWidget {
  final _PlanCard card;
  final VoidCallback onTap;
  final VoidCallback onDelete;
  const _PlanCardView({required this.card, required this.onTap, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 20),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          border: Border.all(color: AppColors.black, width: 2),
          borderRadius: BorderRadius.circular(12),
          boxShadow: const [
            BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    card.cityName,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                      color: AppColors.black,
                    ),
                  ),
                ),
                // 删除这张计划(计划文本+预算一起删)
                GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: onDelete,
                  child: const Padding(
                    padding: EdgeInsets.all(4),
                    child: Icon(Icons.delete_outline, size: 22, color: AppColors.greyMedium),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Expanded(child: _BillBlock(budget: card.budget)),
                  const SizedBox(width: 12),
                  Expanded(child: _NoteBlock(note: card.note)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BillBlock extends StatelessWidget {
  final double budget;
  const _BillBlock({required this.budget});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.white,
        border: Border.all(color: AppColors.black, width: 2),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '预算',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppColors.greyText,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            budget == 0 ? '未设置' : formatMoney(budget),
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: AppColors.black),
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
        color: AppColors.white,
        border: Border.all(color: AppColors.black, width: 2),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '笔记',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppColors.greyText,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            note.isEmpty ? '暂无计划' : note,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 14,
              color: note.isEmpty ? AppColors.greyMedium : AppColors.black,
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
          Icon(Icons.event_note_outlined, size: 64, color: AppColors.greyMedium),
          SizedBox(height: 12),
          Text('还没有计划', style: TextStyle(fontSize: 16, color: AppColors.greyText)),
          SizedBox(height: 4),
          Text(
            '点击右下角 + 号添加计划',
            style: TextStyle(fontSize: 14, color: AppColors.greyMedium),
          ),
        ],
      ),
    );
  }
}

