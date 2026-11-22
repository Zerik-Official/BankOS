import 'package:bankos_mobile/core/widgets/transaction_tile.dart';
import 'package:bankos_mobile/data/models/bank_transaction.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  BankTransaction build({required String status}) {
    return BankTransaction(
      id: 'tx-9',
      type: 'withdrawal',
      status: status,
      amount: '999999.00',
      currency: 'EUR',
      fee: '0.00',
      createdAt: DateTime(2026, 11, 17),
    );
  }

  testWidgets('a rejected operation is shown as rejected, not as money moved', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: TransactionTile(
            transaction: build(status: 'error'),
            isIncoming: false,
          ),
        ),
      ),
    );

    expect(find.text('Retiro rechazado'), findsOneWidget);
    expect(find.text('999999.00 EUR'), findsOneWidget);
  });

  testWidgets('a successful withdrawal shows a minus sign', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: TransactionTile(
            transaction: build(status: 'success'),
            isIncoming: false,
          ),
        ),
      ),
    );

    expect(find.text('Retiro'), findsOneWidget);
    expect(find.text('-999999.00 EUR'), findsOneWidget);
  });
}
