import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../trips/models/category.dart';
import '../services/plan_service.dart';
import 'plan_text_page.dart';

class PlanPage extends StatefulWidget {
  final String adcode;
  final String cityName;
  final Dio authDio;

  const PlanPage({
    super.key,
    required this.adcode,
    required this.cityName,
    required this.authDio,
  });

  @override
  State<PlanPage> createState() => _PlanPageState();
}

class _PlanPageState extends State<PlanPage> {
  late final PlanService _service;
  List<Map<String, dynamic>>? _budgets;

  double get _totalBudget {
    if (_budgets == null) return 0;
    double sum = 0;
    for (final b in _budgets!) {
      final v = b['amount'];
      if (v is num) sum += v.toDouble();
      if (v is String) sum += double.tryParse(v) ?? 0;
    }
    return sum;
  }

  @override
  void initState() {
    super.initState();
    _service = PlanService(widget.authDio);
    _load();
  }

  Future<void> _load() async {
    try {
      final budgets = await _service.getBudgets(widget.adcode);
      if (mounted) setState(() => _budgets = budgets);
    } catch (_) {
      if (mounted) setState(() => _budgets = []);
    }
  }

  Future<void> _deleteBudget(int id) async {
    try {
      await _service.deleteBudget(id);
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
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _Header(
              cityName: widget.cityName,
              onPlan: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => PlanTextPage(adcode: widget.adcode, cityName: widget.cityName, authDio: widget.authDio),
              )),
            ),
            if (_budgets != null) _TotalBudget(amount: _totalBudget),
            Expanded(child: _buildBody()),
            _BottomButton(onTap: () async {
              await Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => AddBudgetPage(adcode: widget.adcode, cityName: widget.cityName, authDio: widget.authDio),
              ));
              _load();
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_budgets == null) {
      return const Center(child: CircularProgressIndicator(color: Colors.black));
    }
    if (_budgets!.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.savings_outlined, size: 64, color: AppColors.greyMedium),
            const SizedBox(height: 12),
            const Text('还没有预算', style: TextStyle(fontSize: 16, color: AppColors.greyText)),
          ],
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: _budgets!.length,
      itemBuilder: (_, i) {
        final b = _budgets![i];
        final cat = _parseInt(b['category']);
        final amt = _parseAmount(b['amount']);
        final customCategory = b['custom_category'] as String?;
        final catName = (cat == 6 && customCategory != null && customCategory.isNotEmpty)
            ? customCategory
            : (BillCategory.names[cat] ?? '');
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: AppColors.white,
            border: Border.all(color: AppColors.black, width: 2),
            borderRadius: BorderRadius.circular(8),
            boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12)],
          ),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(color: AppColors.black, borderRadius: BorderRadius.circular(8)),
                child: Icon(BillCategory.icon(cat), color: AppColors.white, size: 20),
              ),
              const SizedBox(width: 12),
              Text(catName, style: const TextStyle(fontSize: 14, color: AppColors.black)),
              const Spacer(),
              Text('¥ ${amt.toStringAsFixed(0)}',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.black)),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: () => _deleteBudget(_parseInt(b['id'])),
                child: const Icon(Icons.close, size: 18, color: AppColors.greyMedium),
              ),
            ],
          ),
        );
      },
    );
  }

  int _parseInt(dynamic v) {
    if (v is int) return v;
    if (v is String) return int.tryParse(v) ?? 0;
    return 0;
  }

  double _parseAmount(dynamic v) {
    if (v is num) return v.toDouble();
    if (v is String) return double.tryParse(v) ?? 0;
    return 0;
  }
}

// ---- 顶栏（照着 TripDetailPage 抄） ----
class _Header extends StatelessWidget {
  final String cityName;
  final VoidCallback onPlan;
  const _Header({required this.cityName, required this.onPlan});

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
            child: Text(cityName,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.black),
                overflow: TextOverflow.ellipsis),
          ),
          GestureDetector(
            onTap: onPlan,
            child: const Text('计划', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: AppColors.black)),
          ),
        ],
      ),
    );
  }
}

