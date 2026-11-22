import 'package:bankos_mobile/data/models/bank_transaction.dart';
import 'package:bankos_mobile/providers/notifications_provider.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

BankTransaction _movement({
  required String id,
  required String type,
  String status = 'success',
  String? source,
  String? target,
}) {
  return BankTransaction(
    id: id,
    type: type,
    status: status,
    amount: '20.00',
    currency: 'EUR',
    fee: '0.00',
    createdAt: DateTime.utc(2026, 11, 19, 9, 30),
    sourceAccountNumber: source,
    targetAccountNumber: target,
  );
}

void main() {
  const Set<String> mine = <String>{'111111111111', '222222222222'};

  test('an incoming transfer from someone else creates one notice', () {
    final List<AppNotice> notices = newMovementNotices(
      seenIds: <String>{},
      ownAccountNumbers: mine,
      transactions: <BankTransaction>[
        _movement(
          id: 'a',
          type: 'transfer',
          source: '999988887777',
          target: '111111111111',
        ),
      ],
    );

    expect(notices, hasLength(1));
    expect(notices.single.title, 'Has recibido 20.00 EUR');
    expect(
      notices.single.body,
      'Transferencia desde la cuenta terminada en 7777',
    );
  });

  test('movements already seen or failed do not create notices', () {
    final List<AppNotice> notices = newMovementNotices(
      seenIds: <String>{'seen'},
      ownAccountNumbers: mine,
      transactions: <BankTransaction>[
        _movement(
          id: 'seen',
          type: 'transfer',
          source: '999988887777',
          target: '111111111111',
        ),
        _movement(
          id: 'failed',
          type: 'transfer',
          status: 'error',
          source: '999988887777',
          target: '111111111111',
        ),
      ],
    );

    expect(notices, isEmpty);
  });

  test('money sent to someone outside the user creates a sent notice', () {
    final List<AppNotice> notices = newMovementNotices(
      seenIds: <String>{},
      ownAccountNumbers: mine,
      transactions: <BankTransaction>[
        _movement(
          id: 'out',
          type: 'transfer',
          source: '111111111111',
          target: '999988887777',
        ),
        _movement(id: 'wd', type: 'withdrawal', source: '222222222222'),
      ],
    );

    expect(notices, hasLength(2));
    expect(notices.every((AppNotice n) => !n.isIncoming), isTrue);
    expect(notices.first.title, 'Has enviado 20.00 EUR');
    expect(notices.first.body, 'Transferencia a la cuenta terminada en 7777');
    expect(notices.last.body, 'Retiro de tu cuenta');
  });

  test('transfers between the user own accounts create no notice', () {
    final List<AppNotice> notices = newMovementNotices(
      seenIds: <String>{},
      ownAccountNumbers: mine,
      transactions: <BankTransaction>[
        _movement(
          id: 'own',
          type: 'transfer',
          source: '111111111111',
          target: '222222222222',
        ),
      ],
    );

    expect(notices, isEmpty);
  });

  test('a deposit into an own account is described as a deposit', () {
    final List<AppNotice> notices = newMovementNotices(
      seenIds: <String>{},
      ownAccountNumbers: mine,
      transactions: <BankTransaction>[
        _movement(id: 'd', type: 'deposit', target: '111111111111'),
      ],
    );

    expect(notices.single.body, 'Ingreso en tu cuenta');
  });

  test('the notices provider keeps the newest notice first', () {
    final ProviderContainer container = ProviderContainer();
    addTearDown(container.dispose);
    final NoticesNotifier notifier = container.read(noticesProvider.notifier);
    final AppNotice older = AppNotice(
      id: 'old',
      title: 'antiguo',
      body: '',
      receivedAt: DateTime.utc(2026, 11, 19),
    );
    final AppNotice newer = AppNotice(
      id: 'new',
      title: 'nuevo',
      body: '',
      receivedAt: DateTime.utc(2026, 11, 19, 1),
    );

    notifier.add(<AppNotice>[older]);
    notifier.add(<AppNotice>[newer]);
    expect(container.read(noticesProvider).first.title, 'nuevo');
  });

  test('marking one notice as read keeps it and only changes that one', () {
    final ProviderContainer container = ProviderContainer();
    addTearDown(container.dispose);
    final NoticesNotifier notifier = container.read(noticesProvider.notifier);
    notifier.add(<AppNotice>[
      AppNotice(id: 'a', title: 'a', body: '', receivedAt: DateTime.utc(2026)),
      AppNotice(id: 'b', title: 'b', body: '', receivedAt: DateTime.utc(2026)),
    ]);

    notifier.markAsRead('a');

    final List<AppNotice> notices = container.read(noticesProvider);
    expect(notices, hasLength(2));
    expect(notices.firstWhere((AppNotice n) => n.id == 'a').isRead, isTrue);
    expect(notices.firstWhere((AppNotice n) => n.id == 'b').isRead, isFalse);
  });

  test('the badge counts only the notices that are still unread', () {
    final ProviderContainer container = ProviderContainer();
    addTearDown(container.dispose);
    final NoticesNotifier notifier = container.read(noticesProvider.notifier);
    notifier.add(<AppNotice>[
      AppNotice(id: 'a', title: 'a', body: '', receivedAt: DateTime.utc(2026)),
      AppNotice(id: 'b', title: 'b', body: '', receivedAt: DateTime.utc(2026)),
    ]);
    expect(container.read(unreadNoticesCountProvider), 2);

    notifier.markAsRead('a');
    expect(container.read(unreadNoticesCountProvider), 1);

    notifier.markAllAsRead();
    expect(container.read(unreadNoticesCountProvider), 0);
    expect(container.read(noticesProvider), hasLength(2));
  });
}
