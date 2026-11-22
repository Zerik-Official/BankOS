import 'package:flutter/foundation.dart';

/// Connection settings for the BankOS API.
abstract final class ApiConfig {
  /// Base URL passed at build time with `--dart-define=API_BASE_URL=...`.
  static const String _overrideBaseUrl = String.fromEnvironment('API_BASE_URL');

  /// Full API base URL, including the `/api/v1` prefix.
  static String get baseUrl {
    if (_overrideBaseUrl.isNotEmpty) {
      return _overrideBaseUrl;
    }
    // The Android emulator reaches the computer that runs the API through 10.0.2.2.
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    return 'http://localhost:8000/api/v1';
  }
}
