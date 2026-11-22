/// Error raised by the bank layer. It mirrors the backend error envelope (`code` and `message`).
class BankException implements Exception {
  /// Creates an error with a machine-readable [code] and a user-facing [message].
  const BankException({required this.code, required this.message});

  /// Machine-readable code, such as `INSUFFICIENT_FUNDS`.
  final String code;

  /// Message in Spanish that can be shown to the user.
  final String message;

  @override
  String toString() => 'BankException($code): $message';
}
