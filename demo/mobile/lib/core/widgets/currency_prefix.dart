import 'package:flutter/material.dart';

/// Symbol shown at the start of an amount field, so it matches the currency of the account.
Widget currencyPrefix(String currency) {
  if (currency == 'EUR') {
    return const Icon(Icons.euro);
  }
  if (currency == 'USD') {
    return const Icon(Icons.attach_money);
  }
  return Padding(
    padding: const EdgeInsets.symmetric(horizontal: 12),
    child: Text(currency, style: const TextStyle(fontWeight: FontWeight.w700)),
  );
}