// ---- 总预算（照着 TotalSpent 抄） ----
class _TotalBudget extends StatelessWidget {
  final double amount;
  const _TotalBudget({required this.amount});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Column(
        children: [
          const Text('总预算', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.greyText, letterSpacing: 1)),
          const SizedBox(height: 4),
          Text('¥ ${amount.toStringAsFixed(0)}',
              style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: AppColors.black)),
        ],
      ),
    );
  }
}

// ---- 底部按钮（照着 TripDetailPage 的 _BottomButton 抄） ----
class _BottomButton extends StatelessWidget {
  final VoidCallback onTap;
  const _BottomButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.black, width: 2)),
      ),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: AppColors.black,
            border: Border.all(color: AppColors.black, width: 2),
            borderRadius: BorderRadius.circular(12),
            boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 2), blurRadius: 12)],
          ),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.add_circle_outline, color: AppColors.white, size: 20),
              SizedBox(width: 8),
              Text('添加预算', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.white)),
            ],
          ),
        ),
      ),
    );
  }
}

// ============================================================
// AddBudgetPage — 照着 AddBillPage 抄
// ============================================================
class AddBudgetPage extends StatefulWidget {
  final String adcode;
  final String cityName;
  final Dio authDio;

  const AddBudgetPage({
    super.key,
    required this.adcode,
    required this.cityName,
    required this.authDio,
  });

  @override
  State<AddBudgetPage> createState() => _AddBudgetPageState();
}

class _AddBudgetPageState extends State<AddBudgetPage> {
  late final PlanService _service;
  final _amountCtrl = TextEditingController();
  final _customCtrl = TextEditingController();
  int? _selectedCategory;
  bool _saving = false;

  bool get _needsCustom => _selectedCategory == 6;

  @override
  void initState() {
    super.initState();
    _service = PlanService(widget.authDio);
  }

  @override
  void dispose() {
    _amountCtrl.dispose();
    _customCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final raw = _amountCtrl.text.trim();
    if (raw.isEmpty) { _showError('请输入金额'); return; }
    final amount = double.tryParse(raw);
    if (amount == null || amount <= 0) { _showError('请输入有效的金额'); return; }
    if (_selectedCategory == null) { _showError('请选择分类'); return; }
    final custom = _needsCustom ? _customCtrl.text.trim() : null;
    if (_needsCustom && custom!.isEmpty) { _showError('请输入自定义分类名称'); return; }

    setState(() => _saving = true);
    try {
      await _service.setBudget(
        adcode: widget.adcode,
        category: _selectedCategory!,
        amount: amount,
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
            _AddHeader(cityName: widget.cityName),
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
                    _CategoryGrid(selected: _selectedCategory, onSelect: (cat) => setState(() => _selectedCategory = cat)),
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

class _AddHeader extends StatelessWidget {
  final String cityName;
  const _AddHeader({required this.cityName});

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
            child: Text('$cityName 添加预算',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.black),
                overflow: TextOverflow.ellipsis),
          ),
        ],
      ),
    );
  }
}

// ---- 以下照着 AddBillPage 的部件抄 ----
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

class _CategoryLabel extends StatelessWidget {
  const _CategoryLabel();
  @override
  Widget build(BuildContext context) {
    return const Text('分类', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500, color: AppColors.black));
  }
}

class _CategoryGrid extends StatelessWidget {
  final int? selected;
  final ValueChanged<int> onSelect;
  const _CategoryGrid({required this.selected, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    final entries = BillCategory.names.entries.toList();
    return GridView.count(
      crossAxisCount: 4,
      mainAxisSpacing: 10,
      crossAxisSpacing: 10,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      children: entries.map((e) {
        final cat = e.key;
        final name = e.value;
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
                Icon(BillCategory.icon(cat), size: 20, color: isSelected ? AppColors.white : AppColors.black),
                const SizedBox(height: 4),
                Text(name, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.5, color: isSelected ? AppColors.white : AppColors.black)),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

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
              ? const Center(child: SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.white)))
              : const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.check_circle, color: AppColors.white, size: 20),
                    SizedBox(width: 8),
                    Text('保存预算', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.white)),
                  ],
                ),
        ),
      ),
    );
  }
}
