import 'package:bankos_mobile/data/models/user_profile.dart';
import 'package:bankos_mobile/providers/notifications_provider.dart';
import 'package:bankos_mobile/providers/repository_provider.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Keeps the signed-in user. It is `null` when nobody is signed in.
class SessionNotifier extends Notifier<UserProfile?> {
  @override
  UserProfile? build() {
    return null;
  }

  /// Signs in and stores the user. Throws `BankException` when the credentials are wrong.
  Future<void> signIn({
    required String tenantSlug,
    required String email,
    required String password,
  }) async {
    state = await ref
        .read(bankRepositoryProvider)
        .signIn(tenantSlug: tenantSlug, email: email, password: password);
  }

  /// Forgets the token and the signed-in user.
  Future<void> signOut() async {
    await ref.read(bankRepositoryProvider).signOut();
    ref.read(noticesProvider.notifier).clear();
    state = null;
  }
}

/// Exposes the current session to the widgets.
final NotifierProvider<SessionNotifier, UserProfile?> sessionProvider =
    NotifierProvider<SessionNotifier, UserProfile?>(SessionNotifier.new);
