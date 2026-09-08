import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

/// 行程时间轴卡片（AI 规划结果的展示）
/// 数据来源：后端发回的 ⟦PLAN⟧JSON⟦/PLAN⟧ 里解析出的 plan，结构：
/// { days, people, start_city, target_city, total_cost, warning,
///   itinerary: [ { day, activities: [ {type, position, start, end, vehicle,
///     start_time, end_time, cost, transports: [{mode, start_time, end_time, cost}]} ] } ] }
class ItineraryCard extends StatelessWidget {
  final Map<String, dynamic> plan;
  const ItineraryCard({super.key, required this.plan});

  // 活动类型 → 中文（后端只会发这9种；没对上的直接显示原文）
  static const _typeLabels = {
    'train': '火车',
    'airplane': '飞机',
    'intercity': '跨城',
    'breakfast': '早餐',
    'lunch': '午餐',
    'dinner': '晚餐',
    'attraction': '游览',
    'accommodation': '入住',
    'free': '自由活动',
  };

  // 市内交通方式 → 中文（后端只会发这3种）
  static const _modeLabels = {
    'metro': '地铁',
    'taxi': '打车',
    'walk': '步行',
  };

  // ---- 宽松取值：jsonDecode 出来的数字可能是 int 也可能是 double，字段也可能缺 ----
  static String _str(Map<String, dynamic> m, String key) => (m[key] ?? '').toString();

  static num _num(Map<String, dynamic> m, String key) {
    final v = m[key];
    return v is num ? v : 0;
  }

  /// 费用文案：0 → 免费；整数 → ¥73；小数 → ¥73.5（去掉多余的 0）
  static String _money(num v) {
    if (v <= 0) return '免费';
    if (v == v.roundToDouble()) return '¥${v.toInt()}';
    return '¥${v.toStringAsFixed(2).replaceAll(RegExp(r'0+$'), '')}';
  }

