import 'dart:async';

import 'package:bankos_mobile/core/errors/bank_exception.dart';
import 'package:bankos_mobile/data/bank_repository.dart';
import 'package:bankos_mobile/data/models/account.dart';
import 'package:bankos_mobile/data/models/bank_transaction.dart';
import 'package:bankos_mobile/data/models/user_profile.dart';
import 'package:bankos_mobile/providers/notifications_provider.dart';
import 'package:bankos_mobile/providers/repository_provider.dart';
import 'package:bankos_mobile/providers/session_provider.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Accounts and movements shown on the home and transactions screens.
class BankSnapshot {
  /// Creates a snapshot of the bank data.
  const BankSnapshot({required this.accounts, required this.transactions});

  /// Snapshot without data, used when nobody is signed in.
  const BankSnapshot.empty()
    : accounts = const <Account>[],
      transactions = const <BankTransaction>[];

  /// Accounts of the user.
  final List<Account> accounts;

  /// Movement history, most recent first.
  final List<BankTransaction> transactions;

  /// Account numbers that belong to the user.
  Set<String> get accountNumbers {
    return accounts.map((Account account) => account.accountNumber).toSet();
  }
}

/// Loads the bank data for the signed-in user and reloads it after every operation.
class BankNotifier extends AsyncNotifier<BankSnapshot> {
  /// Ids of the movements already loaded, so only new ones produce notices.
  final Set<String> _seenIds = <String>{};

  /// Periodic check for new movements while someone is signed in.
  Timer? _timer;

  @override
  Future<BankSnapshot> build() async {
    _timer?.cancel();
    ref.onDispose(() => _timer?.cancel());
    // Watching the session reloads the data on sign-in and clears it on sign-out.
    final UserProfile? user = ref.watch(sessionProvider);
    _seenIds.clear();
    if (user == null) {
      return const BankSnapshot.empty();
    }
    final BankSnapshot snapshot = await _load();
    _startPolling();
    return snapshot;
  }

  /// Starts checking the backend every poll interval. Tests disable it with a zero interval.
  void _startPolling() {
    final Duration interval = ref.read(pollIntervalProvider);
    if (interval == Duration.zero) {
      return;
    }
    _timer = Timer.periodic(interval, (Timer _) => _poll());
  }

  /// Reloads the data and turns new incoming movements into notices.
  Future<void> _poll() async {
    final Set<String> seen = Set<String>.of(_seenIds);
    try {
      final BankSnapshot snapshot = await _load();
      final List<AppNotice> notices = newMovementNotices(
        seenIds: seen,
        transactions: snapshot.transactions,
        ownAccountNumbers: snapshot.accountNumbers,
      );
      if (notices.isNotEmpty) {
        ref.read(noticesProvider.notifier).add(notices);
      }
      state = AsyncData<BankSnapshot>(snapshot);
    } on BankException {
      // A failed refresh keeps the data on screen; the next tick tries again.
    }
  }

  /// Credits an account. Throws `BankException` when the operation fails.
  Future<void> deposit({
    required String accountId,
    required String amount,
    String? description,
  }) async {
    await _repository.deposit(
      accountId: accountId,
      amount: amount,
      description: description,
    );
    state = AsyncData<BankSnapshot>(await _load());
  }

  /// Debits an account. Throws `BankException` when the operation fails.
  Future<void> withdraw({
    required String accountId,
    required String amount,
    String? description,
  }) async {
    await _repository.withdraw(
      accountId: accountId,
      amount: amount,
      description: description,
    );
    state = AsyncData<BankSnapshot>(await _load());
  }

  /// Moves money between accounts. Throws `BankException` when the operation fails.
  Future<void> transfer({
    required String sourceAccountId,
    required String targetAccountNumber,
    required String amount,
    String? description,
  }) async {
    await _repository.transfer(
      sourceAccountId: sourceAccountId,
      targetAccountNumber: targetAccountNumber,
      amount: amount,
      description: description,
    );
    state = AsyncData<BankSnapshot>(await _load());
  }

  /// Repository used by every operation.
  BankRepository get _repository => ref.read(bankRepositoryProvider);

  /// Loads accounts and movements from the repository.
  Future<BankSnapshot> _load() async {
    final List<Account> accounts = await _repository.getAccounts();
    final List<BankTransaction> transactions = await _repository
        .getTransactions();
    _seenIds.addAll(
      transactions.map((BankTransaction transaction) => transaction.id),
    );
    return BankSnapshot(accounts: accounts, transactions: transactions);
  }
}

/// Exposes the bank data to the widgets.
final AsyncNotifierProvider<BankNotifier, BankSnapshot> bankProvider =
    AsyncNotifierProvider<BankNotifier, BankSnapshot>(BankNotifier.new);
