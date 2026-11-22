import 'package:bankos_mobile/app/router.dart';
import 'package:bankos_mobile/app/theme.dart';
import 'package:bankos_mobile/providers/notifications_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Lets notices show a snackbar from outside the page that is on screen.
final GlobalKey<ScaffoldMessengerState> _messengerKey =
    GlobalKey<ScaffoldMessengerState>();

/// Root widget of the BankOS demo app.
class BankOsApp extends ConsumerWidget {
  /// Creates the app.
  const BankOsApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final GoRouter router = ref.watch(routerProvider);
    ref.listen<List<AppNotice>>(noticesProvider, (
      List<AppNotice>? previous,
      List<AppNotice> next,
    ) {
      final int before = previous?.length ?? 0;
      if (next.length <= before) {
        return;
      }
      final AppNotice latest = next.first;
      _messengerKey.currentState?.showSnackBar(
        SnackBar(content: Text('${latest.title}. ${latest.body}')),
      );
    });
    return MaterialApp.router(
      title: 'BankOS',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      scaffoldMessengerKey: _messengerKey,
      scrollBehavior: MaterialScrollBehavior().copyWith(overscroll: false),
      builder: (BuildContext context, Widget? child) {
        // Portrait phones get a centered 480 px column; landscape uses the full width.
        final bool landscape =
            MediaQuery.orientationOf(context) == Orientation.landscape;
        return ColoredBox(
          color: const Color(0xFF140821),
          child: Center(
            child: ConstrainedBox(
              constraints: BoxConstraints(
                maxWidth: landscape ? double.infinity : 480,
              ),
              child: child,
            ),
          ),
        );
      },
      routerConfig: router,
    );
  }
}
