import 'package:bankos_mobile/app/theme.dart';
import 'package:bankos_mobile/core/format/money.dart';
import 'package:bankos_mobile/core/widgets/brand_logo.dart';
import 'package:bankos_mobile/data/models/bank_transaction.dart';
import 'package:bankos_mobile/providers/bank_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Direction filter of the movements list.
enum _Filter { all, incoming, outgoing }

const List<String> _months = <String>[
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre',
];

/// Full list of movements, grouped by day, with search and direction filters.
class TransactionsPage extends ConsumerStatefulWidget {
  /// Creates the movements screen.
  const TransactionsPage({super.key});

  @override
  ConsumerState<TransactionsPage> createState() => _TransactionsPageState();
}

class _TransactionsPageState extends ConsumerState<TransactionsPage> {
  _Filter _filter = _Filter.all;
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final AsyncValue<BankSnapshot> bank = ref.watch(bankProvider);
    final double topInset = MediaQuery.of(context).padding.top;
    final bool landscape =
        MediaQuery.orientationOf(context) == Orientation.landscape;

    final Widget search = TextField(
      onChanged: (String value) =>
          setState(() => _query = value.trim().toLowerCase()),
      decoration: const InputDecoration(
        hintText: 'Buscar movimiento...',
        prefixIcon: Icon(Icons.search),
        border: InputBorder.none,
      ),
    );
    final Widget filters = _FilterRow(
      selected: _filter,
      onSelected: (_Filter filter) => setState(() => _filter = filter),
    );

