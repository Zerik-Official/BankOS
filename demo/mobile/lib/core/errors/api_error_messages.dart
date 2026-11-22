/// Spanish messages for the error codes returned by the BankOS API.
abstract final class ApiErrorMessages {
  /// Message used when the server cannot be reached.
  static const String networkError =
      'No se pudo conectar con el servidor. Revisa tu conexión';

  /// Message used when the server answers with something that is not valid JSON.
  static const String invalidResponse =
      'El servidor respondió de forma no válida';

  static const Map<String, String> _byCode = <String, String>{
    'UNAUTHENTICATED': 'Credenciales incorrectas o sesión caducada',
    'INSUFFICIENT_FUNDS': 'No tienes fondos suficientes para esta operación',
    'SAME_ACCOUNT_TRANSFER': 'No puedes transferir a la misma cuenta',
    'EXCHANGE_RATE_NOT_FOUND': 'No hay tipo de cambio entre estas monedas',
    'TRANSACTION_LIMIT_EXCEEDED': 'El importe supera el límite permitido',
    'ACCOUNT_NOT_ACTIVE': 'La cuenta no está activa',
    'IDEMPOTENCY_IN_PROGRESS': 'Esta operación ya se está procesando',
    'RATE_LIMIT_EXCEEDED': 'Demasiadas operaciones seguidas. Espera un minuto',
    'VALIDATION_ERROR': 'Revisa los datos introducidos',
  };

  /// Returns the Spanish message for [code], or [fallback] when the code is unknown.
  static String forCode(String code, String fallback) {
    return _byCode[code] ?? fallback;
  }
}
