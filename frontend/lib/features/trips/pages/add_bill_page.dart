import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../services/bill_service.dart';
import '../models/category.dart';

class AddBillPage extends StatefulWidget {
  final int tripId;
  final String tripName;
  final Dio authDio;

  const AddBillPage({
    super.key,
    required this.tripId,
    required this.tripName,
    required this.authDio,
  });

  @override
  State<AddBillPage> createState() => _AddBillPageState();
}

class _AddBillPageState extends State<AddBillPage> {
  late final BillService _billService;
  final _amountCtrl = TextEditingController();
  final _customCtrl = TextEditingController();
  Map<int, String> _categories = {};
  int? _selectedCategory;
  bool _saving = false;

  bool get _needsCustom =>
      _selectedCategory != null && _selectedCategory == 6;

  @override
  void initState() {
    super.initState();
    _billService = BillService(widget.authDio);
    _loadCategories();
  }

  @override
  void dispose() {
    _amountCtrl.dispose();
    _customCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadCategories() async {
    try {
      final cats = await _billService.getCategories();
      if (mounted) setState(() => _categories = cats);
    } catch (_) {
      // 使用静态默认值
    }
  }

  Future<void> _save() async {
    final raw = _amountCtrl.text.trim();
    if (raw.isEmpty) {
      _showError('请输入金额');
      return;
    }
    final amount = double.tryParse(raw);
    if (amount == null || amount <= 0) {
      _showError('请输入有效的金额');
      return;
    }
    if (_selectedCategory == null) {
      _showError('请选择消费分类');
      return;
    }
    final custom = _needsCustom ? _customCtrl.text.trim() : null;
    if (_needsCustom && custom!.isEmpty) {
      _showError('请输入自定义分类名称');
      return;
    }

    setState(() => _saving = true);
    try {
      await _billService.addBill(
        tripId: widget.tripId,
        amount: amount,
        category: _selectedCategory!,
        customCategory: custom,
      );
      if (mounted) Navigator.of(context).pop(true);
    } catch (_) {
      if (mounted) _showError('保存失败');
    }
    if (mounted) setState(() => _saving = false);
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.black, behavior: SnackBarBehavior.floating),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _Header(tripName: widget.tripName),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _AmountInput(ctrl: _amountCtrl),
                    const SizedBox(height: 28),
                    const _CategoryLabel(),
                    const SizedBox(height: 12),
                    _CategoryGrid(
                      categories: _categories,
                      selected: _selectedCategory,
                      onSelect: (cat) => setState(() => _selectedCategory = cat),
                    ),
                    if (_needsCustom) ...[
                      const SizedBox(height: 16),
                      _CustomCategoryInput(ctrl: _customCtrl),
                    ],
                  ],
                ),
              ),
            ),
            _SaveButton(saving: _saving, onTap: _save),
          ],
        ),
      ),
    );
  }
}

// ---- 顶栏 ----
class _Header extends StatelessWidget {
  final String tripName;
  const _Header({required this.tripName});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.black, width: 2)),
      ),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.of(context).pop(),
            child: const Icon(Icons.arrow_back, color: AppColors.black),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Text(tripName,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.black),
                overflow: TextOverflow.ellipsis),
          ),
        ],
      ),
    );
  }
}

// ---- 金额输入 ----
class _AmountInput extends StatelessWidget {
  final TextEditingController ctrl;
  const _AmountInput({required this.ctrl});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.white,
        border: Border.all(color: AppColors.black, width: 2),
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('金额', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500, color: AppColors.black)),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              const Text('¥', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: AppColors.black)),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: ctrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(fontSize: 40, height: 1.2, fontWeight: FontWeight.w700, color: AppColors.black),
                  decoration: const InputDecoration(
                    hintText: '0.00',
                    border: InputBorder.none,
                    hintStyle: TextStyle(color: Color(0xFFC6C6C7)),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ---- 分类标签 ----
class _CategoryLabel extends StatelessWidget {
  const _CategoryLabel();

  @override
  Widget build(BuildContext context) {
    return const Text('分类', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500, color: AppColors.black));
  }
}

// ---- 分类网格 ----
class _CategoryGrid extends StatelessWidget {
  final Map<int, String> categories;
  final int? selected;
  final ValueChanged<int> onSelect;
  const _CategoryGrid({required this.categories, required this.selected, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    // 固定 6 个分类以 BillCategory.names 顺序为准
    final entries = BillCategory.names.entries.toList();

    return GridView.count(
      crossAxisCount: 4,
      mainAxisSpacing: 10,
      crossAxisSpacing: 10,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      children: entries.map((e) {
        final cat = e.key;
        final name = categories[cat] ?? e.value;
        final isSelected = selected == cat;
        return GestureDetector(
          onTap: () => onSelect(cat),
          child: Container(
            decoration: BoxDecoration(
              color: isSelected ? AppColors.black : AppColors.white,
              border: Border.all(color: AppColors.black, width: 2),
              borderRadius: BorderRadius.circular(8),
              boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12)],
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(BillCategory.icon(cat),
                    size: 20,
                    color: isSelected ? AppColors.white : AppColors.black),
                const SizedBox(height: 4),
                Text(name,
                    style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 0.5,
                        color: isSelected ? AppColors.white : AppColors.black)),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

// ---- 自定义分类输入 ----
class _CustomCategoryInput extends StatelessWidget {
  final TextEditingController ctrl;
  const _CustomCategoryInput({required this.ctrl});

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: ctrl,
      style: const TextStyle(fontSize: 14, color: AppColors.black),
      decoration: InputDecoration(
        hintText: '请输入分类名称',
        filled: true,
        fillColor: AppColors.greyLight,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.greyMedium, width: 1.5),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.greyMedium, width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.black, width: 1.5),
        ),
        hintStyle: const TextStyle(color: AppColors.greyMedium),
      ),
    );
  }
}

// ---- 保存按钮 ----
class _SaveButton extends StatelessWidget {
  final bool saving;
  final VoidCallback onTap;
  const _SaveButton({required this.saving, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.black, width: 2)),
      ),
      child: GestureDetector(
        onTap: saving ? null : onTap,
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: AppColors.black,
            border: Border.all(color: AppColors.black, width: 2),
            borderRadius: BorderRadius.circular(12),
            boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12)],
          ),
          child: saving
              ? const Center(
                  child: SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.white)))
              : const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.check_circle, color: AppColors.white, size: 20),
                    SizedBox(width: 8),
                    Text('保存支出',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.white)),
                  ],
                ),
        ),
      ),
    );
  }
}
