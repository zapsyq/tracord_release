class Trip {
  final int id;
  final String adcode;
  final DateTime createTime;

  const Trip({required this.id, required this.adcode, required this.createTime});

  factory Trip.fromJson(Map<String, dynamic> json) => Trip(
        id: json['id'] as int,
        adcode: json['adcode'] as String,
        createTime: DateTime.tryParse(json['create_time'] as String? ?? '') ??
            DateTime.fromMillisecondsSinceEpoch(0),
      );
}
