/// 从 gb 编码取后 6 位作为 adcode
String toAdcode(String code) =>
    code.length >= 6 ? code.substring(code.length - 6) : code;

/// 城市名去掉「市」后缀
String stripCitySuffix(String name) => name.replaceAll('市', '');
