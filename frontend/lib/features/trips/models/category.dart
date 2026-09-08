import 'package:flutter/material.dart';

/// 账单消费分类（静态默认值，服务端 /bills/categories 获取的实际值优先）
class BillCategory {
  BillCategory._();

  static const Map<int, String> names = {
    1: '交通',
    2: '餐饮',
    3: '购物',
    4: '住宿',
    5: '娱乐',
    6: '其他',
  };

  static const Map<int, IconData> icons = {
    1: Icons.directions_bus,
    2: Icons.restaurant,
    3: Icons.shopping_bag,
    4: Icons.hotel,
    5: Icons.celebration,
    6: Icons.more_horiz,
  };

  static String name(int cat, {Map<int, String>? serverCategories}) {
    return serverCategories?[cat] ?? names[cat] ?? '自定义';
  }

  static IconData icon(int cat) => icons[cat] ?? Icons.more_horiz;
}
