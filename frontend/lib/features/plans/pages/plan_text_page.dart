import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/lined_pad.dart';
import '../services/plan_service.dart';

class PlanTextPage extends StatefulWidget {
  final String adcode;
  final String cityName;
  final Dio authDio;
  const PlanTextPage({super.key, required this.adcode, required this.cityName, required this.authDio});
  @override
  State<PlanTextPage> createState() => _PlanTextPageState();
}

class _PlanTextPageState extends State<PlanTextPage> {
  late final PlanService _service;
  final _ctrl = TextEditingController();
  bool _loading = true;

  static const _style = TextStyle(fontSize: 16, color: AppColors.black, height: 2.0);
  static const _pad = EdgeInsets.fromLTRB(24, 16, 24, 16);
  static final _baseOffset = (() {
    final tp = TextPainter(text: const TextSpan(text: 'X', style: _style), textDirection: TextDirection.ltr)..layout();
    return tp.computeLineMetrics().first.baseline;
  })();
  static final _lineH = _style.fontSize! * _style.height!;

  @override
  void initState() {
    super.initState();
    _service = PlanService(widget.authDio);
    _load();
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  Future<void> _load() async {
    try {
      final content = await _service.getPlan(widget.adcode);
      if (mounted) setState(() { _ctrl.text = content; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    try {
      await _service.setPlan(widget.adcode, _ctrl.text.trim());
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('已保存'), backgroundColor: Colors.black, behavior: SnackBarBehavior.floating));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('保存失败'), backgroundColor: Colors.black, behavior: SnackBarBehavior.floating));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator(color: Colors.black)));
    return Scaffold(
      backgroundColor: AppColors.white,
      body: SafeArea(
        child: Column(children: [
          _TopBar(cityName: widget.cityName, onSave: _save),
          Expanded(child: LinedPad(ctrl: _ctrl, style: _style, padding: _pad, baseOffset: _baseOffset, lineH: _lineH)),
        ]),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  final String cityName;
  final VoidCallback onSave;
  const _TopBar({required this.cityName, required this.onSave});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(color: AppColors.white, border: Border(bottom: BorderSide(color: AppColors.black, width: 2))),
      child: Row(children: [
        GestureDetector(onTap: () => Navigator.of(context).pop(), child: const Icon(Icons.arrow_back, color: AppColors.black)),
        const SizedBox(width: 16),
        Expanded(child: Text('$cityName 计划', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.black), overflow: TextOverflow.ellipsis)),
        GestureDetector(onTap: onSave, child: const Text('保存', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: AppColors.black))),
      ]),
    );
  }
}

