import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';
import 'package:smartnutri_ai/screens/profile/nutrition_profile_screen.dart';
import 'package:smartnutri_ai/services/multilingual_service.dart';
import 'package:smartnutri_ai/providers/history_provider.dart';
import 'package:smartnutri_ai/screens/history_dashboard_screen.dart';

// ==================== GLOBAL GOAL CONTROLLER SERVICE ====================
class UserGoalService extends ChangeNotifier {
  static final UserGoalService _instance = UserGoalService._internal();
  factory UserGoalService() => _instance;
  UserGoalService._internal();

  String _currentGoal = 'Healthy Eating'; // Default initial goal
  String get currentGoal => _currentGoal;

  void updateGoal(String newGoal) {
    _currentGoal = newGoal;
    notifyListeners(); // Notify all listening widgets to rebuild instantly
  }
}

// ==================== MAIN DASHBOARD SCREEN ====================
class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const HomeDashboardContent(),
    const ProductSearchScreen(), 
    const ProductComparisonScreen(), 
    const HistoryDashboardScreenWrapper(), 
    const NutritionProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: _screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        selectedItemColor: const Color(0xFF1E88E5),
        unselectedItemColor: Colors.grey,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_rounded), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.analytics_rounded), label: 'Analyze'),
          BottomNavigationBarItem(icon: Icon(Icons.compare_arrows_rounded), label: 'Compare'),
          BottomNavigationBarItem(icon: Icon(Icons.history_rounded), label: 'History'),
          BottomNavigationBarItem(icon: Icon(Icons.person_rounded), label: 'Profile'),
        ],
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
      ),
    );
  }
}

// ==================== HISTORY DASHBOARD WRAPPER ====================
class HistoryDashboardScreenWrapper extends StatefulWidget {
  const HistoryDashboardScreenWrapper({super.key});

  @override
  State<HistoryDashboardScreenWrapper> createState() => _HistoryDashboardScreenWrapperState();
}

class _HistoryDashboardScreenWrapperState extends State<HistoryDashboardScreenWrapper> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<HistoryProvider>(context, listen: false).fetchHistory();
    });
  }

  @override
  Widget build(BuildContext context) {
    return const HistoryDashboardScreen();
  }
}

// ==================== PRODUCT SEARCH & OPEN FOOD FACTS ====================
class ProductSearchScreen extends StatefulWidget {
  const ProductSearchScreen({super.key});

  @override
  State<ProductSearchScreen> createState() => _ProductSearchScreenState();
}

class _ProductSearchScreenState extends State<ProductSearchScreen> {
  final TextEditingController _searchController = TextEditingController();
  List<dynamic> _searchResults = [];
  bool _isLoading = false;
  bool _hasSearched = false;

