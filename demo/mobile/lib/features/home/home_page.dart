import 'package:bankos_mobile/core/format/account_name.dart';
import 'package:bankos_mobile/app/theme.dart';
import 'package:bankos_mobile/core/format/money.dart';
import 'package:bankos_mobile/core/widgets/brand_logo.dart';
import 'package:bankos_mobile/core/widgets/transaction_tile.dart';
import 'package:bankos_mobile/data/models/account.dart';
import 'package:bankos_mobile/data/models/bank_transaction.dart';
import 'package:bankos_mobile/data/models/user_profile.dart';
import 'package:bankos_mobile/providers/bank_provider.dart';
import 'package:bankos_mobile/providers/notifications_provider.dart';
import 'package:bankos_mobile/providers/session_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Home screen: gradient header, primary balance, quick actions, accounts and movements.
class HomePage extends ConsumerWidget {
  /// Creates the home screen.
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final UserProfile? user = ref.watch(sessionProvider);
    final AsyncValue<BankSnapshot> bank = ref.watch(bankProvider);
    final int noticeCount = ref.watch(unreadNoticesCountProvider);

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        body: bank.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (Object error, StackTrace stackTrace) =>
              const Center(child: Text('No se pudieron cargar tus datos')),
          data: (BankSnapshot snapshot) => _HomeContent(
            userName: user?.fullName ?? '',
            snapshot: snapshot,
            noticeCount: noticeCount,
          ),
        ),
      ),
    );
  }
}

/// Scrollable body of the home screen once the bank data is loaded.
class _HomeContent extends StatelessWidget {
  /// Creates the body for [snapshot].
  const _HomeContent({
    required this.userName,
    required this.snapshot,
    required this.noticeCount,
  });

  /// Name shown in the greeting.
  final String userName;

  /// Accounts and movements of the user.
  final BankSnapshot snapshot;

  /// Number of unread notices, shown on the bell.
  final int noticeCount;

