import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:latlong2/latlong.dart';

class CityData {
  final String name;
  final String code;
  final List<List<LatLng>> rings;
  const CityData({required this.name, required this.code, required this.rings});
}

/// 后台 isolate 解析 JSON
List<CityData> _parseAll(String json) {
  final data = jsonDecode(json) as Map<String, dynamic>;
  return (data['features'] as List<dynamic>).map<CityData>((f) {
    final props = f['properties'] as Map<String, dynamic>;
    final geom = f['geometry'] as Map<String, dynamic>;
    final coords = geom['coordinates'] as List<dynamic>;
    final rings = <List<LatLng>>[];
    void addRing(List<dynamic> ring) {
      rings.add(ring.map<LatLng>((p) {
        final c = p as List<dynamic>;
        return LatLng(c[1].toDouble(), c[0].toDouble());
      }).toList());
    }
    if (geom['type'] == 'MultiPolygon') {
      for (final p in coords) {
        addRing((p as List<dynamic>)[0] as List<dynamic>);
      }
    } else {
      addRing(coords[0] as List<dynamic>);
    }
    return CityData(name: props['name'] as String, code: (props['gb'] as String?) ?? '', rings: rings);
  }).toList();
}

class CityLoader {
  static Future<List<CityData>> load(String assetPath) async {
    final json = await rootBundle.loadString(assetPath);
    return compute(_parseAll, json);
  }
}
