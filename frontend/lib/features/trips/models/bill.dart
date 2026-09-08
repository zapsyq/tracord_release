class Bill {
  final int id;
  final String amount;
  final int category;
  final String? customCategory;

  const Bill({
    required this.id,
    required this.amount,
    required this.category,
    this.customCategory,
  });

  factory Bill.fromJson(Map<String, dynamic> json) => Bill(
        id: json['id'] as int,
        amount: json['amount'].toString(),
        category: json['category'] as int,
        customCategory: json['custom_category'] as String?,
      );

  double get amountValue => double.tryParse(amount) ?? 0.0;
}
