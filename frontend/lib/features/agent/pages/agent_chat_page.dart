import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/theme/app_theme.dart';
import '../services/agent_service.dart';
import '../widgets/itinerary_card.dart';

class AgentChatPage extends StatefulWidget {
  final AgentService service;
  const AgentChatPage({super.key, required this.service});

  @override
  State<AgentChatPage> createState() => _AgentChatPageState();
}

class _AgentChatPageState extends State<AgentChatPage> {
  static const _storageKey = 'agent_chat_messages';

  final _messages = <_ChatMsg>[];
  final _scrollCtrl = ScrollController();
  bool _loading = false;
  bool _loaded = false;

  @override
  void initState() {
    super.initState();
    _loadMessages();
  }

  Future<void> _loadMessages() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw != null) {
      try {
        final list = json.decode(raw) as List<dynamic>;
        _messages.addAll(list.map((e) => _ChatMsg.fromJson(e as Map<String, dynamic>)));
      } catch (_) {}
    }
    if (mounted) setState(() => _loaded = true);
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, json.encode(_messages.map((m) => m.toJson()).toList()));
  }

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _send(String text) async {
    if (text.isEmpty || _loading) return;
    setState(() {
      _messages.add(_ChatMsg(text: text, isUser: true));
      _messages.add(_ChatMsg(text: '', isUser: false));
      _loading = true;
    });
    _scrollDown();
    await _persist();

    try {
      final aiIndex = _messages.length - 1;
      final buffer = StringBuffer();
      await for (final chunk in widget.service.chat(text)) {
        buffer.write(chunk);
        if (mounted) {
          // 实时显示时把行程数据段藏掉(哨兵没闭合就连同后面一起藏), 只露纯文本
          setState(() =>
              _messages[aiIndex] = _ChatMsg(text: _stripPlan(buffer.toString()), isUser: false));
          _scrollDown();
        }
      }
      // 流结束: 有行程标记就解析成卡片数据; 解析失败显示固定兜底话术(后端已无保底文本)
      final raw = buffer.toString();
      Map<String, dynamic>? plan;
      var finalText = raw;
      if (raw.contains(_planStart)) {
        plan = _extractPlan(raw);
        finalText = plan != null ? _stripPlan(raw) : _planBrokenText;
      }
      if (mounted) {
        setState(() => _messages[aiIndex] = _ChatMsg(text: finalText, isUser: false, plan: plan));
        _scrollDown();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _messages.removeLast();
          // 不糊原始报错(DioException 一长串), 给用户一句人话
          _messages.add(_ChatMsg(text: '连接不上服务器，请检查网络后再试', isUser: false));
        });
      }
    }
    if (mounted) {
      setState(() => _loading = false);
      await _persist();
    }
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(_scrollCtrl.position.maxScrollExtent,
            duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
      }
    });
  }

  //清空聊天记录: 弹确认框, 确认后清内存+删本地存储
  Future<void> _clearChat() async {
    final sure = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: AppColors.black, width: 2),
        ),
        title: const Text('清空聊天记录',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.black)),
        content: const Text('确定要删除所有聊天记录吗？删除后无法恢复。',
            style: TextStyle(fontSize: 14, color: AppColors.greyText)),
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
    if (sure == true && mounted) {
      setState(() => _messages.clear());
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_storageKey);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_loaded) return const Scaffold(body: Center(child: CircularProgressIndicator(color: Colors.black)));
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _HeaderBar(onClearChat: _clearChat),
            Expanded(child: _ChatList(messages: _messages, scrollCtrl: _scrollCtrl)),
            _InputBar(loading: _loading, onSend: _send),
          ],
        ),
      ),
    );
  }
}

class _ChatMsg {
  final String text;
  final bool isUser;
  final Map<String, dynamic>? plan; // 行程卡片数据(来自⟦PLAN⟧JSON, 只有AI消息可能有)

  const _ChatMsg({required this.text, required this.isUser, this.plan});

  Map<String, dynamic> toJson() =>
      {'text': text, 'isUser': isUser, if (plan != null) 'plan': plan};
  factory _ChatMsg.fromJson(Map<String, dynamic> json) => _ChatMsg(
        text: json['text'] as String,
        isUser: json['isUser'] as bool,
        plan: json['plan'] is Map<String, dynamic> ? json['plan'] as Map<String, dynamic> : null,
      );
}

class _HeaderBar extends StatelessWidget {
  final VoidCallback onClearChat;
  const _HeaderBar({required this.onClearChat});

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
          const Text('迹录',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.black)),
          const Spacer(),
          // 清空聊天记录(扫把)
          GestureDetector(
            onTap: onClearChat,
            child: const Icon(Icons.cleaning_services_outlined, size: 22, color: AppColors.black),
          ),
        ],
      ),
    );
  }
}

