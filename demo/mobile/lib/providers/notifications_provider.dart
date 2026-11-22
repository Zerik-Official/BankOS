import 'package:bankos_mobile/data/models/bank_transaction.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Notice shown to the user when money arrives in one of their accounts.
class AppNotice {
  /// Creates a notice for the movement [id], unread unless [isRead] is true.
  const AppNotice({
    required this.id,
    required this.title,
    required this.body,
    required this.receivedAt,
    this.isRead = false,
    this.isIncoming = true,
  });

  /// Id of the movement that produced the notice.
  final String id;

  /// Short line, such as the amount received.
  final String title;

  /// Detail line, such as where the money came from.
  final String body;

  /// Time of the movement that produced the notice.
  final DateTime receivedAt;

  /// Whether the user has already opened or marked the notice.
  final bool isRead;

  /// True when money arrived in the user's account, false when it left.
  final bool isIncoming;

  /// Returns a copy of this notice marked as read.
  AppNotice markedAsRead() {
    return AppNotice(
      id: id,
      title: title,
      body: body,
      receivedAt: receivedAt,
      isRead: true,
      isIncoming: isIncoming,
    );
  }
}

/// How often the app asks the backend for new movements.
final Provider<Duration> pollIntervalProvider = Provider<Duration>((Ref ref) {
  return const Duration(seconds: 15);
});

/// Keeps the notices received while the app is open, newest first.
class NoticesNotifier extends Notifier<List<AppNotice>> {
  @override
  List<AppNotice> build() {
    return const <AppNotice>[];
  }

  /// Adds [notices] in front of the current list, keeping their order.
  void add(List<AppNotice> notices) {
    state = <AppNotice>[...notices.reversed, ...state];
  }

  /// Marks the notice with [id] as read. Other notices are not changed.
  void markAsRead(String id) {
    state = <AppNotice>[
      for (final AppNotice notice in state)
        if (notice.id == id) notice.markedAsRead() else notice,
    ];
  }

  /// Marks every notice as read.
  void markAllAsRead() {
    state = <AppNotice>[
      for (final AppNotice notice in state) notice.markedAsRead(),
    ];
  }

  /// Removes every notice.
  void clear() {
    state = const <AppNotice>[];
  }
}

/// Exposes the notices to the widgets.
final NotifierProvider<NoticesNotifier, List<AppNotice>> noticesProvider =
    NotifierProvider<NoticesNotifier, List<AppNotice>>(NoticesNotifier.new);

/// Number of notices the user has not read yet. Drives the badge on the bell.
final Provider<int> unreadNoticesCountProvider = Provider<int>((Ref ref) {
  return ref
      .watch(noticesProvider)
      .where((AppNotice notice) => !notice.isRead)
      .length;
});

/// Builds notices for the movements whose ids are not in [seenIds].
///
/// Incoming money gives a "received" notice. Money that leaves one of the user's
/// accounts to someone else (a transfer or a withdrawal) gives a "sent" notice.
/// Failed operations, transfers between the user's own accounts and movements
/// already seen are skipped.
List<AppNotice> newMovementNotices({
  required Set<String> seenIds,
  required List<BankTransaction> transactions,
  required Set<String> ownAccountNumbers,
}) {
  final List<AppNotice> notices = <AppNotice>[];
  for (final BankTransaction transaction in transactions) {
    if (seenIds.contains(transaction.id) || transaction.status != 'success') {
      continue;
    }
    if (transaction.isIncomingFor(ownAccountNumbers)) {
      notices.add(
        AppNotice(
          id: transaction.id,
          title: 'Has recibido ${transaction.amount} ${transaction.currency}',
          body: _incomingOrigin(transaction),
          receivedAt: transaction.createdAt,
        ),
      );
      continue;
    }
    if (_isSentToSomeoneElse(transaction, ownAccountNumbers)) {
      notices.add(
        AppNotice(
          id: transaction.id,
          title: 'Has enviado ${transaction.amount} ${transaction.currency}',
          body: _outgoingDestination(transaction),
          receivedAt: transaction.createdAt,
          isIncoming: false,
        ),
      );
    }
  }
  return notices;
}

/// True when money left one of [ownAccountNumbers] and went to an account outside it.
bool _isSentToSomeoneElse(
  BankTransaction transaction,
  Set<String> ownAccountNumbers,
) {
  if (transaction.type == 'withdrawal') {
    return true;
  }
  final String? source = transaction.sourceAccountNumber;
  final String? target = transaction.targetAccountNumber;
  final bool fromOwn = source != null && ownAccountNumbers.contains(source);
  final bool toOwn = target != null && ownAccountNumbers.contains(target);
  return fromOwn && !toOwn;
}

/// Last four digits of an account number, so the full number is not shown.
String _lastFour(String accountNumber) {
  if (accountNumber.length < 4) {
    return accountNumber;
  }
  return accountNumber.substring(accountNumber.length - 4);
}

/// Describes where an outgoing movement went, without showing the full number.
String _outgoingDestination(BankTransaction transaction) {
  if (transaction.type == 'withdrawal') {
    return 'Retiro de tu cuenta';
  }
  final String? target = transaction.targetAccountNumber;
  if (target == null) {
    return 'Transferencia enviada';
  }
  return 'Transferencia a la cuenta terminada en ${_lastFour(target)}';
}

/// Describes where an incoming movement came from, without showing the full number.
String _incomingOrigin(BankTransaction transaction) {
  if (transaction.type == 'deposit') {
    return 'Ingreso en tu cuenta';
  }
  final String? source = transaction.sourceAccountNumber;
  if (source == null || source.length < 4) {
    return 'Transferencia recibida';
  }
  return 'Transferencia desde la cuenta terminada en ${source.substring(source.length - 4)}';
}
