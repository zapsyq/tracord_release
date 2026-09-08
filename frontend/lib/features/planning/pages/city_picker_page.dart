import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/utils/city.dart';
import '../../map/models/city_data.dart';

/// 城市选择页：输入城市名搜索。
/// 选中城市后调用 onPick(adcode, 城市名)：
/// - 返回 null 表示成功，关闭本页；
/// - 返回错误字符串则提示并停留，让用户重新选。
class CityPickerPage extends StatefulWidget {
  final Future<String?> Function(String adcode, String name) onPick;
  const CityPickerPage({super.key, required this.onPick});

  @override
  State<CityPickerPage> createState() => _CityPickerPageState();
}

class _CityPickerPageState extends State<CityPickerPage> {
  List<CityData>? _cities;
  String _keyword = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final cities = await CityLoader.load('assets/中国_市.geojson');
      if (mounted) setState(() => _cities = cities);
    } catch (_) {
      if (mounted) setState(() => _cities = []);
    }
  }

  List<CityData> get _filtered {
    final cities = _cities ?? const <CityData>[];
    final kw = _keyword.trim();
    if (kw.isEmpty) return cities;
    return cities.where((c) => c.name.contains(kw)).toList();
  }

  Future<void> _pick(CityData c) async {
    final error = await widget.onPick(toAdcode(c.code), stripCitySuffix(c.name));
    if (!mounted) return;
    if (error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error), backgroundColor: Colors.black, behavior: SnackBarBehavior.floating),
      );
      return;
    }
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.white,
      body: SafeArea(
        child: Column(
          children: [
            _TopBar(onChanged: (v) => setState(() => _keyword = v)),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    final cities = _cities;
    if (cities == null) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.black),
      );
    }
    final list = _filtered;
    if (list.isEmpty) {
      return const Center(
        child: Text('没有找到城市', style: TextStyle(fontSize: 16, color: AppColors.greyText)),
      );
    }
    return ListView.builder(
      itemCount: list.length,
      itemBuilder: (_, i) {
        final c = list[i];
        return GestureDetector(
          onTap: () => _pick(c),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.greyLight, width: 1)),
            ),
            child: Text(
              stripCitySuffix(c.name),
              style: const TextStyle(fontSize: 16, color: AppColors.black),
            ),
          ),
        );
      },
    );
  }
}

class _TopBar extends StatelessWidget {
  final ValueChanged<String> onChanged;
  const _TopBar({required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(8, 8, 16, 12),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.black, width: 2)),
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: () => Navigator.of(context).pop(),
            icon: const Icon(Icons.arrow_back, color: AppColors.black),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: TextField(
              autofocus: true,
              onChanged: onChanged,
              decoration: InputDecoration(
                hintText: '搜索城市',
                prefixIcon: const Icon(Icons.search, color: AppColors.greyText),
                filled: true,
                fillColor: AppColors.greyLight,
                contentPadding: const EdgeInsets.symmetric(vertical: 10),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
