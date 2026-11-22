import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Scaffold with the bottom navigation bar, shown on the main tabs.
class MainShell extends StatelessWidget {
  /// Creates the shell. [location] is the current path and [child] is the active tab.
  const MainShell({super.key, required this.location, required this.child});

  /// Current path, used to highlight the selected tab.
  final String location;

  /// Screen of the active tab.
  final Widget child;

  /// Paths of the tabs, in the same order as the navigation destinations.
  static const List<String> _tabPaths = <String>[
    '/',
    '/transactions',
    '/profile',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex(),
        onDestinationSelected: (int index) => context.go(_tabPaths[index]),
        destinations: const <NavigationDestination>[
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Inicio',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long),
            label: 'Movimientos',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Perfil',
          ),
        ],
      ),
    );
  }

  /// Returns the index of the tab that matches the current location.
  int _selectedIndex() {
    final int index = _tabPaths.indexOf(location);
    return index < 0 ? 0 : index;
  }
}
