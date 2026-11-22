import 'package:bankos_mobile/core/format/money.dart';
import 'package:bankos_mobile/data/models/bank_transaction.dart';
import 'package:flutter/material.dart';

/// List row that shows one financial movement.
class TransactionTile extends StatelessWidget {
  /// Creates a row for [transaction]. [isIncoming] decides the sign and color.
  const TransactionTile({
    super.key,
    required this.transaction,
    required this.isIncoming,
  });

  /// Movement to display.
  final BankTransaction transaction;

  /// True when the money arrives at one of the user's accounts.
  final bool isIncoming;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    if (transaction.status == 'error') {
      return _buildRejected(theme);
    }
    final String sign = isIncoming ? '+' : '-';
    final Color amountColor = isIncoming
        ? Colors.green.shade700
        : theme.colorScheme.error;

    return ListTile(
      leading: CircleAvatar(
        backgroundColor: theme.colorScheme.surfaceContainerHighest,
        child: Icon(
          _iconFor(transaction.type),
          color: theme.colorScheme.primary,
        ),
      ),
      title: Text(_labelFor(transaction.type)),
      subtitle: Text(_subtitleFor(transaction)),
      trailing: Text(
        '$sign${formatMoney(transaction.amount, transaction.currency)}',
        style: theme.textTheme.titleSmall?.copyWith(color: amountColor),
      ),
    );
  }

  /// Row for a rejected operation. The backend keeps these records, but no money moved.
  Widget _buildRejected(ThemeData theme) {
    final Color muted = theme.colorScheme.onSurfaceVariant;
    return ListTile(
      leading: CircleAvatar(
        backgroundColor: theme.colorScheme.surfaceContainerHighest,
        child: Icon(Icons.error_outline, color: muted),
      ),
      title: Text('${_labelFor(transaction.type)} rechazado'),
      subtitle: Text(_subtitleFor(transaction)),
      trailing: Text(
        formatMoney(transaction.amount, transaction.currency),
        style: theme.textTheme.titleSmall?.copyWith(color: muted),
      ),
    );
  }

  /// Returns the Spanish name of a movement type.
  String _labelFor(String type) {
    switch (type) {
      case 'deposit':
        return 'Depósito';
      case 'withdrawal':
        return 'Retiro';
      case 'transfer':
        return 'Transferencia';
      default:
        return 'Movimiento';
    }
  }

  /// Returns the icon of a movement type.
  IconData _iconFor(String type) {
    switch (type) {
      case 'deposit':
        return Icons.arrow_downward;
      case 'withdrawal':
        return Icons.arrow_upward;
      case 'transfer':
        return Icons.swap_horiz;
      default:
        return Icons.receipt;
    }
  }

  /// Builds the second line: description (if any) and the date.
  String _subtitleFor(BankTransaction transaction) {
    final DateTime date = transaction.createdAt.toLocal();
    final String day = date.day.toString().padLeft(2, '0');
    final String month = date.month.toString().padLeft(2, '0');
    final String dateText = '$day/$month/${date.year}';
    final String? description = transaction.description;
    if (description == null || description.isEmpty) {
      return dateText;
    }
    return '$description · $dateText';
  }
}