  Future<void> _searchOpenFoodFacts(String query) async {
    if (query.trim().isEmpty) return;

    setState(() {
      _isLoading = true;
      _hasSearched = true;
    });

    try {
      final url = Uri.parse(
        'https://world.openfoodfacts.org/cgi/search.pl?search_terms=${Uri.encodeComponent(query)}&search_simple=1&action=process&json=1',
      );

      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _searchResults = data['products'] ?? [];
          _isLoading = false;
        });
      } else {
        setState(() {
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Search failed: $e'), backgroundColor: Colors.red),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F7FC),
      appBar: AppBar(
        title: const Text('SmartNutri AI - Product Search', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Color(0xFF1565C0))),
        backgroundColor: Colors.white,
        elevation: 0.5,
        centerTitle: false,
      ),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Open Food Facts Database',
              style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A)),
            ),
            const SizedBox(height: 4),
            Text(
              'Search products globally via Open Food Facts to fetch instant nutrition information.',
              style: TextStyle(fontSize: 14, color: Colors.grey[600]),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: 'Enter product name (e.g., Nutella, Oat Milk)...',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE2E8F0))),
                      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE2E8F0))),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    ),
                    onSubmitted: (value) => _searchOpenFoodFacts(value),
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton.icon(
                  onPressed: () => _searchOpenFoodFacts(_searchController.text),
                  icon: const Icon(Icons.search, color: Colors.white),
                  label: const Text('Search', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1E88E5),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator(color: Color(0xFF1E88E5)))
                  : _searchResults.isEmpty
                      ? Center(
                          child: Text(
                            _hasSearched ? 'No products found.' : 'Search for a food item above to view nutrition details.',
                            style: TextStyle(fontSize: 14, color: Colors.grey[500]),
                          ),
                        )
                      : ListView.builder(
                          itemCount: _searchResults.length,
                          itemBuilder: (context, index) {
                            var product = _searchResults[index];
                            String name = product['product_name'] ?? 'Unknown Product';
                            String brand = product['brands'] ?? 'Unknown Brand';
                            String nutriScore = (product['nutriscore_grade'] ?? 'N/A').toUpperCase();
                            var nutriments = product['nutriments'] ?? {};
                            var calories = nutriments['energy-kcal_100g'] ?? nutriments['energy-kcal'] ?? 0;
                            var proteins = nutriments['proteins_100g'] ?? 0;

                            return Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: const Color(0xFFE2E8F0)),
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    width: 50,
                                    height: 50,
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFF1F5F9),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: product['image_front_small_url'] != null
                                        ? Image.network(product['image_front_small_url'], fit: BoxFit.cover)
                                        : const Icon(Icons.fastfood, color: Colors.grey),
                                  ),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A))),
                                        const SizedBox(height: 2),
                                        Text('Brand: $brand', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                                        const SizedBox(height: 6),
                                        Row(
                                          children: [
                                            Text('Calories: ${calories.toStringAsFixed(0)} kcal', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                            const SizedBox(width: 12),
                                            Text('Protein: ${proteins.toStringAsFixed(1)} g', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: nutriScore == 'A' || nutriScore == 'B' ? Colors.green.shade50 : Colors.orange.shade50,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      'Grade $nutriScore',
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        color: nutriScore == 'A' || nutriScore == 'B' ? Colors.green.shade800 : Colors.orange.shade800,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }
}

// ==================== PRODUCT COMPARISON SCREEN ====================
class ProductComparisonScreen extends StatefulWidget {
  const ProductComparisonScreen({super.key});

  @override
  State<ProductComparisonScreen> createState() => _ProductComparisonScreenState();
}

class _ProductComparisonScreenState extends State<ProductComparisonScreen> {
  Map<String, dynamic>? _productA;
  Map<String, dynamic>? _productB;
  bool _isLoadingSelection = false;
  List<dynamic> _pickerResults = [];
  
  void _showProductSearchDialog(String slot) {
    TextEditingController controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Select Product $slot'),
          content: SizedBox(
            width: 400,
            height: 400,
            child: StatefulBuilder(
              builder: (BuildContext context, StateSetter setStateDialog) {
                return Column(
                  children: [
                    TextField(
                      controller: controller,
                      decoration: const InputDecoration(
                        hintText: 'Search product...',
                        suffixIcon: Icon(Icons.search),
                      ),
                      onSubmitted: (val) async {
                        setStateDialog(() => _isLoadingSelection = true);
                        try {
                          final url = Uri.parse(
                            'https://world.openfoodfacts.org/cgi/search.pl?search_terms=${Uri.encodeComponent(val)}&search_simple=1&action=process&json=1&page_size=10',
                          );
                          final res = await http.get(url);
                          if (res.statusCode == 200) {
                            var data = jsonDecode(res.body);
                            setStateDialog(() {
                              _pickerResults = data['products'] ?? [];
                              _isLoadingSelection = false;
                            });
                          }
                        } catch (e) {
                          setStateDialog(() => _isLoadingSelection = false);
                        }
                      },
                    ),
                    const SizedBox(height: 12),
                    Expanded(
                      child: _isLoadingSelection
                          ? const Center(child: CircularProgressIndicator())
                          : ListView.builder(
                              itemCount: _pickerResults.length,
                              itemBuilder: (context, index) {
                                var p = _pickerResults[index];
                                String name = p['product_name'] ?? 'Unknown';
                                String brand = p['brands'] ?? 'Unknown Brand';
                                return ListTile(
                                  title: Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                  subtitle: Text(brand, style: const TextStyle(fontSize: 11)),
                                  onTap: () {
                                    setState(() {
                                      if (slot == 'A') _productA = p;
                                      else _productB = p;
                                    });
                                    Navigator.pop(context);
                                  },
                                );
                              },
                            ),
                    ),
                  ],
                );
              },
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F7FC),
      appBar: AppBar(
        title: const Text('SmartNutri AI - Product Comparison', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Color(0xFF1565C0))),
        backgroundColor: Colors.white,
        elevation: 0.5,
        centerTitle: false,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Side-by-Side Comparison',
              style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A)),
            ),
            const SizedBox(height: 4),
            Text(
              'Select Product A and Product B to compare nutrition metrics and AI evaluations.',
              style: TextStyle(fontSize: 14, color: Colors.grey[600]),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(child: _buildProductSelectorCard('Product A', _productA, 'A')),
                const SizedBox(width: 20),
                Expanded(child: _buildProductSelectorCard('Product B', _productB, 'B')),
              ],
            ),
            const SizedBox(height: 32),
            if (_productA != null && _productB != null) ...[
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFFE2E8F0)),
                  boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 10, offset: const Offset(0, 4))],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Nutritional Comparison Matrix',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A)),
                    ),
                    const SizedBox(height: 16),
                    _buildComparisonTableHeader(),
                    const Divider(height: 24),
                    _buildComparisonRow('Calories', _getNutrientValue(_productA, 'energy-kcal_100g'), _getNutrientValue(_productB, 'energy-kcal_100g'), 'kcal'),
                    _buildComparisonRow('Sugar', _getNutrientValue(_productA, 'sugars_100g'), _getNutrientValue(_productB, 'sugars_100g'), 'g'),
                    _buildComparisonRow('Protein', _getNutrientValue(_productA, 'proteins_100g'), _getNutrientValue(_productB, 'proteins_100g'), 'g'),
                    _buildComparisonRow('Fat', _getNutrientValue(_productA, 'fat_100g'), _getNutrientValue(_productB, 'fat_100g'), 'g'),
                    _buildComparisonRow('Salt', _getNutrientValue(_productA, 'salt_100g'), _getNutrientValue(_productB, 'salt_100g'), 'g'),
                    _buildNutriScoreRow(_productA, _productB),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFFEFF6FF),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFFBFDBFE)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.auto_awesome, color: Color(0xFF1E88E5), size: 20),
                        SizedBox(width: 8),
                        Text('AI Comparison Summary', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E3A8A))),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      _generateAIComparisonText(_productA!, _productB!),
                      style: const TextStyle(fontSize: 14, color: Color(0xFF1E293B), height: 1.5),
                    ),
                  ],
                ),
              ),
            ] else ...[
              Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 40.0),
                  child: Text(
                    'Please select both Product A and Product B above to view side-by-side analysis.',
                    style: TextStyle(fontSize: 14, color: Colors.grey.shade500),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildProductSelectorCard(String label, Map<String, dynamic>? product, String slot) {
    String name = product != null ? (product['product_name'] ?? 'Selected Product') : 'Click to select $label';
    String brand = product != null ? (product['brands'] ?? 'Unknown Brand') : 'Open Food Facts Database';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF1E88E5))),
          const SizedBox(height: 8),
          Text(name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A))),
          const SizedBox(height: 2),
          Text(brand, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: () => _showProductSearchDialog(slot),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF1E88E5),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: Text(product == null ? 'Select $label' : 'Change Product', style: const TextStyle(color: Colors.white, fontSize: 12)),
          ),
        ],
      ),
    );
  }

  Widget _buildComparisonTableHeader() {
    String nameA = _productA?['product_name'] ?? 'Product A';
    String nameB = _productB?['product_name'] ?? 'Product B';
    return Row(
      children: [
        const Expanded(flex: 3, child: Text('Metric', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey))),
        Expanded(flex: 3, child: Text(nameA, style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1E88E5)))),
        Expanded(flex: 3, child: Text(nameB, style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A)))),
      ],
    );
  }

  Widget _buildComparisonRow(String label, double valA, double valB, String unit) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        children: [
          Expanded(flex: 3, child: Text(label, style: const TextStyle(fontSize: 14, color: Colors.black87))),
          Expanded(flex: 3, child: Text('${valA.toStringAsFixed(1)} $unit', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold))),
          Expanded(flex: 3, child: Text('${valB.toStringAsFixed(1)} $unit', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold))),
        ],
      ),
    );
  }

  Widget _buildNutriScoreRow(Map<String, dynamic>? pA, Map<String, dynamic>? pB) {
    String gradeA = (pA?['nutriscore_grade'] ?? 'N/A').toUpperCase();
    String gradeB = (pB?['nutriscore_grade'] ?? 'N/A').toUpperCase();

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        children: [
          const Expanded(flex: 3, child: Text('Nutri-Score', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.black87))),
          Expanded(flex: 3, child: Text('Grade $gradeA', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: gradeA == 'A' || gradeA == 'B' ? Colors.green : Colors.orange))),
          Expanded(flex: 3, child: Text('Grade $gradeB', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: gradeB == 'A' || gradeB == 'B' ? Colors.green : Colors.orange))),
        ],
      ),
    );
  }

  double _getNutrientValue(Map<String, dynamic>? product, String key) {
    if (product == null) return 0.0;
    var nutriments = product['nutriments'] ?? {};
    var val = nutriments[key] ?? nutriments[key.replaceAll('_100g', '')] ?? 0;
    if (val is num) return val.toDouble();
    return double.tryParse(val.toString()) ?? 0.0;
  }

  String _generateAIComparisonText(Map<String, dynamic> a, Map<String, dynamic> b) {
    String nameA = a['product_name'] ?? 'Product A';
    String nameB = b['product_name'] ?? 'Product B';
    double calA = _getNutrientValue(a, 'energy-kcal_100g');
    double calB = _getNutrientValue(b, 'energy-kcal_100g');
    double sugarA = _getNutrientValue(a, 'sugars_100g');
    double sugarB = _getNutrientValue(b, 'sugars_100g');

    if (sugarA < sugarB) {
      return '$nameA is generally the healthier option compared to $nameB. It contains lower sugar content (${sugarA.toStringAsFixed(1)}g vs ${sugarB.toStringAsFixed(1)}g per 100g) and provides a more balanced profile for your nutritional objectives.';
    } else {
      return '$nameB stands out as the superior choice against $nameA. It maintains a better balance with lower calorie and sugar densities (${calB.toStringAsFixed(0)} kcal vs ${calA.toStringAsFixed(0)} kcal), supporting healthier everyday dietary tracking.';
    }
  }
}

