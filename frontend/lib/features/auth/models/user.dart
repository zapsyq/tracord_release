class User {
  final int id;
  final String email;
  final String username;

  const User({
    required this.id,
    required this.email,
    required this.username,
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
        id: json['id'] as int,
        email: json['email'] as String,
        username: json['username'] as String,
      );
}
