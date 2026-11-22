import 'package:bankos_mobile/core/format/money.dart';
import 'package:bankos_mobile/data/models/account.dart';
import 'package:flutter/material.dart';

/// Card that shows the number and balance of one account.
class AccountCard extends StatelessWidget {
  /// Creates a card for [account].
  const AccountCard({super.key, required this.account});

  /// Account to display.
  final Account account;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: <Widget>[
            CircleAvatar(
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Icon(
                Icons.account_balance_wallet,
                color: theme.colorScheme.primary,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    'Cuenta ${account.accountNumber}',
                    style: theme.textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    formatMoney(account.balance, account.currency),
                    style: theme.textTheme.titleLarge,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