// ==================== HOME DASHBOARD CONTENT ====================
class HomeDashboardContent extends StatefulWidget {
  const HomeDashboardContent({super.key});

  @override
  State<HomeDashboardContent> createState() => _HomeDashboardContentState();
}

class _HomeDashboardContentState extends State<HomeDashboardContent> {
  final MultilingualService _multilingualService = MultilingualService();
  String _selectedLanguageCode = 'en'; 

  Map<String, dynamic>? _latestScanResult;
  List<dynamic> _healthierAlternatives = [];
  bool _isLoadingAlternatives = false;

  // Remember the last image so we can re-analyze it when the goal/language changes
  File? _lastScannedFile;
  bool _isRefreshing = false;
  int _requestId = 0; // used to ignore out-of-date responses

  // Phase 16: Voice Assistant Controllers
  late stt.SpeechToText _speech;
  late FlutterTts _flutterTts;
  bool _isListening = false;
  String _lastRecognizedWords = '';
  String? _spokenAiResponse;
  bool _isVoiceProcessing = false;

  @override
  void initState() {
    super.initState();
    UserGoalService().addListener(_onGoalChanged);
    _initVoiceAssistant();
  }

  void _initVoiceAssistant() async {
    _speech = stt.SpeechToText();
    _flutterTts = FlutterTts();
    await _flutterTts.setLanguage("en-US");
    await _flutterTts.setSpeechRate(0.5);
  }