  @override
  Widget build(BuildContext context) {
    final itinerary = (plan['itinerary'] as List?) ?? const [];
    final warning = _str(plan, 'warning');

    return Container(
      // clipBehavior 让黑条不顶出圆角
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: AppColors.white,
        border: Border.all(color: AppColors.black, width: 2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 预算警告等提示条（没有就不占地方）
          if (warning.isNotEmpty) _warningBar(warning),
          for (var i = 0; i < itinerary.length; i++)
            _daySection(itinerary[i] as Map<String, dynamic>, isLastDay: i == itinerary.length - 1),
          _summaryBar(),
        ],
      ),
    );
  }

  /// 顶部提示条（如"预算不足：预计花费 ¥1900，超出预算 ¥120"）
  Widget _warningBar(String text) {
    return Container(
      color: AppColors.greyLight,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          const Icon(Icons.info_outline, size: 14, color: AppColors.greyText),
          const SizedBox(width: 6),
          Expanded(
            child: Text(text, style: const TextStyle(fontSize: 12, color: AppColors.greyText)),
          ),
        ],
      ),
    );
  }

  /// 一天的内容：黑底白字"第N天"条（跨城天带上 出发→到达，右侧当日花费）+ 时间轴
  Widget _daySection(Map<String, dynamic> day, {required bool isLastDay}) {
    final activities = (day['activities'] as List?) ?? const [];

    // 这天有没有跨城交通，有就把"上海→杭州"标在"第N天"旁边
    String route = '';
    num dayCost = 0;
    for (final a in activities) {
      final m = a as Map<String, dynamic>;
      if (route.isEmpty) {
        final start = _str(m, 'start');
        final end = _str(m, 'end');
        if (start.isNotEmpty && end.isNotEmpty) route = ' $start→$end';
      }
      // 当日花费 = 每个活动的费用 + 它的市内交通费（口径和后端 total_cost 一致）
      dayCost += _num(m, 'cost');
      for (final t in (m['transports'] as List?) ?? const []) {
        dayCost += _num(t as Map<String, dynamic>, 'cost');
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          color: AppColors.black,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          child: Row(
            children: [
              Text('第${day['day']}天',
                  style: const TextStyle(
                      color: AppColors.white, fontSize: 12, fontWeight: FontWeight.w700)),
              if (route.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(left: 8),
                  child: Text(route.trim(),
                      style: const TextStyle(color: AppColors.white, fontSize: 12)),
                ),
              const Spacer(),
              Text(_money(dayCost),
                  style: const TextStyle(
                      color: AppColors.white, fontSize: 12, fontWeight: FontWeight.w700)),
            ],
          ),
        ),
        Padding(
          padding: EdgeInsets.fromLTRB(12, 10, 12, isLastDay ? 12 : 4),
          child: Column(
            children: [
              for (var i = 0; i < activities.length; i++)
                _activityRow(
                  activities[i] as Map<String, dynamic>,
                  isLast: isLastDay && i == activities.length - 1,
                ),
            ],
          ),
        ),
      ],
    );
  }

  /// 时间轴上的一行活动：左边圆点+竖线，右边时间/类型标签/事项名/费用
  Widget _activityRow(Map<String, dynamic> a, {required bool isLast}) {
    final start = _str(a, 'start');
    final end = _str(a, 'end');
    final isIntercity = start.isNotEmpty && end.isNotEmpty;
    final vehicle = _str(a, 'vehicle');

    // 事项名：跨城交通显示"车次 出发→到达"，其他显示地点名
    final name = isIntercity
        ? (vehicle.isNotEmpty ? '$vehicle $start→$end' : '$start→$end')
        : _str(a, 'position');
    final transports = (a['transports'] as List?) ?? const [];

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 左侧时间轴轨道：实心圆点 + 2px 黑竖线（最后一个活动不画线）
          SizedBox(
            width: 14,
            child: Column(
              children: [
                const SizedBox(height: 5),
                Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(color: AppColors.black, shape: BoxShape.circle),
                ),
                Expanded(
                  child: isLast
                      ? const SizedBox()
                      : Center(child: Container(width: 2, color: AppColors.black)),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      SizedBox(
                        width: 40,
                        child: Text(_str(a, 'start_time'),
                            style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: AppColors.black)),
                      ),
                      // 类型小胶囊：黑底白字
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppColors.black,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(_typeLabels[_str(a, 'type')] ?? _str(a, 'type'),
                            style: const TextStyle(
                                fontSize: 10,
                                color: AppColors.white,
                                fontWeight: FontWeight.w600)),
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(name,
                            style: const TextStyle(fontSize: 13, color: AppColors.black),
                            overflow: TextOverflow.ellipsis),
                      ),
                      const SizedBox(width: 6),
                      Text(_money(_num(a, 'cost')),
                          style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: AppColors.black)),
                    ],
                  ),
                  // 市内交通：活动行下面的灰色小字（如"09:50 地铁前往西湖 ¥5"）
                  for (final t in transports) _transportLine(t as Map<String, dynamic>, name),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 市内交通灰色小字行：时间 + 方式 + 去哪 + 花费（0 元不显示费用）
  Widget _transportLine(Map<String, dynamic> t, String dest) {
    final mode = _modeLabels[_str(t, 'mode')] ?? _str(t, 'mode');
    final cost = _num(t, 'cost');
    return Padding(
      padding: const EdgeInsets.only(top: 3, left: 40),
      child: Row(
        children: [
          Expanded(
            child: Text(
              dest.isEmpty
                  ? '${_str(t, 'start_time')} $mode'
                  : '${_str(t, 'start_time')} $mode前往$dest',
              style: const TextStyle(fontSize: 11, color: AppColors.greyText),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (cost > 0)
            Text(_money(cost), style: const TextStyle(fontSize: 11, color: AppColors.greyText)),
        ],
      ),
    );
  }

  /// 卡尾黑底白字摘要条
  Widget _summaryBar() {
    return Container(
      color: AppColors.black,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Text(
        '共${plan['days']}天 · 出行${plan['people']}人 · 总花费约${_money(_num(plan, 'total_cost'))}',
        textAlign: TextAlign.center,
        style: const TextStyle(color: AppColors.white, fontSize: 12, fontWeight: FontWeight.w700),
      ),
    );
  }
}