    return Scaffold(
      body: Column(
        children: <Widget>[
          _Header(topInset: topInset, showSubtitle: !landscape),
          if (landscape)
            // Landscape: search and filters share one row to leave room for the list.
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 4),
              child: Row(
                children: <Widget>[
                  Expanded(child: search),
                  const SizedBox(width: 12),
                  SizedBox(width: 340, child: filters),
                ],
              ),
            )
          else ...<Widget>[
            Transform.translate(
              offset: const Offset(0, -28),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 4),
                child: search,
              ),
            ),
            Transform.translate(offset: const Offset(0, -20), child: filters),
          ],
          Expanded(
            child: bank.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (Object error, StackTrace stackTrace) => const Center(
                child: Text('No se pudieron cargar los movimientos'),
              ),
              data: (BankSnapshot snapshot) {
                final Set<String> own = snapshot.accountNumbers;
                final List<BankTransaction> items = snapshot.transactions
                    .where(
                      (BankTransaction t) => _matchesFilter(t, own, _filter),
                    )
                    .where((BankTransaction t) => _matchesQuery(t, _query))
                    .toList();
                if (items.isEmpty) {
                  return const Center(child: Text('No hay movimientos'));
                }
                final List<Object> rows = _grouped(items);
                return ListView.builder(
                  padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
                  itemCount: rows.length,
                  itemBuilder: (BuildContext context, int index) {
                    final Object row = rows[index];
                    if (row is String) {
                      return Padding(
                        padding: const EdgeInsets.fromLTRB(4, 12, 4, 8),
                        child: Text(
                          row,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.brandDeep,
                          ),
                        ),
                      );
                    }
                    final BankTransaction transaction = row as BankTransaction;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _MovementRow(
                        transaction: transaction,
                        isIncoming: transaction.isIncomingFor(own),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  /// Inserts a day label before the first movement of each day.
  List<Object> _grouped(List<BankTransaction> items) {
    final List<Object> rows = <Object>[];
    String? current;
    for (final BankTransaction transaction in items) {
      final String label = _dayLabel(transaction.createdAt);
      if (label != current) {
        rows.add(label);
        current = label;
      }
      rows.add(transaction);
    }
    return rows;
  }
}

/// Purple header with the logo, the title and a curved bottom edge.
class _Header extends StatelessWidget {
  /// Creates the header. [topInset] is the height of the status bar.
  const _Header({required this.topInset, this.showSubtitle = true});

  /// Height of the status bar, so the content starts below it.
  final double topInset;

  /// Whether to show the line under the title. Hidden in landscape to save height.
  final bool showSubtitle;

  @override
  Widget build(BuildContext context) {
    // Landscape has little height: the header gets a more compact layout.
    final bool landscape =
        MediaQuery.orientationOf(context) == Orientation.landscape;
    return ClipPath(
      clipper: _HeaderClipper(),
      child: Container(
        width: double.infinity,
        padding: EdgeInsets.fromLTRB(
          20,
          topInset + (landscape ? 8 : 16),
          20,
          landscape ? 36 : 60,
        ),
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: <Color>[AppTheme.brandDeep, AppTheme.brandPurple],
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const Row(
              children: <Widget>[
                BankOsStar(size: 22, color: Colors.white),
                SizedBox(width: 8),
                Text(
                  'BankOS',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            SizedBox(height: landscape ? 6 : 18),
            Text(
              'Movimientos',
              style: TextStyle(
                color: Colors.white,
                fontSize: landscape ? 22 : 30,
                fontWeight: FontWeight.w800,
              ),
            ),
            if (showSubtitle) ...<Widget>[
              const SizedBox(height: 4),
              Text(
                'Consulta el historial de tus transacciones',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.75),
                  fontSize: 14,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Three pills to show all movements, only incoming ones or only outgoing ones.
class _FilterRow extends StatelessWidget {
  /// Creates the row with the [selected] filter.
  const _FilterRow({required this.selected, required this.onSelected});

  /// Filter currently applied.
  final _Filter selected;

  /// Called with the filter the user taps.
  final ValueChanged<_Filter> onSelected;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: <Widget>[
          _FilterPill(
            label: 'Todos',
            selected: selected == _Filter.all,
            onTap: () => onSelected(_Filter.all),
          ),
          const SizedBox(width: 10),
          _FilterPill(
            label: 'Ingresos',
            selected: selected == _Filter.incoming,
            onTap: () => onSelected(_Filter.incoming),
          ),
          const SizedBox(width: 10),
          _FilterPill(
            label: 'Egresos',
            selected: selected == _Filter.outgoing,
            onTap: () => onSelected(_Filter.outgoing),
          ),
        ],
      ),
    );
  }
}

/// One rounded filter button.
class _FilterPill extends StatelessWidget {
  /// Creates the pill with [label].
  const _FilterPill({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  /// Text shown inside the pill.
  final String label;

  /// Whether this pill is the active filter.
  final bool selected;

  /// Called when the user taps the pill.
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        color: selected ? AppTheme.brandPurple : Colors.white,
        borderRadius: BorderRadius.circular(20),
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Center(
              child: Text(
                label,
                style: TextStyle(
                  fontWeight: FontWeight.w700,
                  color: selected ? Colors.white : AppTheme.brandDeep,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// White rounded row with the icon, the type, the time and the signed amount.
class _MovementRow extends StatelessWidget {
  /// Creates the row for [transaction].
  const _MovementRow({required this.transaction, required this.isIncoming});

  /// Movement to show.
  final BankTransaction transaction;

  /// True when the money arrives at one of the user's accounts.
  final bool isIncoming;

  @override
  Widget build(BuildContext context) {
    final bool rejected = transaction.status == 'error';
    final String label = _typeLabel(transaction.type);
    final String sign = rejected ? '' : (isIncoming ? '+' : '-');
    final Color amountColor = rejected
        ? Colors.grey
        : (isIncoming ? Colors.green.shade700 : Colors.red.shade700);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: <Widget>[
          CircleAvatar(
            radius: 22,
            backgroundColor: AppTheme.brandSoft,
            child: Icon(
              _typeIcon(transaction.type),
              color: AppTheme.brandPurple,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  rejected ? '$label rechazado' : label,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.brandDeep,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  _timeLabel(transaction.createdAt),
                  style: const TextStyle(fontSize: 13, color: Colors.black54),
                ),
              ],
            ),
          ),
          Text(
            '$sign${formatMoney(transaction.amount, transaction.currency)}',
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: amountColor,
            ),
          ),
        ],
      ),
    );
  }
}

/// True when [transaction] belongs to the selected direction filter.
bool _matchesFilter(
  BankTransaction transaction,
  Set<String> ownAccounts,
  _Filter filter,
) {
  switch (filter) {
    case _Filter.all:
      return true;
    case _Filter.incoming:
      return transaction.status == 'success' &&
          transaction.isIncomingFor(ownAccounts);
    case _Filter.outgoing:
      return transaction.status == 'success' &&
          !transaction.isIncomingFor(ownAccounts);
  }
}

/// True when the search text appears in the type, the description or the amount.
bool _matchesQuery(BankTransaction transaction, String query) {
  if (query.isEmpty) {
    return true;
  }
  final String text =
      '${_typeLabel(transaction.type)} '
              '${transaction.description ?? ''} '
              '${transaction.amount}'
          .toLowerCase();
  return text.contains(query);
}

/// Spanish name of a movement type.
String _typeLabel(String type) {
  switch (type) {
    case 'deposit':
      return 'Depósito';
    case 'withdrawal':
      return 'Retiro';
    case 'transfer':
      return 'Transferencia';
    default:
      return type;
  }
}

/// Icon that represents a movement type.
IconData _typeIcon(String type) {
  switch (type) {
    case 'deposit':
      return Icons.arrow_downward;
    case 'withdrawal':
      return Icons.arrow_upward;
    default:
      return Icons.swap_horiz;
  }
}

/// Day label used as a group header: "Hoy", "Ayer" or a full date.
String _dayLabel(DateTime createdAt) {
  final DateTime now = DateTime.now();
  final DateTime day = createdAt.toLocal();
  final int days = DateTime(
    now.year,
    now.month,
    now.day,
  ).difference(DateTime(day.year, day.month, day.day)).inDays;
  if (days == 0) {
    return 'Hoy';
  }
  if (days == 1) {
    return 'Ayer';
  }
  return '${day.day} de ${_months[day.month - 1]} de ${day.year}';
}

/// Local time of [createdAt] as HH:mm.
String _timeLabel(DateTime createdAt) {
  final DateTime local = createdAt.toLocal();
  final String hour = local.hour.toString().padLeft(2, '0');
  final String minute = local.minute.toString().padLeft(2, '0');
  return '$hour:$minute';
}

/// Clips the header to a rectangle with a curved bottom edge.
class _HeaderClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    final double w = size.width;
    final double h = size.height;
    return Path()
      ..moveTo(0, 0)
      ..lineTo(w, 0)
      ..lineTo(w, h * 0.8)
      ..quadraticBezierTo(w * 0.55, h * 1.08, 0, h * 0.8)
      ..close();
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}