  @override
  void dispose() {
    UserGoalService().removeListener(_onGoalChanged);
    _speech.stop();
    _flutterTts.stop();
    super.dispose();
  }

  void _onGoalChanged() {
    if (!mounted) return;
    setState(() {});
    final file = _lastScannedFile;
    if (file != null && _latestScanResult?['goal'] != UserGoalService().currentGoal) {
      _analyzeImage(file, isRefresh: true);
    }
  }

  // Phase 16: Speech-to-Text Listener & Backend Voice Query Call
  void _listen() async {
    if (_latestScanResult == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please scan a product first before asking AI!'), backgroundColor: Colors.orange),
      );
      return;
    }

    if (!_isListening) {
      bool available = await _speech.initialize(
        onStatus: (val) => debugPrint('onStatus: $val'),
        onError: (val) => debugPrint('onError: $val'),
      );
      if (available) {
        setState(() {
          _isListening = true;
          _spokenAiResponse = null;
        });
        _speech.listen(
          onResult: (val) => setState(() {
            _lastRecognizedWords = val.recognizedWords;
            if (val.finalResult) {
              _isListening = false;
              _sendVoiceQuestionToBackend(_lastRecognizedWords);
            }
          }),
        );
      }
    } else {
      setState(() => _isListening = false);
      _speech.stop();
    }
  }

  Future<void> _sendVoiceQuestionToBackend(String question) async {
    if (question.trim().isEmpty) return;
    setState(() => _isVoiceProcessing = true);

    try {
      var data = _latestScanResult!;
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('http://127.0.0.1:8000/api/voice-query'),
      );
      request.fields['question'] = question;
      request.fields['product_name'] = data['title'] ?? 'Product';
      request.fields['calories'] = data['calories'].toString();
      request.fields['protein'] = data['protein'].toString();
      request.fields['sugar'] = data['sugar'].toString();
      request.fields['fat'] = data['fat'].toString();
      request.fields['salt'] = data['salt'].toString();
      request.fields['grade'] = data['grade'].toString();
      request.fields['goal'] = UserGoalService().currentGoal;
      request.fields['language'] = _selectedLanguageCode;

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        var resData = jsonDecode(response.body);
        String answer = resData['answer'] ?? 'Analysis complete.';
        
        setState(() {
          _spokenAiResponse = answer;
          _isVoiceProcessing = false;
        });

        await _flutterTts.speak(answer);
      } else {
        throw Exception('Server error: ${response.statusCode}');
      }
    } catch (e) {
      setState(() {
        _isVoiceProcessing = false;
        _spokenAiResponse = 'Sorry, connection error encountered.';
      });
      await _flutterTts.speak(_spokenAiResponse!);
    }
  }

  Future<void> _fetchHealthierAlternatives(String productName) async {
    setState(() {
      _isLoadingAlternatives = true;
      _healthierAlternatives = [];
    });

    String query = productName.toLowerCase();
    if (query.contains('nutella') || query.contains('spread') || query.contains('chocolat')) {
      query = 'chocolate spread';
    } else if (query.contains('yogurt') || query.contains('yoghurt')) {
      query = 'yogurt';
    } else if (query.contains('milk')) {
      query = 'milk';
    } else if (query.contains('cereal') || query.contains('granola')) {
      query = 'cereal';
    } else {
      List<String> words = productName.split(' ');
      query = words.isNotEmpty ? words.first : 'snack';
    }

    try {
      final url = Uri.parse(
        'https://world.openfoodfacts.org/cgi/search.pl?search_terms=${Uri.encodeComponent(query)}&action=process&json=1&page_size=20',
      );
      final response = await http.get(url);

      List products = [];
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        products = data['products'] ?? [];
      }

      List filteredProducts = products.where((p) {
        String grade = (p['nutriscore_grade'] ?? '').toString().toLowerCase();
        return grade == 'a' || grade == 'b';
      }).take(3).toList();

      if (filteredProducts.isEmpty && products.isNotEmpty) {
        filteredProducts = products.take(3).toList();
      }

      setState(() {
        _healthierAlternatives = filteredProducts;
        _isLoadingAlternatives = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingAlternatives = false;
      });
    }
  }

  Future<void> _uploadAndScanImage(BuildContext context) async {
    final result = await FilePicker.platform.pickFiles(type: FileType.image);
    if (result != null && result.files.single.path != null) {
      await _analyzeImage(File(result.files.single.path!));
    }
  }

  Future<void> _analyzeImage(File file, {bool isRefresh = false}) async {
    final goal = UserGoalService().currentGoal;
    final lang = _selectedLanguageCode;
    final requestId = ++_requestId;
    _lastScannedFile = file;

    bool dialogOpen = false;
    if (isRefresh) {
      setState(() => _isRefreshing = true);
    } else {
      dialogOpen = true;
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (_) => const Center(
          child: CircularProgressIndicator(color: Color(0xFF1E88E5)),
        ),
      );
    }

    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('http://127.0.0.1:8000/api/scan'),
      );
      request.files.add(await http.MultipartFile.fromPath('file', file.path));
      request.fields['language'] = lang;

      final streamed = await request.send();
      final response = await http.Response.fromStream(streamed);

      if (response.statusCode != 200) {
        throw Exception('Server error: ${response.statusCode} ${response.body}');
      }

      final data = jsonDecode(response.body);
      final analysis = data['analysis'] ?? {};

      final String foodName = analysis['food_name'] ?? 'Scanned Product';
      final String grade = analysis['grade'] ?? 'C';
      final int calories = (analysis['calories'] as num?)?.toInt() ?? 0;
      final int protein = (analysis['protein'] as num?)?.toInt() ?? 0;
      final int fat = (analysis['fat'] as num?)?.toInt() ?? 0;
      final int carbs = (analysis['carbs'] as num?)?.toInt() ?? 0;
      final double sugar = (analysis['sugar'] as num?)?.toDouble() ?? 0.0;
      final double salt = (analysis['salt'] as num?)?.toDouble() ?? 0.0;

      final Map<String, dynamic> evaluations = analysis['evaluations'] ?? {};
      final List ingredients = analysis['ingredients'] ?? [];
      final Map<String, dynamic> recommendation = data['recommendation'] ??
          {'is_recommended': true, 'status': 'Recommended', 'reasons': []};
      final bool isRecommended = recommendation['is_recommended'] ?? true;

      if (!isRefresh && mounted) {
        Provider.of<HistoryProvider>(context, listen: false).addScan(
          productName: foodName,
          nutriScore: grade,
          isRecommended: isRecommended,
          sugar: sugar,
          protein: protein.toDouble(),
          calories: calories.toDouble(),
        );
      }

      String explanation = (data['genai_explanation'] ?? '').toString().trim();
      if (explanation.isEmpty) {
        explanation = 'This product was analyzed against your goal: $goal.';
      }
      List<String> tips = ((data['tips'] as List?) ?? [])
          .map((e) => e.toString())
          .where((e) => e.trim().isNotEmpty)
          .toList();
      final String source = (data['explanation_source'] ?? 'llm').toString();
      final String? llmError = data['explanation_error']?.toString();
      final String usedGoal = (data['goal'] ?? goal).toString();

      if (source != 'llm' && lang != 'en') {
        explanation = await _multilingualService.localizeRecommendation(explanation, lang);
        tips = await Future.wait(
          tips.map((t) => _multilingualService.localizeRecommendation(t, lang)),
        );
      }

      if (!mounted || requestId != _requestId) return;

      Color gradeColor = Colors.orange;
      if (grade == 'A') {
        gradeColor = Colors.green;
      } else if (grade == 'B') {
        gradeColor = Colors.lightGreen;
      } else if (grade == 'C') {
        gradeColor = Colors.orange;
      } else if (grade == 'D' || grade == 'E') {
        gradeColor = Colors.red;
      }

      setState(() {
        _latestScanResult = {
          'title': foodName,
          'grade': grade,
          'gradeColor': gradeColor,
          'calories': calories,
          'protein': protein,
          'fat': fat,
          'carbs': carbs,
          'sugar': sugar,
          'salt': salt,
          'evaluations': evaluations,
          'ingredients': ingredients,
          'recommendation': recommendation,
          'genai_explanation': explanation,
          'explanation_source': source,
          'tips': tips,
          'goal': usedGoal,
          'explanation_error': llmError,
          'alerts': data['alerts'] ?? [],
          'warnings': data['warnings'] ?? [],
        };
      });

      if (UserGoalService().currentGoal != usedGoal) {
        UserGoalService().updateGoal(usedGoal);
      }

      if (!isRefresh) _fetchHealthierAlternatives(foodName);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(isRefresh
                ? 'Updated analysis for your goal: $usedGoal'
                : 'Analyzed "$foodName" for your goal: $usedGoal'),
            backgroundColor: const Color(0xFF1E88E5),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to analyze: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (dialogOpen && mounted) {
        Navigator.of(context, rootNavigator: true).pop();
      }
      if (mounted && requestId == _requestId && _isRefreshing) {
        setState(() => _isRefreshing = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F7FC),
      appBar: AppBar(
        title: const Text('SmartNutri AI', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Color(0xFF1565C0))),
        backgroundColor: Colors.white,
        elevation: 0.5,
        centerTitle: false,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'SmartNutri AI',
                  style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFE2E8F0)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.language, size: 16, color: Color(0xFF1E88E5)),
                      const SizedBox(width: 8),
                      DropdownButton<String>(
                        value: _selectedLanguageCode,
                        underline: const SizedBox(),
                        items: MultilingualService.supportedLanguages.entries.map((entry) {
                          return DropdownMenuItem(
                            value: entry.key,
                            child: Text(entry.value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                          );
                        }).toList(),
                        onChanged: (String? newLang) {
                          if (newLang != null) {
                            setState(() {
                              _selectedLanguageCode = newLang;
                            });
                            if (_lastScannedFile != null) {
                              _analyzeImage(_lastScannedFile!, isRefresh: true);
                            }
                          }
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'Upload a nutrition label or scan a product to get instant insights and personalized recommendations.',
              style: TextStyle(fontSize: 14, color: Colors.grey[600]),
            ),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFE2E8F0)),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 10, offset: const Offset(0, 4)),
                ],
              ),
              child: Row(
                children: [
                  Expanded(
                    flex: 6,
                    child: Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF8FAFC),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFFE2E8F0)),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: const Color(0xFFE3F2FD),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Icon(Icons.cloud_upload_rounded, color: Color(0xFF1E88E5), size: 32),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Upload Nutrition Label',
                                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E3A8A)),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  'Supports PNG, JPG files from your device',
                                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                                ),
                                const SizedBox(height: 12),
                                ElevatedButton.icon(
                                  onPressed: () => _uploadAndScanImage(context),
                                  icon: const Icon(Icons.upload_file, size: 16, color: Colors.white),
                                  label: const Text('Choose File', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: const Color(0xFF1E88E5),
                                    elevation: 0,
                                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 24),
                  Expanded(
                    flex: 4,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildFeatureRow(Icons.bolt, 'Instant Analysis', 'Get nutrition insights in seconds'),
                        const SizedBox(height: 12),
                        _buildFeatureRow(Icons.verified_user, 'Personalized Recommendations', 'Based on your health goals'),
                        const SizedBox(height: 12),
                        _buildFeatureRow(Icons.trending_up, 'Track Your Progress', 'Build healthier habits over time'),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            if (_latestScanResult != null) ...[
              Row(
                children: [
                  const Icon(Icons.auto_awesome, color: Color(0xFF1E88E5), size: 20),
                  const SizedBox(width: 8),
                  const Text(
                    'Scan Result & AI Assistant',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A)),
                  ),
                  if (_isRefreshing) ...[
                    const SizedBox(width: 12),
                    const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
                    const SizedBox(width: 8),
                    Text('Updating for your new goal...', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                  ],
                ],
              ),
              const SizedBox(height: 16),
              LayoutBuilder(
                builder: (context, constraints) {
                  bool isWide = constraints.maxWidth > 900;
                  if (isWide) {
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: _buildLeftProductColumn(_latestScanResult!)),
                        const SizedBox(width: 24),
                        Expanded(
                          child: Column(
                            children: [
                              _buildRightInsightColumn(_latestScanResult!),
                              _buildVoiceAssistantCard(), // Phase 16 Voice Assistant Widget
                            ],
                          ),
                        ),
                      ],
                    );
                  } else {
                    return Column(
                      children: [
                        _buildLeftProductColumn(_latestScanResult!),
                        const SizedBox(height: 20),
                        _buildRightInsightColumn(_latestScanResult!),
                        _buildVoiceAssistantCard(), // Phase 16 Voice Assistant Widget
                      ],
                    );
                  }
                },
              ),
              const SizedBox(height: 32),
              Row(
                children: const [
                  Text('🥗', style: TextStyle(fontSize: 20)),
                  SizedBox(width: 8),
                  Text(
                    'Healthier Alternatives',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A)),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              _isLoadingAlternatives
                  ? const Center(child: CircularProgressIndicator(color: Color(0xFF1E88E5)))
                  : _healthierAlternatives.isEmpty
                      ? Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: const Color(0xFFE2E8F0)),
                          ),
                          child: const Text('No closer alternatives found in database.', style: TextStyle(color: Colors.grey)),
                        )
                      : Column(
                          children: _healthierAlternatives.map((alt) {
                            String altName = alt['product_name'] ?? 'Alternative Product';
                            String altBrand = alt['brands'] ?? 'Unknown Brand';
                            String altGrade = (alt['nutriscore_grade'] ?? 'B').toUpperCase();
                            var altNutriments = alt['nutriments'] ?? {};
                            var altCalories = altNutriments['energy-kcal_100g'] ?? altNutriments['energy-kcal'] ?? 0;

                            return Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: const Color(0xFFE2E8F0)),
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    width: 50,
                                    height: 50,
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFF1F5F9),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: alt['image_front_small_url'] != null
                                        ? Image.network(alt['image_front_small_url'], fit: BoxFit.cover)
                                        : const Icon(Icons.eco, color: Colors.green),
                                  ),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(altName, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A))),
                                        const SizedBox(height: 2),
                                        Text('Brand: $altBrand', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                                        const SizedBox(height: 4),
                                        Text('Calories: ${altCalories.toStringAsFixed(0)} kcal / 100g', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.black87)),
                                      ],
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                    decoration: BoxDecoration(
                                      color: Colors.green.shade50,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      'Grade $altGrade',
                                      style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green.shade800),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                        ),
            ] else ...[
              Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 60.0),
                  child: Column(
                    children: [
                      Icon(Icons.qr_code_scanner_rounded, size: 56, color: Colors.grey.shade300),
                      const SizedBox(height: 16),
                      Text(
                        'No product scanned yet.\nUpload a label above to view your detailed personalized insights.',
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 14, color: Colors.grey.shade500),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  // Phase 16: Voice Assistant UI Card Widget
  Widget _buildVoiceAssistantCard() {
    return Container(
      margin: const EdgeInsets.only(top: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFFEFF6FF),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFBFDBFE)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: const [
                  Icon(Icons.mic_rounded, color: Color(0xFF1E88E5), size: 20),
                  SizedBox(width: 8),
                  Text('🎤 Ask AI Voice Assistant', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E3A8A))),
                ],
              ),
              ElevatedButton.icon(
                onPressed: _listen,
                icon: Icon(_isListening ? Icons.stop : Icons.mic, size: 16, color: Colors.white),
                label: Text(_isListening ? 'Listening...' : 'Ask AI', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: _isListening ? Colors.red : const Color(0xFF1E88E5),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            _isListening 
                ? 'Listening to your question...' 
                : (_lastRecognizedWords.isEmpty ? 'Tap "Ask AI" and ask: "Is this product high in sugar?"' : 'You asked: "$_lastRecognizedWords"'),
            style: TextStyle(fontSize: 13, fontStyle: FontStyle.italic, color: Colors.grey[700]),
          ),
          if (_isVoiceProcessing) ...[
            const SizedBox(height: 12),
            const LinearProgressIndicator(color: Color(0xFF1E88E5)),
          ],
          if (_spokenAiResponse != null) ...[
            const Divider(height: 20),
            Text(
              _spokenAiResponse!,
              style: const TextStyle(fontSize: 13, color: Color(0xFF1E293B), fontWeight: FontWeight.w500, height: 1.4),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildFeatureRow(IconData icon, String title, String subtitle) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(color: const Color(0xFFF1F5F9), borderRadius: BorderRadius.circular(8)),
          child: Icon(icon, color: const Color(0xFF1E88E5), size: 18),
        ),
        const SizedBox(width: 12),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF1E3A8A))),
            Text(subtitle, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
          ],
        ),
      ],
    );
  }

  Widget _buildLeftProductColumn(Map<String, dynamic> data) {
    Map<String, dynamic> eval = data['evaluations'] ?? {};
    bool isRec = data['recommendation']['is_recommended'] ?? true;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 8, offset: const Offset(0, 3))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 70,
                height: 90,
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.fastfood, color: Colors.grey, size: 36),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            data['title'],
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A)),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(4)),
                          child: Row(
                            children: const [
                              Icon(Icons.check, size: 12, color: Colors.green),
                              SizedBox(width: 2),
                              Text('Verified', style: TextStyle(fontSize: 10, color: Colors.green, fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Evaluated based on your active health goals.',
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: isRec ? Colors.green.shade50 : Colors.red.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(isRec ? Icons.check_circle : Icons.cancel, color: isRec ? Colors.green : Colors.red, size: 18),
                const SizedBox(width: 8),
                Text(
                  isRec ? 'Good choice for your goals!' : 'Not recommended for your goals',
                  style: TextStyle(color: isRec ? Colors.green.shade800 : Colors.red.shade800, fontWeight: FontWeight.bold, fontSize: 13),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildMetricChip('Calories', '${data['calories']} kcal', Icons.local_fire_department, Colors.red.shade50, Colors.red),
              _buildMetricChip('Protein', '${data['protein']} g', Icons.fitness_center, Colors.green.shade50, Colors.green),
              _buildMetricChip('Fat', '${data['fat']} g', Icons.water_drop, Colors.orange.shade50, Colors.orange),
              _buildMetricChip('Carbs', '${data['carbs']} g', Icons.grain, Colors.blue.shade50, Colors.blue),
            ],
          ),
          const SizedBox(height: 20),
          const Text('Nutrition Facts', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A))),
          const SizedBox(height: 10),
          _buildFactRow('Calories', '${data['calories']} kcal', ''),
          _buildFactRow('Sugar', '${data['sugar']} g', eval['sugar'] ?? 'HIGH'),
          _buildFactRow('Fat', '${data['fat']} g', eval['fat'] ?? 'MEDIUM'),
          _buildFactRow('Protein', '${data['protein']} g', eval['protein'] ?? 'GOOD'),
          _buildFactRow('Salt', '${data['salt']} g', eval['salt'] ?? 'MEDIUM'),
        ],
      ),
    );
  }

  Widget _buildRightInsightColumn(Map<String, dynamic> data) {
    List reasons = data['recommendation']['reasons'] ?? [];

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 8, offset: const Offset(0, 3))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: const [
                  Icon(Icons.auto_awesome, color: Color(0xFF1E88E5), size: 18),
                  SizedBox(width: 8),
                  Text('AI Nutrition Insight', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A))),
                ],
              ),
              Container(
                width: 34,
                height: 34,
                alignment: Alignment.center,
                decoration: BoxDecoration(color: data['gradeColor'], shape: BoxShape.circle),
                child: Text(data['grade'], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFF8FAFC),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFE2E8F0)),
            ),
            child: Text(
              data['genai_explanation'],
              style: const TextStyle(fontSize: 13, color: Color(0xFF334155), height: 1.4),
            ),
          ),
          if (data['explanation_source'] == 'fallback') ...[
            const SizedBox(height: 6),
            Text('AI service unavailable - showing a rule-based summary.${data['explanation_error'] != null ? '\n${data['explanation_error']}' : ''}',
                style: TextStyle(fontSize: 11, color: Colors.grey[500])),
          ],
          const SizedBox(height: 16),
          const Text('Reasons', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A))),
          const SizedBox(height: 6),
          ...reasons.map((r) => Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(
              children: [
                const Text('• ', style: TextStyle(color: Colors.grey)),
                Expanded(child: Text(r.toString(), style: const TextStyle(fontSize: 12, color: Colors.black87))),
              ],
            ),
          )),
          const SizedBox(height: 16),
          const Text('Quick Tips', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A))),
          const SizedBox(height: 6),
          ...List<String>.from(data['tips'] ?? []).map(_buildTipRow),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFF1F5F9),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                const Icon(Icons.flag, color: Color(0xFF1E88E5), size: 18),
                const SizedBox(width: 8),
                const Text('Your Goal: ', style: TextStyle(fontSize: 12, color: Colors.grey)),
                Text((data['goal'] ?? UserGoalService().currentGoal).toString(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A))),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricChip(String label, String value, IconData icon, Color bg, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(8)),
      child: Column(
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(fontSize: 10, color: Colors.grey[600])),
          Text(value, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }

  Widget _buildFactRow(String label, String value, String status) {
    Color statusColor = Colors.grey;
    if (status == 'HIGH') statusColor = Colors.red;
    if (status == 'MEDIUM') statusColor = Colors.orange;
    if (status == 'GOOD') statusColor = Colors.green;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: Colors.black54)),
          Row(
            children: [
              Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A))),
              if (status.isNotEmpty) ...[
                const SizedBox(width: 12),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
                  child: Text(status, style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: statusColor)),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTipRow(String tip) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        children: [
          const Icon(Icons.check, size: 14, color: Colors.green),
          const SizedBox(width: 6),
          Expanded(child: Text(tip, style: const TextStyle(fontSize: 12, color: Color(0xFF334155)))),
        ],
      ),
    );
  }
}