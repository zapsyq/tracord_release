/// 金额千分位格式化：12345 -> "¥ 12,345"
String formatMoney(double v) {
  final s = v.round().toString();
  final buf = StringBuffer();
  for (var i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 == 0) buf.write(',');
    buf.write(s[i]);
  }
  return '¥ $buf';
}
