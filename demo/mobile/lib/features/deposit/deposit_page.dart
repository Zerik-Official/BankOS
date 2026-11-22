import 'package:bankos_mobile/core/format/account_name.dart';
import 'package:bankos_mobile/core/widgets/currency_prefix.dart';
import 'package:bankos_mobile/core/errors/bank_exception.dart';
import 'package:bankos_mobile/core/format/money.dart';
import 'package:bankos_mobile/data/models/account.dart';
import 'package:bankos_mobile/providers/bank_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Form to deposit money into one of the user's accounts.
class DepositPage extends ConsumerStatefulWidget {
  /// Creates the deposit screen.
  const DepositPage({super.key});

  @override
  ConsumerState<DepositPage> createState() => _DepositPageState();
}

class _DepositPageState extends ConsumerState<DepositPage> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _amountController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  String? _selectedAccountId;
  bool _saving = false;

  @override
  void dispose() {
    _amountController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final List<Account> accounts =
        ref.watch(bankProvider).value?.accounts ?? <Account>[];

    return Scaffold(
      appBar: AppBar(title: const Text('Nuevo depósito')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: <Widget>[
            DropdownButtonFormField<String>(
              initialValue: _currentAccountId(accounts),
              decoration: InputDecoration(labelText: 'Cuenta de destino'),
              items: <DropdownMenuItem<String>>[
                for (final Account account in accounts)
                  DropdownMenuItem<String>(
                    value: account.id,
                    child: Text(
                      '${accountNameFor(account.currency)} · ${account.currency}',
                    ),
                  ),
              ],
              onChanged: (String? value) =>
                  setState(() => _selectedAccountId = value),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _amountController,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: InputDecoration(
                labelText: 'Importe',
                prefixIcon: currencyPrefix(_selectedCurrency(accounts)),
              ),
              validator: validateAmountInput,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _descriptionController,
              decoration: InputDecoration(labelText: 'Descripción (opcional)'),
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _saving ? null : () => _submit(accounts),
              child: _saving
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Depositar'),
            ),
          ],
        ),
      ),
    );
  }

  /// Returns the selected account, or the first one when none was chosen yet.
  /// Currency code of the selected account, or an empty string when there is none.
  String _selectedCurrency(List<Account> accounts) {
    final String? id = _currentAccountId(accounts);
    for (final Account account in accounts) {
      if (account.id == id) {
        return account.currency;
      }
    }
    return '';
  }

  String? _currentAccountId(List<Account> accounts) {
    if (_selectedAccountId != null) {
      return _selectedAccountId;
    }
    return accounts.isNotEmpty ? accounts.first.id : null;
  }

  /// Sends the deposit and goes back to the previous screen when it succeeds.
  Future<void> _submit(List<Account> accounts) async {
    final String? accountId = _currentAccountId(accounts);
    if (accountId == null || !(_formKey.currentState?.validate() ?? false)) {
      return;
    }
    final int cents = parseUserAmountToCents(_amountController.text) ?? 0;
    final String description = _descriptionController.text.trim();

    setState(() => _saving = true);
    try {
      await ref
          .read(bankProvider.notifier)
          .deposit(
            accountId: accountId,
            amount: formatCents(cents),
            description: description.isEmpty ? null : description,
          );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Depósito realizado')));
      Navigator.of(context).pop();
    } on BankException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _saving = false);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error.message)));
    }
  }
}