  @override
  Widget build(BuildContext context) {
    final double topInset = MediaQuery.of(context).padding.top;
    final bool landscape =
        MediaQuery.orientationOf(context) == Orientation.landscape;
    final double headerHeight = topInset + (landscape ? 180 : 196);
    final List<BankTransaction> recent = snapshot.transactions.take(3).toList();

    return ListView(
      padding: const EdgeInsets.only(bottom: 24),
      children: <Widget>[
        SizedBox(
          height: headerHeight + (landscape ? 200 : 186),
          child: Stack(
            children: <Widget>[
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                height: headerHeight,
                child: _Header(
                  topInset: topInset,
                  userName: userName,
                  noticeCount: noticeCount,
                ),
              ),
              if (snapshot.accounts.isNotEmpty)
                Positioned(
                  // Landscape has no room to overlap the header's subtitle.
                  top: headerHeight - (landscape ? 0 : 36),
                  left: 0,
                  right: 0,
                  height: 206,
                  child: _AccountCarousel(accounts: snapshot.accounts),
                ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            children: <Widget>[
              Expanded(
                child: _QuickAction(
                  icon: Icons.arrow_downward,
                  label: 'Depositar',
                  onTap: () => context.push('/deposit'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _QuickAction(
                  icon: Icons.arrow_upward,
                  label: 'Retirar',
                  onTap: () => context.push('/withdraw'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _QuickAction(
                  icon: Icons.swap_horiz,
                  label: 'Transferir',
                  onTap: () => context.push('/transfer'),
                  filled: true,
                ),
              ),
            ],
          ),
        ),
        _SectionTitle(
          title: 'Últimos movimientos',
          actionLabel: 'Ver todos',
          onAction: () => context.go('/transactions'),
        ),
        const SizedBox(height: 12),
        Container(
          margin: const EdgeInsets.symmetric(horizontal: 20),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Column(
            children: <Widget>[
              for (int index = 0; index < recent.length; index++) ...<Widget>[
                if (index > 0)
                  const Divider(height: 1, indent: 72, endIndent: 16),
                TransactionTile(
                  transaction: recent[index],
                  isIncoming: recent[index].isIncomingFor(
                    snapshot.accountNumbers,
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

/// Purple gradient header with the logo, the bell and the greeting.
class _Header extends StatelessWidget {
  /// Creates the header. [topInset] is the height of the status bar.
  const _Header({
    required this.topInset,
    required this.userName,
    required this.noticeCount,
  });

  /// Height of the status bar, so the content starts below it.
  final double topInset;

  /// Name shown in the greeting.
  final String userName;

  /// Number of unread notices.
  final int noticeCount;

  @override
  Widget build(BuildContext context) {
    return ClipPath(
      clipper: _HeaderClipper(),
      child: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: <Color>[Color(0xFF1C0838), Color(0xFF5A14B8)],
          ),
        ),
        padding: EdgeInsets.fromLTRB(20, topInset + 12, 20, 0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                const BankOsLogo(
                  size: 26,
                  color: Colors.white,
                  starColor: Colors.white,
                ),
                const Spacer(),
                _BellButton(count: noticeCount),
              ],
            ),
            const SizedBox(height: 22),
            Text.rich(
              TextSpan(
                text: 'Hola, ',
                style: const TextStyle(color: Colors.white, fontSize: 22),
                children: <TextSpan>[
                  TextSpan(
                    text: userName,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '¿Qué quieres hacer hoy?',
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.7),
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Rounded button with the bell and a badge for the unread notices.
class _BellButton extends StatelessWidget {
  /// Creates the bell for [count] unread notices.
  const _BellButton({required this.count});

  /// Number of unread notices.
  final int count;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(14),
      ),
      child: IconButton(
        tooltip: 'Avisos',
        onPressed: () => context.push('/notices'),
        icon: Badge(
          isLabelVisible: count > 0,
          label: Text('$count'),
          child: const Icon(Icons.notifications_outlined, color: Colors.white),
        ),
      ),
    );
  }
}

/// Card with the primary account, its balance and a hide/show toggle.
class _BalanceCard extends StatefulWidget {
  /// Creates the card for [account].
  const _BalanceCard({required this.account});

  /// Account whose balance is shown.
  final Account account;

  @override
  State<_BalanceCard> createState() => _BalanceCardState();
}

class _BalanceCardState extends State<_BalanceCard> {
  bool _visible = true;

  @override
  Widget build(BuildContext context) {
    final String number = widget.account.accountNumber;
    final String lastFour = number.length < 4
        ? number
        : number.substring(number.length - 4);
    final Color ink = Colors.white;

    return Container(
      height: 180,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: AppTheme.brandPurple.withValues(alpha: 0.15),
            blurRadius: 24,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: _cardColors(widget.account.currency),
            ),
          ),
          child: Stack(
            children: <Widget>[
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 30, 12, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                accountNameFor(widget.account.currency),
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w600,
                                  color: ink,
                                ),
                              ),
                              Text(
                                '•••• $lastFour',
                                style: TextStyle(
                                  fontSize: 13,
                                  color: ink.withValues(alpha: 0.7),
                                ),
                              ),
                            ],
                          ),
                        ),
                        _CurrencyPill(currency: widget.account.currency),
                        IconButton(
                          tooltip: _visible ? 'Ocultar saldo' : 'Mostrar saldo',
                          onPressed: () => setState(() => _visible = !_visible),
                          icon: Icon(
                            _visible
                                ? Icons.visibility_outlined
                                : Icons.visibility_off_outlined,
                            color: ink,
                          ),
                        ),
                      ],
                    ),
                    const Spacer(),
                    Padding(
                      padding: const EdgeInsets.only(bottom: 52),
                      child: Text(
                        _visible
                            ? formatMoney(
                                widget.account.balance,
                                widget.account.currency,
                              )
                            : '•••••• ${widget.account.currency}',
                        style: TextStyle(
                          fontSize: 30,
                          fontWeight: FontWeight.w800,
                          color: ink,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Positioned(
                left: 0,
                right: 0,
                bottom: 0,
                height: 64,
                child: ClipPath(
                  clipper: _WaveClipper(),
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: _waveColors(widget.account.currency),
                      ),
                    ),
                  ),
                ),
              ),
              Positioned(
                right: 18,
                bottom: 14,
                child: BankOsStar(size: 22, color: Colors.white),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// White rounded button with a purple icon, used for deposit, withdrawal and transfer.
class _QuickAction extends StatelessWidget {
  /// Creates the quick action.
  const _QuickAction({
    required this.icon,
    required this.label,
    required this.onTap,
    this.filled = false,
  });

  /// Whether the action is the highlighted one (purple background).
  final bool filled;

  /// Icon shown in the middle.
  final IconData icon;

  /// Text shown under the icon.
  final String label;

  /// Called when the user taps the card.
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final Color foreground = filled ? Colors.white : AppTheme.brandDeep;
    return Material(
      color: filled ? AppTheme.brandPurple : AppTheme.brandSoft,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16),
          child: Column(
            children: <Widget>[
              Icon(icon, size: 28, color: foreground),
              const SizedBox(height: 8),
              Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: foreground,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Section title with an optional action on the right.
class _SectionTitle extends StatelessWidget {
  /// Creates the title. The action is shown only when [actionLabel] is set.
  _SectionTitle({required this.title, this.actionLabel, this.onAction});

  /// Text of the title.
  final String title;

  /// Text of the optional action.
  final String? actionLabel;

  /// Called when the action is tapped.
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: <Widget>[
          Expanded(
            child: Text(
              title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: AppTheme.brandDeep,
              ),
            ),
          ),
          if (actionLabel != null)
            TextButton(
              onPressed: onAction,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Text(actionLabel!),
                  const Icon(Icons.chevron_right, size: 18),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

/// Header shape: a rectangle with a curved bottom edge.
class _HeaderClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    final double w = size.width;
    final double h = size.height;
    return Path()
      ..moveTo(0, 0)
      ..lineTo(w, 0)
      ..lineTo(w, h * 0.82)
      ..quadraticBezierTo(w * 0.5, h * 1.04, 0, h * 0.82)
      ..close();
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}

/// Shape of the purple wave at the bottom of the balance card.
class _WaveClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    final double w = size.width;
    final double h = size.height;
    return Path()
      ..moveTo(0, h * 0.6)
      ..cubicTo(w * 0.45, h * 0.95, w * 0.6, h * 0.05, w, h * 0.3)
      ..lineTo(w, h)
      ..lineTo(0, h)
      ..close();
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}

/// Swipeable row of balance cards, one per account, with dots for the current card.
class _AccountCarousel extends StatefulWidget {
  /// Creates the carousel for [accounts].
  const _AccountCarousel({required this.accounts});

  /// Accounts shown as cards, one page each.
  final List<Account> accounts;

  @override
  State<_AccountCarousel> createState() => _AccountCarouselState();
}

class _AccountCarouselState extends State<_AccountCarousel> {
  final PageController _controller = PageController();
  int _page = 0;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        SizedBox(
          height: 180,
          child: PageView.builder(
            controller: _controller,
            itemCount: widget.accounts.length,
            onPageChanged: (int index) => setState(() => _page = index),
            itemBuilder: (BuildContext context, int index) {
              // Side margins show the background; landscape caps the width.
              final bool landscape =
                  MediaQuery.orientationOf(context) == Orientation.landscape;
              return Center(
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    maxWidth: landscape ? 520 : double.infinity,
                  ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: _BalanceCard(account: widget.accounts[index]),
                  ),
                ),
              );
            },
          ),
        ),
        if (widget.accounts.length > 1) ...<Widget>[
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              for (int index = 0; index < widget.accounts.length; index++)
                AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  margin: const EdgeInsets.symmetric(horizontal: 3),
                  width: index == _page ? 18 : 7,
                  height: 7,
                  decoration: BoxDecoration(
                    color: index == _page
                        ? AppTheme.brandPurple
                        : AppTheme.brandSoft,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
            ],
          ),
        ],
      ],
    );
  }
}

/// Colors of the bottom wave. USD uses the inverse of EUR: a deep wave on the light card.
List<Color> _waveColors(String currency) {
  if (currency == 'USD') {
    return const <Color>[Color(0xFF4A12A0), Color(0xFF2A0B55)];
  }
  return const <Color>[AppTheme.brandPurple, Color(0xFF8A2BE2)];
}

/// Gradient of a balance card. Each currency has its own tone: purple for EUR, teal for USD.
List<Color> _cardColors(String currency) {
  if (currency == 'USD') {
    return const <Color>[AppTheme.brandPurple, Color(0xFF8A2BE2)];
  }
  return const <Color>[Color(0xFF2A0B55), Color(0xFF4A12A0)];
}

/// Small label with the currency code of an account.
class _CurrencyPill extends StatelessWidget {
  /// Creates the label for [currency].
  const _CurrencyPill({required this.currency});

  /// Currency code, such as EUR or USD.
  final String currency;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 4),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: _pillInk(currency).withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        currency,
        style: TextStyle(
          color: _pillInk(currency),
          fontSize: 12,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.6,
        ),
      ),
    );
  }
}

/// Text color of the currency label: dark purple on the light USD card, white on the EUR card.
Color _pillInk(String currency) {
  return Colors.white;
}
