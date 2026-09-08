import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../../core/theme/app_theme.dart';
import '../providers/auth_provider.dart';
import '../widgets/auth_text_field.dart';

class RegisterPage extends StatefulWidget {
  const RegisterPage({super.key});

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _emailController = TextEditingController();
  final _codeController = TextEditingController();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _emailController.dispose();
    _codeController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _sendCode() async {
    final email = _emailController.text.trim();
    if (!email.contains('@')) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('请先输入有效的邮箱地址'),
          backgroundColor: AppColors.black,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    final auth = context.read<AuthProvider>();
    await auth.sendVerifyCode(email);
    if (mounted && auth.errorMessage != null && auth.errorMessage!.isNotEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(auth.errorMessage!),
          backgroundColor: AppColors.black,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Widget _buttonChild(bool sending, int cooldown) {
    if (sending) {
      return const SizedBox(
        width: 16, height: 16,
        child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.white),
      );
    }
    if (cooldown > 0) {
      return Text('${cooldown}s', style: const TextStyle(fontSize: 12));
    }
    return const Text('发送验证码', style: TextStyle(fontSize: 12));
  }

  Future<void> _register() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final auth = context.read<AuthProvider>();
    final success = await auth.register(
      email: _emailController.text.trim(),
      username: _usernameController.text.trim(),
      password: _passwordController.text,
      confirmPassword: _confirmPasswordController.text,
      code: _codeController.text.trim(),
    );
    if (!mounted) return;
    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('注册成功'),
          backgroundColor: AppColors.black,
          behavior: SnackBarBehavior.floating,
        ),
      );
      Navigator.of(context).pop();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(auth.errorMessage ?? '注册失败'),
          backgroundColor: AppColors.black,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('迹录 · Tracord',
                      style: Theme.of(context).textTheme.headlineLarge),
                  const SizedBox(height: 8),
                  Text('创建您的账号',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 32),
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: AppColors.greyLight,
                      border: Border.all(color: AppColors.black, width: 2),
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: const [
                        BoxShadow(
                          color: AppColors.black,
                          offset: Offset(4, 4),
                          blurRadius: 0,
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        AuthTextField(
                          label: '邮箱',
                          hint: '请输入您的邮箱',
                          controller: _emailController,
                          validator: (v) {
                            if (v == null || v.trim().isEmpty) return '请输入邮箱';
                            if (!v.contains('@')) return '邮箱格式不正确';
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Expanded(
                              child: AuthTextField(
                                label: '验证码',
                                hint: '4位验证码',
                                controller: _codeController,
                                validator: (v) {
                                  if (v == null || v.trim().isEmpty) return '请输入验证码';
                                  if (v.trim().length != 4) return '验证码为4位';
                                  return null;
                                },
                              ),
                            ),
                            const SizedBox(width: 12),
                            Padding(
                              padding: const EdgeInsets.only(bottom: 2),
                              child: Consumer<AuthProvider>(
                                builder: (context, auth, _) {
                                  final sending = auth.isSendingCode;
                                  final cooldown = auth.cooldownSeconds;
                                  final disabled = sending || cooldown > 0;
                                  return SizedBox(
                                    height: 48,
                                    child: OutlinedButton(
                                      onPressed: disabled ? null : _sendCode,
                                      style: OutlinedButton.styleFrom(
                                        backgroundColor: AppColors.black,
                                        foregroundColor: AppColors.white,
                                        disabledBackgroundColor: AppColors.greyMedium,
                                        disabledForegroundColor: AppColors.white,
                                        side: const BorderSide(color: AppColors.black, width: 1.5),
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(8),
                                        ),
                                        padding: const EdgeInsets.symmetric(horizontal: 12),
                                      ),
                                      child: _buttonChild(sending, cooldown),
                                    ),
                                  );
                                },
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        AuthTextField(
                          label: '用户名',
                          hint: '3-20位用户名',
                          controller: _usernameController,
                          validator: (v) {
                            if (v == null || v.trim().isEmpty) return '请输入用户名';
                            if (v.trim().length < 3 || v.trim().length > 20) {
                              return '用户名需要3-20位';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        AuthTextField(
                          label: '密码',
                          hint: '6-20位密码',
                          isPassword: true,
                          controller: _passwordController,
                          validator: (v) {
                            if (v == null || v.isEmpty) return '请输入密码';
                            if (v.length < 6 || v.length > 20) return '密码需要6-20位';
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        AuthTextField(
                          label: '确认密码',
                          hint: '再次输入密码',
                          isPassword: true,
                          controller: _confirmPasswordController,
                          validator: (v) {
                            if (v == null || v.isEmpty) return '请确认密码';
                            if (v != _passwordController.text) return '两次密码不一致';
                            return null;
                          },
                        ),
                        const SizedBox(height: 24),
                        Consumer<AuthProvider>(
                          builder: (context, auth, _) => SizedBox(
                            height: 48,
                            child: ElevatedButton(
                              onPressed: auth.isLoading ? null : _register,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.black,
                                foregroundColor: AppColors.white,
                                disabledBackgroundColor: AppColors.greyMedium,
                                disabledForegroundColor: AppColors.white,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(8),
                                  side: const BorderSide(color: AppColors.black, width: 2),
                                ),
                                elevation: 0,
                              ),
                              child: auth.isLoading
                                  ? const SizedBox(
                                      width: 20,
                                      height: 20,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: AppColors.white,
                                      ),
                                    )
                                  : const Text('注册',
                                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  GestureDetector(
                    onTap: () => Navigator.of(context).pop(),
                    child: Text(
                      '已有账号？去登录',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
