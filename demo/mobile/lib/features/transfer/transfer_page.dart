import 'package:bankos_mobile/core/format/account_name.dart';
import 'package:bankos_mobile/core/widgets/currency_prefix.dart';
import 'package:bankos_mobile/core/errors/bank_exception.dart';
import 'package:bankos_mobile/core/format/money.dart';
import 'package:bankos_mobile/data/models/account.dart';
import 'package:bankos_mobile/data/models/transfer_quote.dart';
import 'package:bankos_mobile/providers/bank_provider.dart';
import 'package:bankos_mobile/providers/repository_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Form to send money to another account. Shows the fee before confirming.
class TransferPage extends ConsumerStatefulWidget {
  /// Creates the transfer screen.
  const TransferPage({super.key});

  @override
  ConsumerState<TransferPage> createState() => _TransferPageState();
}

class _TransferPageState extends ConsumerState<TransferPage> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _targetController = TextEditingController();
  final TextEditingController _amountController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  String? _selectedAccountId;
  TransferQuote? _quote;
  bool _saving = false;
  bool _toOwnAccount = false;
  String? _ownTargetId;

  @override
  void dispose() {
    _targetController.dispose();
    _amountController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final List<Account> accounts =
        ref.watch(bankProvider).value?.accounts ?? <Account>[];

    return Scaffold(
      appBar: AppBar(title: const Text('Nueva transferencia')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: <Widget>[
            DropdownButtonFormField<String>(
              initialValue: _currentAccountId(accounts),
              decoration: InputDecoration(labelText: 'Cuenta de origen'),
              items: <DropdownMenuItem<String>>[
                for (final Account account in accounts)
                  DropdownMenuItem<String>(
                    value: account.id,
                    child: Text(
                      '${accountNameFor(account.currency)} · ${account.balance} ${account.currency}',
                    ),
                  ),
              ],
              onChanged: (String? value) {
                setState(() {
                  _selectedAccountId = value;
                  _quote = null;
                });
              },
            ),
            const SizedBox(height: 16),
            SegmentedButton<bool>(
              segments: const <ButtonSegment<bool>>[
                ButtonSegment<bool>(value: true, label: Text('Mi cuenta')),
                ButtonSegment<bool>(value: false, label: Text('Otra persona')),
              ],
              selected: <bool>{_toOwnAccount},
              onSelectionChanged: (Set<bool> selection) {
                setState(() {
                  _toOwnAccount = selection.first;
                  _ownTargetId = null;
                  _targetController.clear();
                  _quote = null;
                });
              },
            ),
            const SizedBox(height: 16),
            if (_toOwnAccount)
              DropdownButtonFormField<String>(
                initialValue: _ownTargetId,
                decoration: InputDecoration(
                  labelText: 'Cuenta de destino',
                  prefixIcon: Icon(Icons.account_balance_wallet_outlined),
                ),
                items: <DropdownMenuItem<String>>[
                  for (final Account account in accounts)
                    if (account.id != _currentAccountId(accounts))
                      DropdownMenuItem<String>(
                        value: account.id,
                        child: Text(
                          '${accountNameFor(account.currency)} · ${account.currency}',
                        ),
                      ),
                ],
                validator: (String? value) =>
                    value == null ? 'Elige una cuenta' : null,
                onChanged: (String? value) {
                  final List<Account> matches = accounts
                      .where((Account account) => account.id == value)
                      .toList();
                  final Account? chosen = matches.isEmpty
                      ? null
                      : matches.first;
                  setState(() {
                    _ownTargetId = value;
                    _targetController.text = chosen?.accountNumber ?? '';
                    _quote = null;
                  });
                },
              )
            else
              TextFormField(
                controller: _targetController,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  labelText: 'Número de cuenta destino',
                  helperText: 'Cuenta de otro cliente de tu entidad',
                  prefixIcon: Icon(Icons.account_balance),
                ),
                validator: (String? value) =>
                    (value == null || value.trim().length < 4)
                    ? 'Introduce un número de cuenta válido'
                    : null,
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
              onChanged: (String value) => setState(() => _quote = null),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _descriptionController,
              decoration: InputDecoration(labelText: 'Descripción (opcional)'),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: _saving ? null : () => _calculateQuote(accounts),
              icon: const Icon(Icons.calculate_outlined),
              label: const Text('Calcular comisión'),
            ),
            if (_quote != null) ...<Widget>[
              const SizedBox(height: 16),
              _QuoteCard(quote: _quote!),
            ],
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _saving ? null : () => _submit(accounts),
              child: _saving
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Transferir'),
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

  /// Asks the repository for the fee and shows it. Nothing is moved yet.
  Future<void> _calculateQuote(List<Account> accounts) async {
    final String? accountId = _currentAccountId(accounts);
    if (accountId == null || !(_formKey.currentState?.validate() ?? false)) {
      return;
    }
    final int cents = parseUserAmountToCents(_amountController.text) ?? 0;
    try {
      final TransferQuote quote = await ref
          .read(bankRepositoryProvider)
          .quoteTransfer(
            sourceAccountId: accountId,
            targetAccountNumber: _targetController.text.trim(),
            amount: formatCents(cents),
          );
      if (!mounted) {
        return;
      }
      setState(() => _quote = quote);
    } on BankException catch (error) {
      _showError(error.message);
    }
  }

  /// Asks the user to confirm a transfer to someone else's account before sending it.
  Future<bool> _confirmExternal(
    List<Account> accounts,
    String accountId,
    int cents,
  ) async {
    final List<Account> sources = accounts
        .where((Account a) => a.id == accountId)
        .toList();
    final String currency = sources.isEmpty ? '' : sources.first.currency;
    final bool? confirmed = await showDialog<bool>(
      context: context,
      builder: (BuildContext dialogContext) => AlertDialog(
        title: const Text('Confirmar transferencia'),
        content: Text(
          'Vas a enviar ${formatCents(cents)} $currency a la cuenta '
          '${_targetController.text.trim()}, que es de otra persona. '
          'Revisa el número antes de confirmar.',
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
    return confirmed ?? false;
  }

  /// Sends the transfer and goes back when it succeeds. Shows the error otherwise.
  Future<void> _submit(List<Account> accounts) async {
    final String? accountId = _currentAccountId(accounts);
    if (accountId == null || !(_formKey.currentState?.validate() ?? false)) {
      return;
    }
    final int cents = parseUserAmountToCents(_amountController.text) ?? 0;
    final String description = _descriptionController.text.trim();

    if (!_toOwnAccount) {
      final bool confirmed = await _confirmExternal(accounts, accountId, cents);
      if (!confirmed || !mounted) {
        return;
      }
    }

    setState(() => _saving = true);
    try {
      await ref
          .read(bankProvider.notifier)
          .transfer(
            sourceAccountId: accountId,
            targetAccountNumber: _targetController.text.trim(),
            amount: formatCents(cents),
            description: description.isEmpty ? null : description,
          );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Transferencia realizada')));
      Navigator.of(context).pop();
    } on BankException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _saving = false);
      _showError(error.message);
    }
  }

  /// Shows an error message in a snackbar.
  void _showError(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }
}

/// Card that shows the cost breakdown of a transfer.
class _QuoteCard extends StatelessWidget {
  /// Creates the card for [quote].
  const _QuoteCard({required this.quote});

  /// Cost breakdown to display.
  final TransferQuote quote;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text('Resumen', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            _QuoteLine(
              label: 'Importe',
              value: formatMoney(quote.amount, quote.sourceCurrency),
            ),
            _QuoteLine(
              label: 'Comisión',
              value: formatMoney(quote.fee, quote.sourceCurrency),
            ),
            _QuoteLine(
              label: 'Total a cargar',
              value: formatMoney(quote.totalDebit, quote.sourceCurrency),
            ),
            _QuoteLine(label: 'Tipo de cambio', value: quote.exchangeRate),
            _QuoteLine(
              label: 'Importe recibido',
              value: formatMoney(quote.convertedAmount, quote.targetCurrency),
            ),
          ],
        ),
      ),
    );
  }
}

/// One label and value row of the quote card.
class _QuoteLine extends StatelessWidget {
  /// Creates a row with [label] and [value].
  const _QuoteLine({required this.label, required this.value});

  /// Text on the left side.
  final String label;

  /// Text on the right side.
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: <Widget>[
          Text(label),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
