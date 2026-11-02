class ScanHistoryItem {
  final String id;
  final String productName;
  final String nutriScore;
  final bool isRecommended;
  final double sugar;
  final double protein;
  final double calories;
  final DateTime timestamp;

  ScanHistoryItem({
    required this.id,
    required this.productName,
    required this.nutriScore,
    required this.isRecommended,
    required this.sugar,
    required this.protein,
    required this.calories,
    required this.timestamp,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'productName': productName,
        'nutriScore': nutriScore,
        'isRecommended': isRecommended,
        'sugar': sugar,
        'protein': protein,
        'calories': calories,
        'timestamp': timestamp.toIso8601String(),
      };

  factory ScanHistoryItem.fromJson(Map<String, dynamic> json) => ScanHistoryItem(
        id: json['id'] ?? DateTime.now().toIso8601String(),
        productName: json['productName'] ?? 'Unknown Product',
        nutriScore: json['nutriScore'] ?? 'C',
        isRecommended: json['isRecommended'] ?? false,
        sugar: (json['sugar'] ?? 0.0).toDouble(),
        protein: (json['protein'] ?? 0.0).toDouble(),
        calories: (json['calories'] ?? 0.0).toDouble(),
        timestamp: DateTime.parse(json['timestamp'] ?? DateTime.now().toIso8601String()),
      );
}