class _ChatList extends StatelessWidget {
  final List<_ChatMsg> messages;
  final ScrollController scrollCtrl;
  const _ChatList({required this.messages, required this.scrollCtrl});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: scrollCtrl,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: messages.length,
      itemBuilder: (_, i) => _Bubble(msg: messages[i]),
    );
  }
}

class _Bubble extends StatelessWidget {
  final _ChatMsg msg;
  const _Bubble({required this.msg});

  @override
  Widget build(BuildContext context) {
    // 带行程数据的AI消息: 渲染成整行占满的时间轴卡片, 不套普通气泡
    if (msg.plan != null) {
      return Container(
        margin: const EdgeInsets.only(bottom: 12),
        child: ItineraryCard(plan: msg.plan!),
      );
    }
    return Align(
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        constraints: const BoxConstraints(maxWidth: 300),
        decoration: BoxDecoration(
          color: msg.isUser ? AppColors.black : AppColors.white,
          border: Border.all(color: AppColors.black, width: 2),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: msg.isUser ? const Radius.circular(16) : const Radius.circular(4),
            bottomRight: msg.isUser ? const Radius.circular(4) : const Radius.circular(16),
          ),
        ),
        child: Text(
          msg.text.isEmpty ? '...' : msg.text,
          style: TextStyle(
            fontSize: 16,
            color: msg.isUser ? AppColors.white : AppColors.black,
          ),
        ),
      ),
    );
  }
}

class _InputBar extends StatefulWidget {
  final bool loading;
  final Future<void> Function(String text) onSend;
  const _InputBar({required this.loading, required this.onSend});

  @override
  State<_InputBar> createState() => _InputBarState();
}

class _InputBarState extends State<_InputBar> {
  final _ctrl = TextEditingController();

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _send() {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    _ctrl.clear();
    widget.onSend(text);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.black, width: 2)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _ctrl,
              style: const TextStyle(fontSize: 14, color: AppColors.black),
              decoration: const InputDecoration(
                hintText: '输入消息...',
                filled: true,
                fillColor: AppColors.greyLight,
                contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.all(Radius.circular(8)),
                  borderSide: BorderSide(color: AppColors.greyMedium, width: 1.5),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.all(Radius.circular(8)),
                  borderSide: BorderSide(color: AppColors.greyMedium, width: 1.5),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.all(Radius.circular(8)),
                  borderSide: BorderSide(color: AppColors.black, width: 1.5),
                ),
                hintStyle: TextStyle(color: AppColors.greyMedium, fontSize: 14),
              ),
              onSubmitted: (_) => _send(),
            ),
          ),
          const SizedBox(width: 12),
          GestureDetector(
            onTap: widget.loading ? null : _send,
            child: Container(
              width: 40,
              height: 40,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppColors.black,
                shape: BoxShape.circle,
                boxShadow: const [BoxShadow(color: Color(0x0A000000), offset: Offset(0, 1), blurRadius: 8)],
              ),
              child: widget.loading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.white),
                    )
                  : const Icon(Icons.send, color: AppColors.white, size: 18),
            ),
          ),
        ],
      ),
    );
  }
}

// ---- 行程数据(哨兵包裹的JSON)处理 ----
const _planStart = '⟦PLAN⟧';
const _planEnd = '⟦/PLAN⟧';
// 行程JSON解析失败时的兜底话术(后端已无保底文本)
const _planBrokenText = '行程已生成，但展示出了点问题，请重新询问';

/// 去掉行程数据段只留正文; 哨兵没闭合时从 ⟦PLAN⟧ 截到末尾, 避免半截JSON闪现
String _stripPlan(String raw) {
  final start = raw.indexOf(_planStart);
  if (start == -1) return raw;
  final end = raw.indexOf(_planEnd, start);
  final head = raw.substring(0, start);
  if (end == -1) return head;
  return head + _stripPlan(raw.substring(end + _planEnd.length));
}

/// 从文本里抠出行程JSON并解析; 没有/解析失败返回 null
Map<String, dynamic>? _extractPlan(String raw) {
  final start = raw.indexOf(_planStart);
  if (start == -1) return null;
  final end = raw.indexOf(_planEnd, start);
  if (end == -1) return null;
  try {
    final decoded = json.decode(raw.substring(start + _planStart.length, end));
    return decoded is Map<String, dynamic> ? decoded : null;
  } catch (_) {
    return null;
  }
}
