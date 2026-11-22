/// Helpers to convert between the API money format ("898.00") and integer cents.
library;

/// Matches amounts typed by the user, such as "12", "12.5" or "12,50".
final RegExp _amountPattern = RegExp(r'^\d+([.,]\d{1,2})?$');

/// Converts an API amount such as "898.00" into cents.
int parseAmountToCents(String amount) {
  final List<String> parts = amount.split('.');
  final int whole = int.parse(parts.first);
  final String fraction = parts.length > 1 ? parts[1].padRight(2, '0') : '00';
  return whole * 100 + int.parse(fraction);
}

/// Converts user input such as "12,5" into cents, or returns null when invalid.
int? parseUserAmountToCents(String input) {
  final String trimmed = input.trim();
  if (!_amountPattern.hasMatch(trimmed)) {
    return null;
  }
  return parseAmountToCents(trimmed.replaceAll(',', '.'));
}

/// Formats cents as an API amount with two decimals, such as "898.00".
String formatCents(int cents) {
  final String whole = (cents ~/ 100).toString();
  final String fraction = (cents % 100).toString().padLeft(2, '0');
  return '$whole.$fraction';
}

/// Formats an amount together with its currency code, such as "898.00 USD".
String formatMoney(String amount, String currency) {
  return '$amount $currency';
}

/// Validates an amount field in a form. Returns a Spanish message when invalid.
String? validateAmountInput(String? value) {
  final int? cents = parseUserAmountToCents(value ?? '');
  if (cents == null) {
    return 'Introduce un importe válido, por ejemplo 25.50';
  }
  if (cents <= 0) {
    return 'El importe debe ser mayor que cero';
  }
  return null;
}
