/// Name shown for an account, built from its currency since the backend has no account name.
String accountNameFor(String currency) {
  switch (currency) {
    case 'EUR':
      return 'Cuenta en euros';
    case 'USD':
      return 'Cuenta en dólares';
    default:
      return 'Cuenta en $currency';
  }
}
