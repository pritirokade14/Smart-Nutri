import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/scan_history_item.dart';

class HistoryStorageService {
  static const String _storageKey = 'nutrition_scan_history_v1';

  static Future<List<ScanHistoryItem>> loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final String? jsonString = prefs.getString(_storageKey);
    if (jsonString == null) return [];

    try {
      final List<dynamic> decoded = jsonDecode(jsonString);
      return decoded.map((item) => ScanHistoryItem.fromJson(item)).toList();
    } catch (e) {
      print('Error loading history: $e');
      return [];
    }
  }

  static Future<void> saveHistory(List<ScanHistoryItem> items) async {
    final prefs = await SharedPreferences.getInstance();
    final String encoded = jsonEncode(items.map((i) => i.toJson()).toList());
    await prefs.setString(_storageKey, encoded);
  }

  static Future<void> addItem(ScanHistoryItem newItem) async {
    final items = await loadHistory();
    items.insert(0, newItem); // Add to the beginning (most recent)
    await saveHistory(items);
  }
}