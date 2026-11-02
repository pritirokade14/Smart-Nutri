import 'package:flutter/foundation.dart';
import '../models/scan_history_item.dart';
import '../services/history_storage_service.dart';

class HistoryProvider extends ChangeNotifier {
  List<ScanHistoryItem> _items = [];
  bool _isLoading = false;

  List<ScanHistoryItem> get items => _items;
  bool get isLoading => _isLoading;

  int get totalScanned => _items.length;
  int get recommendedCount => _items.where((i) => i.isRecommended).length;
  int get avoidCount => totalScanned - recommendedCount;

  // ==================== DYNAMIC WEEKLY AGGREGATE GETTERS ====================
  double get totalSugar => _items.fold(0.0, (sum, item) => sum + item.sugar);
  double get totalProtein => _items.fold(0.0, (sum, item) => sum + item.protein);
  double get totalCalories => _items.fold(0.0, (sum, item) => sum + item.calories);

  // Progress bar percentages (normalized 0.0 to 1.0 based on standard weekly target thresholds)
  // You can adjust these baseline denominators to match your target goals.
  double get sugarProgress => (totalSugar / 350.0).clamp(0.0, 1.0);     // Example target: 350g weekly limit
  double get proteinProgress => (totalProtein / 450.0).clamp(0.0, 1.0); // Example target: 450g weekly goal
  double get caloriesProgress => (totalCalories / 14000.0).clamp(0.0, 1.0); // Example target: 14000 kcal weekly goal
  // ===========================================================================

  Future<void> fetchHistory() async {
    _isLoading = true;
    notifyListeners();

    _items = await HistoryStorageService.loadHistory();

    _isLoading = false;
    notifyListeners();
  }

  Future<void> addScan({
    required String productName,
    required String nutriScore,
    required bool isRecommended,
    required double sugar,
    required double protein,
    required double calories,
  }) async {
    final newItem = ScanHistoryItem(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      productName: productName,
      nutriScore: nutriScore,
      isRecommended: isRecommended,
      sugar: sugar,
      protein: protein,
      calories: calories,
      timestamp: DateTime.now(),
    );

    await HistoryStorageService.addItem(newItem);
    _items.insert(0, newItem);
    
    // Notify listeners so UI dashboard progress bars instantly react to the new scan data
    notifyListeners();
  }
}