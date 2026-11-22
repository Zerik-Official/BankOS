import 'package:flutter/material.dart';

/// Four-pointed star that forms the BankOS mark. Drawn with code, so no image asset is needed.
class BankOsStar extends StatelessWidget {
  /// Creates the star with the given [size] and [color].
  const BankOsStar({super.key, required this.size, required this.color});

  /// Width and height of the square the star is drawn in.
  final double size;

  /// Fill color of the star.
  final Color color;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size.square(size),
      painter: _StarPainter(color: color),
    );
  }
}

/// Star mark next to the BankOS wordmark.
class BankOsLogo extends StatelessWidget {
  /// Creates the logo. [size] sets the height of the star; the text scales with it.
  const BankOsLogo({
    super.key,
    this.size = 28,
    this.color = const Color(0xFF3F0072),
    this.starColor = const Color(0xFF6A00D4),
  });

  /// Height of the star. The wordmark is sized from it.
  final double size;

  /// Color of the BankOS wordmark.
  final Color color;

  /// Color of the star.
  final Color starColor;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        BankOsStar(size: size, color: starColor),
        SizedBox(width: size * 0.3),
        Text(
          'BankOS',
          style: TextStyle(
            fontSize: size * 0.9,
            fontWeight: FontWeight.w700,
            letterSpacing: -0.5,
            color: color,
          ),
        ),
      ],
    );
  }
}

/// Paints the four-pointed star with concave sides.
class _StarPainter extends CustomPainter {
  /// Creates the painter for the given [color].
  const _StarPainter({required this.color});

  /// Fill color of the star.
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final double cx = size.width / 2;
    final double cy = size.height / 2;
    final double r = size.width / 2;
    final double d = r * 0.18;

    final Path path = Path()
      ..moveTo(cx, cy - r)
      ..quadraticBezierTo(cx + d, cy - d, cx + r, cy)
      ..quadraticBezierTo(cx + d, cy + d, cx, cy + r)
      ..quadraticBezierTo(cx - d, cy + d, cx - r, cy)
      ..quadraticBezierTo(cx - d, cy - d, cx, cy - r)
      ..close();

    canvas.drawPath(path, Paint()..color = color);
  }

  @override
  bool shouldRepaint(covariant _StarPainter oldDelegate) {
    return oldDelegate.color != color;
  }
}
