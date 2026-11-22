import 'package:flutter/material.dart';

/// Round icon with a label below it, used for the quick actions on the home screen.
class ActionButton extends StatelessWidget {
  /// Creates a quick action.
  const ActionButton({
    super.key,
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  /// Icon shown inside the circle.
  final IconData icon;

  /// Text shown below the circle.
  final String label;

  /// Called when the user taps the button.
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onPressed,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            CircleAvatar(
              radius: 26,
              backgroundColor: theme.colorScheme.primary,
              child: Icon(icon, color: theme.colorScheme.onPrimary),
            ),
            const SizedBox(height: 8),
            Text(label, style: theme.textTheme.labelLarge),
          ],
        ),
      ),
    );
  }
}
