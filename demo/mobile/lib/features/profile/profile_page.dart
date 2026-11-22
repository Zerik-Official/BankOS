import 'package:bankos_mobile/app/theme.dart';
import 'package:bankos_mobile/core/widgets/brand_logo.dart';
import 'package:bankos_mobile/data/models/user_profile.dart';
import 'package:bankos_mobile/providers/session_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Profile screen: purple header, the user card, the account data and the sign-out button.
class ProfilePage extends ConsumerWidget {
  /// Creates the profile screen.
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final UserProfile? user = ref.watch(sessionProvider);
    final double topInset = MediaQuery.of(context).padding.top;

    return Scaffold(
      body: SingleChildScrollView(
        child: Column(
          children: <Widget>[
            ClipPath(
              clipper: _HeaderClipper(),
              child: Container(
                width: double.infinity,
                padding: EdgeInsets.fromLTRB(20, topInset + 16, 20, 80),
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: <Color>[AppTheme.brandDeep, AppTheme.brandPurple],
                  ),
                ),
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
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
                    SizedBox(height: 18),
                    Text(
                      'Perfil',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 30,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            Transform.translate(
              offset: const Offset(0, -56),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  children: <Widget>[
                    _UserCard(user: user),
                    const SizedBox(height: 16),
                    _InfoCard(user: user),
                    const SizedBox(height: 20),
                    _SignOutButton(
                      onPressed: () async {
                        await ref.read(sessionProvider.notifier).signOut();
                        if (context.mounted) {
                          context.go('/login');
                        }
                      },
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Card with the round avatar, the name and the role of the user.
class _UserCard extends StatelessWidget {
  /// Creates the card for [user].
  const _UserCard({required this.user});

  /// Signed-in user, or null while nobody is signed in.
  final UserProfile? user;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[Colors.white, Color(0xFFF1EAFF)],
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: AppTheme.brandPurple.withValues(alpha: 0.10),
            blurRadius: 24,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Row(
        children: <Widget>[
          CircleAvatar(
            radius: 36,
            backgroundColor: AppTheme.brandPurple,
            child: Text(
              _initials(user?.fullName ?? ''),
              style: const TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  user?.fullName ?? '',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.brandDeep,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _roleLabel(user?.role ?? ''),
                  style: const TextStyle(fontSize: 14, color: Colors.black54),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Returns the initials of a full name, such as "AD" for "Alice Demo".
  String _initials(String fullName) {
    final List<String> words = fullName.trim().split(RegExp(r'\s+'));
    final String first = words.isNotEmpty && words.first.isNotEmpty
        ? words.first[0]
        : '';
    final String second = words.length > 1 && words[1].isNotEmpty
        ? words[1][0]
        : '';
    return (first + second).toUpperCase();
  }

  /// Spanish label of the role stored in the backend.
  String _roleLabel(String role) {
    return role == 'client' ? 'Cliente' : 'Administrador';
  }
}

/// White card with the account data, one row per field.
class _InfoCard extends StatelessWidget {
  /// Creates the card for [user].
  const _InfoCard({required this.user});

  /// Signed-in user, or null while nobody is signed in.
  final UserProfile? user;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: <Widget>[
          _InfoRow(
            icon: Icons.mail_outline,
            label: 'Correo electrónico',
            value: user?.email ?? '',
          ),
          const Divider(height: 1, indent: 72, endIndent: 16),
          _InfoRow(
            icon: Icons.account_balance_outlined,
            label: 'Entidad',
            value: user?.tenantSlug ?? '',
          ),
          const Divider(height: 1, indent: 72, endIndent: 16),
          _InfoRow(
            icon: Icons.badge_outlined,
            label: 'Rol',
            value: user?.role == 'client' ? 'Cliente' : 'Administrador',
          ),
        ],
      ),
    );
  }
}

/// One row of the account card: an icon, a label and its value.
class _InfoRow extends StatelessWidget {
  /// Creates the row.
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  /// Icon shown on the left.
  final IconData icon;

  /// Name of the field.
  final String label;

  /// Value of the field.
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: <Widget>[
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AppTheme.brandSoft,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: AppTheme.brandPurple, size: 20),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  label,
                  style: const TextStyle(fontSize: 13, color: Colors.black54),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.brandDeep,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Full-width soft button that signs the user out.
class _SignOutButton extends StatelessWidget {
  /// Creates the button. [onPressed] runs when the user taps it.
  const _SignOutButton({required this.onPressed});

  /// Called when the user taps the button.
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppTheme.brandSoft,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onPressed,
        child: const SizedBox(
          height: 56,
          width: double.infinity,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Icon(Icons.logout, color: AppTheme.brandPurple),
              SizedBox(width: 10),
              Text(
                'Cerrar sesión',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.brandPurple,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
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
