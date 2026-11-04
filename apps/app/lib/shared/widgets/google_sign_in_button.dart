import 'package:flutter/material.dart';

import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';

/// "Continue with Google", styled per Google's sign-in branding guidelines:
/// the standard multi-colour "G" on a white (light) or #131314 (dark) pill
/// with a 1 px outline, and the label in Roboto Medium.
class GoogleSignInButton extends StatelessWidget {
  const GoogleSignInButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.busy = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    final enabled = onPressed != null && !busy;
    return Semantics(
      button: true,
      enabled: enabled,
      child: Opacity(
        opacity: enabled ? 1 : 0.6,
        child: Material(
          color: c.googleSurface,
          shape: StadiumBorder(side: BorderSide(color: c.googleBorder)),
          clipBehavior: Clip.antiAlias,
          child: InkWell(
            onTap: enabled ? onPressed : null,
            child: SizedBox(
              height: SnTokens.space7 + SnTokens.space1,
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: SnTokens.space3,
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    busy
                        ? SizedBox.square(
                            dimension: SnTokens.fontSizeLg,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: c.googleText,
                            ),
                          )
                        : const SizedBox.square(
                            dimension: SnTokens.fontSizeLg,
                            child: CustomPaint(painter: _GoogleGPainter()),
                          ),
                    const SizedBox(width: SnTokens.space3),
                    Flexible(
                      child: Text(
                        label,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          // Google's guidelines ask for Roboto Medium; on
                          // Android it is the system font.
                          fontFamily: 'Roboto',
                          fontWeight: FontWeight.w500,
                          fontSize: SnTokens.fontSizeMd,
                          color: c.googleText,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// The standard Google "G" mark (48x48 artboard, scaled to the box).
class _GoogleGPainter extends CustomPainter {
  const _GoogleGPainter();

  @override
  void paint(Canvas canvas, Size size) {
    canvas.scale(size.width / 48, size.height / 48);
    final paint = Paint()..style = PaintingStyle.fill;
    final red = Path()
      ..moveTo(24.0, 9.5)
      ..cubicTo(27.54, 9.5, 30.71, 10.72, 33.21, 13.1)
      ..lineTo(40.06, 6.25)
      ..cubicTo(35.9, 2.38, 30.47, 0.0, 24.0, 0.0)
      ..cubicTo(14.62, 0.0, 6.51, 5.38, 2.56, 13.22)
      ..lineTo(10.54, 19.41)
      ..cubicTo(12.43, 13.72, 17.74, 9.5, 24.0, 9.5)
      ..close();
    final blue = Path()
      ..moveTo(46.98, 24.55)
      ..cubicTo(46.98, 22.98, 46.83, 21.46, 46.6, 20.0)
      ..lineTo(24.0, 20.0)
      ..lineTo(24.0, 29.02)
      ..lineTo(36.94, 29.02)
      ..cubicTo(36.36, 31.98, 34.68, 34.5, 32.16, 36.2)
      ..lineTo(39.89, 42.2)
      ..cubicTo(44.4, 38.02, 46.98, 31.84, 46.98, 24.55)
      ..close();
    final yellow = Path()
      ..moveTo(10.53, 28.59)
      ..cubicTo(10.05, 27.14, 9.77, 25.6, 9.77, 24.0)
      ..cubicTo(9.77, 22.4, 10.04, 20.86, 10.53, 19.41)
      ..lineTo(2.55, 13.22)
      ..cubicTo(0.92, 16.46, 0.0, 20.12, 0.0, 24.0)
      ..cubicTo(0.0, 27.88, 0.92, 31.54, 2.56, 34.78)
      ..lineTo(10.53, 28.59)
      ..close();
    final green = Path()
      ..moveTo(24.0, 48.0)
      ..cubicTo(30.48, 48.0, 35.93, 45.87, 39.89, 42.19)
      ..lineTo(32.16, 36.19)
      ..cubicTo(30.01, 37.64, 27.24, 38.49, 24.0, 38.49)
      ..cubicTo(17.74, 38.49, 12.43, 34.27, 10.53, 28.58)
      ..lineTo(2.55, 34.77)
      ..cubicTo(6.51, 42.62, 14.62, 48.0, 24.0, 48.0)
      ..close();
    canvas
      ..drawPath(red, paint..color = SnTokens.googleRed)
      ..drawPath(blue, paint..color = SnTokens.googleBlue)
      ..drawPath(yellow, paint..color = SnTokens.googleYellow)
      ..drawPath(green, paint..color = SnTokens.googleGreen);
  }

  @override
  bool shouldRepaint(_GoogleGPainter oldDelegate) => false;
}
