import 'package:translator/translator.dart';

class MultilingualService {
  final GoogleTranslator _translator = GoogleTranslator();

  // Supported Languages Map for Phase 14
  static const Map<String, String> supportedLanguages = {
    'en': 'English',
    'hi': 'Hindi (हिंदी)',
    'mr': 'Marathi (मराठी)',
  };

  /// Preprocesses food label text by translating non-English text to English 
  /// so standard nutrition parsers and databases can understand it.
  Future<String> preprocessLabelText(String rawOcrText) async {
    if (rawOcrText.trim().isEmpty) return rawOcrText;
    
    try {
      var translation = await _translator.translate(rawOcrText, to: 'en');
      return translation.text;
    } catch (e) {
      // Fallback to raw text if translation fails or network is unavailable
      return rawOcrText;
    }
  }

  /// Translates final AI recommendations or nutrition analyses back into 
  /// the user's selected target language (English, Hindi, or Marathi).
  Future<String> localizeRecommendation(String analysisText, String targetLangCode) async {
    if (targetLangCode == 'en' || analysisText.trim().isEmpty) {
      return analysisText;
    }
    
    try {
      var translation = await _translator.translate(analysisText, to: targetLangCode);
      return translation.text;
    } catch (e) {
      return analysisText; // Fallback to original text on failure
    }
  }
}