import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../core/theme/sn_colors.dart';

/// The sign-in hero: a food pack under a magnifying glass, with three
/// family figures, drawn with shapes in the brand palette (no image asset,
/// so it stays sharp at any size and follows the dark theme).
class BrandHeroIllustration extends StatelessWidget {
  const BrandHeroIllustration({super.key, this.height = 220});

  final double height;

  @override
  Widget build(BuildContext context) => ExcludeSemantics(
    child: SizedBox(
      height: height,
      width: double.infinity,
      child: CustomPaint(painter: _HeroPainter(SnColors.of(context))),
    ),
  );
}

class _HeroPainter extends CustomPainter {
  _HeroPainter(this.c);

  final SnColors c;

  @override
  void paint(Canvas canvas, Size size) {
    // Draw in a square that fits the box, centred.
    final s = math.min(size.width, size.height);
    canvas.save();
    canvas.translate((size.width - s) / 2, (size.height - s) / 2);
    Offset p(double x, double y) => Offset(x * s, y * s);
    final fill = Paint()..style = PaintingStyle.fill;

    // Backdrop blob and confetti dots.
    canvas.drawCircle(p(0.5, 0.52), s * 0.44, fill..color = c.brandSoft);
    canvas.drawCircle(p(0.12, 0.22), s * 0.035, fill..color = c.accentWarm);
    canvas.drawCircle(p(0.9, 0.3), s * 0.025, fill..color = c.brand);
    canvas.drawCircle(p(0.84, 0.86), s * 0.03, fill..color = c.accentWarm);
    canvas.drawCircle(p(0.16, 0.8), s * 0.02, fill..color = c.brand);

    // The food pack, tilted.
    canvas.save();
    canvas.translate(s * 0.42, s * 0.5);
    canvas.rotate(-0.14);
    final pack = RRect.fromRectAndRadius(
      Rect.fromCenter(center: Offset.zero, width: s * 0.36, height: s * 0.5),
      Radius.circular(s * 0.05),
    );
    canvas.drawRRect(
      pack.shift(Offset(s * 0.015, s * 0.02)),
      fill..color = c.brandStrong.withValues(alpha: 0.18),
    );
    canvas.drawRRect(pack, fill..color = c.accentWarm);
    // Crimped top band.
    canvas.drawRRect(
      RRect.fromRectAndCorners(
        Rect.fromLTWH(-s * 0.18, -s * 0.25, s * 0.36, s * 0.07),
        topLeft: Radius.circular(s * 0.05),
        topRight: Radius.circular(s * 0.05),
      ),
      fill..color = c.brand,
    );
    // Label panel with text lines and a barcode.
    final label = RRect.fromRectAndRadius(
      Rect.fromLTWH(-s * 0.13, -s * 0.13, s * 0.26, s * 0.3),
      Radius.circular(s * 0.025),
    );
    canvas.drawRRect(label, fill..color = c.surface);
    final line = Paint()
      ..color = c.borderStrong
      ..strokeWidth = s * 0.018
      ..strokeCap = StrokeCap.round;
    for (final (y, w) in [(-0.08, 0.17), (-0.04, 0.12), (0.0, 0.15)]) {
      canvas.drawLine(
        Offset(-s * 0.09, s * y),
        Offset(-s * 0.09 + s * w, s * y),
        line,
      );
    }
    final bar = Paint()..color = c.textPrimary;
    var x = -s * 0.09;
    for (final w in [2, 1, 3, 1, 2, 1, 1, 3, 2, 1, 2]) {
      final bw = s * 0.004 * w;
      canvas.drawRect(Rect.fromLTWH(x, s * 0.05, bw, s * 0.08), bar);
      x += bw + s * 0.006;
    }
    canvas.restore();

    // Magnifying glass over the label.
    final lensCentre = p(0.64, 0.4);
    final lensR = s * 0.15;
    canvas.drawCircle(
      lensCentre,
      lensR,
      fill..color = c.surface.withValues(alpha: 0.55),
    );
    final ring = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = s * 0.035
      ..color = c.brand;
    canvas.drawCircle(lensCentre, lensR, ring);
    final handle = Paint()
      ..strokeWidth = s * 0.05
      ..strokeCap = StrokeCap.round
      ..color = c.brandStrong;
    final dir = Offset(math.cos(math.pi / 4), math.sin(math.pi / 4));
    canvas.drawLine(
      lensCentre + dir * (lensR + s * 0.02),
      lensCentre + dir * (lensR + s * 0.14),
      handle,
    );

    // Three family figures inside the lens.
    for (final (dx, r, color) in [
      (-0.06, 0.028, c.brand),
      (0.0, 0.034, c.brandStrong),
      (0.06, 0.024, c.accentWarm),
    ]) {
      final head = lensCentre + Offset(s * dx, -s * 0.03);
      canvas.drawCircle(head, s * r * 0.75, fill..color = color);
      canvas.drawArc(
        Rect.fromCenter(
          center: head + Offset(0, s * r * 2.1),
          width: s * r * 2.4,
          height: s * r * 2.4,
        ),
        math.pi,
        math.pi,
        true,
        fill..color = color,
      );
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(_HeroPainter old) => old.c != c;
}
