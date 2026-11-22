import 'package:bankos_mobile/app/app.dart';
import 'package:bankos_mobile/data/fake_bank_repository.dart';
import 'package:bankos_mobile/providers/notifications_provider.dart';
import 'package:bankos_mobile/providers/repository_provider.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  /// Starts the app with a repository that does not wait, so tests stay fast.
  Future<void> pumpApp(WidgetTester tester) {
    return tester.pumpWidget(
      ProviderScope(
        overrides: [
          bankRepositoryProvider.overrideWithValue(
            FakeBankRepository(latency: Duration.zero),
          ),
          pollIntervalProvider.overrideWithValue(Duration.zero),
        ],
        child: const BankOsApp(),
      ),
    );
  }

  testWidgets('shows the login screen first', (WidgetTester tester) async {
    await pumpApp(tester);
    await tester.pumpAndSettle();

    expect(find.text('Iniciar sesión'), findsOneWidget);
  });

  testWidgets('signs in and opens the deposit screen from the home actions', (
    WidgetTester tester,
  ) async {
    await pumpApp(tester);
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.text('Iniciar sesión'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Iniciar sesión'));
    await tester.pumpAndSettle();
    expect(find.text('Últimos movimientos'), findsOneWidget);

    await tester.tap(find.text('Depositar'));
    await tester.pumpAndSettle();
    expect(find.text('Nuevo depósito'), findsOneWidget);
  });
}
