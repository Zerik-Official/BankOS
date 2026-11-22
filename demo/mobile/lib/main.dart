import 'package:bankos_mobile/app/app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Starts the app inside a Riverpod scope so every provider is available.
void main() {
  runApp(const ProviderScope(child: BankOsApp()));
}
